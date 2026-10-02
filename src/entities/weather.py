"""
Weather and Biome module for Recoil Wing.
Handles dynamic weather FX (Acid Rain, Floating Embers, Lightning) and Sector progression.
"""
import random
import math
import pygame
from src.config import SCREEN_WIDTH, SCREEN_HEIGHT


class RainDrop:
    """Slanted cyber-rain streak with terminal velocity."""
    def __init__(self, ground_y):
        self.x = random.uniform(-30, SCREEN_WIDTH + 50)
        self.y = random.uniform(-40, ground_y - 20)
        self.vx = random.uniform(-3.2, -2.0)
        self.vy = random.uniform(15.0, 20.0)
        self.ground_y = ground_y
        self.alive = True

    def update(self):
        self.x += self.vx
        self.y += self.vy
        if self.y >= self.ground_y or self.x < -40:
            self.alive = False

    def draw(self, surface):
        ex = self.x - self.vx * 0.75
        ey = self.y - self.vy * 0.75
        pygame.draw.line(surface, (74, 222, 128), (int(self.x), int(self.y)), (int(ex), int(ey)), width=1)


class SplashParticle:
    """Tiny water droplet splash on ground impact."""
    def __init__(self, x, y):
        self.x = float(x)
        self.y = float(y)
        self.vx = random.uniform(-2.2, 2.2)
        self.vy = random.uniform(-2.8, -1.0)
        self.life = random.randint(5, 10)
        self.max_life = self.life
        self.alive = True

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.alive = False
            return
        self.x += self.vx
        self.y += self.vy
        self.vy += 0.30

    def draw(self, surface):
        if not self.alive:
            return
        alpha = int(200 * (self.life / self.max_life))
        s = pygame.Surface((3, 3), pygame.SRCALPHA)
        pygame.draw.circle(s, (74, 222, 128, alpha), (1, 1), 1)
        surface.blit(s, (int(self.x - 1), int(self.y - 1)))


class EmberParticle:
    """Glowing hot ember rising and swaying upwards."""
    def __init__(self, ground_y):
        self.x = random.uniform(0, SCREEN_WIDTH)
        self.y = random.uniform(ground_y - 30, ground_y + 10)
        self.vy = random.uniform(-1.2, -2.4)
        self.vx_base = random.uniform(-1.2, -0.4)
        self.sway_timer = random.uniform(0, 6.28)
        self.sway_speed = random.uniform(0.04, 0.08)
        self.size = random.uniform(2.0, 3.8)
        self.life = random.randint(65, 120)
        self.max_life = self.life
        self.color = random.choice([
            (249, 115, 22),  # Amber
            (244, 63, 94),   # Rose Red
            (251, 191, 36),  # Gold
        ])
        self.alive = True

    def update(self):
        self.life -= 1
        if self.life <= 0 or self.y < -15:
            self.alive = False
            return
        self.sway_timer += self.sway_speed
        self.x += self.vx_base + math.sin(self.sway_timer) * 0.8
        self.y += self.vy

    def draw(self, surface):
        if not self.alive:
            return
        ratio = self.life / self.max_life
        alpha = int(220 * ratio)
        r = max(1, int(self.size * ratio))
        s = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
        pygame.draw.circle(s, (self.color[0], self.color[1], self.color[2], alpha), (r + 1, r + 1), r)
        surface.blit(s, (int(self.x - r - 1), int(self.y - r - 1)))


class SectorBanner:
    """Holographic sliding banner announcing sector transitions."""
    def __init__(self, sector_num, name, subtitle, accent_color, font_title, font_sub):
        self.sector_num = sector_num
        self.name = name
        self.subtitle = subtitle
        self.accent_color = accent_color
        self.font_title = font_title
        self.font_sub = font_sub
        self.life = 135
        self.max_life = 135
        self.alive = True

    def update(self):
        self.life -= 1
        if self.life <= 0:
            self.alive = False

    def draw(self, surface):
        if not self.alive:
            return

        # Slide in from top, hold, then fade out
        if self.life > self.max_life - 20:
            t = (self.max_life - self.life) / 20.0
            cur_y = int(-50 + 98 * t)
            alpha = int(240 * t)
        elif self.life < 25:
            t = self.life / 25.0
            cur_y = 48
            alpha = int(240 * t)
        else:
            cur_y = 48
            alpha = 240

        box_w = 268
        box_h = 38
        box_x = (SCREEN_WIDTH - box_w) // 2

        # Translucent glassmorphic banner backing
        banner_surf = pygame.Surface((box_w, box_h), pygame.SRCALPHA)
        pygame.draw.rect(banner_surf, (15, 23, 42, min(alpha, 220)), (0, 0, box_w, box_h), border_radius=8)
        pygame.draw.rect(banner_surf, (self.accent_color[0], self.accent_color[1], self.accent_color[2], alpha), (0, 0, box_w, box_h), width=2, border_radius=8)

        # Tech corner markers
        c_len = 6
        pygame.draw.line(banner_surf, (255, 255, 255, alpha), (0, 0), (c_len, 0), width=2)
        pygame.draw.line(banner_surf, (255, 255, 255, alpha), (0, 0), (0, c_len), width=2)
        pygame.draw.line(banner_surf, (255, 255, 255, alpha), (box_w - c_len, 0), (box_w, 0), width=2)
        pygame.draw.line(banner_surf, (255, 255, 255, alpha), (box_w, 0), (box_w, c_len), width=2)

        surface.blit(banner_surf, (box_x, cur_y))

        # Text labels
        sub_surf = self.font_sub.render(self.subtitle, True, self.accent_color)
        title_surf = self.font_title.render(self.name, True, (248, 250, 252))

        surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, cur_y + 11)))
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, cur_y + 26)))


