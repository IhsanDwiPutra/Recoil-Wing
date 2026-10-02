"""
Enemy module for Recoil Wing.
Handles airborne security drones and patrol bots.
"""
import math
import random
import pygame


class Drone:
    """
    Airborne patrol drone that hovers and bobs up and down inside pipe gaps.
    Can be destroyed by downward shots for bonus points and instant ammo refund!
    """
    def __init__(self, x, y, min_y, max_y):
        self.x = float(x)
        self.y = float(y)
        self.base_y = float(y)
        self.min_y = float(min_y)
        self.max_y = float(max_y)

        self.width = 30
        self.height = 22
        self.hp = 1
        self.alive = True

        # Bobbing sinusoidal motion
        self.bob_timer = random.uniform(0.0, 6.28)
        self.bob_speed = random.uniform(0.05, 0.08)
        self.bob_amplitude = min(35.0, (self.max_y - self.min_y) * 0.35)

        # Visual thruster pulse
        self.thruster_timer = 0.0

    @property
    def rect(self):
        """Bounding box for collisions."""
        return pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )

    def update(self, speed):
        """Updates horizontal scrolling and vertical patrol oscillation."""
        # Scroll left with pipe regardless of alive state
        self.x -= speed

        if not self.alive:
            return

        # Vertical bobbing
        self.bob_timer += self.bob_speed
        self.thruster_timer += 0.2
        target_y = self.base_y + math.sin(self.bob_timer) * self.bob_amplitude

        # Keep strictly inside safe corridor
        self.y = max(self.min_y + self.height // 2, min(self.max_y - self.height // 2, target_y))

    def take_damage(self):
        """Damages the drone. Returns True if destroyed."""
        self.hp -= 1
        if self.hp <= 0:
            self.alive = False
            return True
        return False

    def draw(self, surface):
        """Render stylish cyberpunk patrol drone with blinking red optic eye."""
        if not self.alive:
            return

        cx = int(self.x)
        cy = int(self.y)

        # 0. Subtle Optical Pulse Wave (Radar Scan Ping)
        pulse_phase = (self.bob_timer * 3.5) % 18
        if pulse_phase > 4:
            pulse_alpha = int(max(0, 110 - (pulse_phase / 18.0) * 110))
            if pulse_alpha > 0:
                p_surf = pygame.Surface((int(pulse_phase * 2 + 4), int(pulse_phase * 2 + 4)), pygame.SRCALPHA)
                pygame.draw.circle(p_surf, (239, 68, 68, pulse_alpha), (int(pulse_phase + 2), int(pulse_phase + 2)), int(pulse_phase), width=1)
                surface.blit(p_surf, (cx - int(pulse_phase + 2), cy - int(pulse_phase + 2)))

        # 1. Side Thrusters & Jet Glow
        thruster_glow_h = int(6 + math.sin(self.thruster_timer) * 3)
        for offset_x in (-12, 12):
            # Engine pod
            pygame.draw.rect(surface, (51, 65, 85), (cx + offset_x - 3, cy - 5, 6, 10), border_radius=2)
            # Energy flame jet
            pygame.draw.line(surface, (239, 68, 68), (cx + offset_x, cy + 5), (cx + offset_x, cy + 5 + thruster_glow_h), width=3)
            pygame.draw.line(surface, (254, 202, 202), (cx + offset_x, cy + 5), (cx + offset_x, cy + 3 + thruster_glow_h // 2), width=1)

        # 2. Main Chassis (Dark metallic hex-capsule)
        chassis_rect = pygame.Rect(cx - 11, cy - 8, 22, 16)
        pygame.draw.rect(surface, (30, 41, 59), chassis_rect, border_radius=5)
        pygame.draw.rect(surface, (71, 85, 105), chassis_rect, width=2, border_radius=5)

        # 3. Glowing Red Sensor Eye
        eye_pulse = 0.7 + 0.3 * math.sin(self.bob_timer * 2.5)
        eye_color = (int(239 * eye_pulse), 68, 68)
        pygame.draw.circle(surface, eye_color, (cx, cy), 5)
        pygame.draw.circle(surface, (255, 255, 255), (cx, cy), 2)  # Hot core

        # 4. Antenna Spike on top
        pygame.draw.line(surface, (100, 116, 139), (cx, cy - 8), (cx, cy - 13), width=2)
        pygame.draw.circle(surface, (239, 68, 68), (cx, cy - 13), 2)

