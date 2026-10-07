import pygame
import time
import json
from game.maze import generate_maze, CELL
from game.player import Player

FPS = 60
BG = (240, 235, 220)
WALL_COLOR = (40, 40, 60)
EXIT_COLOR = (80, 200, 80)
FOG_COLOR = (0, 0, 0, 210)
FOG_RADIUS = 3
LEADERBOARD_FILE = "leaderboard.json"
MAX_SCORES = 5
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
        self.leaderboard = self.load_leaderboard()
        self.reset()

    def load_leaderboard(self):
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as f:
                scores = json.load(f)
            if not isinstance(scores, list):
                return []
            return sorted(float(score) for score in scores)[:MAX_SCORES]
        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            return []

    def save_leaderboard(self):
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as f:
            json.dump(self.leaderboard, f, indent=2)

    def add_score(self, score):
        self.leaderboard.append(round(score, 3))
        self.leaderboard.sort()
        self.leaderboard = self.leaderboard[:MAX_SCORES]
        self.save_leaderboard()

    def reset(self):
        self.walls = generate_maze(COLS, ROWS)
        self.player = Player(0, 0)
        self.exit_rect = pygame.Rect((COLS-1)*CELL+5, (ROWS-1)*CELL+5, CELL-10, CELL-10)
        self.start_time = time.time()
        self.elapsed = 0
        self.won = False
        self.score_saved = False
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
            if not self.score_saved:
                self.add_score(self.elapsed)
                self.score_saved = True

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