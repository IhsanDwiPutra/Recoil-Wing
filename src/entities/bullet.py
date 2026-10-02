"""
Bullet entity for Recoil Wing.
Handles projectile physics, trail rendering, and lifecycle.
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
    def __init__(self, x, y, spread=True):
        self.x = float(x)
        self.y = float(y)
        self.width = BULLET_WIDTH
        self.height = BULLET_HEIGHT
        
        # Downward trajectory with slight horizontal spread for game feel
        self.vx = random.uniform(-0.8, 0.8) if spread else 0.0
        self.vy = BULLET_SPEED + random.uniform(0.0, 1.5)

        self.alive = True
        self.trail = []  # Stores previous (x, y) coordinates for motion blur trail

    @property
    def rect(self):
        """Bounding box for collisions."""
        return pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )

    def update(self, max_y):
        """Update bullet position and trail."""
        if not self.alive:
            return

        # Record trail position
        self.trail.append((self.x, self.y))
        if len(self.trail) > 5:
            self.trail.pop(0)

        # Move
        self.x += self.vx
        self.y += self.vy

        # Check bounds (ground or screen bottom)
        if self.y >= max_y:
            self.alive = False

    def draw(self, surface):
        """Render the bullet and its glowing energy trail."""
        if not self.alive:
            return

        # 1. Draw motion trail (gradient fade)
        for i, (tx, ty) in enumerate(self.trail):
            ratio = (i + 1) / len(self.trail)
            trail_radius = max(1, int(self.width * 0.4 * ratio))
            trail_color = (
                int(COLOR_BULLET_TRAIL[0] * ratio),
                int(COLOR_BULLET_TRAIL[1] * ratio),
                int(COLOR_BULLET_TRAIL[2] * ratio),
            )
            pygame.draw.circle(surface, trail_color, (int(tx), int(ty)), trail_radius)

        # 2. Outer Glow / Body
        body_rect = pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )
        pygame.draw.rect(surface, COLOR_BULLET_TRAIL, body_rect, border_radius=3)

        # 3. Inner Bright Core
        core_rect = pygame.Rect(
            int(self.x - (self.width - 2) // 2),
            int(self.y - (self.height - 2) // 2),
            max(2, self.width - 2),
            max(2, self.height - 4),
        )
        pygame.draw.rect(surface, COLOR_BULLET, core_rect, border_radius=2)
