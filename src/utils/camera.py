"""
Camera and screen shake system for Recoil Wing.
Uses trauma-based screen shake for punchy, organic game feel.
"""
import random


class Camera:
    def __init__(self):
        self.trauma = 0.0          # Range 0.0 to 1.0
        self.trauma_decay = 0.04   # Decay per frame
        self.max_offset = 9.0      # Max pixel offset at 1.0 trauma

    def add_trauma(self, amount):
        """Add shake trauma, capped at 1.0."""
        self.trauma = min(1.0, self.trauma + amount)

    def update(self):
        """Decay trauma over time."""
        if self.trauma > 0:
            self.trauma = max(0.0, self.trauma - self.trauma_decay)

    def get_offset(self):
        """
        Calculates (dx, dy) screen shake offset.
        Uses quadratic falloff (shake = trauma^2) for punchy impact that settles quickly.
        """
        if self.trauma <= 0.001:
            return 0, 0

        shake = self.trauma * self.trauma
        dx = int(self.max_offset * shake * random.uniform(-1.0, 1.0))
        dy = int(self.max_offset * shake * random.uniform(-1.0, 1.0))
        return dx, dy
