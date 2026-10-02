"""
Particle system for Recoil Wing.
Handles visual sparks, debris chunks, and smoke.
"""
import random
import pygame


class Particle:
    def __init__(self, x, y, vx, vy, color, size, life, gravity=0.2, fade=True):
        self.x = float(x)
        self.y = float(y)
        self.vx = float(vx)
        self.vy = float(vy)
        self.color = color
        self.size = float(size)
        self.initial_size = float(size)
        self.life = float(life)
        self.max_life = float(life)
        self.gravity = gravity
        self.fade = fade
        self.alive = True

    def update(self):
        if not self.alive:
            return

        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return

        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy

        # Shrink over time
        ratio = self.life / self.max_life
        self.size = max(1.0, self.initial_size * ratio)

    def draw(self, surface):
        if not self.alive:
            return

        radius = int(self.size)
        if radius < 1:
            return

        # Simple circle rendering
        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius)


def create_crate_debris(x, y, count=12):
    """Spawns an explosive burst of square/chunky debris when a crate is destroyed."""
    particles = []
    colors = [(239, 68, 68), (249, 115, 22), (251, 191, 36), (254, 202, 202)]
    for _ in range(count):
        angle_vx = random.uniform(-4.0, 4.0)
        angle_vy = random.uniform(-6.0, -1.0)
        color = random.choice(colors)
        size = random.uniform(3.0, 6.0)
        life = random.randint(18, 30)
        particles.append(Particle(x, y, angle_vx, angle_vy, color, size, life, gravity=0.28))
    return particles


def create_spark_burst(x, y, count=6, color=(250, 204, 21)):
    """Spawns tiny high-speed sparks on metallic impact."""
    particles = []
    for _ in range(count):
        vx = random.uniform(-3.0, 3.0)
        vy = random.uniform(-4.0, 1.0)
        size = random.uniform(1.5, 3.0)
        life = random.randint(8, 16)
        particles.append(Particle(x, y, vx, vy, color, size, life, gravity=0.15))
    return particles
