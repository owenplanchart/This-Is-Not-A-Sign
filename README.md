# flipChart

Standalone flip-dot audio generator:

```sh
source .venv/bin/activate
python -m pip install -r requirements.txt
python generate_flip_dot.py --seed 42
```

Writes `flip_dot_sign.wav`: 260 jittered plastic-disc impacts over 2 seconds,
44.1 kHz mono 16-bit PCM. Uses only NumPy math and SciPy WAV export, with no
playback or external samples. Omit `--seed` for a fresh pattern; `--flips`
accepts 100–300 and `--duration` accepts 1.5–2.5 seconds.

For five distinct sound characters, run `python generate_flip_dot.py --audition`,
then `afplay flip_dot_audition.wav` on macOS. The 14-second comparison plays
Loose Clatter, Plastic Snap, Plastic Clack, Hollow Plastic, and Hard Plastic, with one-second gaps.
Separate WAVs are also saved for each. Use `--preset plastic-clack` (or `loose-clatter`,
`plastic-snap`, `hollow-plastic`, `hard-plastic`) to generate a chosen character.
Replaying a WAV always plays the same recording; rerunning the generator
changes the random pattern, while changing the preset changes its character.

A Python / Pygame sketch of a four-character mechanical split-flap board.
Displays **THIS IS NOT A SIGN** in a single row of matching split-flap tiles.
The letters in **THIS IS NOT A** stay still. Spaces use matching blank tiles,
including the same centre seam and hinges.
The display starts with **SIGN**, then randomly selects four-letter dictionary
nouns beginning with consonants, holding each finished word for 2.8 seconds. Every word appears once per
shuffled cycle, without an immediate repeat when a new cycle starts. Letters flip through the alphabet with
staggered starts; the preceding tiles stay fixed.

```sh
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -r requirements.txt
python3 main.py
```

For later sessions, run `source .venv/bin/activate` before starting the sketch.
Run `deactivate` to leave the virtual environment.

Each moving letter triggers an individual click from the same synthesis used
for the WAV auditions. Loose Clatter (number 1) is the default, with twelve
precomputed click variations. The live rhythm follows the visible letter flips;
the standalone WAV demonstrates a denser, full flip-dot screen wipe.
No audio downloads are needed; the sketch also works without an audio device.

Space pauses/resumes, Right Arrow advances when the current word has settled,
Up/Down selects and previews one of five sounds: Loose Clatter (original, default),
Plastic Snap, Plastic Clack, Hollow Plastic, and Hard Plastic.
The four plastic variations play about 2.4 dB louder in the app. The choice wraps at either
end and applies to subsequent flips. Previewing works while paused and respects
mute.

| Key | Action |
| --- | --- |
| Space | Pause / resume |
| Right Arrow | Next word once the current word has settled (while running) |
| Up / Down | Select and preview a sound |
| M | Mute / unmute |
| G | Hide / show all labels, status text, and keyboard hints |
| Q or Escape | Quit |

The GUI starts visible. With it hidden, the sign and frame remain visible and
all keyboard controls, animation, and sound continue to work.

The offline dictionary lives in `data/four_letter_words.txt`; add or remove
noun entries there using one four-letter A–Z word per line. It is derived from the
macOS Webster word list, excluding capitalized entries to reduce proper names.
The pool is filtered against WordNet 3.0 noun entries: every word has at least
one noun meaning, though some also function as verbs (such as PLAY).
Nouns beginning with A, E, I, O, or U are excluded; Y is retained.
It includes rare/archaic vocabulary and is not an exhaustive list of modern
English nouns or inflections. WordNet attribution is in `data/WORDNET_LICENSE.txt`. Source notes are in `data/SOURCE.txt`.

Save a preview without opening a window:

```sh
python3 main.py --snapshot preview.png
```

The active pool also applies a conservative “a ___” filter: suspected plurals,
substance-only senses, proper-name senses, and silent-H article exceptions are
excluded. Singular countability is inferred from WordNet definitions, not an
explicit dictionary tag, so this can exclude valid words and retain awkward
ones. HERB is excluded because its article differs between dialects.

The 1,754 pre-filter candidates are preserved in `data/noun_candidates.txt`.
`data/noun_filter_audit.csv` records every keep/exclude decision for later
curation. Rebuild with `python scripts/filter_nouns.py /path/to/wordnet.zip`.
The application uses the bundled filtered list and needs no dictionary download.
