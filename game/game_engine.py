import json
import os
import time
from collections import deque

import pygame

from game.maze import generate_maze, CELL
from game.player import Player


FPS = 60

BG = (240, 235, 220)
WALL_COLOR = (40, 40, 60)
EXIT_COLOR = (80, 200, 80)
FOG_COLOR = (0, 0, 0, 210)
PATH_COLOR = (255, 210, 60)

FOG_RADIUS = 3
LEADERBOARD_FILE = "leaderboard.json"
MAX_SCORES = 5

DIFFICULTIES = {
    "Easy": (10, 8),
    "Medium": (15, 13),
    "Hard": (20, 18),
}


class GameEngine:
    def __init__(self):
        pygame.init()

        self.font = pygame.font.SysFont("monospace", 22)
        self.big_font = pygame.font.SysFont("monospace", 36, bold=True)
        self.title_font = pygame.font.SysFont("monospace", 42, bold=True)

        self.clock = pygame.time.Clock()
        self.screen = pygame.display.set_mode((800, 700))
        pygame.display.set_caption("Maze Runner")

        self.leaderboard = self.load_leaderboard()

        self.difficulty = None
        self.cols = None
        self.rows = None
        self.selecting_difficulty = True
        self.difficulty_buttons = {}

        self.walls = None
        self.player = None
        self.exit_rect = None
        self.start_time = 0
        self.elapsed = 0
        self.won = False
        self.score_saved = False

        self.path = []
        self.show_hint = False

    # ---------------- Difficulty selection ----------------

    def choose_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.cols, self.rows = DIFFICULTIES[difficulty]

        width = self.cols * CELL
        height = self.rows * CELL + 60
        self.screen = pygame.display.set_mode((width, height))

        pygame.display.set_caption(
            f"Maze Runner - {difficulty} ({self.cols}x{self.rows})"
        )

        self.selecting_difficulty = False
        self.reset()

    def draw_difficulty_screen(self):
        self.screen.fill((30, 30, 50))

        title = self.title_font.render("MAZE RUNNER", True, (240, 240, 240))
        subtitle = self.font.render(
            "Choose your difficulty",
            True,
            (200, 200, 200),
        )

        self.screen.blit(
            title,
            (
                self.screen.get_width() // 2 - title.get_width() // 2,
                80,
            ),
        )
        self.screen.blit(
            subtitle,
            (
                self.screen.get_width() // 2 - subtitle.get_width() // 2,
                145,
            ),
        )

        button_width = 300
        button_height = 75
        gap = 25
        start_y = 220

        self.difficulty_buttons.clear()

        for i, (name, (cols, rows)) in enumerate(DIFFICULTIES.items()):
            rect = pygame.Rect(
                self.screen.get_width() // 2 - button_width // 2,
                start_y + i * (button_height + gap),
                button_width,
                button_height,
            )
            self.difficulty_buttons[name] = rect

            pygame.draw.rect(
                self.screen,
                (70, 70, 95),
                rect,
                border_radius=8,
            )
            pygame.draw.rect(
                self.screen,
                (150, 150, 170),
                rect,
                width=2,
                border_radius=8,
            )

            label = self.font.render(
                f"{name}  ({cols} x {rows})",
                True,
                (240, 240, 240),
            )
            self.screen.blit(
                label,
                (
                    rect.centerx - label.get_width() // 2,
                    rect.centery - label.get_height() // 2,
                ),
            )

        pygame.display.flip()

    # ---------------- Leaderboard ----------------

    def load_leaderboard(self):
        try:
            with open(LEADERBOARD_FILE, "r", encoding="utf-8") as file:
                scores = json.load(file)

            if not isinstance(scores, list):
                return []

            return sorted(float(score) for score in scores)[:MAX_SCORES]

        except (FileNotFoundError, json.JSONDecodeError, TypeError, ValueError):
            return []

    def save_leaderboard(self):
        with open(LEADERBOARD_FILE, "w", encoding="utf-8") as file:
            json.dump(self.leaderboard, file, indent=2)

    def add_score(self, score):
        self.leaderboard.append(round(score, 3))
        self.leaderboard.sort()
        self.leaderboard = self.leaderboard[:MAX_SCORES]
        self.save_leaderboard()

    # ---------------- Maze / reset ----------------

    def reset(self):
        if self.cols is None or self.rows is None:
            return

        self.walls = generate_maze(self.cols, self.rows)

        self.player = Player(0, 0)

        self.exit_rect = pygame.Rect(
            (self.cols - 1) * CELL + 5,
            (self.rows - 1) * CELL + 5,
            CELL - 10,
            CELL - 10,
        )

        self.start_time = time.time()
        self.elapsed = 0
        self.won = False
        self.score_saved = False

        self.path = []
        self.show_hint = False

    # ---------------- BFS shortest path ----------------

    def get_neighbors(self, r, c):
        # Maze wall format is [N, S, E, W].
        directions = [
            (-1, 0, 0),  # North
            (1, 0, 1),   # South
            (0, 1, 2),   # East
            (0, -1, 3),  # West
        ]

        for dr, dc, wall_index in directions:
            nr = r + dr
            nc = c + dc

            if 0 <= nr < self.rows and 0 <= nc < self.cols:
                if not self.walls[r][c][wall_index]:
                    yield nr, nc

    def find_shortest_path(self):
        start = (0, 0)
        target = (self.rows - 1, self.cols - 1)

        queue = deque([start])
        parent = {start: None}

        while queue:
            current = queue.popleft()

            if current == target:
                break

            for neighbor in self.get_neighbors(*current):
                if neighbor not in parent:
                    parent[neighbor] = current
                    queue.append(neighbor)

        if target not in parent:
            return []

        path = []
        current = target

        while current is not None:
            path.append(current)
            current = parent[current]

        path.reverse()
        return path

    # ---------------- Events ----------------

    def handle_events(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return False

            if self.selecting_difficulty:
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    for name, rect in self.difficulty_buttons.items():
                        if rect.collidepoint(event.pos):
                            self.choose_difficulty(name)
                            break
                continue

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_r:
                    self.reset()

                elif event.key == pygame.K_h:
                    if not self.show_hint:
                        self.path = self.find_shortest_path()
                        self.show_hint = True
                    else:
                        self.show_hint = False

        return True

    # ---------------- Game update ----------------

    def update(self):
        if self.won:
            return

        keys = pygame.key.get_pressed()
        self.player.move(keys, self.walls, self.rows, self.cols)

        self.elapsed = time.time() - self.start_time

        if self.player.rect.colliderect(self.exit_rect):
            self.won = True

            if not self.score_saved:
                self.add_score(self.elapsed)
                self.score_saved = True

    # ---------------- Drawing ----------------

    def draw_maze(self):
        wall_w = 3

        for r in range(self.rows):
            for c in range(self.cols):
                x = c * CELL
                y = r * CELL
                walls = self.walls[r][c]

                if walls[0]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y),
                        (x + CELL, y),
                        wall_w,
                    )

                if walls[1]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y + CELL),
                        (x + CELL, y + CELL),
                        wall_w,
                    )

                if walls[2]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x + CELL, y),
                        (x + CELL, y + CELL),
                        wall_w,
                    )

                if walls[3]:
                    pygame.draw.line(
                        self.screen,
                        WALL_COLOR,
                        (x, y),
                        (x, y + CELL),
                        wall_w,
                    )

    def draw_path(self):
        if not self.show_hint:
            return

        for r, c in self.path:
            # Leave the exit/player readable by using an inset square.
            rect = pygame.Rect(
                c * CELL + 7,
                r * CELL + 7,
                CELL - 14,
                CELL - 14,
            )
            pygame.draw.rect(
                self.screen,
                PATH_COLOR,
                rect,
                border_radius=5,
            )

    def draw_fog(self):
        fog = pygame.Surface(
            (self.cols * CELL, self.rows * CELL),
            pygame.SRCALPHA,
        )
        fog.fill(FOG_COLOR)

        pygame.draw.circle(
            fog,
            (0, 0, 0, 0),
            self.player.rect.center,
            FOG_RADIUS * CELL,
        )

        self.screen.blit(fog, (0, 0))

    def draw(self):
        self.screen.fill(BG)

        self.draw_maze()
        self.draw_path()

        pygame.draw.rect(
            self.screen,
            EXIT_COLOR,
            self.exit_rect,
            border_radius=4,
        )

        ex_label = self.font.render("EXIT", True, (20, 80, 20))
        self.screen.blit(
            ex_label,
            (self.exit_rect.x + 2, self.exit_rect.y + 4),
        )

        self.player.draw(self.screen)

        # Fog is applied over the maze area, revealing a 3-cell radius.
        self.draw_fog()

        hud = pygame.Rect(
            0,
            self.rows * CELL,
            self.cols * CELL,
            60,
        )
        pygame.draw.rect(self.screen, (30, 30, 50), hud)

        time_surf = self.font.render(
            f"Time: {self.elapsed:.1f}s   H = Hint   R = New Maze",
            True,
            (200, 200, 200),
        )
        self.screen.blit(
            time_surf,
            (10, self.rows * CELL + 18),
        )

        if self.won:
            overlay = pygame.Surface(
                (self.cols * CELL, self.rows * CELL),
                pygame.SRCALPHA,
            )
            overlay.fill((0, 0, 0, 160))
            self.screen.blit(overlay, (0, 0))

            msg = self.big_font.render(
                f"Solved in {self.elapsed:.1f}s!",
                True,
                (80, 240, 80),
            )
            self.screen.blit(
                msg,
                (
                    self.cols * CELL // 2 - msg.get_width() // 2,
                    45,
                ),
            )

            title = self.font.render(
                "TOP 5 TIMES",
                True,
                (255, 220, 80),
            )
            self.screen.blit(
                title,
                (
                    self.cols * CELL // 2 - title.get_width() // 2,
                    100,
                ),
            )

            for i, score in enumerate(self.leaderboard):
                entry = self.font.render(
                    f"{i + 1}. {score:.3f}s",
                    True,
                    (230, 230, 230),
                )
                self.screen.blit(
                    entry,
                    (
                        self.cols * CELL // 2 - entry.get_width() // 2,
                        135 + i * 32,
                    ),
                )

            sub = self.font.render(
                "Press R for a new maze",
                True,
                (200, 200, 200),
            )
            self.screen.blit(
                sub,
                (
                    self.cols * CELL // 2 - sub.get_width() // 2,
                    self.rows * CELL - 45,
                ),
            )

        pygame.display.flip()

    # ---------------- Main loop ----------------

    def run(self):
        running = True

        while running:
            running = self.handle_events()

            if self.selecting_difficulty:
                self.draw_difficulty_screen()
            else:
                self.update()
                self.draw()

            self.clock.tick(FPS)

        pygame.quit()
