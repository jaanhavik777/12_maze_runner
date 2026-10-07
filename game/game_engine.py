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

DIFFICULTIES = {
    "Easy": (10, 8),
    "Medium": (15, 13),
    "Hard": (20, 18),
}

self.width = self.cols * CELL
self.height = self.rows * CELL + 60

class GameEngine:
    def __init__(self):
        pygame.init()
        self.width = 800
        self.height = 700
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Maze Runner")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("monospace", 22)
        self.big_font = pygame.font.SysFont("monospace", 36, bold=True)
        self.title_font = pygame.font.SysFont("monospace", 42, bold=True)
        self.leaderboard = self.load_leaderboard()

        self.difficulty = None
        self.selecting_difficulty = True
        self.cols = None
        self.rows = None

        self.reset()

    def choose_difficulty(self, difficulty):
        self.difficulty = difficulty
        self.cols, self.rows = DIFFICULTIES[difficulty]
        self.width = self.cols * CELL
        self.height = self.rows * CELL + 60
        self.screen = pygame.display.set_mode((self.width, self.height))
        self.selecting_difficulty = False
        self.reset()

    def draw_difficulty_screen(self):
        self.screen.fill((30, 30, 50))

        title = self.title_font.render("MAZE RUNNER", True, (240, 240, 240))
        subtitle = self.font.render("Choose your difficulty", True, (200, 200, 200))

        self.screen.blit(
            title,
            (self.screen.get_width() // 2 - title.get_width() // 2, 80)
        )
        self.screen.blit(
            subtitle,
            (self.screen.get_width() // 2 - subtitle.get_width() // 2, 145)
        )

        button_width = 300
        button_height = 75
        gap = 25
        start_y = 220
        self.difficulty_buttons = {}

        for i, (name, (cols, rows)) in enumerate(DIFFICULTIES.items()):
            rect = pygame.Rect(
                self.screen.get_width() // 2 - button_width // 2,
                start_y + i * (button_height + gap),
                button_width,
                button_height
            )
            self.difficulty_buttons[name] = rect

            pygame.draw.rect(self.screen, (70, 70, 95), rect, border_radius=8)
            pygame.draw.rect(
                self.screen, (150, 150, 170), rect, width=2, border_radius=8
            )

            label = self.font.render(
                f"{name}  ({cols} x {rows})",
                True,
                (240, 240, 240)
            )
            self.screen.blit(
                label,
                (rect.centerx - label.get_width() // 2,
                 rect.centery - label.get_height() // 2)
            )

        pygame.display.flip()

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
        if self.cols is None or self.rows is None:
            return

        self.walls = generate_maze(self.cols, self.rows)
        self.player = Player(0, 0)
        self.exit_rect = pygame.Rect(
            (self.cols - 1) * CELL + 5,
            (self.rows - 1) * CELL + 5,
            CELL - 10,
            CELL - 10
        )
        self.start_time = time.time()
        self.elapsed = 0
        self.won = False
        self.score_saved = False
        self.path = []
        self.show_hint = False
        self.show_solution = False
        self.solution_path = self._bfs_shortest_path()

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
                    self.show_hint = not self.show_hint

        return True

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

    def _bfs_shortest_path(self):
        """Return the shortest path from the start cell to the exit using BFS."""
        start = (0, 0)
        goal = (self.rows - 1, self.cols - 1)

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

                if not (0 <= nr < self.rows and 0 <= nc < self.cols):
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
        while current is not None:
            path.append(current)
            current = parent[current]

        path.reverse()
        return path

    def draw_solution(self):
        """Draw the BFS solution as colored squares inside each path cell."""
        if not self.show_solution:
            return

        path_color = (255, 210, 70)
        inset = 7

        for r, c in self.solution_path:
            rect = pygame.Rect(
                c * CELL + inset,
                r * CELL + inset,
                CELL - 2 * inset,
                CELL - 2 * inset,
            )
            pygame.draw.rect(self.screen, path_color, rect, border_radius=5)

    def draw_maze(self):
        wall_w = 3
        for r in range(self.rows):
            for c in range(self.cols):
                x, y = c*CELL, r*CELL
                w = self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x+CELL,y), wall_w)
                if w[1]: pygame.draw.line(self.screen, WALL_COLOR, (x,y+CELL), (x+CELL,y+CELL), wall_w)
                if w[2]: pygame.draw.line(self.screen, WALL_COLOR, (x+CELL,y), (x+CELL,y+CELL), wall_w)
                if w[3]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x,y+CELL), wall_w)

    def draw_fog(self):
        """Draw a dark overlay, revealing only a circular area around the player."""
        fog = pygame.Surface((self.width, self.rows * CELL), pygame.SRCALPHA)
        fog.fill(FOG_COLOR)

        # Reveal a circular area centered on the player's current position.
        pygame.draw.circle(
            fog,
            (0, 0, 0, 0),
            self.player.rect.center,
            FOG_RADIUS * CELL
        )

        self.screen.blit(fog, (0, 0))

    def draw(self):
        self.screen.fill(BG)
        self.draw_solution()
        self.draw_maze()
        pygame.draw.rect(self.screen, EXIT_COLOR, self.exit_rect, border_radius=4)
        ex_label = self.font.render("EXIT", True, (20,80,20))
        self.screen.blit(ex_label, (self.exit_rect.x+2, self.exit_rect.y+4))
        self.player.draw(self.screen)
        self.draw_fog()

        hud = pygame.Rect(0, self.rows*CELL, self.width, 60)
        pygame.draw.rect(self.screen, (30,30,50), hud)
        hint_state = "ON" if self.show_solution else "OFF"
        time_surf = self.font.render(
            f"Time: {self.elapsed:.1f}s   H = Hint ({hint_state})   R = New Maze",
            True,
            (200,200,200),
        )
        self.screen.blit(time_surf, (10, self.rows*CELL+18))

        if self.won:
            overlay = pygame.Surface((self.width, self.rows*CELL), pygame.SRCALPHA)
            overlay.fill((0,0,0,160))
            self.screen.blit(overlay, (0,0))

            msg = self.big_font.render(
                f"Solved in {self.elapsed:.1f}s!",
                True,
                (80,240,80)
            )
            self.screen.blit(
                msg,
                (self.width//2 - msg.get_width()//2, 55)
            )

            title = self.font.render("TOP 5 TIMES", True, (255,220,80))
            self.screen.blit(
                title,
                (self.width//2 - title.get_width()//2, 110)
            )

            for i, score in enumerate(self.leaderboard):
                entry = self.font.render(
                    f"{i + 1}. {score:.3f}s",
                    True,
                    (230,230,230)
                )
                self.screen.blit(
                    entry,
                    (self.width//2 - entry.get_width()//2, 145 + i * 32)
                )

            sub = self.font.render(
                "Press R for a new maze",
                True,
                (200,200,200)
            )
            self.screen.blit(
                sub,
                (self.width//2 - sub.get_width()//2, self.rows*CELL - 45)
            )
        pygame.display.flip()

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