class WeatherManager:
    """Manages weather FX (rain, embers, ambient lightning) and sector transitions."""
    def __init__(self, ground_y, font_title, font_sub):
        self.ground_y = ground_y
        self.font_title = font_title
        self.font_sub = font_sub

        self.current_sector = 1
        self.banner = None

        # Weather particle pools
        self.raindrops = []
        self.splashes = []
        self.embers = []

        # Ambient lightning flash
        self.lightning_alpha = 0
        self.lightning_timer = random.randint(220, 380)

    def set_sector(self, sector_num, sound_mgr=None):
        if sector_num == self.current_sector and self.banner:
            return
        self.current_sector = sector_num

        if sector_num == 1:
            self.banner = SectorBanner(1, "NEON DOWNTOWN", "SECTOR 01 // ARRIVAL", (56, 189, 248), self.font_title, self.font_sub)
        elif sector_num == 2:
            self.banner = SectorBanner(2, "ACID RAIN DISTRICT", "SECTOR 02 // STORM WARNING", (74, 222, 128), self.font_title, self.font_sub)
            if sound_mgr:
                sound_mgr.play("portal", 0.6)
        elif sector_num == 3:
            self.banner = SectorBanner(3, "SOLAR OVERDRIVE", "SECTOR 03 // RED CORE", (244, 63, 94), self.font_title, self.font_sub)
            if sound_mgr:
                sound_mgr.play("portal", 0.7)

    def update(self, score, sound_mgr=None):
        # Sector Milestone Thresholds:
        # Sector 1: 0 - 14
        # Sector 2: 15 - 29 (Acid Rain Storm)
        # Sector 3: 30+ (Solar Overdrive)
        if score >= 30:
            target = 3
        elif score >= 15:
            target = 2
        else:
            target = 1

        if target != self.current_sector:
            self.set_sector(target, sound_mgr)

        # Update holographic sector banner
        if self.banner:
            self.banner.update()
            if not self.banner.alive:
                self.banner = None

        # Weather spawning based on active sector
        if self.current_sector == 2:
            # Acid rain streaks
            if len(self.raindrops) < 42:
                for _ in range(3):
                    self.raindrops.append(RainDrop(self.ground_y))

            # Lightning timer
            self.lightning_timer -= 1
            if self.lightning_timer <= 0:
                self.lightning_alpha = random.randint(90, 140)
                self.lightning_timer = random.randint(220, 380)

        elif self.current_sector == 3:
            # Glowing hot embers
            if len(self.embers) < 28 and random.random() < 0.65:
                self.embers.append(EmberParticle(self.ground_y))

        # Decay lightning flash
        if self.lightning_alpha > 0:
            self.lightning_alpha = max(0, self.lightning_alpha - 20)

        # Update raindrops & create ground splash droplets
        for r in self.raindrops:
            r.update()
            if not r.alive and r.y >= self.ground_y - 4:
                if len(self.splashes) < 32 and random.random() < 0.45:
                    self.splashes.append(SplashParticle(r.x, self.ground_y))
        self.raindrops = [r for r in self.raindrops if r.alive]

        # Update splashes
        for s in self.splashes:
            s.update()
        self.splashes = [s for s in self.splashes if s.alive]

        # Update embers
        for e in self.embers:
            e.update()
        self.embers = [e for e in self.embers if e.alive]

    def reset(self):
        """Reset to Sector 1 and clear particles."""
        self.current_sector = 1
        self.raindrops.clear()
        self.splashes.clear()
        self.embers.clear()
        self.banner = None
        self.lightning_alpha = 0
        self.set_sector(1)

    def draw_background_fx(self, surface):
        """Draw ambient weather between skyline and obstacles."""
        # Lightning screen flash in Sector 2
        if self.lightning_alpha > 0:
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            flash_surf.fill((180, 240, 220, self.lightning_alpha))
            surface.blit(flash_surf, (0, 0))

        # Floating embers in Sector 3
        for e in self.embers:
            e.draw(surface)

    def draw_foreground_fx(self, surface):
        """Draw rain streaks and ground splashes in foreground."""
        for r in self.raindrops:
            r.draw(surface)
        for s in self.splashes:
            s.draw(surface)
        if self.banner:
            self.banner.draw(surface)
