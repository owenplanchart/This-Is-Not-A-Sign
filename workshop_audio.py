"""Pure array synthesis and portable presets for the interactive workshop."""
from dataclasses import asdict, dataclass
import json
from pathlib import Path

import numpy as np

RATE = 44100
# field, label, minimum, maximum, unit, description
CONTROLS = (
    ('brightness', 'Impact brightness', 0., 1., '%', 'Dull plastic  /  sharp snap'),
    ('noise', 'Noise / body balance', 0., 1., '%', 'Housing resonance  /  impact friction'),
    ('pitch', 'Body pitch', 100., 500., 'Hz', 'Heavy housing  /  small mechanism'),
    ('decay', 'Decay', .3, 4., 'ms', 'Tight snap  /  longer clack'),
    ('density', 'Flip density', 100., 300., 'dots', 'Sparse  /  busy (full update only)'),
    ('jitter', 'Timing irregularity', 0., 35., 'ms', 'Ordered clusters  /  loose clatter (full update only)'),
)


@dataclass
class Settings:
    brightness: float = .8
    noise: float = .75
    pitch: float = 220.
    decay: float = 1.4
    density: float = 260.
    jitter: float = 18.

    def validate(self):
        for name, _, low, high, _, _ in CONTROLS:
            value = getattr(self, name)
            if isinstance(value, bool) or not isinstance(value, (int, float)) or not np.isfinite(value) or not low <= value <= high:
                raise ValueError(f'{name} must be between {low} and {high}')
        return self


def click(settings, rng):
    # Draw a fixed amount of randomness per click. Changing a control does not
    # shift the following clicks' random sequence during a locked comparison.
    count = round(rng.uniform(.005, .015) * RATE)
    noise = rng.standard_normal(count)
    pitch_factor, decay_factor = rng.uniform(.94, 1.06), rng.uniform(.85, 1.15)
    t = np.arange(count) / RATE
    width = round(16 - 15 * settings.brightness)
    noise = np.convolve(noise, np.ones(width) / width, mode='same')
    noise /= max(float(np.std(noise)), 1e-12)
    body = np.sin(2 * np.pi * settings.pitch * pitch_factor * t)
    envelope = np.minimum(t / .00012, 1) * np.exp(-t / (settings.decay * .001 * decay_factor))
    envelope *= np.minimum((t[-1] - t) / .0008, 1)
    audio = (settings.noise * noise + (1 - settings.noise) * body) * envelope
    return audio / max(float(np.max(np.abs(audio))), 1e-12)


def synthesize(settings, mode='wipe', seed=42):
    settings.validate()
    if mode not in ('single', 'wipe'):
        raise ValueError('Unknown listening mode')
    # Separate timing and timbre streams keep comparisons predictable.
    timing = np.random.default_rng(seed)
    timbre = np.random.default_rng(seed + 1)
    if mode == 'single':
        audio = click(settings, timbre)
    else:
        audio = np.zeros(2 * RATE)
        count = round(settings.density)
        spacing = timing.uniform(.7, 1.3, 13)
        columns = np.r_[0, np.cumsum(spacing)]
        columns = .035 + columns / columns[-1] * 1.915
        # Fixed schedules for the maximum density keep existing dots stable.
        assignment = np.arange(300) % 14
        jitter = timing.normal(0, 1, 300)
        gains = timing.uniform(.45, 1, 300)
        onsets = np.clip(columns[assignment] + jitter * settings.jitter / 1000, .005, 1.980)
        for onset, gain in zip(onsets[:count], gains[:count]):
            wave = click(settings, timbre) * gain
            start = round(onset * RATE)
            audio[start:start + len(wave)] += wave
    audio -= np.mean(audio)
    edge = min(round(.0001 * RATE), len(audio) // 2)
    audio[:edge] *= np.linspace(0, 1, edge)
    audio[-edge:] *= np.linspace(1, 0, edge)
    # Approximate level matching, capped at -0.9 dBFS to avoid PCM clipping.
    rms = float(np.sqrt(np.mean(audio ** 2)))
    peak = float(np.max(np.abs(audio)))
    gain = min((.12 if mode == 'single' else .065) / max(rms, 1e-12), .9 / max(peak, 1e-12))
    audio *= gain
    return np.rint(audio * 32767).astype(np.int16)


def save_preset(path, settings, seed, mode, volume=.5):
    settings.validate()
    Path(path).write_text(json.dumps({'version': 1, 'settings': asdict(settings), 'seed': seed, 'mode': mode, 'volume': volume}, indent=2) + '\n')


def load_preset(path):
    data = json.loads(Path(path).read_text())
    if not isinstance(data, dict) or data.get('version') != 1:
        raise ValueError('Unsupported preset version')
    settings = Settings(**data['settings']).validate()
    seed, mode = data['seed'], data['mode']
    if isinstance(seed, bool) or not isinstance(seed, int) or not 0 <= seed < 2**32:
        raise ValueError('Invalid random seed')
    if mode not in ('single', 'wipe'):
        raise ValueError('Invalid listening mode')
    volume = data.get('volume', .5)
    if isinstance(volume, bool) or not isinstance(volume, (int, float)) or not np.isfinite(volume) or not 0 <= volume <= 1:
        raise ValueError('Invalid volume')
    return settings, seed, mode, volume
