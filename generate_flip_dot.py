"""Synthesize a flip-dot sign wipe as 16-bit PCM, without audio playback.

Run: python generate_flip_dot.py --seed 42
"""

import argparse
from pathlib import Path

import numpy as np
from scipy.io import wavfile


# Noise weight, noise smoothing, decay, housing Hz, columns, jitter, dot count.
PRESETS = {
    'loose-clatter': (.75, 4, .0014, 220, 14, .018, 260),
    'plastic-snap': (.83, 6, .0011, 210, 14, .018, 260),
    'plastic-clack': (.68, 10, .0017, 185, 14, .018, 260),
    'hollow-plastic': (.53, 14, .0020, 160, 14, .018, 260),
    'hard-plastic': (.87, 3, .00095, 250, 14, .018, 260),
}

# The original stays at its existing level; the new live sounds are ~2.4 dB louder.
LIVE_VOLUMES = {name: (.34 if name == 'loose-clatter' else .45) for name in PRESETS}


def dot_flip(rng, sample_rate=44100, preset='loose-clatter'):
    """One 5–15 ms plastic impact with a short 150–300 Hz housing response."""
    duration = rng.uniform(.005, .015)
    count = round(duration * sample_rate)
    t = np.arange(count) / sample_rate
    noise_weight, smoothing, decay_time, frequency, *_ = PRESETS[preset]
    noise = rng.standard_normal(count)
    noise = np.convolve(noise, np.ones(smoothing) / smoothing, mode='same')
    noise /= max(np.std(noise), 1e-12)
    housing = np.sin(2 * np.pi * np.clip(frequency * rng.uniform(.94, 1.06), 150, 300) * t)
    # A near-instant attack and an aggressive decay keep the impact a snap.
    attack = np.minimum(t / .00012, 1)
    decay = np.exp(-t / (decay_time * rng.uniform(.85, 1.15)))
    # Explicitly zero both ends so a truncated sample never makes a hard step.
    tail = np.minimum((t[-1] - t) / .0008, 1)
    click = (noise_weight * noise + (1 - noise_weight) * housing) * attack * decay * tail
    peak = np.max(np.abs(click))
    return click / peak if peak else click


def generate_wipe(seed=None, duration=2.0, flips=None, sample_rate=44100, preset='loose-clatter'):
    """Schedule clustered columns, then jitter every solenoid independently."""
    if preset not in PRESETS:
        raise ValueError(f'Unknown preset: {preset}')
    *_, columns, jitter, default_flips = PRESETS[preset]
    flips = default_flips if flips is None else flips
    if not 1.5 <= duration <= 2.5:
        raise ValueError('Duration must be between 1.5 and 2.5 seconds.')
    if not 100 <= flips <= 300:
        raise ValueError('Choose between 100 and 300 dot flips.')
    rng = np.random.default_rng(seed)
    audio = np.zeros(round(duration * sample_rate), dtype=np.float64)
    # Irregular column spacing suggests a traveling wipe. Several dots share
    # each column, with independent jitter to produce brief mechanical clumps.
    spacing = rng.uniform(.7, 1.3, columns - 1)
    column_times = np.r_[0, np.cumsum(spacing)]
    column_times = .035 + column_times / column_times[-1] * (duration - .085)
    assignments = np.arange(flips) % columns
    rng.shuffle(assignments)
    onsets = column_times[assignments] + rng.normal(0, jitter, flips)
    onsets = np.clip(onsets, .005, duration - .020)
    for onset in np.sort(onsets):
        click = dot_flip(rng, sample_rate, preset) * rng.uniform(.45, 1)
        start = round(onset * sample_rate)
        audio[start:start + len(click)] += click
    # Remove any tiny DC offset, taper the file edges, and normalize only after
    # summation: overlapping impacts cannot overflow the integer PCM range.
    audio -= audio.mean()
    fade = round(.004 * sample_rate)
    audio[:fade] *= np.linspace(0, 1, fade)
    audio[-fade:] *= np.linspace(1, 0, fade)
    peak = np.max(np.abs(audio))
    if peak:
        audio *= .95 / peak
    return np.rint(audio * 32767).astype(np.int16)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--seed', type=int, help='optional reproducible random seed')
    parser.add_argument('--duration', type=float, default=2.0)
    parser.add_argument('--flips', type=int, help='override preset dot count (100–300)')
    parser.add_argument('--preset', choices=PRESETS, default='loose-clatter')
    parser.add_argument('--audition', action='store_true', help='export all five presets and a combined comparison')
    parser.add_argument('--output', type=Path, default=Path('flip_dot_sign.wav'))
    args = parser.parse_args()
    try:
        if args.audition:
            parts = []
            for index, preset in enumerate(PRESETS, 1):
                pcm = generate_wipe(args.seed, args.duration, args.flips, preset=preset)
                # Match relative live volumes while retaining WAV peak headroom.
                pcm = np.rint(pcm.astype(np.float64) * LIVE_VOLUMES[preset] / .45).astype(np.int16)
                target = args.output.parent / f'flip_dot_{index}_{preset}.wav'
                wavfile.write(target, 44100, pcm)
                if parts:
                    parts.append(np.zeros(44100, dtype=np.int16))
                parts.append(pcm)
                print(f'{index}. {preset}: {target}')
            target = args.output.parent / 'flip_dot_audition.wav'
            wavfile.write(target, 44100, np.concatenate(parts))
            print(f'Comparison: {target} (one-second silence between presets)')
            return
        pcm = generate_wipe(args.seed, args.duration, args.flips, preset=args.preset)
    except ValueError as error:
        parser.error(str(error))
    wavfile.write(args.output, 44100, pcm)
    print(f'Saved {args.output}: {args.preset}, {args.duration:g}s, 44.1 kHz, mono 16-bit PCM')


if __name__ == '__main__':
    main()
