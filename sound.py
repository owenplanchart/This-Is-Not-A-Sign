"""Live flip sounds using the same synthesis as the five WAV auditions."""

from io import BytesIO
from pathlib import Path
import random
import warnings

import numpy as np
from scipy.io import wavfile

from generate_flip_dot import PRESETS as SYNTH_PRESETS, LIVE_VOLUMES, dot_flip

from workshop_audio import load_preset, synthesize

PRESETS = tuple(SYNTH_PRESETS)


class FlipSound:
    def __init__(self, pygame, enabled=True, workshop_preset=None, preset_dir=None):
        self.muted = False
        self.selected = 0
        self.banks = []
        self.rng = random.Random(42)
        self.names = [name.replace('-', ' ').upper() for name in PRESETS]
        directory = Path(preset_dir) if preset_dir is not None else Path(__file__).parent / 'workshop_presets'
        paths = sorted(directory.glob('*.json'), key=lambda path: path.name.lower())
        requested = Path(workshop_preset).resolve() if workshop_preset is not None else None
        if requested is not None and all(path.resolve() != requested for path in paths):
            paths.append(requested)
        custom_presets = []
        for path in paths:
            try:
                custom = load_preset(path)
            except (OSError, ValueError, TypeError, KeyError) as error:
                if requested == path.resolve():
                    raise
                warnings.warn(f'Skipping invalid sound preset {path.name}: {error}')
                continue
            if requested == path.resolve():
                self.selected = len(self.names)
            self.names.append('CUSTOM: ' + path.stem)
            custom_presets.append(custom)
        if not enabled or not pygame.mixer.get_init():
            return
        pygame.mixer.set_num_channels(16)
        synthesis_rng = np.random.default_rng(42)
        for preset in PRESETS:
            bank = []
            for _ in range(12):
                samples = dot_flip(synthesis_rng, preset=preset)
                pcm = np.rint(samples * .68 * 32767).astype(np.int16)
                buffer = BytesIO()
                wavfile.write(buffer, 44100, pcm)
                buffer.seek(0)
                sound = pygame.mixer.Sound(file=buffer)
                sound.set_volume(LIVE_VOLUMES[preset])
                bank.append(sound)
            self.banks.append(bank)

        for settings, seed, _mode, volume in custom_presets:
            bank = []
            for variation in range(12):
                pcm = synthesize(settings, mode='single', seed=seed + variation)
                buffer = BytesIO()
                wavfile.write(buffer, 44100, pcm)
                buffer.seek(0)
                sound = pygame.mixer.Sound(file=buffer)
                sound.set_volume(volume)
                bank.append(sound)
            self.banks.append(bank)

    @property
    def sounds(self):
        return self.banks[self.selected] if self.banks else []

    @property
    def status(self):
        state = ' / MUTED' if self.muted else ''
        if not self.banks:
            state = ' / AUDIO UNAVAILABLE'
        name = self.names[self.selected]
        return f'{self.selected + 1}/{len(self.names)}  {name}{state}'

    def select(self, direction):
        self.stop()
        self.selected = (self.selected + direction) % len(self.names)
        self.click()

    def stop(self):
        for bank in self.banks:
            for sound in bank:
                sound.stop()

    def toggle(self):
        self.muted = not self.muted
        if self.muted:
            self.stop()

    def click(self):
        if self.sounds and not self.muted:
            self.rng.choice(self.sounds).play()
