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
from src.entities.enemy import Drone


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

        # Spawn hazards inside the gap:
        # 36% chance for a destructible crate on the lower edge
        # 34% chance for an airborne patrol drone bobbing in the middle
        # 30% chance for a clean unobstructed gap
        self.crate = None
        self.drone = None
        roll = random.random()
        if roll < 0.36:
            crate_x = self.x + (self.width - CRATE_SIZE) // 2
            crate_y = self.gap_bottom - CRATE_SIZE
            self.crate = Crate(crate_x, crate_y)
        elif roll < 0.70:
            drone_x = self.x + self.width // 2
            drone_y = self.gap_y
            min_drone_y = self.gap_top + 22
            max_drone_y = self.gap_bottom - 22
            self.drone = Drone(drone_x, drone_y, min_drone_y, max_drone_y)

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
        if self.drone:
            self.drone.update(speed)

    def collides_with_player(self, player_rect):
        """Check collision against solid pipes, active crate, or active drone."""
        if self.top_rect.colliderect(player_rect):
            return True
        if self.bottom_rect.colliderect(player_rect):
            return True
        if self.crate and self.crate.alive and self.crate.rect.colliderect(player_rect):
            return True
        if self.drone and self.drone.alive and self.drone.rect.colliderect(player_rect):
            return True
        return False

    def check_bullet_hit(self, bullet):
        """
        Check if a bullet hits the drone, crate, or pipes.
        Supports piercing laser beams and ricochet bounces.
        Returns a tuple: (hit_type, hit_x, hit_y, destroyed) or None.
        """
        # 1. Drone collision (check first since it bobs centrally in the flight corridor)
        if self.drone and self.drone.alive and self.drone.rect.colliderect(bullet.rect):
            destroyed = self.drone.take_damage()
            if not bullet.piercing:
                bullet.alive = False
            return ("drone", self.drone.rect.centerx, self.drone.rect.centery, destroyed)

        # 2. Crate collision
        if self.crate and self.crate.alive and self.crate.rect.colliderect(bullet.rect):
            destroyed = self.crate.take_damage()
            if not bullet.piercing:
                bullet.alive = False
            return ("crate", self.crate.rect.centerx, self.crate.rect.centery, destroyed)

        # 3. Bottom Pipe collision
        if self.bottom_rect.colliderect(bullet.rect):
            if bullet.bounces > 0:
                bullet.bounce_vertical()
                return ("ricochet", bullet.x, self.bottom_rect.top, False)
            else:
                bullet.alive = False
                return ("pipe", bullet.x, self.bottom_rect.top, False)

        # 4. Top Pipe collision
        if self.top_rect.colliderect(bullet.rect):
            if bullet.bounces > 0:
                bullet.bounce_vertical()
                return ("ricochet", bullet.x, self.top_rect.bottom, False)
            else:
                bullet.alive = False
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

        # 4. Draw Drone if present
        if self.drone and self.drone.alive:
            self.drone.draw(surface)



class PerkGate:
    """Individual glowing holographic energy portal in a gate pair."""
    def __init__(self, perk_data, y, height=120):
        self.perk = perk_data
        self.y = float(y)
        self.height = height
        self.width = 76
        self.pulse = random.uniform(0, 6.28)

    def draw(self, surface, x, font):
        color = self.perk["color"]
        self.pulse += 0.08
        r = pygame.Rect(int(x), int(self.y - self.height // 2), self.width, self.height)

        # Translucent energy field
        gate_surf = pygame.Surface((r.width, r.height), pygame.SRCALPHA)
        gate_surf.fill((color[0], color[1], color[2], 40))
        # Pulsing energy border
        pygame.draw.rect(gate_surf, color, (0, 0, r.width, r.height), width=3, border_radius=8)

        # Inner holographic lines
        for line_y in range(12, r.height - 10, 18):
            pygame.draw.line(gate_surf, (255, 255, 255, 130), (8, line_y), (r.width - 8, line_y), width=1)
        surface.blit(gate_surf, r.topleft)

        # Top & Bottom metallic emitter nodes
        pygame.draw.circle(surface, (203, 213, 225), (r.centerx, r.top), 6)
        pygame.draw.circle(surface, color, (r.centerx, r.top), 3)
        pygame.draw.circle(surface, (203, 213, 225), (r.centerx, r.bottom), 6)
        pygame.draw.circle(surface, color, (r.centerx, r.bottom), 3)

        # Center Badge Pill with Perk Name
        pill_w = 88
        pill_rect = pygame.Rect(r.centerx - pill_w // 2, r.centery - 13, pill_w, 26)
        pygame.draw.rect(surface, (15, 23, 42), pill_rect, border_radius=6)
        pygame.draw.rect(surface, color, pill_rect, width=2, border_radius=6)

        text_surf = font.render(self.perk["badge"], True, color)
        surface.blit(text_surf, text_surf.get_rect(center=pill_rect.center))


class PerkGatePair:
    """
    In-flight choice gate pair.
    Offers two perks (Upper Gate vs Lower Gate) in real-time.
    Safe to fly through, no pauses, and no crash if missed!
    """
    def __init__(self, x, perk1, perk2, ground_y):
        self.x = float(x)
        self.width = 76
        self.ground_y = ground_y
        self.passed = False
        self.collected = False

        # Two gates placed vertically
        self.gate_top = PerkGate(perk1, 230)
        self.gate_bottom = PerkGate(perk2, ground_y - 190)

    def update(self, speed):
        self.x -= speed

    def check_player_interaction(self, player_rect):
        """
        Checks if player flew through either gate.
        Returns the chosen perk dict if collected, or None.
        """
        if self.collected:
            return None

        top_rect = pygame.Rect(
            int(self.x),
            int(self.gate_top.y - self.gate_top.height // 2),
            self.width,
            self.gate_top.height,
        )
        if top_rect.colliderect(player_rect):
            self.collected = True
            return self.gate_top.perk

        bottom_rect = pygame.Rect(
            int(self.x),
            int(self.gate_bottom.y - self.gate_bottom.height // 2),
            self.width,
            self.gate_bottom.height,
        )
        if bottom_rect.colliderect(player_rect):
            self.collected = True
            return self.gate_bottom.perk

        return None

    def draw(self, surface, font):
        """Draw top and bottom choice portals with glowing label."""
        if not self.collected:
            self.gate_top.draw(surface, self.x, font)
            self.gate_bottom.draw(surface, self.x, font)

