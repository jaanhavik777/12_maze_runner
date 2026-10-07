import pygame
from game.maze import CELL

SPEED = 3
WALL_THICKNESS = 3


class Player:
    def __init__(self, r, c):
        self.r = r
        self.c = c

        x = c * CELL + CELL // 2
        y = r * CELL + CELL // 2

        self.rect = pygame.Rect(x - 10, y - 10, 20, 20)
        self.color = (60, 120, 220)

    def move(self, keys, walls, rows, cols):
        dx, dy = 0, 0

        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -SPEED
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = SPEED
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -SPEED
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = SPEED

        # Move one axis at a time so the player cannot pass through
        # a wall while moving diagonally.
        if dx:
            new_rect = self.rect.move(dx, 0)
            if not self._hits_wall(new_rect, walls, rows, cols):
                self.rect = new_rect

        if dy:
            new_rect = self.rect.move(0, dy)
            if not self._hits_wall(new_rect, walls, rows, cols):
                self.rect = new_rect

        # Keep the cell coordinates synchronized with the player's center.
        self.r = min(rows - 1, max(0, self.rect.centery // CELL))
        self.c = min(cols - 1, max(0, self.rect.centerx // CELL))

    def _hits_wall(self, rect, walls, rows, cols):
        # Outer maze boundary.
        if rect.left < 0 or rect.right > cols * CELL:
            return True
        if rect.top < 0 or rect.bottom > rows * CELL:
            return True

        # Only inspect cells touched by the candidate player rectangle.
        left_cell = max(0, rect.left // CELL)
        right_cell = min(cols - 1, rect.right // CELL)
        top_cell = max(0, rect.top // CELL)
        bottom_cell = min(rows - 1, rect.bottom // CELL)

        for r in range(top_cell, bottom_cell + 1):
            for c in range(left_cell, right_cell + 1):
                x = c * CELL
                y = r * CELL

                # Walls are stored as [N, S, E, W].
                wall_rects = []

                if walls[r][c][0]:  # North
                    wall_rects.append(
                        pygame.Rect(x, y, CELL, WALL_THICKNESS)
                    )

                if walls[r][c][1]:  # South
                    wall_rects.append(
                        pygame.Rect(
                            x,
                            y + CELL - WALL_THICKNESS,
                            CELL,
                            WALL_THICKNESS,
                        )
                    )

                if walls[r][c][2]:  # East
                    wall_rects.append(
                        pygame.Rect(
                            x + CELL - WALL_THICKNESS,
                            y,
                            WALL_THICKNESS,
                            CELL,
                        )
                    )

                if walls[r][c][3]:  # West
                    wall_rects.append(
                        pygame.Rect(x, y, WALL_THICKNESS, CELL)
                    )

                for wall_rect in wall_rects:
                    if rect.colliderect(wall_rect):
                        return True

        return False

    def draw(self, screen):
        pygame.draw.ellipse(screen, self.color, self.rect)
