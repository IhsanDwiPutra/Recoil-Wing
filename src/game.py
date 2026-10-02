"""
Game controller and main loop for Recoil Wing.
Handles state management, camera screen shake, parallax backgrounds,
persistent high scores, and roguelite perk evolution.
"""
import os
import sys
import math
import random
import pygame

from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    TITLE,
    COLOR_BG_TOP,
    COLOR_BG_BOTTOM,
    COLOR_GROUND,
    COLOR_GROUND_LINE,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_ACCENT,
    COLOR_AMMO_FILLED,
    COLOR_AMMO_EMPTY,
    COLOR_AMMO_BORDER,
    MAX_AMMO,
    AMMO_RELOAD_FRAMES,
    PIPE_SPEED,
    PIPE_SPAWN_FRAMES,
)
from src.entities.player import Player
from src.entities.obstacle import PipePair
from src.entities.particle import (
    create_crate_debris,
    create_spark_burst,
    ShellCasing,
    SmokePuff,
    FloatingText,
)
from src.entities.perks import (
    PerkID,
    PERK_REGISTRY,
    get_random_perk_choices,
)
from src.utils.camera import Camera


class GameState:
    READY = "ready"
    PLAYING = "playing"
    UPGRADE_SELECTION = "upgrade_selection"
    GAME_OVER = "game_over"


