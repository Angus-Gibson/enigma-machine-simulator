"""
sound_manager.py
Real audio samples for the Enigma Machine Simulator.

Sounds sourced from Freesound.org (CC0 Public Domain — no attribution required):
  key_press.mp3   – "typewriter.wav"  by BMacZero  (freesound.org/s/160678)
  rotor_click.mp3 – "MECHRtch_Ratchet01" by InMotionAudio (freesound.org/s/689528)
  place_rotor.mp3 – "Thud2.wav"       by BMacZero  (freesound.org/s/96137)

Fallback: if any file is missing or the mixer fails, that slot is silently skipped.
"""

import os
import sys
import pathlib
import platform
import pygame

# ── WSL2 audio fix ────────────────────────────────────────────────────────────
# WSLg sets PULSE_SERVER automatically; SDL just needs to be told to use Pulse
# instead of ALSA.  Must run before pygame.init().
if 'microsoft' in platform.uname().release.lower():
    os.environ.setdefault('SDL_AUDIODRIVER', 'pulse')


def _resource_path(relative: str) -> pathlib.Path:
    """Resolve a bundled-resource path for both source and PyInstaller builds."""
    base = pathlib.Path(getattr(sys, '_MEIPASS', pathlib.Path(__file__).parent))
    return base / relative


# ── File locations ─────────────────────────────────────────────────────────────
_SOUNDS_DIR = _resource_path('sounds')

# Map every logical sound name to a file.
# rotor_click and ring_click both use the ratchet sample (ring_click plays at
# lower volume to feel lighter).
# rotor_step uses the same ratchet; it fires alongside key_press.
# fmt: off
_SOUND_FILES: dict[str, str] = {
    'key_press':    'key_press.mp3',
    'rotor_step':   'rotor_click.mp3',
    'rotor_click':  'rotor_click.mp3',
    'ring_click':   'rotor_click.mp3',
    'place_rotor':  'place_rotor.mp3',
}

# Per-sound volume (0.0–1.0).  ring_click is quieter to feel like a lighter action.
_VOLUMES: dict[str, float] = {
    'key_press':   0.9,
    'rotor_step':  0.6,
    'rotor_click': 0.8,
    'ring_click':  0.45,
    'place_rotor': 1.0,
}
# fmt: on


class SoundManager:
    """Loads audio samples and plays them by name."""

    def __init__(self):
        self._sounds: dict[str, pygame.mixer.Sound] = {}
        self._ok = False

        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=512)
        except Exception as exc:
            print(f"[SoundManager] Mixer init failed: {exc}")
            return

        # Load each file; skip gracefully if a file is absent or unreadable.
        loaded: list[str] = []
        failed: list[str] = []
        _file_cache: dict[str, pygame.mixer.Sound] = {}  # avoid loading the same file twice

        for name, filename in _SOUND_FILES.items():
            path = _SOUNDS_DIR / filename
            try:
                if filename not in _file_cache:
                    _file_cache[filename] = pygame.mixer.Sound(str(path))
                snd = _file_cache[filename]
                snd.set_volume(_VOLUMES.get(name, 1.0))
                # Each logical name gets its own Sound object so volumes are independent
                snd_copy = pygame.mixer.Sound(str(path))
                snd_copy.set_volume(_VOLUMES.get(name, 1.0))
                self._sounds[name] = snd_copy
                loaded.append(name)
            except Exception as exc:
                failed.append(f"{name} ({exc})")

        if loaded:
            self._ok = True
            print(f"[SoundManager] Loaded: {', '.join(loaded)}")
        if failed:
            print(f"[SoundManager] Skipped: {'; '.join(failed)}")

    def play(self, name: str):
        if self._ok and name in self._sounds:
            try:
                self._sounds[name].play()
            except Exception:
                pass
