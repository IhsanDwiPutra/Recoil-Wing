"""
Bullet entity for Recoil Wing.
Handles projectile physics, trail rendering, bouncing, and piercing.
"""
import random
import pygame
from src.config import (
    BULLET_SPEED,
    BULLET_WIDTH,
    BULLET_HEIGHT,
    COLOR_BULLET,
    COLOR_BULLET_TRAIL,
)


class Bullet:
    def __init__(
        self,
        x,
        y,
        vx=None,
        vy=None,
        bounces=0,
        piercing=False,
        core_color=COLOR_BULLET,
        trail_color=COLOR_BULLET_TRAIL,
    ):
        self.x = float(x)
        self.y = float(y)
        self.width = BULLET_WIDTH
        self.height = BULLET_HEIGHT

        # Velocity
        if vx is None:
            self.vx = random.uniform(-0.8, 0.8)
        else:
            self.vx = float(vx)

        if vy is None:
            self.vy = BULLET_SPEED + random.uniform(0.0, 1.5)
        else:
            self.vy = float(vy)

        self.bounces = bounces
        self.piercing = piercing
        self.core_color = core_color
        self.trail_color = trail_color

        self.alive = True
        self.trail = []

    @property
    def rect(self):
        """Bounding box for collisions."""
        return pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )

    def bounce_vertical(self):
        """Reverses vertical velocity if bounces remain."""
        if self.bounces > 0:
            self.vy = -self.vy * 0.85
            self.bounces -= 1
            return True
        return False

    def bounce_horizontal(self):
        """Reverses horizontal velocity if bounces remain."""
        if self.bounces > 0:
            self.vx = -self.vx * 0.85
            self.bounces -= 1
            return True
        return False

    def update(self, max_y):
        """Update bullet position, trail, and bounds."""
        if not self.alive:
            return

        # Record trail position
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)

        # Move
        self.x += self.vx
        self.y += self.vy

        # Check floor collision
        if self.y >= max_y:
            if self.bounces > 0:
                self.y = max_y - 2
                self.vy = -abs(self.vy) * 0.85
                self.bounces -= 1
            else:
                self.alive = False

        # Check screen edge bounds
        if self.x < -20 or self.x > 500 or self.y < -50:
            self.alive = False

    def draw(self, surface):
        """Render the bullet and its glowing energy trail."""
        if not self.alive:
            return

        # 1. Motion trail
        for i, (tx, ty) in enumerate(self.trail):
            ratio = (i + 1) / len(self.trail)
            trail_radius = max(1, int(self.width * 0.45 * ratio))
            tc = (
                int(self.trail_color[0] * ratio),
                int(self.trail_color[1] * ratio),
                int(self.trail_color[2] * ratio),
            )
            pygame.draw.circle(surface, tc, (int(tx), int(ty)), trail_radius)

        # 2. Outer Glow / Body
        body_rect = pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )
        pygame.draw.rect(surface, self.trail_color, body_rect, border_radius=3)

        # 3. Inner Core
        core_rect = pygame.Rect(
            int(self.x - (self.width - 2) // 2),
            int(self.y - (self.height - 2) // 2),
            max(2, self.width - 2),
            max(2, self.height - 4),
        )
        pygame.draw.rect(surface, self.core_color, core_rect, border_radius=2)
