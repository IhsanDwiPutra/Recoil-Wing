"""
Game controller and main loop for Recoil Wing.
"""
import sys
import math
import pygame

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TITLE,
    COLOR_BG_TOP,
    COLOR_BG_BOTTOM,
    COLOR_GROUND,
    COLOR_GROUND_LINE,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_ACCENT,
    COLOR_AMMO_FILLED,
    COLOR_AMMO_EMPTY,
    COLOR_AMMO_BORDER,
    MAX_AMMO,
    AMMO_RELOAD_FRAMES,
    PIPE_SPEED,
    PIPE_SPAWN_FRAMES,
)
from src.entities.player import Player
from src.entities.obstacle import PipePair
from src.entities.particle import create_crate_debris, create_spark_burst


class GameState:
    READY = "ready"
    PLAYING = "playing"
    GAME_OVER = "game_over"


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # Fonts
        self.font_score = pygame.font.SysFont("Trebuchet MS", 48, bold=True)
        self.font_score_label = pygame.font.SysFont("Trebuchet MS", 14, bold=True)
        self.font_title = pygame.font.SysFont("Trebuchet MS", 36, bold=True)
        self.font_body = pygame.font.SysFont("Trebuchet MS", 18, bold=True)
        self.font_small = pygame.font.SysFont("Trebuchet MS", 13)


        # Ground setting
        self.ground_height = 80
        self.ground_y = SCREEN_HEIGHT - self.ground_height

        # Pre-render background gradient for high performance
        self.bg_surface = self._create_gradient_surface(
            SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG_TOP, COLOR_BG_BOTTOM
        )

        # Entities & States
        self.player = Player()
        self.bullets = []
        self.obstacles = []
        self.particles = []
        self.pipe_spawn_timer = 0
        self.state = GameState.READY
        self.score = 0
        self.high_score = 0
        self.ready_timer = 0.0

    def _create_gradient_surface(self, width, height, top_color, bottom_color):
        """Pre-renders a smooth 2-color vertical linear gradient surface."""
        surf = pygame.Surface((width, height))
        for y in range(height):
            ratio = y / height
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
        return surf

    def handle_input(self):
        """Process input events."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                    self.on_jump_action()
                elif event.key == pygame.K_r:
                    self.reset_game()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left Click
                    self.on_jump_action()

    def on_jump_action(self):
        """Handle jump/recoil action across different states."""
        if self.state == GameState.READY:
            self.state = GameState.PLAYING
            bullet = self.player.shoot()
            if bullet:
                self.bullets.append(bullet)
        elif self.state == GameState.PLAYING:
            bullet = self.player.shoot()
            if bullet:
                self.bullets.append(bullet)
        elif self.state == GameState.GAME_OVER:
            self.reset_game()

    def reset_game(self):
        """Reset game to initial ready state."""
        self.player.reset()
        self.bullets.clear()
        self.obstacles.clear()
        self.particles.clear()
        self.pipe_spawn_timer = 0
        self.state = GameState.READY
        self.score = 0
        self.ready_timer = 0.0

    def update(self):
        """Update game logic."""
        if self.state == GameState.READY:
            # Idle gentle floating bobbing animation
            self.ready_timer += 0.05
            self.player.y = self.player.start_y + math.sin(self.ready_timer) * 8
            self.player.rotation = 0.0

        elif self.state == GameState.PLAYING:
            self.player.update()

            # 1. Spawn Obstacles
            self.pipe_spawn_timer += 1
            if self.pipe_spawn_timer >= PIPE_SPAWN_FRAMES:
                self.obstacles.append(PipePair(SCREEN_WIDTH + 10, self.ground_y))
                self.pipe_spawn_timer = 0

            # 2. Update Obstacles & Check Player Collision / Scoring
            for o in self.obstacles:
                o.update(PIPE_SPEED)

                # Point scored when clearing obstacle
                if not o.passed and self.player.x > o.x + o.width:
                    o.passed = True
                    self.score += 1

                # Player collision with solid pipe or intact crate
                if o.collides_with_player(self.player.rect):
                    self.player.is_alive = False
                    self.particles.extend(create_spark_burst(self.player.x, self.player.y, count=12))
                    self.state = GameState.GAME_OVER
                    if self.score > self.high_score:
                        self.high_score = self.score

            # Remove off-screen obstacles
            self.obstacles = [o for o in self.obstacles if o.x + o.width > -40]

            # 3. Update Bullets & Check Collisions with Obstacles
            for b in self.bullets:
                b.update(self.ground_y)
                if not b.alive:
                    continue

                for o in self.obstacles:
                    hit = o.check_bullet_hit(b)
                    if hit:
                        b.alive = False
                        hit_type, hx, hy, destroyed = hit
                        if hit_type == "crate":
                            if destroyed:
                                self.particles.extend(create_crate_debris(hx, hy, count=14))
                                self.score += 2  # Tactical demolition reward!
                            else:
                                self.particles.extend(create_spark_burst(hx, hy, count=5))
                        else:
                            self.particles.extend(create_spark_burst(hx, hy, count=6))
                        break

            self.bullets = [b for b in self.bullets if b.alive]

            # 4. Update Particles
            for p in self.particles:
                p.update()
            self.particles = [p for p in self.particles if p.alive]

            # 5. Ceiling clamp
            if self.player.y - self.player.height // 2 < 0:
                self.player.y = self.player.height // 2
                self.player.vy = max(0.0, self.player.vy)

            # 6. Ground collision
            if self.player.y + self.player.height // 2 >= self.ground_y:
                self.player.y = self.ground_y - self.player.height // 2
                if self.player.is_alive:
                    self.player.is_alive = False
                    self.particles.extend(create_spark_burst(self.player.x, self.player.y, count=8))
                    self.state = GameState.GAME_OVER
                    if self.score > self.high_score:
                        self.high_score = self.score

        elif self.state == GameState.GAME_OVER:
            # Update remaining bullets & particles
            for b in self.bullets:
                b.update(self.ground_y)
            self.bullets = [b for b in self.bullets if b.alive]

            for p in self.particles:
                p.update()
            self.particles = [p for p in self.particles if p.alive]

            # Allow dead bird to drop to the floor
            if self.player.y + self.player.height // 2 < self.ground_y:
                self.player.update()
                if self.player.y + self.player.height // 2 >= self.ground_y:
                    self.player.y = self.ground_y - self.player.height // 2

    def draw(self):
        """Render frame."""
        # 1. Background
        self.screen.blit(self.bg_surface, (0, 0))

        # 2. Obstacles (behind bullets & player)
        for o in self.obstacles:
            o.draw(self.screen)

        # 3. Bullets
        for b in self.bullets:
            b.draw(self.screen)

        # 4. Particles
        for p in self.particles:
            p.draw(self.screen)

        # 5. Player
        self.player.draw(self.screen)

        # 6. Ground
        ground_rect = pygame.Rect(0, self.ground_y, SCREEN_WIDTH, self.ground_height)
        pygame.draw.rect(self.screen, COLOR_GROUND, ground_rect)
        pygame.draw.line(
            self.screen,
            COLOR_GROUND_LINE,
            (0, self.ground_y),
            (SCREEN_WIDTH, self.ground_y),
            width=3,
        )

        # Subtle ground grid dashes
        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(
                self.screen,
                (25, 28, 44),
                (x, self.ground_y + 12),
                (x + 20, self.ground_y + 12),
                width=2,
            )

        # 7. HUD & State Text
        self._draw_hud()

        pygame.display.flip()

    def _draw_hud(self):
        """Draw UI elements, status text, live score, and ammo meter."""
        # Ammo Meter
        self._draw_ammo_meter()

        if self.state == GameState.READY:
            title_surf = self.font_title.render("RECOIL WING", True, COLOR_TEXT)
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 180))
            self.screen.blit(title_surf, title_rect)

            sub_surf = self.font_body.render("Press SPACE or CLICK to Shoot & Fly", True, COLOR_ACCENT)
            sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 230))
            self.screen.blit(sub_surf, sub_rect)

            hint_surf = self.font_small.render("[Milestone 3: Obstacles & Destructible Crates]", True, COLOR_TEXT_MUTED)
            hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
            self.screen.blit(hint_surf, hint_rect)

        elif self.state == GameState.PLAYING:
            # Active Score display in top-center
            score_str = str(self.score)
            # Soft shadow
            shadow_surf = self.font_score.render(score_str, True, (15, 23, 42))
            self.screen.blit(shadow_surf, shadow_surf.get_rect(center=(SCREEN_WIDTH // 2 + 2, 98 + 2)))
            # Foreground text
            score_surf = self.font_score.render(score_str, True, COLOR_TEXT)
            self.screen.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH // 2, 98)))

        elif self.state == GameState.GAME_OVER:
            # Game Over Box Modal
            modal_rect = pygame.Rect(45, 180, SCREEN_WIDTH - 90, 240)
            pygame.draw.rect(self.screen, (24, 27, 44), modal_rect, border_radius=12)
            pygame.draw.rect(self.screen, (55, 62, 92), modal_rect, width=2, border_radius=12)

            go_surf = self.font_title.render("GAME OVER", True, COLOR_ACCENT)
            self.screen.blit(go_surf, go_surf.get_rect(center=(SCREEN_WIDTH // 2, 220)))

            score_txt = self.font_body.render(f"SCORE: {self.score}", True, COLOR_TEXT)
            self.screen.blit(score_txt, score_txt.get_rect(center=(SCREEN_WIDTH // 2, 270)))

            best_txt = self.font_small.render(f"BEST SCORE: {self.high_score}", True, COLOR_TEXT_MUTED)
            self.screen.blit(best_txt, best_txt.get_rect(center=(SCREEN_WIDTH // 2, 305)))

            restart_surf = self.font_body.render("Press SPACE / R to Retry", True, (45, 212, 191))
            self.screen.blit(restart_surf, restart_surf.get_rect(center=(SCREEN_WIDTH // 2, 360)))

    def _draw_ammo_meter(self):
        """Draw modern arcade cartridge pips representing available ammo."""
        pip_w = 22
        pip_h = 9
        pip_spacing = 6
        total_w = MAX_AMMO * pip_w + (MAX_AMMO - 1) * pip_spacing
        start_x = (SCREEN_WIDTH - total_w) // 2
        start_y = 35

        for i in range(MAX_AMMO):
            px = start_x + i * (pip_w + pip_spacing)
            pip_rect = pygame.Rect(px, start_y, pip_w, pip_h)

            if i < self.player.ammo:
                pygame.draw.rect(self.screen, COLOR_AMMO_FILLED, pip_rect, border_radius=3)
                pygame.draw.rect(self.screen, (255, 255, 255), pip_rect, width=1, border_radius=3)
            elif i == self.player.ammo and self.player.ammo < MAX_AMMO:
                pygame.draw.rect(self.screen, COLOR_AMMO_EMPTY, pip_rect, border_radius=3)
                progress = self.player.ammo_reload_timer / AMMO_RELOAD_FRAMES
                progress_w = int(pip_w * progress)
                if progress_w > 0:
                    fill_rect = pygame.Rect(px, start_y, progress_w, pip_h)
                    pygame.draw.rect(self.screen, (34, 197, 94), fill_rect, border_radius=3)
                pygame.draw.rect(self.screen, COLOR_AMMO_BORDER, pip_rect, width=1, border_radius=3)
            else:
                pygame.draw.rect(self.screen, COLOR_AMMO_EMPTY, pip_rect, border_radius=3)
                pygame.draw.rect(self.screen, (40, 50, 70), pip_rect, width=1, border_radius=3)

    def run(self):
        """Main game loop."""
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)


