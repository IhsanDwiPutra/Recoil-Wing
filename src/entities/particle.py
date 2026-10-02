"""
Particle and visual effects system for Recoil Wing.
Handles visual sparks, debris chunks, shell casings, smoke puffs, and floating score texts.
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

        pygame.draw.circle(surface, self.color, (int(self.x), int(self.y)), radius)


class ShellCasing:
    """Ejected brass bullet casing that flips through the air."""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        # Ejected backwards & upward
        self.vx = random.uniform(-3.5, -1.5)
        self.vy = random.uniform(-4.5, -2.0)
        self.angle = random.uniform(0, 360)
        self.rotation_speed = random.uniform(-18.0, 18.0)
        self.gravity = 0.32
        self.life = 55
        self.alive = True

    def update(self, ground_y):
        if not self.alive:
            return

        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return

        self.vy += self.gravity
        self.x += self.vx
        self.y += self.vy
        self.angle += self.rotation_speed

        # Bounce on ground
        if self.y >= ground_y - 2:
            self.y = ground_y - 2
            self.vy = -self.vy * 0.4
            self.vx *= 0.6
            self.rotation_speed *= 0.5
            if abs(self.vy) < 1.0:
                self.vy = 0

    def draw(self, surface):
        if not self.alive:
            return

        casing_surf = pygame.Surface((3, 6), pygame.SRCALPHA)
        # Golden brass casing
        casing_surf.fill((234, 179, 8))
        pygame.draw.rect(casing_surf, (202, 138, 4), (0, 0, 3, 2))  # Rim

        rotated = pygame.transform.rotate(casing_surf, self.angle)
        rect = rotated.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated, rect.topleft)


class SmokePuff:
    """Soft expanding smoke puff from weapon nozzle."""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-0.6, 0.6)
        self.vy = random.uniform(0.5, 1.5)
        self.radius = 3.0
        self.max_radius = random.uniform(9.0, 13.0)
        self.life = 20
        self.max_life = 20
        self.alive = True

    def update(self):
        if not self.alive:
            return
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return

        self.x += self.vx
        self.y += self.vy
        ratio = 1.0 - (self.life / self.max_life)
        self.radius = 3.0 + (self.max_radius - 3.0) * ratio

    def draw(self, surface):
        if not self.alive:
            return

        alpha = int(140 * (self.life / self.max_life))
        r = int(self.radius)
        if r < 1:
            return

        smoke_surf = pygame.Surface((r * 2, r * 2), pygame.SRCALPHA)
        pygame.draw.circle(smoke_surf, (148, 163, 184, alpha), (r, r), r)
        surface.blit(smoke_surf, (int(self.x - r), int(self.y - r)))


class FloatingText:
    """Floating score / combo popup text."""
    def __init__(self, text, x, y, color, font):
        self.text = text
        self.x = float(x)
        self.y = float(y)
        self.color = color
        self.font = font
        self.vy = -1.6
        self.life = 36
        self.max_life = 36
        self.alive = True

    def update(self):
        if not self.alive:
            return
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        self.y += self.vy
        self.vy *= 0.94  # Decelerate upward glide

    def draw(self, surface):
        if not self.alive:
            return
        # Render text with drop shadow
        shadow_surf = self.font.render(self.text, True, (15, 23, 42))
        text_surf = self.font.render(self.text, True, self.color)
        rect = text_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(shadow_surf, (rect.x + 1, rect.y + 1))
        surface.blit(text_surf, rect)


def create_crate_debris(x, y, count=14):
    """Spawns an explosive burst of square/chunky debris when a crate is destroyed."""
    particles = []
    colors = [(239, 68, 68), (249, 115, 22), (251, 191, 36), (254, 202, 202)]
    for _ in range(count):
        angle_vx = random.uniform(-4.5, 4.5)
        angle_vy = random.uniform(-6.5, -1.0)
        color = random.choice(colors)
        size = random.uniform(3.0, 6.0)
        life = random.randint(20, 32)
        particles.append(Particle(x, y, angle_vx, angle_vy, color, size, life, gravity=0.28))
    return particles


def create_spark_burst(x, y, count=7, color=(250, 204, 21)):
    """Spawns tiny high-speed sparks on metallic impact."""
    particles = []
    for _ in range(count):
        vx = random.uniform(-3.5, 3.5)
        vy = random.uniform(-4.5, 1.5)
        size = random.uniform(1.5, 3.0)
        life = random.randint(8, 16)
        particles.append(Particle(x, y, vx, vy, color, size, life, gravity=0.15))
    return particles


def create_drone_debris(x, y, count=16):
    """Spawns cybernetic shrapnel and electrical sparks when a drone is destroyed."""
    particles = []
    colors = [(51, 65, 85), (30, 41, 59), (239, 68, 68), (250, 204, 21), (254, 202, 202)]
    for _ in range(count):
        vx = random.uniform(-5.0, 5.0)
        vy = random.uniform(-6.0, 2.0)
        color = random.choice(colors)
        size = random.uniform(2.0, 5.0)
        life = random.randint(18, 30)
        particles.append(Particle(x, y, vx, vy, color, size, life, gravity=0.25))
    return particles

