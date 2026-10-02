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
        self.passed = False

        self.crate = None
        self.drone = None
        self.is_dual_lane = False

        # Hazard spawning strategy:
        # 38% chance: Dual-Lane Drone Obstacle (1 safe evasion lane, 1 combat drone lane)
        # 36% chance: Single-Lane Crate Obstacle (destructible crate on bottom edge)
        # 26% chance: Single-Lane Clear Obstacle (unobstructed single gap)
        roll = random.random()
        if roll < 0.38:
            # === DUAL-LANE DRONE PIPE ===
            self.is_dual_lane = True

            # Two generous 150px corridors divided by a 44px central pipe hub
            lane_h = 150
            divider_h = 44
            total_span = lane_h * 2 + divider_h  # 344 px

            # Randomize vertical placement within ground limits
            min_top = 45
            max_top = max(min_top, int(ground_y - total_span - 45))
            self.gap1_top = random.randint(min_top, max_top)
            self.gap1_bottom = self.gap1_top + lane_h

            self.mid_top = self.gap1_bottom
            self.mid_bottom = self.mid_top + divider_h

            self.gap2_top = self.mid_bottom
            self.gap2_bottom = self.gap2_top + lane_h

            # Decide which lane has the drone: "top" or "bottom"
            self.drone_lane = random.choice(["top", "bottom"])
            if self.drone_lane == "top":
                drone_y = (self.gap1_top + self.gap1_bottom) // 2
                min_y = self.gap1_top + 16
                max_y = self.gap1_bottom - 16
            else:
                drone_y = (self.gap2_top + self.gap2_bottom) // 2
                min_y = self.gap2_top + 16
                max_y = self.gap2_bottom - 16

            drone_x = self.x + self.width // 2
            self.drone = Drone(drone_x, drone_y, min_y, max_y)
            self.drone.bob_amplitude = 18.0  # Controlled bobbing for fair hitboxes

        else:
            # === SINGLE-LANE STANDARD PIPE ===
            self.is_dual_lane = False
            self.gap_height = PIPE_GAP

            min_gap_y = PIPE_MIN_HEIGHT + self.gap_height // 2
            max_gap_y = ground_y - PIPE_MIN_HEIGHT - self.gap_height // 2
            self.gap_y = random.randint(min_gap_y, max_gap_y)

            self.gap_top = self.gap_y - self.gap_height // 2
            self.gap_bottom = self.gap_y + self.gap_height // 2

            # Spawn crate on bottom edge if roll < 0.74 (36% of total pipes)
            if roll < 0.74:
                crate_x = self.x + (self.width - CRATE_SIZE) // 2
                crate_y = self.gap_bottom - CRATE_SIZE
                self.crate = Crate(crate_x, crate_y)

    @property
    def top_rect(self):
        if self.is_dual_lane:
            return pygame.Rect(int(self.x), 0, self.width, self.gap1_top)
        return pygame.Rect(int(self.x), 0, self.width, self.gap_top)

    @property
    def middle_rect(self):
        if self.is_dual_lane:
            return pygame.Rect(int(self.x), self.mid_top, self.width, self.mid_bottom - self.mid_top)
        return pygame.Rect(0, 0, 0, 0)

    @property
    def bottom_rect(self):
        if self.is_dual_lane:
            return pygame.Rect(
                int(self.x),
                self.gap2_bottom,
                self.width,
                self.ground_y - self.gap2_bottom,
            )
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
        """Check collision against solid pipes, middle divider, active crate, or active drone."""
        if self.top_rect.colliderect(player_rect):
            return True
        if self.bottom_rect.colliderect(player_rect):
            return True
        if self.is_dual_lane and self.middle_rect.colliderect(player_rect):
            return True
        if self.crate and self.crate.alive and self.crate.rect.colliderect(player_rect):
            return True
        if self.drone and self.drone.alive and self.drone.rect.colliderect(player_rect):
            return True
        return False

    def check_bullet_hit(self, bullet):
        """
        Check if a bullet hits the drone, crate, middle divider, or pipes.
        Supports piercing laser beams and ricochet bounces.
        Returns a tuple: (hit_type, hit_x, hit_y, destroyed) or None.
        """
        # 1. Drone collision (check first since drone is an active airborne target)
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

        # 3. Middle divider collision (in dual-lane pipes)
        if self.is_dual_lane and self.middle_rect.colliderect(bullet.rect):
            if bullet.bounces > 0:
                bullet.bounce_vertical()
                return ("ricochet", bullet.x, self.middle_rect.centery, False)
            else:
                bullet.alive = False
                return ("pipe", bullet.x, self.middle_rect.centery, False)

        # 4. Bottom Pipe collision
        if self.bottom_rect.colliderect(bullet.rect):
            if bullet.bounces > 0:
                bullet.bounce_vertical()
                return ("ricochet", bullet.x, self.bottom_rect.top, False)
            else:
                bullet.alive = False
                return ("pipe", bullet.x, self.bottom_rect.top, False)

        # 5. Top Pipe collision
        if self.top_rect.colliderect(bullet.rect):
            if bullet.bounces > 0:
                bullet.bounce_vertical()
                return ("ricochet", bullet.x, self.top_rect.bottom, False)
            else:
                bullet.alive = False
                return ("pipe", bullet.x, self.top_rect.bottom, False)

        return None

    def draw(self, surface):
        """Draw top, bottom, and optional middle divider pipes with shaded industrial styling."""
        ix = int(self.x)
        collar_h = 22
        collar_overhang = 4

        if self.is_dual_lane:
            # === DUAL-LANE RENDERING ===
            # 1. Top Pipe Body & Collar
            top_body_rect = pygame.Rect(ix, 0, self.width, max(0, self.gap1_top - collar_h))
            pygame.draw.rect(surface, COLOR_PIPE, top_body_rect)
            top_collar = pygame.Rect(
                ix - collar_overhang,
                max(0, self.gap1_top - collar_h),
                self.width + collar_overhang * 2,
                collar_h,
            )
            pygame.draw.rect(surface, (51, 65, 85), top_collar, border_radius=2)
            pygame.draw.rect(surface, COLOR_PIPE_OUTLINE, top_collar, width=2, border_radius=2)

            # 2. Middle Divider Pipe Hub
            mid_r = self.middle_rect
            pygame.draw.rect(surface, COLOR_PIPE, mid_r, border_radius=3)
            pygame.draw.rect(surface, COLOR_PIPE_OUTLINE, mid_r, width=2, border_radius=3)

            # Divider rim collars (top & bottom rims of divider)
            pygame.draw.rect(surface, (51, 65, 85), (ix - 2, mid_r.top, self.width + 4, 6), border_radius=2)
            pygame.draw.rect(surface, (51, 65, 85), (ix - 2, mid_r.bottom - 6, self.width + 4, 6), border_radius=2)

            # Waypoint Status LEDs on Divider Hub (showing Safe vs Danger lane!)
            top_led_color = (239, 68, 68) if self.drone_lane == "top" else (45, 212, 191)
            bot_led_color = (239, 68, 68) if self.drone_lane == "bottom" else (45, 212, 191)
            pygame.draw.circle(surface, top_led_color, (ix + self.width // 2, mid_r.top + 10), 3)
            pygame.draw.circle(surface, bot_led_color, (ix + self.width // 2, mid_r.bottom - 10), 3)

            # 3. Bottom Pipe Body & Collar
            bottom_collar = pygame.Rect(
                ix - collar_overhang,
                self.gap2_bottom,
                self.width + collar_overhang * 2,
                collar_h,
            )
            pygame.draw.rect(surface, (51, 65, 85), bottom_collar, border_radius=2)
            pygame.draw.rect(surface, COLOR_PIPE_OUTLINE, bottom_collar, width=2, border_radius=2)

            bottom_body_rect = pygame.Rect(
                ix,
                self.gap2_bottom + collar_h,
                self.width,
                max(0, self.ground_y - (self.gap2_bottom + collar_h)),
            )
            pygame.draw.rect(surface, COLOR_PIPE, bottom_body_rect)

            # Cylindrical highlights & shadows
            hl_x = ix + 10
            sh_x = ix + self.width - 6
            if top_body_rect.height > 0:
                pygame.draw.line(surface, (100, 116, 139), (hl_x, 0), (hl_x, top_body_rect.bottom), width=3)
                pygame.draw.line(surface, (30, 41, 59), (sh_x, 0), (sh_x, top_body_rect.bottom), width=3)
            if bottom_body_rect.height > 0:
                pygame.draw.line(surface, (100, 116, 139), (hl_x, bottom_body_rect.top), (hl_x, bottom_body_rect.bottom), width=3)
                pygame.draw.line(surface, (30, 41, 59), (sh_x, bottom_body_rect.top), (sh_x, bottom_body_rect.bottom), width=3)

            # 4. Draw Drone if alive
            if self.drone and self.drone.alive:
                self.drone.draw(surface)

        else:
            # === SINGLE-LANE RENDERING ===
            # 1. Top Pipe Body & Collar
            top_body_rect = pygame.Rect(ix, 0, self.width, max(0, self.gap_top - collar_h))
            pygame.draw.rect(surface, COLOR_PIPE, top_body_rect)
            top_collar_rect = pygame.Rect(
                ix - collar_overhang,
                max(0, self.gap_top - collar_h),
                self.width + collar_overhang * 2,
                collar_h,
            )
            pygame.draw.rect(surface, (51, 65, 85), top_collar_rect, border_radius=2)
            pygame.draw.rect(surface, COLOR_PIPE_OUTLINE, top_collar_rect, width=2, border_radius=2)

            # 2. Bottom Pipe Body & Collar
            bottom_body_rect = pygame.Rect(
                ix,
                self.gap_bottom + collar_h,
                self.width,
                max(0, self.ground_y - (self.gap_bottom + collar_h)),
            )
            pygame.draw.rect(surface, COLOR_PIPE, bottom_body_rect)
            bottom_collar_rect = pygame.Rect(
                ix - collar_overhang,
                self.gap_bottom,
                self.width + collar_overhang * 2,
                collar_h,
            )
            pygame.draw.rect(surface, (51, 65, 85), bottom_collar_rect, border_radius=2)
            pygame.draw.rect(surface, COLOR_PIPE_OUTLINE, bottom_collar_rect, width=2, border_radius=2)

            # Cylindrical Highlight & Shadow Lines
            hl_x = ix + 10
            sh_x = ix + self.width - 6
            if top_body_rect.height > 0:
                pygame.draw.line(surface, (100, 116, 139), (hl_x, 0), (hl_x, top_body_rect.bottom), width=3)
                pygame.draw.line(surface, (30, 41, 59), (sh_x, 0), (sh_x, top_body_rect.bottom), width=3)
            if bottom_body_rect.height > 0:
                pygame.draw.line(surface, (100, 116, 139), (hl_x, bottom_body_rect.top), (hl_x, bottom_body_rect.bottom), width=3)
                pygame.draw.line(surface, (30, 41, 59), (sh_x, bottom_body_rect.top), (sh_x, bottom_body_rect.bottom), width=3)

            # 3. Draw Crate if present
            if self.crate and self.crate.alive:
                self.crate.draw(surface)



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

