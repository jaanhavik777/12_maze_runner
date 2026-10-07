import pygame
import time
from game.maze import generate_maze, CELL
from game.player import Player

FPS = 60
BG = (240, 235, 220)
WALL_COLOR = (40, 40, 60)
EXIT_COLOR = (80, 200, 80)
FOG_COLOR = (0, 0, 0, 210)
FOG_RADIUS = 3
COLS, ROWS = 15, 13

WIDTH = COLS * CELL
HEIGHT = ROWS * CELL + 60

class GameEngine:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((WIDTH, HEIGHT))
        pygame.display.set_caption("Maze Runner")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.big_font = pygame.font.SysFont("monospace", 36, bold=True)
        self.reset()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.player = Player(0, 0)
        self.exit_rect = pygame.Rect((COLS-1)*CELL+5, (ROWS-1)*CELL+5, CELL-10, CELL-10)
        self.start_time = time.time()
        self.elapsed = 0
        self.won = False
        self.show_solution = False
        self.solution_path = self._bfs_shortest_path()

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()
                elif event.key == pygame.K_h:
                    self.show_solution = not self.show_solution
        return True

    def update(self):
        if self.won:
            return
        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, ROWS, COLS)
        self.elapsed = time.time() - self.start_time
        if self.player.rect.colliderect(self.exit_rect):
            self.won = True

    def _bfs_shortest_path(self):
        """Return the shortest path from the start cell to the exit using BFS."""
        start = (0, 0)
        goal = (ROWS - 1, COLS - 1)

        # Each cell stores [N, S, E, W]. False means that side is open.
        directions = [
            (-1, 0, 0),  # North
            (1, 0, 1),   # South
            (0, 1, 2),   # East
            (0, -1, 3),  # West
        ]

        queue = [start]
        parent = {start: None}

        while queue:
            current = queue.pop(0)
            if current == goal:
                break

            r, c = current
            for dr, dc, wall_dir in directions:
                nr, nc = r + dr, c + dc

                if not (0 <= nr < ROWS and 0 <= nc < COLS):
                    continue
                if self.walls[r][c][wall_dir]:
                    continue

                neighbor = (nr, nc)
                if neighbor not in parent:
                    parent[neighbor] = current
                    queue.append(neighbor)

        if goal not in parent:
            return []

        path = []
        current = goal