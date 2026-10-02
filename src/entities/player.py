"""
Player entity module for Recoil Wing.
Handles physics, rotation tilt, weapons/perks, and procedural rendering.
"""
import math
import random
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
    MAX_AMMO,
    AMMO_RELOAD_FRAMES,
    COLOR_PLAYER,
    COLOR_PLAYER_EYE,
    COLOR_PLAYER_BEAK,
    COLOR_GUN,
    COLOR_MUZZLE_FLASH,
)
from src.entities.bullet import Bullet


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

        # Ammo and weapon state
        self.max_ammo = MAX_AMMO
        self.ammo = MAX_AMMO
        self.ammo_reload_timer = 0
        self.reload_frames = AMMO_RELOAD_FRAMES
        self.muzzle_flash_timer = 0

        # Perks & Upgrades
        self.weapon_type = "STANDARD"   # "STANDARD", "SHOTGUN", "PIERCER"
        self.has_bouncy = False
        self.shield_charges = 0
        self.shield_pulse = 0.0

        # Visual kickback offset when firing
        self.kickback_y = 0.0

        # Combo Streak Afterimage Trail
        self.trail_history = []

    @property
    def rect(self):
        """Bounding box for collision detection."""
        return pygame.Rect(
            int(self.x - self.width // 2),
            int(self.y - self.height // 2),
            self.width,
            self.height,
        )

    def shoot(self):
        """
        Shoots proyektil(s) downward, generating upward recoil impulse.
        Returns a list of spawned Bullet instances (empty list if dry fire).
        """
        if not self.is_alive or self.ammo <= 0:
            return []

        # Deduct ammo
        self.ammo -= 1

        # Base spawn coords
        spawn_x = self.x - 2
        spawn_y = self.y + self.height // 2 + 6
        bullets = []

        # Weapon Type Branching
        if self.weapon_type == "SHOTGUN":
            recoil = RECOIL_FORCE * 1.25
            self.vy = -recoil
            self.kickback_y = -6.0
            self.muzzle_flash_timer = 5
            # 3 pellets spread
            bullets.append(Bullet(spawn_x - 4, spawn_y, vx=-2.6, vy=14.5))
            bullets.append(Bullet(spawn_x, spawn_y, vx=0.0, vy=15.5))
            bullets.append(Bullet(spawn_x + 4, spawn_y, vx=2.6, vy=14.5))

        elif self.weapon_type == "PIERCER":
            self.vy = -RECOIL_FORCE
            self.kickback_y = -4.0
            self.muzzle_flash_timer = 6
            # High speed laser beam
            laser = Bullet(
                spawn_x,
                spawn_y,
                vx=0.0,
                vy=22.0,
                piercing=True,
                core_color=(240, 171, 252),
                trail_color=(192, 132, 252),
            )
            bullets.append(laser)

        elif self.has_bouncy:
            self.vy = -RECOIL_FORCE
            self.kickback_y = -4.0
            self.muzzle_flash_timer = 4
            # Ricochet bullet
            b = Bullet(
                spawn_x,
                spawn_y,
                vx=random.uniform(-1.5, 1.5),
                vy=14.0,
                bounces=2,
                core_color=(254, 240, 138),
                trail_color=(234, 179, 8),
            )
            bullets.append(b)

        else:
            # Standard single shot
            self.vy = -RECOIL_FORCE
            self.kickback_y = -4.0
            self.muzzle_flash_timer = 4
            bullets.append(Bullet(spawn_x, spawn_y))

        # Clamp max upward climb speed
        if self.vy < MAX_CLIMB_SPEED:
            self.vy = MAX_CLIMB_SPEED

        return bullets

    def update(self, dt=1.0, combo_count=0):
        """Update physics, position, ammo reload, rotation tilt, and combo trail."""
        # Shield pulse animation
        if self.shield_charges > 0:
            self.shield_pulse += 0.08

        # Decay visual kickback
        if self.kickback_y < 0:
            self.kickback_y = min(0.0, self.kickback_y + 0.6)

        # Decay muzzle flash
        if self.muzzle_flash_timer > 0:
            self.muzzle_flash_timer -= 1

        # Ammo regeneration over time
        if self.ammo < self.max_ammo:
            self.ammo_reload_timer += 1
            if self.ammo_reload_timer >= self.reload_frames:
                self.ammo += 1
                self.ammo_reload_timer = 0
        else:
            self.ammo_reload_timer = 0

        # Apply gravity
        self.vy += GRAVITY * dt
        if self.vy > MAX_FALL_SPEED:
            self.vy = MAX_FALL_SPEED

        # Update position
        self.y += self.vy * dt

        # Smooth rotation tilt
        if self.vy < 0:
            self.target_rotation = max(-25.0, self.vy * 3.5)
        else:
            self.target_rotation = min(70.0, self.vy * 6.5)

        self.rotation += (self.target_rotation - self.rotation) * 0.18

        # Combo Afterimage Trail Recording
        if combo_count >= 2 and self.is_alive:
            self.trail_history.append((self.x, self.y, self.rotation, combo_count))
            if len(self.trail_history) > 6:
                self.trail_history.pop(0)
        else:
            if self.trail_history:
                self.trail_history.pop(0)

    def draw(self, surface):
        """Draw stylized cyber-bird, combo afterimage trail, and active energy shield."""
        # 0. Combo Streak Afterimage Motion Trail
        if self.trail_history:
            for idx, (tx, ty, trot, tcombo) in enumerate(self.trail_history):
                ratio = (idx + 1) / len(self.trail_history)
                alpha = int(75 * ratio)
                if tcombo == 2:
                    tcolor = (45, 212, 191, alpha)   # Neon Teal
                elif tcombo == 3:
                    tcolor = (250, 204, 21, alpha)   # Electric Gold
                elif tcombo == 4:
                    tcolor = (244, 63, 94, alpha)    # Hyper Rose
                else:
                    tcolor = (168, 85, 247, alpha)   # Cosmic Violet

                ghost_surf = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
                pygame.draw.ellipse(ghost_surf, tcolor, (0, 0, self.width, self.height))
                rot_ghost = pygame.transform.rotate(ghost_surf, -trot)
                surface.blit(rot_ghost, rot_ghost.get_rect(center=(int(tx), int(ty))))

        # 1. Energy Shield Bubble
        if self.shield_charges > 0:
            shield_radius = int(self.width * 0.85 + math.sin(self.shield_pulse) * 3)
            shield_surf = pygame.Surface((shield_radius * 2 + 10, shield_radius * 2 + 10), pygame.SRCALPHA)
            sc = (shield_radius + 5, shield_radius + 5)
            # Soft inner glow
            pygame.draw.circle(shield_surf, (56, 189, 248, 40), sc, shield_radius)
            # Crisp outer shield line
            pygame.draw.circle(shield_surf, (56, 189, 248, 210), sc, shield_radius, width=2)
            # Shield node orbits
            for i in range(3):
                node_angle = self.shield_pulse + (i * (math.pi * 2 / 3))
                nx = sc[0] + int(math.cos(node_angle) * shield_radius)
                ny = sc[1] + int(math.sin(node_angle) * shield_radius)
                pygame.draw.circle(shield_surf, (255, 255, 255), (nx, ny), 3)

            surface.blit(shield_surf, (int(self.x - sc[0]), int(self.y - sc[1])))

        # 2. Main Character Body & Gun
        diag = int(math.hypot(self.width + 16, self.height + 24)) + 14
        char_surf = pygame.Surface((diag, diag), pygame.SRCALPHA)
        center = (diag // 2, diag // 2)

        draw_center_y = center[1] + int(self.kickback_y)

        # Under-Gun
        gun_w = 14 if self.weapon_type == "SHOTGUN" else 10
        gun_rect = pygame.Rect(0, 0, gun_w, 14)
        gun_rect.center = (center[0] - 2, draw_center_y + 10)
        gun_color = (244, 63, 94) if self.weapon_type == "SHOTGUN" else (168, 85, 247) if self.weapon_type == "PIERCER" else COLOR_GUN
        pygame.draw.rect(char_surf, gun_color, gun_rect, border_radius=3)
        pygame.draw.rect(char_surf, (30, 41, 59), (gun_rect.left, gun_rect.bottom - 4, gun_rect.width, 4))

        # Muzzle Flash
        if self.muzzle_flash_timer > 0:
            flash_tip = (gun_rect.centerx, gun_rect.bottom + 9)
            flash_points = [
                (gun_rect.centerx, gun_rect.bottom),
                (gun_rect.centerx + 7, gun_rect.bottom + 4),
                flash_tip,
                (gun_rect.centerx - 7, gun_rect.bottom + 4),
            ]
            flash_color = (254, 240, 138) if self.weapon_type != "PIERCER" else (240, 171, 252)
            pygame.draw.polygon(char_surf, flash_color, flash_points)
            pygame.draw.circle(char_surf, (255, 255, 255), (gun_rect.centerx, gun_rect.bottom + 3), 2)

        # Body Capsule
        body_rect = pygame.Rect(0, 0, self.width, self.height)
        body_rect.center = (center[0], draw_center_y)
        pygame.draw.ellipse(char_surf, COLOR_PLAYER, body_rect)
        pygame.draw.ellipse(char_surf, (20, 184, 166), body_rect, width=2)

        # Visor / Eye
        eye_center = (center[0] + 6, draw_center_y - 4)
        pygame.draw.circle(char_surf, COLOR_PLAYER_EYE, eye_center, 5)
        pygame.draw.circle(char_surf, (15, 23, 42), (eye_center[0] + 1, eye_center[1]), 3)
        pygame.draw.circle(char_surf, (255, 255, 255), (eye_center[0] + 2, eye_center[1] - 1), 1)

        # Beak / Nose Cone
        beak_points = [
            (center[0] + self.width // 2 - 2, draw_center_y - 2),
            (center[0] + self.width // 2 + 8, draw_center_y + 1),
            (center[0] + self.width // 2 - 2, draw_center_y + 5),
        ]
        pygame.draw.polygon(char_surf, COLOR_PLAYER_BEAK, beak_points)

        # Wing Thruster
        wing_rect = pygame.Rect(0, 0, 14, 8)
        wing_rect.center = (center[0] - 6, draw_center_y + 2)
        pygame.draw.ellipse(char_surf, (94, 234, 212), wing_rect)

        # Rotate entire bird according to tilt
        rotated_surf = pygame.transform.rotate(char_surf, -self.rotation)
        rotated_rect = rotated_surf.get_rect(center=(int(self.x), int(self.y)))
        surface.blit(rotated_surf, rotated_rect.topleft)

    def reset(self):
        """Reset player to default state."""
        self.x = float(self.start_x)
        self.y = float(self.start_y)
        self.vy = 0.0
        self.rotation = 0.0
        self.target_rotation = 0.0
        self.is_alive = True
        self.kickback_y = 0.0

        # Reset perks
        self.weapon_type = "STANDARD"
        self.has_bouncy = False
        self.shield_charges = 0
        self.shield_pulse = 0.0
        self.max_ammo = MAX_AMMO
        self.reload_frames = AMMO_RELOAD_FRAMES
        self.ammo = self.max_ammo
        self.ammo_reload_timer = 0
        self.muzzle_flash_timer = 0
        self.trail_history.clear()
