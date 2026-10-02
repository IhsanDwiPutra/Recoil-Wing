"""
Sound manager for Recoil Wing.
Handles pre-loading, audio mixing, volume control, and safe fallback.
"""
import os
import pygame


class SoundManager:
    def __init__(self, sounds_dir=None):
        self.enabled = False
        self.sounds = {}
        self.muted = False
        self.master_volume = 0.85

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

        # Pre-load available sound files
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
        if not self.enabled or self.muted:
            return

        sound = self.sounds.get(sound_name)
        if sound:
            try:
                final_volume = max(0.0, min(1.0, volume * self.master_volume))
                sound.set_volume(final_volume)
                sound.play()
            except Exception:
                pass

    def toggle_mute(self):
        """Toggles audio mute state."""
        self.muted = not self.muted
        return self.muted
