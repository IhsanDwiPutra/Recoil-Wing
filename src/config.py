"""
Configuration and constants for Recoil Wing.
"""

# Screen & Display Settings
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 750
FPS = 60
TITLE = "Recoil Wing"

# Physics Settings
GRAVITY = 0.42
MAX_FALL_SPEED = 12.0
RECOIL_FORCE = 8.5
MAX_CLIMB_SPEED = -10.0

# Player Settings
PLAYER_WIDTH = 34
PLAYER_HEIGHT = 28
PLAYER_START_X = 100
PLAYER_START_Y = 320

# Weapon & Ammo Settings
MAX_AMMO = 4
AMMO_RELOAD_FRAMES = 24       # ~0.4s reload per bullet at 60 FPS
BULLET_SPEED = 15.0
BULLET_WIDTH = 6
BULLET_HEIGHT = 14

# Obstacle & Pipe Settings
PIPE_SPEED = 2.6
PIPE_SPAWN_FRAMES = 115       # Spawn interval in frames (~1.9s at 60 FPS)
PIPE_WIDTH = 64
PIPE_GAP = 185                # Vertical gap between top and bottom pipe (widened for fair navigation)
PIPE_MIN_HEIGHT = 70          # Minimum length for top/bottom pipes
CRATE_SIZE = 44               # Destructible crate block dimension


# Colors (Modern Arcade Palette)
COLOR_BG_TOP = (18, 20, 36)         # Deep Navy
COLOR_BG_BOTTOM = (28, 30, 52)      # Indigo
COLOR_GROUND = (15, 16, 26)         # Dark Soil
COLOR_GROUND_LINE = (55, 62, 92)    # Horizon Outline

COLOR_PLAYER = (45, 212, 191)       # Vibrant Teal
COLOR_PLAYER_EYE = (255, 255, 255)  # White
COLOR_PLAYER_BEAK = (251, 191, 36)  # Amber
COLOR_GUN = (100, 116, 139)         # Steel Slate

COLOR_BULLET = (250, 204, 21)       # Neon Yellow
COLOR_BULLET_TRAIL = (245, 158, 11) # Orange
COLOR_MUZZLE_FLASH = (254, 240, 138)# Bright Flash Yellow

COLOR_AMMO_FILLED = (45, 212, 191)  # Teal pip
COLOR_AMMO_EMPTY = (51, 65, 85)     # Dim dark pip
COLOR_AMMO_BORDER = (148, 163, 184) # Outline

COLOR_PIPE = (71, 85, 105)          # Slate Grey
COLOR_PIPE_OUTLINE = (30, 41, 59)
COLOR_CRATE = (239, 68, 68)         # Destructible Crate Red/Amber
COLOR_CRATE_CRACK = (254, 202, 202)

COLOR_TEXT = (248, 250, 252)        # Bright White
COLOR_TEXT_MUTED = (148, 163, 184)  # Slate Muted
COLOR_ACCENT = (244, 63, 94)        # Rose Accent

