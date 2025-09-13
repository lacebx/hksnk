import pygame
import sys
import random
import time
import asyncio

# Initialize Pygame
pygame.init()

# Constants
WIDTH = 600
HEIGHT = 400
GRID_SIZE = 20
GRID_WIDTH = WIDTH // GRID_SIZE   # 30
GRID_HEIGHT = HEIGHT // GRID_SIZE  # 20

# Colors
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)
DARK_GREEN = (0, 50, 0)    # Level 1 background
DARK_BLUE = (0, 0, 50)     # Level 2 background
DARK_RED = (50, 0, 0)      # Level 3 background
GREEN = (0, 255, 0)        # Level 1 traces
BLUE = (0, 0, 255)         # Level 2 traces
RED = (255, 0, 0)          # Level 3 traces
GRAY = (50, 50, 50)        # Grid lines

# ---------------------------------------------------------------------
# Maze generation functions to create maze-like walls
# ---------------------------------------------------------------------

def generate_maze_value(cols, rows):
    """
    Generate a maze grid (list of lists). 
    Each cell is 0 (path) or 1 (wall). This uses recursive backtracking.
    Ensure cols and rows are odd.
    """
    if cols % 2 == 0:
        cols -= 1
    if rows % 2 == 0:
        rows -= 1
    # Start with every cell as a wall.
    maze = [[1 for _ in range(cols)] for _ in range(rows)]
    # Begin at (0,0)
    maze[0][0] = 0
    stack = [(0, 0)]
    directions = [(2, 0), (-2, 0), (0, 2), (0, -2)]
    while stack:
        cx, cy = stack[-1]
        neighbors = []
        for dx, dy in directions:
            nx, ny = cx + dx, cy + dy
            if 0 <= nx < cols and 0 <= ny < rows and maze[ny][nx] == 1:
                neighbors.append((nx, ny, dx, dy))
        if neighbors:
            nx, ny, dx, dy = random.choice(neighbors)
            maze[ny][nx] = 0
            maze[cy + dy//2][cx + dx//2] = 0  # remove wall between current and neighbor
            stack.append((nx, ny))
        else:
            stack.pop()
    return maze

def generate_maze_walls():
    """
    Generate the maze and convert wall cells into a list of (x,y) coordinates.
    The maze is centered on the available grid.
    """
    # Use an odd number of cells for maze generation
    maze_cols = GRID_WIDTH if GRID_WIDTH % 2 == 1 else GRID_WIDTH - 1
    maze_rows = GRID_HEIGHT if GRID_HEIGHT % 2 == 1 else GRID_HEIGHT - 1
    maze = generate_maze_value(maze_cols, maze_rows)
    # Center the maze in the full grid
    offset_x = ((GRID_WIDTH - maze_cols) // 2) * GRID_SIZE
    offset_y = ((GRID_HEIGHT - maze_rows) // 2) * GRID_SIZE
    walls = []
    for j in range(maze_rows):
        for i in range(maze_cols):
            if maze[j][i] == 1:  # wall cell
                walls.append((i * GRID_SIZE + offset_x, j * GRID_SIZE + offset_y))
    return walls

def generate_level_maze(level):
    """
    For different levels, tweak the maze walls:
      - Level 0 (Easy): Remove about 30% of the walls to open up the maze.
      - Level 1 (Medium): Use the generated maze as is.
      - Level 2 (Hard): Add extra random walls to create additional obstacles.
    """
    base_walls = generate_maze_walls()
    if level == 0:
        # Remove some walls to lighten the maze
        easy_walls = [w for w in base_walls if random.random() > 0.3]
        return easy_walls
    elif level == 1:
        return base_walls
    elif level == 2:
        extra_walls = list(base_walls)
        additional = int(len(base_walls) * 0.2)
        for _ in range(additional):
            x = random.randrange(0, GRID_WIDTH) * GRID_SIZE
            y = random.randrange(0, GRID_HEIGHT) * GRID_SIZE
            if (x, y) not in extra_walls:
                extra_walls.append((x, y))
        return extra_walls

def get_exit(walls):
    """
    Scan the grid (in cell steps) for a free (not wall) cell and
    choose the one farthest from the snake's starting point.
    """
    free_cells = []
    for x in range(0, WIDTH, GRID_SIZE):
        for y in range(0, HEIGHT, GRID_SIZE):
            if (x, y) not in walls:
                free_cells.append((x, y))
    if not free_cells:
        return (WIDTH - GRID_SIZE, HEIGHT - GRID_SIZE)
    start = (100, 100)
    best_cell = max(free_cells, key=lambda cell: (cell[0]-start[0])**2 + (cell[1]-start[1])**2)
    return best_cell

# Level settings
# Instead of fixed wall patterns, we now generate maze-like walls.
level_walls = [
    generate_level_maze(0),  # Easy: more open maze
    generate_level_maze(1),  # Medium: perfect maze
    generate_level_maze(2)   # Hard: maze plus extra obstacles
]

level_colors = [GREEN, BLUE, RED]               # Trace colors
level_backgrounds = [DARK_GREEN, DARK_BLUE, DARK_RED]  # Background tints
level_diagonals = [False, True, True]             # Whether to draw diagonal traces
level_components = [3, 6, 10]                     # Number of component-like rectangles

# Function to draw the circuit board background
def draw_circuit_board(screen, walls, color, background_color, diagonals_enabled, num_components):
    # Draw grid background
    screen.fill(background_color)
    for x in range(0, WIDTH, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (x, 0), (x, HEIGHT), 1)
    for y in range(0, HEIGHT, GRID_SIZE):
        pygame.draw.line(screen, GRAY, (0, y), (WIDTH, y), 1)
    
    wall_set = set(walls)
    drawn_lines = set()  # to prevent drawing duplicate lines
    
    # Draw solder points and traces between walls
    for wall in walls:
        x, y = wall
        center = (x + GRID_SIZE // 2, y + GRID_SIZE // 2)
        pygame.draw.circle(screen, color, center, 4)
        
        # Check adjacent connections (horizontal/vertical plus diagonals if enabled)
        directions = [(GRID_SIZE, 0), (-GRID_SIZE, 0), (0, GRID_SIZE), (0, -GRID_SIZE)]
        if diagonals_enabled:
            directions += [(GRID_SIZE, GRID_SIZE), (-GRID_SIZE, -GRID_SIZE),
                           (GRID_SIZE, -GRID_SIZE), (-GRID_SIZE, GRID_SIZE)]
        for dx, dy in directions:
            neighbor = (x + dx, y + dy)
            if neighbor in wall_set:
                neighbor_center = (neighbor[0] + GRID_SIZE // 2, neighbor[1] + GRID_SIZE // 2)
                line = tuple(sorted([center, neighbor_center]))
                if line not in drawn_lines:
                    pygame.draw.line(screen, color, center, neighbor_center, 3)
                    drawn_lines.add(line)
    
    # Draw random components (small rectangles) on some wall cells
    component_spots = random.sample(walls, min(num_components, len(walls)))
    for spot in component_spots:
        pygame.draw.rect(screen, color, (spot[0] + 5, spot[1] + 5, 10, 10))

# Set up the display
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Snake with Maze-like Circuit Board")
clock = pygame.time.Clock()

# Game state variables
current_level = 0
walls = level_walls[current_level]
color = level_colors[current_level]
background_color = level_backgrounds[current_level]
diagonals_enabled = level_diagonals[current_level]
num_components = level_components[current_level]
snake = [(100, 100)]
direction = (GRID_SIZE, 0)
exit_pos = get_exit(walls)
font = pygame.font.SysFont(None, 48)

async def main():
    global current_level, walls, color, background_color, diagonals_enabled, num_components, snake, direction, exit_pos
    
    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP and direction != (0, GRID_SIZE):
                    direction = (0, -GRID_SIZE)
                elif event.key == pygame.K_DOWN and direction != (0, -GRID_SIZE):
                    direction = (0, GRID_SIZE)
                elif event.key == pygame.K_LEFT and direction != (GRID_SIZE, 0):
                    direction = (-GRID_SIZE, 0)
                elif event.key == pygame.K_RIGHT and direction != (-GRID_SIZE, 0):
                    direction = (GRID_SIZE, 0)

        # Move the snake
        new_head = (snake[0][0] + direction[0], snake[0][1] + direction[1])
        
        # Check collision with walls or borders
        if (new_head in walls or
            new_head[0] < 0 or new_head[0] >= WIDTH or
            new_head[1] < 0 or new_head[1] >= HEIGHT):
            snake = [(100, 100)]
            direction = (GRID_SIZE, 0)
        else:
            snake = [new_head] + snake[:-1]

        # Check if reached the exit
        if new_head == exit_pos:
            text = font.render("Hacked!", True, color)
            screen.blit(text, (WIDTH // 2 - 50, HEIGHT // 2))
            pygame.display.flip()
            await asyncio.sleep(1)
            
            current_level += 1
            if current_level < len(level_walls):
                walls = level_walls[current_level]
                color = level_colors[current_level]
                background_color = level_backgrounds[current_level]
                diagonals_enabled = level_diagonals[current_level]
                num_components = level_components[current_level]
                snake = [(100, 100)]
                direction = (GRID_SIZE, 0)
                exit_pos = get_exit(walls)
            else:
                text = font.render("All levels complete!", True, WHITE)
                screen.blit(text, (WIDTH // 2 - 100, HEIGHT // 2))
                pygame.display.flip()
                await asyncio.sleep(2)
                pygame.quit()
                sys.exit()

        # Draw everything
        draw_circuit_board(screen, walls, color, background_color, diagonals_enabled, num_components)
        for segment in snake:
            pygame.draw.rect(screen, GREEN, (segment[0], segment[1], GRID_SIZE, GRID_SIZE))
        pygame.draw.rect(screen, WHITE, (exit_pos[0], exit_pos[1], GRID_SIZE, GRID_SIZE))
        
        level_text = font.render(f"Level {current_level + 1}", True, WHITE)
        screen.blit(level_text, (10, 10))
        
        pygame.display.flip()
        # Slow down movement by approximately 30% (from 15 FPS to about 11 FPS)
        clock.tick(11)
        await asyncio.sleep(0)

if __name__ == "__main__":
    asyncio.run(main())
