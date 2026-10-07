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
        for r in range(ROWS):
            for c in range(COLS):
                x, y = c*CELL, r*CELL
                w = self.walls[r][c]
                if w[0]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x+CELL,y), wall_w)
                if w[1]: pygame.draw.line(self.screen, WALL_COLOR, (x,y+CELL), (x+CELL,y+CELL), wall_w)
                if w[2]: pygame.draw.line(self.screen, WALL_COLOR, (x+CELL,y), (x+CELL,y+CELL), wall_w)
                if w[3]: pygame.draw.line(self.screen, WALL_COLOR, (x,y), (x,y+CELL), wall_w)

    def draw(self):
        self.screen.fill(BG)
        self.draw_solution()
        self.draw_maze()
        pygame.draw.rect(self.screen, EXIT_COLOR, self.exit_rect, border_radius=4)
        ex_label = self.font.render("EXIT", True, (20,80,20))
        self.screen.blit(ex_label, (self.exit_rect.x+2, self.exit_rect.y+4))
        self.player.draw(self.screen)

        hud = pygame.Rect(0, ROWS*CELL, WIDTH, 60)
        pygame.draw.rect(self.screen, (30,30,50), hud)
        hint_state = "ON" if self.show_solution else "OFF"
        time_surf = self.font.render(
            f"Time: {self.elapsed:.1f}s   H = Hint ({hint_state})   R = New Maze",
            True,
            (200,200,200),
        )
        self.screen.blit(time_surf, (10, ROWS*CELL+18))

        if self.won:
            overlay = pygame.Surface((WIDTH, ROWS*CELL), pygame.SRCALPHA)
            overlay.fill((0,0,0,120))
            self.screen.blit(overlay, (0,0))
            msg = self.big_font.render(f"Solved in {self.elapsed:.1f}s!", True, (80,240,80))
            sub = self.font.render("Press R for a new maze", True, (200,200,200))
            self.screen.blit(msg, (WIDTH//2 - msg.get_width()//2, ROWS*CELL//2 - 30))
            self.screen.blit(sub, (WIDTH//2 - sub.get_width()//2, ROWS*CELL//2 + 20))
        pygame.display.flip()

    def run(self):
        running = True