"""
Player entity module for Recoil Wing.
Handles physics, rotation tilt, and rendering.
"""
import math
import pygame
from src.config import (
    GRAVITY,
    MAX_FALL_SPEED,
    MAX_CLIMB_SPEED,
    RECOIL_FORCE,
    PLAYER_WIDTH,
    PLAYER_HEIGHT,
    PLAYER_START_X,
    PLAYER_START_Y,
    COLOR_PLAYER,
    COLOR_PLAYER_EYE,
    COLOR_PLAYER_BEAK,
    COLOR_GUN,
)


class Player:
    def __init__(self, x=PLAYER_START_X, y=PLAYER_START_Y):
        self.start_x = x
        self.start_y = y
        self.x = float(x)
        self.y = float(y)
        self.width = PLAYER_WIDTH
        self.height = PLAYER_HEIGHT
        self.vy = 0.0
        self.rotation = 0.0
        self.target_rotation = 0.0
        self.is_alive = True

        # Visual kickback offset when firing
        self.kickback_y = 0.0

    @property
    def rect(self):
        """Bounding box for collision detection."""
        return pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )

    def recoil_jump(self, force=RECOIL_FORCE):
        """Applies an upward impulse via downward recoil."""
        if not self.is_alive:
            return
        
        # Upward impulse (negative Y in screen space)
        self.vy = -force
        if self.vy < MAX_CLIMB_SPEED:
            self.vy = MAX_CLIMB_SPEED
            
        self.kickback_y = -3.0  # Visual bump upward

    def update(self, dt=1.0):
        """Update physics, position, and rotation tilt."""
        # Decay visual kickback
        if self.kickback_y < 0:
            self.kickback_y = min(0.0, self.kickback_y + 0.5)

        # Apply gravity
        self.vy += GRAVITY * dt
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # Update position
        self.y += self.vy * dt

        # Calculate smooth rotation based on vertical speed
        # Falling tilts nose downward (+angle), rising tilts upward (-angle)
        if self.vy < 0:
            self.target_rotation = max(-25.0, self.vy * 3.5)
        else:
            self.target_rotation = min(70.0, self.vy * 6.5)

        # Smooth interpolation (lerp) for rotation
        self.rotation += (self.target_rotation - self.rotation) * 0.18

    def draw(self, surface):
        """Draw a stylized, sharp cyber-bird with downward heavy cannon nozzle."""
        # Create a surface for rotation
        diag = int(math.hypot(self.width + 12, self.height + 12)) + 10
        char_surf = pygame.Surface((diag, diag), pygame.SRCALPHA)
        center = (diag // 2, diag // 2)

        # Offset for kickback
        draw_center_y = center[1] + int(self.kickback_y)

        # 1. Heavy Under-Gun (Downward pointing blaster)
        gun_rect = pygame.Rect(0, 0, 10, 14)
        gun_rect.center = (center[0] - 2, draw_center_y + 10)
        pygame.draw.rect(char_surf, COLOR_GUN, gun_rect, border_radius=3)
        # Gun barrel tip
        pygame.draw.rect(char_surf, (30, 41, 59), (gun_rect.left, gun_rect.bottom - 4, gun_rect.width, 4))

        # 2. Main Body (Teal / Cyan aerodynamic capsule)
        body_rect = pygame.Rect(0, 0, self.width, self.height)
        body_rect.center = (center[0], draw_center_y)
        pygame.draw.ellipse(char_surf, COLOR_PLAYER, body_rect)
        pygame.draw.ellipse(char_surf, (20, 184, 166), body_rect, width=2)

        # 3. Visor / Eye
        eye_center = (center[0] + 6, draw_center_y - 4)
        pygame.draw.circle(char_surf, COLOR_PLAYER_EYE, eye_center, 5)
        pygame.draw.circle(char_surf, (15, 23, 42), (eye_center[0] + 1, eye_center[1]), 3)
        # Eye highlight reflection
        pygame.draw.circle(char_surf, (255, 255, 255), (eye_center[0] + 2, eye_center[1] - 1), 1)

        # 4. Beak / Aerodynamic Nose Cone
        beak_points = [
            (center[0] + self.width // 2 - 2, draw_center_y - 2),
            (center[0] + self.width // 2 + 8, draw_center_y + 1),
            (center[0] + self.width // 2 - 2, draw_center_y + 5),
        ]
        pygame.draw.polygon(char_surf, COLOR_PLAYER_BEAK, beak_points)

        # 5. Wing Detail (Side thruster/wing)
        wing_rect = pygame.Rect(0, 0, 14, 8)
        wing_rect.center = (center[0] - 6, draw_center_y + 2)
        pygame.draw.ellipse(char_surf, (94, 234, 212), wing_rect)

        # Rotate entire surface according to tilt
        # In pygame, positive rotation rotates counter-clockwise.
        # Nose down should rotate clockwise (negative angle).
        rotated_surf = pygame.transform.rotate(char_surf, -self.rotation)
        rotated_rect = rotated_surf.get_rect(center=(int(self.x), int(self.y)))

        surface.blit(rotated_surf, rotated_rect.topleft)

    def reset(self):
        """Reset player to starting state."""
        self.x = float(self.start_x)
        self.y = float(self.start_y)
        self.vy = 0.0
        self.rotation = 0.0
        self.target_rotation = 0.0
        self.is_alive = True
        self.kickback_y = 0.0