HIGH_SCORE_FILE = os.path.join(os.path.dirname(__file__), "..", "highscore.dat")
UPGRADE_THRESHOLDS = [5, 12, 20, 32]


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(TITLE)
        self.clock = pygame.time.Clock()

        # Canvas surface for screen shake blitting
        self.canvas = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT))
        self.camera = Camera()

        # Fonts
        self.font_score = pygame.font.SysFont("Trebuchet MS", 52, bold=True)
        self.font_score_label = pygame.font.SysFont("Trebuchet MS", 16, bold=True)
        self.font_title = pygame.font.SysFont("Trebuchet MS", 38, bold=True)
        self.font_body = pygame.font.SysFont("Trebuchet MS", 18, bold=True)
        self.font_small = pygame.font.SysFont("Trebuchet MS", 13)
        self.font_badge = pygame.font.SysFont("Trebuchet MS", 14, bold=True)
        self.font_card_desc = pygame.font.SysFont("Trebuchet MS", 12)

        # Ground setting
        self.ground_height = 80
        self.ground_y = SCREEN_HEIGHT - self.ground_height

        # Pre-render background gradient
        self.bg_surface = self._create_gradient_surface(
            SCREEN_WIDTH, SCREEN_HEIGHT, COLOR_BG_TOP, COLOR_BG_BOTTOM
        )

        # Parallax City Skyline
        self.buildings = self._generate_skyline()

        # High score persistence
        self.high_score = self.load_high_score()
        self.is_new_best = False

        # Entities & States
        self.player = Player()
        self.bullets = []
        self.obstacles = []
        self.particles = []
        self.floating_texts = []
        self.pipe_spawn_timer = 0
        self.state = GameState.READY
        self.score = 0
        self.ready_timer = 0.0

        # Perks & Upgrades
        self.active_perks = []
        self.claimed_milestones = set()
        self.current_perk_choices = []
        self.card_rects = []

    def _generate_skyline(self):
        """Generates initial silhouette skyline buildings for parallax."""
        buildings = []
        cur_x = 0
        while cur_x < SCREEN_WIDTH + 140:
            w = random.randint(38, 70)
            h = random.randint(110, 240)
            windows = [
                (random.randint(4, w - 8), random.randint(12, h - 20))
                for _ in range(random.randint(3, 6))
            ]
            buildings.append({
                'x': float(cur_x),
                'w': w,
                'h': h,
                'windows': windows,
            })
            cur_x += w + random.randint(4, 14)
        return buildings

    def _create_gradient_surface(self, width, height, top_color, bottom_color):
        """Pre-renders a smooth 2-color vertical linear gradient surface."""
        surf = pygame.Surface((width, height))
        for y in range(height):
            ratio = y / height
            r = int(top_color[0] + (bottom_color[0] - top_color[0]) * ratio)
            g = int(top_color[1] + (bottom_color[1] - top_color[1]) * ratio)
            b = int(top_color[2] + (bottom_color[2] - top_color[2]) * ratio)
            pygame.draw.line(surf, (r, g, b), (0, y), (width, y))
        return surf

    def load_high_score(self):
        """Load persistent high score from local file."""
        try:
            if os.path.exists(HIGH_SCORE_FILE):
                with open(HIGH_SCORE_FILE, "r") as f:
                    return int(f.read().strip())
        except Exception:
            pass
        return 0

    def save_high_score(self, score):
        """Save persistent high score to local file."""
        try:
            with open(HIGH_SCORE_FILE, "w") as f:
                f.write(str(score))
        except Exception:
            pass

    def handle_input(self):
        """Process input events."""
        mouse_pos = pygame.mouse.get_pos()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

            elif event.type == pygame.KEYDOWN:
                if self.state == GameState.UPGRADE_SELECTION:
                    if event.key == pygame.K_1 and len(self.current_perk_choices) >= 1:
                        self.select_perk(0)
                    elif event.key == pygame.K_2 and len(self.current_perk_choices) >= 2:
                        self.select_perk(1)
                    elif event.key == pygame.K_3 and len(self.current_perk_choices) >= 3:
                        self.select_perk(2)

                else:
                    if event.key in (pygame.K_SPACE, pygame.K_UP, pygame.K_w):
                        self.on_jump_action()
                    elif event.key == pygame.K_r:
                        self.reset_game()

            elif event.type == pygame.MOUSEBUTTONDOWN:
                if event.button == 1:  # Left Click
                    if self.state == GameState.UPGRADE_SELECTION:
                        # Check which card was clicked
                        for idx, rect in enumerate(self.card_rects):
                            if rect.collidepoint(mouse_pos):
                                self.select_perk(idx)
                                break
                    else:
                        self.on_jump_action()

    def on_jump_action(self):
        """Handle jump/recoil action across different states."""
        if self.state == GameState.READY:
            self.state = GameState.PLAYING
            self.fire_weapon()
        elif self.state == GameState.PLAYING:
            self.fire_weapon()
        elif self.state == GameState.GAME_OVER:
            self.reset_game()

    def fire_weapon(self):
        """Fires weapon, spawns bullets, shell casings, muzzle smoke, and recoil shake."""
        new_bullets = self.player.shoot()
        if new_bullets:
            self.bullets.extend(new_bullets)
            # Eject brass casing
            self.particles.append(ShellCasing(self.player.x - 6, self.player.y + 4))
            # Spawn soft muzzle smoke
            self.particles.append(SmokePuff(self.player.x - 2, self.player.y + self.player.height // 2 + 6))
            # Screen shake recoil kick
            self.camera.add_trauma(0.18)

    def trigger_upgrade_phase(self):
        """Transitions into Upgrade Pick screen."""
        self.state = GameState.UPGRADE_SELECTION
        self.current_perk_choices = get_random_perk_choices(self.active_perks, count=3)
        self.player.vy = 0.0  # Zero out velocity during selection

    def select_perk(self, index):
        """Applies chosen perk and resumes gameplay smoothly."""
        if index >= len(self.current_perk_choices):
            return

        choice = self.current_perk_choices[index]
        pid = choice["id"]
        self.active_perks.append(pid)

        # Apply perk effect
        if pid == PerkID.SHOTGUN:
            self.player.weapon_type = "SHOTGUN"
        elif pid == PerkID.PIERCER:
            self.player.weapon_type = "PIERCER"
        elif pid == PerkID.SHIELD:
            self.player.shield_charges += 1
        elif pid == PerkID.BOUNCY:
            self.player.has_bouncy = True
        elif pid == PerkID.EXPANDED_MAG:
            self.player.max_ammo = 6
            self.player.ammo = 6
            self.player.reload_frames = int(AMMO_RELOAD_FRAMES * 0.65)

        # Visual feedback
        self.floating_texts.append(
            FloatingText(f"+ {choice['name']}!", SCREEN_WIDTH // 2, 280, choice["color"], self.font_body)
        )
        self.camera.add_trauma(0.35)

        # Smooth return to gameplay with a gentle hover
        self.player.vy = -3.5
        self.state = GameState.PLAYING

    def reset_game(self):
        """Reset game to initial ready state."""
        self.player.reset()
        self.bullets.clear()
        self.obstacles.clear()
        self.particles.clear()
        self.floating_texts.clear()
        self.active_perks.clear()
        self.claimed_milestones.clear()
        self.pipe_spawn_timer = 0
        self.state = GameState.READY
        self.score = 0
        self.is_new_best = False
        self.ready_timer = 0.0

    def trigger_game_over(self):
        """Transitions into Game Over and checks high score record."""
        if self.state != GameState.GAME_OVER:
            self.state = GameState.GAME_OVER
            self.camera.add_trauma(0.70)  # Crunch crash shake
            if self.score > self.high_score:
                self.high_score = self.score
                self.is_new_best = True
                self.save_high_score(self.high_score)

    def update(self):
        """Update game logic."""
        # Camera trauma decay
        self.camera.update()

        # When in upgrade selection, background stays static
        if self.state == GameState.UPGRADE_SELECTION:
            return

        # Parallax Skyline scrolling
        skyline_speed = PIPE_SPEED * 0.35 if self.state == GameState.PLAYING else 0.4
        for b in self.buildings:
            b['x'] -= skyline_speed
        if self.buildings and self.buildings[0]['x'] + self.buildings[0]['w'] < -20:
            first = self.buildings.pop(0)
            last_x = max(b['x'] + b['w'] for b in self.buildings)
            first['x'] = last_x + random.randint(4, 14)
            self.buildings.append(first)

        if self.state == GameState.READY:
            self.ready_timer += 0.05
            self.player.y = self.player.start_y + math.sin(self.ready_timer) * 8
            self.player.rotation = 0.0

        elif self.state == GameState.PLAYING:
            self.player.update()

            # Check Milestone Upgrade Trigger
            for threshold in UPGRADE_THRESHOLDS:
                if self.score >= threshold and threshold not in self.claimed_milestones:
                    self.claimed_milestones.add(threshold)
                    self.trigger_upgrade_phase()
                    return

            # 1. Spawn Obstacles
            self.pipe_spawn_timer += 1
            if self.pipe_spawn_timer >= PIPE_SPAWN_FRAMES:
                self.obstacles.append(PipePair(SCREEN_WIDTH + 10, self.ground_y))
                self.pipe_spawn_timer = 0

            # 2. Update Obstacles & Check Player Collision / Scoring
            for o in self.obstacles:
                o.update(PIPE_SPEED)

                # Point scored when clearing obstacle
                if not o.passed and self.player.x > o.x + o.width:
                    o.passed = True
                    self.score += 1
                    self.floating_texts.append(
                        FloatingText("+1", self.player.x + 20, self.player.y - 12, COLOR_TEXT, self.font_score_label)
                    )

                # Player collision with solid pipe or intact crate
                if o.collides_with_player(self.player.rect):
                    # Check Energy Shield deflection
                    if self.player.shield_charges > 0:
                        self.player.shield_charges -= 1
                        self.camera.add_trauma(0.55)
                        self.particles.extend(
                            create_spark_burst(self.player.x, self.player.y, count=18, color=(56, 189, 248))
                        )
                        self.floating_texts.append(
                            FloatingText("SHIELD DEFLECT!", self.player.x, self.player.y - 22, (56, 189, 248), self.font_body)
                        )
                        # Push obstacle passed so player doesn't get stuck hitting it again
                        o.passed = True
                        if o.crate and o.crate.alive:
                            o.crate.alive = False
                    else:
                        self.player.is_alive = False
                        self.particles.extend(create_spark_burst(self.player.x, self.player.y, count=14))
                        self.trigger_game_over()

            # Remove off-screen obstacles
            self.obstacles = [o for o in self.obstacles if o.x + o.width > -40]

            # 3. Update Bullets & Check Collisions with Obstacles
            for b in self.bullets:
                b.update(self.ground_y)
                if not b.alive:
                    continue

                for o in self.obstacles:
                    hit = o.check_bullet_hit(b)
                    if hit:
                        hit_type, hx, hy, destroyed = hit
                        if hit_type == "crate":
                            if destroyed:
                                self.particles.extend(create_crate_debris(hx, hy, count=16))
                                self.score += 2  # Tactical demolition reward!
                                self.camera.add_trauma(0.40)
                                self.floating_texts.append(
                                    FloatingText("+2 CRATE!", hx, hy - 14, (250, 204, 21), self.font_body)
                                )
                            else:
                                self.particles.extend(create_spark_burst(hx, hy, count=5))
                                self.camera.add_trauma(0.15)
                        elif hit_type == "ricochet":
                            self.particles.extend(create_spark_burst(hx, hy, count=5, color=(234, 179, 8)))
                        else:
                            self.particles.extend(create_spark_burst(hx, hy, count=6))

                        if not b.piercing:
                            break

            self.bullets = [b for b in self.bullets if b.alive]

            # 4. Update Particles (including shell casings)
            for p in self.particles:
                if isinstance(p, ShellCasing):
                    p.update(self.ground_y)
                else:
                    p.update()
            self.particles = [p for p in self.particles if p.alive]

            # 5. Update Floating Texts
            for ft in self.floating_texts:
                ft.update()
            self.floating_texts = [ft for ft in self.floating_texts if ft.alive]

            # 6. Ceiling clamp
            if self.player.y - self.player.height // 2 < 0:
                self.player.y = self.player.height // 2
                self.player.vy = max(0.0, self.player.vy)

            # 7. Ground collision
            if self.player.y + self.player.height // 2 >= self.ground_y:
                self.player.y = self.ground_y - self.player.height // 2
                if self.player.is_alive:
                    self.player.is_alive = False
                    self.particles.extend(create_spark_burst(self.player.x, self.player.y, count=10))
                    self.trigger_game_over()

        elif self.state == GameState.GAME_OVER:
            for b in self.bullets:
                b.update(self.ground_y)
            self.bullets = [b for b in self.bullets if b.alive]

            for p in self.particles:
                if isinstance(p, ShellCasing):
                    p.update(self.ground_y)
                else:
                    p.update()
            self.particles = [p for p in self.particles if p.alive]

            for ft in self.floating_texts:
                ft.update()
            self.floating_texts = [ft for ft in self.floating_texts if ft.alive]

            if self.player.y + self.player.height // 2 < self.ground_y:
                self.player.update()
                if self.player.y + self.player.height // 2 >= self.ground_y:
                    self.player.y = self.ground_y - self.player.height // 2

    def draw(self):
        """Render frame with camera screen shake."""
        # 1. Background Gradient
        self.canvas.blit(self.bg_surface, (0, 0))

        # 2. Parallax Skyline
        for b in self.buildings:
            by = self.ground_y - b['h']
            b_rect = pygame.Rect(int(b['x']), by, b['w'], b['h'])
            pygame.draw.rect(self.canvas, (24, 27, 46), b_rect)
            pygame.draw.rect(self.canvas, (33, 38, 64), b_rect, width=1)
            for wx, wy in b['windows']:
                win_rect = pygame.Rect(int(b['x']) + wx, by + wy, 3, 4)
                pygame.draw.rect(self.canvas, (56, 189, 248), win_rect)

        # 3. Obstacles
        for o in self.obstacles:
            o.draw(self.canvas)

        # 4. Bullets
        for b in self.bullets:
            b.draw(self.canvas)

        # 5. Particles & Casings
        for p in self.particles:
            p.draw(self.canvas)

        # 6. Player
        self.player.draw(self.canvas)

        # 7. Ground
        ground_rect = pygame.Rect(0, self.ground_y, SCREEN_WIDTH, self.ground_height)
        pygame.draw.rect(self.canvas, COLOR_GROUND, ground_rect)
        pygame.draw.line(
            self.canvas,
            COLOR_GROUND_LINE,
            (0, self.ground_y),
            (SCREEN_WIDTH, self.ground_y),
            width=3,
        )

        for x in range(0, SCREEN_WIDTH, 40):
            pygame.draw.line(
                self.canvas,
                (25, 28, 44),
                (x, self.ground_y + 12),
                (x + 20, self.ground_y + 12),
                width=2,
            )

        # 8. Floating Score Popups
        for ft in self.floating_texts:
            ft.draw(self.canvas)

        # 9. HUD & Menus
        self._draw_hud(self.canvas)

        # 10. Upgrade Selection Modal (if in selection state)
        if self.state == GameState.UPGRADE_SELECTION:
            self._draw_upgrade_modal(self.canvas)

        # 11. Blit Canvas with Screen Shake Offset
        dx, dy = self.camera.get_offset()
        self.screen.fill((10, 11, 20))
        self.screen.blit(self.canvas, (dx, dy))

        pygame.display.flip()

    def _draw_hud(self, surface):
        """Draw UI elements, status text, live score, and ammo meter."""
        self._draw_ammo_meter(surface)
        self._draw_active_perks_hud(surface)

        if self.state == GameState.READY:
            title_surf = self.font_title.render("RECOIL WING", True, COLOR_TEXT)
            title_rect = title_surf.get_rect(center=(SCREEN_WIDTH // 2, 175))
            surface.blit(title_surf, title_rect)

            sub_surf = self.font_body.render("Press SPACE or CLICK to Blast & Fly", True, COLOR_ACCENT)
            sub_rect = sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 225))
            surface.blit(sub_surf, sub_rect)

            if self.high_score > 0:
                best_surf = self.font_badge.render(f"BEST RECORD: {self.high_score}", True, (250, 204, 21))
                best_rect = best_surf.get_rect(center=(SCREEN_WIDTH // 2, 265))
                surface.blit(best_surf, best_rect)

            hint_surf = self.font_small.render("[Milestone 5: Roguelite Perks & Modifiers Prototype]", True, COLOR_TEXT_MUTED)
            hint_rect = hint_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 30))
            surface.blit(hint_surf, hint_rect)

        elif self.state == GameState.PLAYING:
            score_str = str(self.score)
            shadow_surf = self.font_score.render(score_str, True, (15, 23, 42))
            surface.blit(shadow_surf, shadow_surf.get_rect(center=(SCREEN_WIDTH // 2 + 2, 98 + 2)))
            score_surf = self.font_score.render(score_str, True, COLOR_TEXT)
            surface.blit(score_surf, score_surf.get_rect(center=(SCREEN_WIDTH // 2, 98)))

        elif self.state == GameState.GAME_OVER:
            modal_rect = pygame.Rect(45, 175, SCREEN_WIDTH - 90, 260)
            pygame.draw.rect(surface, (24, 27, 44), modal_rect, border_radius=12)
            pygame.draw.rect(surface, (55, 62, 92), modal_rect, width=2, border_radius=12)

            go_surf = self.font_title.render("GAME OVER", True, COLOR_ACCENT)
            surface.blit(go_surf, go_surf.get_rect(center=(SCREEN_WIDTH // 2, 215)))

            score_txt = self.font_body.render(f"SCORE: {self.score}", True, COLOR_TEXT)
            surface.blit(score_txt, score_txt.get_rect(center=(SCREEN_WIDTH // 2, 262)))

            if self.is_new_best and self.score > 0:
                best_txt = self.font_badge.render("★ NEW BEST RECORD! ★", True, (250, 204, 21))
            else:
                best_txt = self.font_small.render(f"BEST SCORE: {self.high_score}", True, COLOR_TEXT_MUTED)
            surface.blit(best_txt, best_txt.get_rect(center=(SCREEN_WIDTH // 2, 296)))

            retry_surf = self.font_body.render("Press SPACE / R to Retry", True, (45, 212, 191))
            surface.blit(retry_surf, retry_surf.get_rect(center=(SCREEN_WIDTH // 2, 355)))

    def _draw_active_perks_hud(self, surface):
        """Displays currently equipped perks as badges in top-left."""
        if not self.active_perks:
            return

        start_x = 16
        start_y = 18
        for pid in self.active_perks:
            pinfo = PERK_REGISTRY.get(pid)
            if not pinfo:
                continue

            badge_text = pinfo["badge"]
            if pid == PerkID.SHIELD:
                badge_text = f"SHIELD x{self.player.shield_charges}"

            surf = self.font_badge.render(badge_text, True, pinfo["color"])
            bg_rect = pygame.Rect(start_x, start_y, surf.get_width() + 10, surf.get_height() + 4)
            pygame.draw.rect(surface, (20, 24, 38), bg_rect, border_radius=4)
            pygame.draw.rect(surface, pinfo["color"], bg_rect, width=1, border_radius=4)
            surface.blit(surf, (start_x + 5, start_y + 2))
            start_y += surf.get_height() + 8

    def _draw_ammo_meter(self, surface):
        """Draw modern arcade cartridge pips representing available ammo."""
        pip_w = 20
        pip_h = 9
        pip_spacing = 5
        curr_max = self.player.max_ammo
        total_w = curr_max * pip_w + (curr_max - 1) * pip_spacing
        start_x = (SCREEN_WIDTH - total_w) // 2
        start_y = 35

        for i in range(curr_max):
            px = start_x + i * (pip_w + pip_spacing)
            pip_rect = pygame.Rect(px, start_y, pip_w, pip_h)

            if i < self.player.ammo:
                pygame.draw.rect(surface, COLOR_AMMO_FILLED, pip_rect, border_radius=3)
                pygame.draw.rect(surface, (255, 255, 255), pip_rect, width=1, border_radius=3)
            elif i == self.player.ammo and self.player.ammo < curr_max:
                pygame.draw.rect(surface, COLOR_AMMO_EMPTY, pip_rect, border_radius=3)
                progress = self.player.ammo_reload_timer / self.player.reload_frames
                progress_w = int(pip_w * progress)
                if progress_w > 0:
                    fill_rect = pygame.Rect(px, start_y, progress_w, pip_h)
                    pygame.draw.rect(surface, (34, 197, 94), fill_rect, border_radius=3)
                pygame.draw.rect(surface, COLOR_AMMO_BORDER, pip_rect, width=1, border_radius=3)
            else:
                pygame.draw.rect(surface, COLOR_AMMO_EMPTY, pip_rect, border_radius=3)
                pygame.draw.rect(surface, (40, 50, 70), pip_rect, width=1, border_radius=3)

    def _draw_upgrade_modal(self, surface):
        """Draw interactive roguelite perk card selection screen."""
        # 1. Dark semi-transparent backdrop
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((12, 14, 26, 220))
        surface.blit(overlay, (0, 0))

        # 2. Header
        header_surf = self.font_title.render("CHOOSE UPGRADE", True, (250, 204, 21))
        surface.blit(header_surf, header_surf.get_rect(center=(SCREEN_WIDTH // 2, 120)))

        sub_surf = self.font_small.render("Press [1], [2], [3] or Click to Select", True, COLOR_TEXT_MUTED)
        surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 155)))

        # 3. Cards
        card_w = SCREEN_WIDTH - 70
        card_h = 100
        start_y = 190
        spacing = 16

        self.card_rects = []
        mouse_pos = pygame.mouse.get_pos()

        for idx, perk in enumerate(self.current_perk_choices):
            cy = start_y + idx * (card_h + spacing)
            card_rect = pygame.Rect(35, cy, card_w, card_h)
            self.card_rects.append(card_rect)

            is_hovered = card_rect.collidepoint(mouse_pos)

            # Card background
            card_bg = (32, 38, 62) if is_hovered else (22, 26, 44)
            pygame.draw.rect(surface, card_bg, card_rect, border_radius=10)

            # Card border (glows with perk's accent color)
            border_color = perk["color"] if is_hovered else (55, 65, 95)
            pygame.draw.rect(surface, border_color, card_rect, width=2 if not is_hovered else 3, border_radius=10)

            # Key Shortcut Badge [1], [2], [3]
            num_surf = self.font_body.render(f"[{idx + 1}]", True, perk["color"])
            surface.blit(num_surf, (card_rect.left + 14, card_rect.top + 14))

            # Category pill tag
            cat_surf = self.font_small.render(perk["category"], True, (203, 213, 225))
            cat_bg = pygame.Rect(card_rect.right - 85, card_rect.top + 12, 72, 18)
            pygame.draw.rect(surface, (15, 23, 42), cat_bg, border_radius=4)
            surface.blit(cat_surf, cat_surf.get_rect(center=cat_bg.center))

            # Perk Title
            title_surf = self.font_body.render(perk["name"], True, COLOR_TEXT)
            surface.blit(title_surf, (card_rect.left + 48, card_rect.top + 14))

            # Description (word wrapped or clean 2-line rendering)
            desc_words = perk["description"].split(" ")
            line1 = " ".join(desc_words[:6])
            line2 = " ".join(desc_words[6:])
            d1_surf = self.font_card_desc.render(line1, True, (203, 213, 225))
            surface.blit(d1_surf, (card_rect.left + 16, card_rect.top + 48))
            if line2:
                d2_surf = self.font_card_desc.render(line2, True, (203, 213, 225))
                surface.blit(d2_surf, (card_rect.left + 16, card_rect.top + 68))

    def run(self):
        """Main game loop."""
        while True:
            self.handle_input()
            self.update()
            self.draw()
            self.clock.tick(FPS)
