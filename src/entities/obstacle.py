"""
Obstacle module for Recoil Wing.
Handles scrolling pipes and destructible crates.
"""
import random
import pygame
from src.config import (
    PIPE_WIDTH,
    PIPE_GAP,
    PIPE_MIN_HEIGHT,
    CRATE_SIZE,
    COLOR_PIPE,
    COLOR_PIPE_OUTLINE,
    COLOR_CRATE,
)


class Crate:
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.size = CRATE_SIZE
        self.hp = 1
        self.alive = True

    @property
    def rect(self):
        return pygame.Rect(int(self.x), int(self.y), self.size, self.size)

    def take_damage(self):
        """Damages the crate. Returns True if destroyed."""
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        if not self.alive:
            return

        r = self.rect
        # 1. Base Crate Box
        pygame.draw.rect(surface, COLOR_CRATE, r, border_radius=4)
        pygame.draw.rect(surface, (185, 28, 28), r, width=2, border_radius=4)

        # 2. Hazard Warning Cross / Stripes
        inner_margin = 6
        inner_r = pygame.Rect(
            r.x + inner_margin,
            r.y + inner_margin,
            r.width - inner_margin * 2,
            r.height - inner_margin * 2,
        )
        pygame.draw.rect(surface, (249, 115, 22), inner_r, border_radius=2)

        # Cross lines
        pygame.draw.line(surface, (153, 27, 27), (inner_r.left, inner_r.top), (inner_r.right, inner_r.bottom), width=2)
        pygame.draw.line(surface, (153, 27, 27), (inner_r.left, inner_r.bottom), (inner_r.right, inner_r.top), width=2)

        # Corner rivets
        rivet_color = (254, 202, 202)
        pygame.draw.circle(surface, rivet_color, (r.left + 4, r.top + 4), 1)
        pygame.draw.circle(surface, rivet_color, (r.right - 5, r.top + 4), 1)
        pygame.draw.circle(surface, rivet_color, (r.left + 4, r.bottom - 5), 1)
        pygame.draw.circle(surface, rivet_color, (r.right - 5, r.bottom - 5), 1)


class PipePair:
    def __init__(self, x, ground_y):
        self.x = float(x)
        self.ground_y = ground_y
        self.width = PIPE_WIDTH
        self.gap_height = PIPE_GAP
        self.passed = False

        # Randomize vertical gap position
        min_gap_y = PIPE_MIN_HEIGHT + self.gap_height // 2
        max_gap_y = ground_y - PIPE_MIN_HEIGHT - self.gap_height // 2
        self.gap_y = random.randint(min_gap_y, max_gap_y)

        self.gap_top = self.gap_y - self.gap_height // 2
        self.gap_bottom = self.gap_y + self.gap_height // 2

        # 55% chance to spawn a destructible crate in the gap
        self.crate = None
        if random.random() < 0.55:
            # Situate crate on the lower threshold of the gap
            crate_x = self.x + (self.width - CRATE_SIZE) // 2
            crate_y = self.gap_bottom - CRATE_SIZE
            self.crate = Crate(crate_x, crate_y)

    @property
    def top_rect(self):
        return pygame.Rect(int(self.x), 0, self.width, self.gap_top)

    @property
    def bottom_rect(self):
        return pygame.Rect(
            int(self.x),
            self.gap_bottom,
            self.width,
            self.ground_y - self.gap_bottom,
        )

    def update(self, speed):
        """Move leftwards."""
        self.x -= speed
        if self.crate:
            self.crate.x -= speed

    def collides_with_player(self, player_rect):
        """Check collision against solid pipes or active crate."""
        if self.top_rect.colliderect(player_rect):
            return True
        if self.bottom_rect.colliderect(player_rect):
            return True
        if self.crate and self.crate.alive and self.crate.rect.colliderect(player_rect):
            return True
        return False

    def check_bullet_hit(self, bullet):
        """
        Check if a bullet hits the crate or pipes.
        Returns a tuple: (hit_type, hit_x, hit_y, destroyed) or None.
        """
        # 1. Crate collision
        if self.crate and self.crate.alive and self.crate.rect.colliderect(bullet.rect):
            destroyed = self.crate.take_damage()
            return ("crate", self.crate.rect.centerx, self.crate.rect.centery, destroyed)

        # 2. Bottom Pipe top surface
        if self.bottom_rect.colliderect(bullet.rect):
            return ("pipe", bullet.x, self.bottom_rect.top, False)

        # 3. Top Pipe
        if self.top_rect.colliderect(bullet.rect):
            return ("pipe", bullet.x, self.top_rect.bottom, False)

        return None

    def draw(self, surface):
        """Draw top and bottom pipes with shaded industrial styling."""
        ix = int(self.x)
        collar_h = 22
        collar_overhang = 4

        # 1. Top Pipe Body
        top_body_rect = pygame.Rect(ix, 0, self.width, max(0, self.gap_top - collar_h))
        pygame.draw.rect(surface, COLOR_PIPE, top_body_rect)
        # Top Pipe Collar (rim at the opening)
        top_collar_rect = pygame.Rect(
            ix - collar_overhang,
            max(0, self.gap_top - collar_h),
            self.width + collar_overhang * 2,
            collar_h,
        )
        pygame.draw.rect(surface, (51, 65, 85), top_collar_rect, border_radius=2)
        pygame.draw.rect(surface, COLOR_PIPE_OUTLINE, top_collar_rect, width=2, border_radius=2)

        # 2. Bottom Pipe Body
        bottom_body_rect = pygame.Rect(
            ix,
            self.gap_bottom + collar_h,
            self.width,
            max(0, self.ground_y - (self.gap_bottom + collar_h)),
        )
        pygame.draw.rect(surface, COLOR_PIPE, bottom_body_rect)
        # Bottom Pipe Collar (rim at the opening)
        bottom_collar_rect = pygame.Rect(
            ix - collar_overhang,
            self.gap_bottom,
            self.width + collar_overhang * 2,
            collar_h,
        )
        pygame.draw.rect(surface, (51, 65, 85), bottom_collar_rect, border_radius=2)
        pygame.draw.rect(surface, COLOR_PIPE_OUTLINE, bottom_collar_rect, width=2, border_radius=2)

        # Cylindrical Highlight Lines (giving metallic curved depth)
        hl_x = ix + 10
        if top_body_rect.height > 0:
            pygame.draw.line(surface, (100, 116, 139), (hl_x, 0), (hl_x, top_body_rect.bottom), width=3)
        if bottom_body_rect.height > 0:
            pygame.draw.line(surface, (100, 116, 139), (hl_x, bottom_body_rect.top), (hl_x, bottom_body_rect.bottom), width=3)

        # Cylindrical Shadow Line on right edge
        sh_x = ix + self.width - 6
        if top_body_rect.height > 0:
            pygame.draw.line(surface, (30, 41, 59), (sh_x, 0), (sh_x, top_body_rect.bottom), width=3)
        if bottom_body_rect.height > 0:
            pygame.draw.line(surface, (30, 41, 59), (sh_x, bottom_body_rect.top), (sh_x, bottom_body_rect.bottom), width=3)

        # 3. Draw Crate if present
        if self.crate and self.crate.alive:
            self.crate.draw(surface)
