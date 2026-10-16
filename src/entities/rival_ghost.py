"""
Recoil Wing - Rival Ghost Entity for Multiplayer 2P Race.
Renders the rival player as a semi-transparent, neon-glowing cyber holographic wing.
Handles interpolated position updates and match status.
"""
import math
import pygame
from src.config import (
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    COLOR_TEXT,
)

COLOR_GHOST_BODY = (255, 42, 133, 160)     # Neon Pink Translucent
COLOR_GHOST_BORDER = (255, 114, 182, 230)  # Bright Pink Glow
COLOR_GHOST_GUN = (190, 24, 93, 180)
COLOR_GHOST_MUZZLE = (254, 240, 138, 200)


class RivalGhost:
    def __init__(self, font_small):
        self.x = -200.0
        self.y = -200.0
        self.target_x = -200.0
        self.target_y = -200.0
        self.vy = 0.0
        self.score = 0
        self.is_alive = True
        self.shooting = False
        self.font = font_small
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.flash_timer = 0

    def reset(self):
        """Resets ghost state for a new match."""
        self.x = -200.0
        self.y = -200.0
        self.target_x = -200.0
        self.target_y = -200.0
        self.vy = 0.0
        self.score = 0
        self.is_alive = True
        self.shooting = False
        self.flash_timer = 0

    def update_from_network(self, data):
        """Updates rival state from received network packet."""
        self.target_x = data.get("x", self.target_x)
        self.target_y = data.get("y", self.target_y)
        self.vy = data.get("vy", self.vy)
        self.score = data.get("score", self.score)
        self.is_alive = data.get("alive", self.is_alive)
        if data.get("shooting"):
            self.flash_timer = 4

        # First packet teleport
        if self.x < -100:
            self.x = self.target_x
            self.y = self.target_y

    def update(self, dt):
        """Smoothly interpolates rival position towards target."""
        # Simple lerp to prevent jitter
        lerp_factor = 0.35
        self.x += (self.target_x - self.x) * lerp_factor
        self.y += (self.target_y - self.y) * lerp_factor

        if self.flash_timer > 0:
            self.flash_timer -= 1

    def draw(self, surface):
        """Renders the rival hologram on screen."""
        if self.x < -50 or self.x > 600:
            return

        rx = int(self.x)
        ry = int(self.y)

        # 1. Floating Rival Name Tag & Score
        tag_text = f"RIVAL [{self.score}]" if self.is_alive else "RIVAL [CRASHED]"
        tag_color = (255, 114, 182) if self.is_alive else (239, 68, 68)
        tag_surf = self.font.render(tag_text, True, tag_color)
        tag_bg = pygame.Surface((tag_surf.get_width() + 8, tag_surf.get_height() + 4), pygame.SRCALPHA)
        tag_bg.fill((15, 23, 42, 180))
        pygame.draw.rect(tag_bg, tag_color, tag_bg.get_rect(), 1, border_radius=4)

        surface.blit(tag_bg, (rx - tag_bg.get_width() // 2, ry - 32))
        surface.blit(tag_surf, (rx - tag_surf.get_width() // 2, ry - 30))

        if not self.is_alive:
            # Draw crashed marker
            skull_txt = self.font.render("X", True, (239, 68, 68))
            surface.blit(skull_txt, skull_txt.get_rect(center=(rx, ry)))
            return

        # 2. Holographic Bird Body
        diag = int(math.hypot(self.width + 12, self.height + 16)) + 8
        hologram = pygame.Surface((diag, diag), pygame.SRCALPHA)
        center = (diag // 2, diag // 2)

        # Body Ellipse
        body_rect = pygame.Rect(0, 0, self.width, self.height)
        body_rect.center = center
        pygame.draw.ellipse(hologram, COLOR_GHOST_BODY, body_rect)
        pygame.draw.ellipse(hologram, COLOR_GHOST_BORDER, body_rect, 2)

        # Hologram scanlines effect
        for y_line in range(body_rect.top, body_rect.bottom, 4):
            pygame.draw.line(hologram, (255, 255, 255, 70), (body_rect.left + 2, y_line), (body_rect.right - 2, y_line), 1)

        # Eye
        eye_center = (center[0] + 6, center[1] - 3)
        pygame.draw.circle(hologram, (255, 255, 255, 220), eye_center, 4)
        pygame.draw.circle(hologram, (15, 23, 42, 220), (eye_center[0] + 1, eye_center[1]), 2)

        # Gun & Muzzle Flash
        gun_rect = pygame.Rect(0, 0, 8, 10)
        gun_rect.center = (center[0] - 2, center[1] + 10)
        pygame.draw.rect(hologram, COLOR_GHOST_GUN, gun_rect, border_radius=2)

        if self.flash_timer > 0:
            flash_tip = (gun_rect.centerx, gun_rect.bottom + 6)
            pygame.draw.polygon(hologram, COLOR_GHOST_MUZZLE, [
                (gun_rect.centerx - 5, gun_rect.bottom),
                (gun_rect.centerx + 5, gun_rect.bottom),
                flash_tip
            ])

        # Rotation tilt based on vertical speed
        tilt = max(-35.0, min(65.0, self.vy * 3.8))
        rotated = pygame.transform.rotate(hologram, -tilt)
        surface.blit(rotated, rotated.get_rect(center=(rx, ry)))
