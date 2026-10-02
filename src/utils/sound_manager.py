"""
Sound manager for Recoil Wing.
Handles pre-loading, audio mixing, background music (BGM) streaming,
custom YouTube MP3/OGG priority, and safe fallback.
"""
import os
import pygame


class SoundManager:
    def __init__(self, sounds_dir=None):
        self.enabled = False
        self.sounds = {}
        self.muted = False
        self.master_volume = 0.85
        self.bgm_volume = 0.38
        self.bgm_playing = False
        self.sfx_enabled = True
        self.bgm_enabled = True

        if sounds_dir is None:
            sounds_dir = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sounds")
        self.sounds_dir = os.path.abspath(sounds_dir)

        # Attempt mixer initialization with safe fallback
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.pre_init(44100, -16, 2, 512)
                pygame.mixer.init()
            pygame.mixer.set_num_channels(16)
            self.enabled = True
        except Exception as e:
            print(f"[SoundManager] Audio device unavailable ({e}). Continuing silently.")
            self.enabled = False
            return

        # Pre-load available sound effects
        self._load_sounds()

    def _load_sounds(self):
        """Pre-loads all .wav sounds from the sounds directory."""
        if not os.path.exists(self.sounds_dir):
            return

        sound_files = {
            "shoot": "shoot.wav",
            "shotgun": "shotgun.wav",
            "laser": "laser.wav",
            "explosion": "explosion.wav",
            "portal": "portal.wav",
            "shield_deflect": "shield_deflect.wav",
            "score": "score.wav",
            "crash": "crash.wav",
        }

        for name, filename in sound_files.items():
            full_path = os.path.join(self.sounds_dir, filename)
            if os.path.exists(full_path):
                try:
                    sound_obj = pygame.mixer.Sound(full_path)
                    self.sounds[name] = sound_obj
                except Exception as e:
                    print(f"[SoundManager] Could not load {filename}: {e}")

    def play(self, sound_name, volume=1.0):
        """Plays a loaded sound effect with custom volume."""
        if not self.enabled or self.muted or not self.sfx_enabled:
            return

        sound = self.sounds.get(sound_name)
        if sound:
            try:
                final_volume = max(0.0, min(1.0, volume * self.master_volume))
                sound.set_volume(final_volume)
                sound.play()
            except Exception:
                pass

    def play_bgm(self):
        """
        Starts looping background music.
        Priority:
        1. Custom user MP3 from YouTube: 'assets/sounds/bgm_gameplay.mp3'
        2. Custom user OGG: 'assets/sounds/bgm_gameplay.ogg'
        3. Built-in procedural synthwave loop: 'assets/sounds/bgm_gameplay.wav'
        """
        if not self.enabled:
            return

        # Check for user custom MP3 first, then OGG, then synthesized WAV
        candidates = [
            os.path.join(self.sounds_dir, "bgm_gameplay.mp3"),
            os.path.join(self.sounds_dir, "bgm_gameplay.ogg"),
            os.path.join(self.sounds_dir, "bgm_gameplay.wav"),
        ]

        music_file = None
        for path in candidates:
            if os.path.exists(path):
                music_file = path
                break

        if not music_file:
            return

        try:
            pygame.mixer.music.load(music_file)
            vol = self.bgm_volume if (self.bgm_enabled and not self.muted) else 0.0
            pygame.mixer.music.set_volume(vol)
            pygame.mixer.music.play(loops=-1)  # Infinite seamless loop
            self.bgm_playing = True
            filename = os.path.basename(music_file)
            print(f"[SoundManager] BGM playing: {filename}")
        except Exception as e:
            print(f"[SoundManager] Could not start BGM: {e}")

    def duck_bgm(self):
        """Softens background music volume during Game Over."""
        if self.enabled and not self.muted and self.bgm_enabled:
            try:
                pygame.mixer.music.set_volume(self.bgm_volume * 0.35)
            except Exception:
                pass

    def restore_bgm(self):
        """Restores normal background music volume."""
        if self.enabled and not self.muted and self.bgm_enabled:
            try:
                pygame.mixer.music.set_volume(self.bgm_volume)
            except Exception:
                pass

    def toggle_mute(self):
        """Toggles audio mute state for both SFX and BGM."""
        self.muted = not self.muted
        if self.enabled:
            try:
                if self.muted or not self.bgm_enabled:
                    pygame.mixer.music.set_volume(0.0)
                else:
                    pygame.mixer.music.set_volume(self.bgm_volume)
            except Exception:
                pass
        return self.muted

    def toggle_bgm(self):
        """Toggles BGM state on or off."""
        self.bgm_enabled = not self.bgm_enabled
        if self.enabled:
            try:
                if not self.bgm_enabled or self.muted:
                    pygame.mixer.music.set_volume(0.0)
                else:
                    pygame.mixer.music.set_volume(self.bgm_volume)
            except Exception:
                pass
        return self.bgm_enabled

    def toggle_sfx(self):
        """Toggles SFX state on or off."""
        self.sfx_enabled = not self.sfx_enabled
        return self.sfx_enabled
