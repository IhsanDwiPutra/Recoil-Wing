"""
Recoil Wing - Multiplayer Lobby & Room Menu.
Provides cyber-arcade UI for creating rooms, entering 4-letter room codes,
waiting for rivals, and triggering synchronized 3-2-1 match countdowns.
"""
import time
import math
import pygame
from src.config import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    COLOR_BG_TOP,
    COLOR_BG_BOTTOM,
    COLOR_TEXT,
    COLOR_TEXT_MUTED,
    COLOR_ACCENT,
    COLOR_PLAYER,
)

# Colors specific to Cyberpunk Rival UI
COLOR_CYAN_NEON = (0, 240, 255)
COLOR_PINK_NEON = (255, 42, 133)
COLOR_GOLD_NEON = (255, 215, 0)
COLOR_CARD_BG = (15, 23, 42, 230)
COLOR_INPUT_BG = (30, 41, 59)


class LobbySubState:
    SELECT = "select"
    HOST_WAITING = "host_waiting"
    JOIN_INPUT = "join_input"
    STARTING_COUNTDOWN = "countdown"


class MultiplayerMenu:
    def __init__(self, network_client, sound_manager, font_title, font_body, font_small, font_score):
        self.net = network_client
        self.sound_mgr = sound_manager
        self.font_title = font_title
        self.font_body = font_body
        self.font_small = font_small
        self.font_score = font_score

        self.sub_state = LobbySubState.SELECT
        self.input_code = ""
        self.status_message = "Connect to rival across devices"
        self.status_color = COLOR_TEXT_MUTED
        self.pulse_timer = 0.0

        # Countdown timer
        self.countdown_val = 3
        self.countdown_timer = 0.0
        self.match_ready = False

        # Interactive UI Rectangles
        btn_w = 260
        btn_h = 48
        cx = (SCREEN_WIDTH - btn_w) // 2

        self.btn_create = pygame.Rect(cx, 320, btn_w, btn_h)
        self.btn_join = pygame.Rect(cx, 384, btn_w, btn_h)
        self.btn_back = pygame.Rect(cx, 448, btn_w, btn_h)

        # Cancel button in submenus
        self.btn_cancel = pygame.Rect(cx, 560, btn_w, 42)
        self.btn_submit_code = pygame.Rect(cx, 380, btn_w, 46)

        # On-screen Quick Keypad for mobile / mouse code entry
        self.keypad_rects = []
        self._init_keypad()

    def _init_keypad(self):
        """Creates on-screen touch buttons for mobile/mouse room code input."""
        letters = "ABCDEFGHJKLMNPQRSTUVWXYZ"  # Common letters without O/I
        self.keypad_rects = []
        kw = 32
        kh = 32
        cols = 6
        spacing = 6
        start_x = (SCREEN_WIDTH - (cols * kw + (cols - 1) * spacing)) // 2
        start_y = 440

        for idx, char in enumerate(letters):
            r = idx // cols
            c = idx % cols
            x = start_x + c * (kw + spacing)
            y = start_y + r * (kh + spacing)
            self.keypad_rects.append((char, pygame.Rect(x, y, kw, kh)))

        # Backspace button
        bs_w = 70
        bs_x = (SCREEN_WIDTH - bs_w) // 2
        bs_y = start_y + 4 * (kh + spacing) + 4
        self.btn_backspace = pygame.Rect(bs_x, bs_y, bs_w, 28)

    def reset(self):
        """Resets menu state when opened."""
        self.sub_state = LobbySubState.SELECT
        self.input_code = ""
        self.status_message = "Connect to rival across devices"
        self.status_color = COLOR_TEXT_MUTED
        self.match_ready = False
        self.countdown_val = 3
        self.countdown_timer = 0.0

    def handle_event(self, event):
        """Handles mouse, touch, and keyboard interactions."""
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            pos = event.pos
            return self._handle_click(pos)

        elif event.type == pygame.KEYDOWN:
            if self.sub_state == LobbySubState.JOIN_INPUT:
                if event.key == pygame.K_BACKSPACE:
                    self.input_code = self.input_code[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_KP_ENTER):
                    self._submit_join_code()
                elif event.key == pygame.K_ESCAPE:
                    self.sub_state = LobbySubState.SELECT
                else:
                    char = event.unicode.upper()
                    if char.isalpha() and len(self.input_code) < 4:
                        self.input_code += char

    def _handle_click(self, pos):
        """Processes button clicks based on active sub-state."""
        if self.sub_state == LobbySubState.SELECT:
            if self.btn_create.collidepoint(pos):
                self._action_create_room()
            elif self.btn_join.collidepoint(pos):
                self.sub_state = LobbySubState.JOIN_INPUT
                self.input_code = ""
                self.status_message = "Enter 4-letter code"
                self.status_color = COLOR_CYAN_NEON
            elif self.btn_back.collidepoint(pos):
                return "back_to_menu"

        elif self.sub_state == LobbySubState.HOST_WAITING:
            if self.btn_cancel.collidepoint(pos):
                self.sub_state = LobbySubState.SELECT

        elif self.sub_state == LobbySubState.JOIN_INPUT:
            if self.btn_cancel.collidepoint(pos):
                self.sub_state = LobbySubState.SELECT
            elif self.btn_submit_code.collidepoint(pos):
                self._submit_join_code()
            elif hasattr(self, "btn_backspace") and self.btn_backspace.collidepoint(pos):
                self.input_code = self.input_code[:-1]
            else:
                for char, rect in self.keypad_rects:
                    if rect.collidepoint(pos):
                        if len(self.input_code) < 4:
                            self.input_code += char
                        break

        return None

    def _action_create_room(self):
        """Sends room creation request to server."""
        if not self.net.connected:
            self.net.start()
        self.sub_state = LobbySubState.HOST_WAITING
        self.status_message = "Generating Room..."
        self.status_color = COLOR_CYAN_NEON
        self.net.create_room()

    def _submit_join_code(self):
        """Submits typed room code to join rival room."""
        code = self.input_code.strip().upper()
        if len(code) != 4:
            self.status_message = "Room code must be 4 letters!"
            self.status_color = COLOR_PINK_NEON
            return
        if not self.net.connected:
            self.net.start()
        self.status_message = f"Connecting to Room {code}..."
        self.status_color = COLOR_GOLD_NEON
        self.net.join_room(code)

    def update(self, dt):
        """Updates network event queue, polling, and countdowns."""
        self.pulse_timer += dt

        # Poll incoming network messages from client queue
        events = self.net.poll_events()
        for ev in events:
            ev_type = ev.get("type")

            if ev_type == "room_created":
                self.status_message = f"Room {ev['room_code']} Ready!"
                self.status_color = COLOR_CYAN_NEON

            elif ev_type == "room_joined":
                self.status_message = "Joined Room! Waiting for Host..."
                self.status_color = COLOR_GOLD_NEON
                # Automatically signal ready
                self.net.send_ready()

            elif ev_type == "rival_joined":
                self.status_message = "Rival joined! Preparing launch..."
                self.status_color = COLOR_PINK_NEON
                # Host signals ready
                self.net.send_ready()

            elif ev_type == "start_countdown":
                self.sub_state = LobbySubState.STARTING_COUNTDOWN
                self.countdown_val = ev.get("seconds", 3)
                self.countdown_timer = 1.0
                self.status_message = "RIVAL CONNECTED! READY..."

            elif ev_type == "error":
                self.status_message = ev.get("message", "Network error.")
                self.status_color = COLOR_PINK_NEON

        # Countdown ticking
        if self.sub_state == LobbySubState.STARTING_COUNTDOWN:
            self.countdown_timer -= dt
            if self.countdown_timer <= 0:
                self.countdown_val -= 1
                self.countdown_timer = 1.0
                if self.countdown_val <= 0:
                    self.match_ready = True
                    return "start_match"

        return None

    def draw(self, surface):
        """Renders the cyber lobby UI."""
        # Semi-transparent overlay card
        overlay = pygame.Surface((SCREEN_WIDTH - 40, SCREEN_HEIGHT - 120), pygame.SRCALPHA)
        overlay.fill(COLOR_CARD_BG)
        surface.blit(overlay, (20, 60))

        # Cyber border
        pygame.draw.rect(surface, COLOR_CYAN_NEON, (20, 60, SCREEN_WIDTH - 40, SCREEN_HEIGHT - 120), 2, border_radius=12)

        # Header Title
        title_surf = self.font_title.render("2P RIVAL RACE", True, COLOR_CYAN_NEON)
        surface.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 105)))

        sub_surf = self.font_small.render("SYNCHRONIZED REAL-TIME DUEL", True, COLOR_TEXT_MUTED)
        surface.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 138)))

        # Server Connection Indicator
        conn_color = (34, 197, 94) if self.net.connected else (234, 179, 8)
        conn_text = "● SERVER ONLINE" if self.net.connected else "● CONNECTING..."
        conn_surf = self.font_small.render(conn_text, True, conn_color)
        surface.blit(conn_surf, conn_surf.get_rect(center=(SCREEN_WIDTH // 2, 168)))

        # Render sub-state specific UI
        if self.sub_state == LobbySubState.SELECT:
            self._draw_select_menu(surface)
        elif self.sub_state == LobbySubState.HOST_WAITING:
            self._draw_host_waiting(surface)
        elif self.sub_state == LobbySubState.JOIN_INPUT:
            self._draw_join_input(surface)
        elif self.sub_state == LobbySubState.STARTING_COUNTDOWN:
            self._draw_countdown(surface)

        # Bottom Status Bar
        status_surf = self.font_small.render(self.status_message, True, self.status_color)
        surface.blit(status_surf, status_surf.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 85)))

    def _draw_button(self, surface, rect, text, bg_color, border_color, text_color):
        """Helper to draw sleek rounded cyber button."""
        pygame.draw.rect(surface, bg_color, rect, border_radius=8)
        pygame.draw.rect(surface, border_color, rect, 2, border_radius=8)
        btn_txt = self.font_body.render(text, True, text_color)
        surface.blit(btn_txt, btn_txt.get_rect(center=rect.center))

    def _draw_select_menu(self, surface):
        """Draws initial Create / Join selection buttons."""
        self._draw_button(surface, self.btn_create, "CREATE ROOM", (15, 23, 42), COLOR_CYAN_NEON, COLOR_TEXT)
        self._draw_button(surface, self.btn_join, "JOIN ROOM", (15, 23, 42), COLOR_PINK_NEON, COLOR_TEXT)
        self._draw_button(surface, self.btn_back, "BACK TO SOLO", (30, 41, 59), (71, 85, 105), COLOR_TEXT_MUTED)

        hint = self.font_small.render("Host a room or enter a friend's code!", True, COLOR_TEXT_MUTED)
        surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 520)))

    def _draw_host_waiting(self, surface):
        """Draws big room code for Player 1 with pulsing waiting animation."""
        code = self.net.room_code or "...."
        lbl = self.font_body.render("YOUR ROOM CODE:", True, COLOR_TEXT_MUTED)
        surface.blit(lbl, lbl.get_rect(center=(SCREEN_WIDTH // 2, 240)))

        # Big Room Code Card
        code_box = pygame.Rect((SCREEN_WIDTH - 220) // 2, 270, 220, 70)
        pygame.draw.rect(surface, (15, 23, 42), code_box, border_radius=10)
        pygame.draw.rect(surface, COLOR_CYAN_NEON, code_box, 3, border_radius=10)

        code_surf = self.font_score.render(code, True, COLOR_CYAN_NEON)
        surface.blit(code_surf, code_surf.get_rect(center=code_box.center))

        # Pulsing text
        pulse_alpha = int(180 + 75 * (0.5 + 0.5 * math.sin(self.pulse_timer * 4.0)))
        wait_surf = self.font_body.render("WAITING FOR RIVAL...", True, (255, 215, 0))
        wait_surf.set_alpha(pulse_alpha)
        surface.blit(wait_surf, wait_surf.get_rect(center=(SCREEN_WIDTH // 2, 380)))

        hint = self.font_small.render("Tell your rival to enter this 4-letter code", True, COLOR_TEXT_MUTED)
        surface.blit(hint, hint.get_rect(center=(SCREEN_WIDTH // 2, 420)))

        self._draw_button(surface, self.btn_cancel, "CANCEL ROOM", (30, 41, 59), COLOR_ACCENT, COLOR_TEXT)

    def _draw_join_input(self, surface):
        """Draws input field and virtual keypad for room code entry."""
        lbl = self.font_body.render("ENTER 4-LETTER CODE:", True, COLOR_TEXT_MUTED)
        surface.blit(lbl, lbl.get_rect(center=(SCREEN_WIDTH // 2, 225)))

        # Input display box
        display_code = self.input_code.ljust(4, "_")
        box = pygame.Rect((SCREEN_WIDTH - 180) // 2, 255, 180, 56)
        pygame.draw.rect(surface, COLOR_INPUT_BG, box, border_radius=8)
        pygame.draw.rect(surface, COLOR_PINK_NEON, box, 2, border_radius=8)

        txt_surf = self.font_score.render(" ".join(display_code), True, COLOR_PINK_NEON)
        surface.blit(txt_surf, txt_surf.get_rect(center=box.center))

        # Join Submit Button
        can_submit = len(self.input_code) == 4
        btn_col = COLOR_PINK_NEON if can_submit else (71, 85, 105)
        self._draw_button(surface, self.btn_submit_code, "JOIN MATCH", (15, 23, 42), btn_col, COLOR_TEXT)

        # Virtual Keypad for touch / mouse clicks
        for char, rect in self.keypad_rects:
            pygame.draw.rect(surface, (20, 28, 48), rect, border_radius=4)
            pygame.draw.rect(surface, (51, 65, 85), rect, 1, border_radius=4)
            k_txt = self.font_small.render(char, True, COLOR_TEXT)
            surface.blit(k_txt, k_txt.get_rect(center=rect.center))

        # Backspace button
        if hasattr(self, "btn_backspace"):
            pygame.draw.rect(surface, (45, 55, 75), self.btn_backspace, border_radius=4)
            bs_txt = self.font_small.render("⌫ DEL", True, COLOR_TEXT)
            surface.blit(bs_txt, bs_txt.get_rect(center=self.btn_backspace.center))

        self._draw_button(surface, self.btn_cancel, "BACK", (30, 41, 59), (71, 85, 105), COLOR_TEXT_MUTED)

    def _draw_countdown(self, surface):
        """Displays large 3-2-1 countdown screen when match starts."""
        lbl = self.font_body.render("RIVAL DETECTED!", True, COLOR_PINK_NEON)
        surface.blit(lbl, lbl.get_rect(center=(SCREEN_WIDTH // 2, 230)))

        # Big Countdown Number
        cd_str = str(self.countdown_val) if self.countdown_val > 0 else "GO!"
        color = COLOR_GOLD_NEON if self.countdown_val > 0 else (34, 197, 94)
        cd_surf = self.font_score.render(cd_str, True, color)
        surface.blit(cd_surf, cd_surf.get_rect(center=(SCREEN_WIDTH // 2, 330)))

        sub = self.font_body.render("GET READY TO BLAST & FLY!", True, COLOR_TEXT)
        surface.blit(sub, sub.get_rect(center=(SCREEN_WIDTH // 2, 420)))
