"""
Procedural 8-bit/Arcade Sound Synthesizer for Recoil Wing.
Generates retro sound effects directly using Python standard libraries (wave, struct, math, random).
No external downloads or dependencies required!
"""
import os
import math
import wave
import struct
import random

SAMPLE_RATE = 44100


def clamp(val, min_val=-1.0, max_val=1.0):
    return max(min_val, min(max_val, val))


def write_wav(filepath, samples):
    """Writes a list of floating point audio samples (-1.0 to 1.0) into a 16-bit PCM WAV file."""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with wave.open(filepath, "w") as wav_file:
        wav_file.setnchannels(1)       # Mono
        wav_file.setsampwidth(2)      # 16-bit
        wav_file.setframerate(SAMPLE_RATE)

        raw_data = bytearray()
        for sample in samples:
            int_val = int(clamp(sample) * 32767)
            raw_data.extend(struct.pack("<h", int_val))

        wav_file.writeframes(raw_data)


def generate_shoot_sound():
    """Crisp arcade pew: fast descending pitch with snappy envelope."""
    duration = 0.13
    total_samples = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(total_samples):
        t = i / total_samples
        # Exponential pitch drop from 750 Hz down to 90 Hz
        freq = 750.0 * (0.12 ** t)
        phase = 2.0 * math.pi * freq * (i / SAMPLE_RATE)
        # Mix sine + soft square
        wave_val = math.sin(phase) * 0.7 + (1.0 if math.sin(phase) > 0 else -1.0) * 0.2
        # Fast decay envelope
        env = (1.0 - t) ** 1.8
        samples.append(wave_val * env * 0.7)

    return samples


def generate_shotgun_sound():
    """Heavy scatter blast: low bass boom mixed with textured noise."""
    duration = 0.24
    total_samples = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(total_samples):
        t = i / total_samples
        # Bass frequency drop 300Hz down to 45Hz
        freq = 300.0 * (0.15 ** t)
        phase = 2.0 * math.pi * freq * (i / SAMPLE_RATE)
        sub_bass = math.sin(phase)

        # White noise burst for blast texture
        noise = random.uniform(-1.0, 1.0) * max(0.0, 1.0 - t * 2.5)

        # Combined with strong punchy decay
        env = (1.0 - t) ** 1.5
        val = (sub_bass * 0.65 + noise * 0.35) * env
        samples.append(val * 0.85)

    return samples


def generate_laser_sound():
    """Sci-fi laser zap: high frequency sweep with resonant metallic tone."""
    duration = 0.17
    total_samples = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(total_samples):
        t = i / total_samples
        # Rapid sweep from 2200Hz down to 280Hz
        freq = 2200.0 * (0.13 ** t)
        phase = 2.0 * math.pi * freq * (i / SAMPLE_RATE)
        # Triangle / sine wave for smooth sci-fi feel
        val = (math.asin(math.sin(phase)) * (2.0 / math.pi))
        env = (1.0 - t) ** 1.3
        samples.append(val * env * 0.65)

    return samples


def generate_explosion_sound():
    """Crunchy obstacle explosion: deep low rumble with decaying noise."""
    duration = 0.34
    total_samples = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(total_samples):
        t = i / total_samples
        # Rumble bass 90Hz to 30Hz
        freq = 90.0 * (0.33 ** t)
        phase = 2.0 * math.pi * freq * (i / SAMPLE_RATE)
        rumble = math.sin(phase)

        # Debris noise
        noise = random.uniform(-1.0, 1.0)
        env = (1.0 - t) ** 1.4

        val = (rumble * 0.45 + noise * 0.55) * env
        samples.append(val * 0.8)

    return samples


def generate_portal_sound():
    """Futuristic ascending arpeggio chime: crystal clear chords."""
    duration = 0.30
    total_samples = int(SAMPLE_RATE * duration)
    samples = []
    # 4 distinct ascending notes (C5, E5, G5, C6)
    notes = [523.25, 659.25, 783.99, 1046.50]

    for i in range(total_samples):
        t = i / total_samples
        note_idx = min(len(notes) - 1, int(t * len(notes)))
        freq = notes[note_idx]
        phase = 2.0 * math.pi * freq * (i / SAMPLE_RATE)
        # Sine chime
        val = math.sin(phase)
        # Note decay
        local_t = (t * len(notes)) % 1.0
        env = math.exp(-local_t * 3.5) * (1.0 - t * 0.3)
        samples.append(val * env * 0.75)

    return samples


def generate_shield_deflect_sound():
    """Resonant metallic ring: harmonic chime that deflects collision."""
    duration = 0.28
    total_samples = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(total_samples):
        t = i / total_samples
        # Dual frequency harmonic ring (880Hz and 1320Hz)
        phase1 = 2.0 * math.pi * 880.0 * (i / SAMPLE_RATE)
        phase2 = 2.0 * math.pi * 1320.0 * (i / SAMPLE_RATE)
        ring = math.sin(phase1) * 0.6 + math.sin(phase2) * 0.4
        env = math.exp(-t * 6.0)
        samples.append(ring * env * 0.8)

    return samples


def generate_score_sound():
    """Happy two-tone arcade chime: passing obstacles."""
    duration = 0.12
    total_samples = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(total_samples):
        t = i / total_samples
        # First half 880Hz, second half 1320Hz
        freq = 880.0 if t < 0.45 else 1320.0
        phase = 2.0 * math.pi * freq * (i / SAMPLE_RATE)
        val = math.sin(phase)
        env = (1.0 - (t if t < 0.45 else (t - 0.45) / 0.55)) ** 1.5
        samples.append(val * env * 0.6)

    return samples


def generate_crash_sound():
    """Heavy fatal crash thud."""
    duration = 0.42
    total_samples = int(SAMPLE_RATE * duration)
    samples = []

    for i in range(total_samples):
        t = i / total_samples
        freq = 130.0 * (0.2 ** t)
        phase = 2.0 * math.pi * freq * (i / SAMPLE_RATE)
        thud = math.sin(phase) * 0.7
        harsh_noise = random.uniform(-1.0, 1.0) * max(0.0, 0.7 - t * 2.0)
        env = (1.0 - t) ** 1.6
        val = (thud + harsh_noise) * env
        samples.append(val * 0.9)

    return samples


def generate_all_sounds(output_dir):
    """Generates all 8 game sound effects into target directory."""
    os.makedirs(output_dir, exist_ok=True)
    sound_generators = {
        "shoot.wav": generate_shoot_sound,
        "shotgun.wav": generate_shotgun_sound,
        "laser.wav": generate_laser_sound,
        "explosion.wav": generate_explosion_sound,
        "portal.wav": generate_portal_sound,
        "shield_deflect.wav": generate_shield_deflect_sound,
        "score.wav": generate_score_sound,
        "crash.wav": generate_crash_sound,
    }

    generated_paths = []
    for filename, gen_fn in sound_generators.items():
        file_path = os.path.join(output_dir, filename)
        samples = gen_fn()
        write_wav(file_path, samples)
        generated_paths.append(file_path)

    return generated_paths


if __name__ == "__main__":
    sounds_folder = os.path.join(os.path.dirname(__file__), "..", "..", "assets", "sounds")
    paths = generate_all_sounds(sounds_folder)
    print(f"Successfully generated {len(paths)} sound effects in {sounds_folder}")
