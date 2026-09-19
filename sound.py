"""Live flip sounds using the same synthesis as the five WAV auditions."""

from io import BytesIO
import random

import numpy as np
from scipy.io import wavfile

from generate_flip_dot import PRESETS as SYNTH_PRESETS, LIVE_VOLUMES, dot_flip

PRESETS = tuple(SYNTH_PRESETS)


class FlipSound:
    def __init__(self, pygame, enabled=True):
        self.muted = False
        self.selected = 0
        self.banks = []
        self.rng = random.Random(42)
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

    @property
    def sounds(self):
        return self.banks[self.selected] if self.banks else []

    @property
    def status(self):
        state = ' / MUTED' if self.muted else ''
        if not self.banks:
            state = ' / AUDIO UNAVAILABLE'
        name = PRESETS[self.selected].replace('-', ' ').upper()
        return f'{self.selected + 1}/{len(PRESETS)}  {name}{state}'

    def select(self, direction):
        self.stop()
        self.selected = (self.selected + direction) % len(PRESETS)
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
