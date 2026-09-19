# flipChart

## Interactive sound workshop

Run the workshop separately from the sign:

```sh
cd "/Users/owenplanchart/Developer/Python/split flap sign"
.venv/bin/python sound_workshop.py
```

The workshop starts from the Loose Clatter sound character. Drag a slider and
release to hear the change. Six controls adjust impact brightness, noise/body
balance, body pitch, decay, flip density, and timing irregularity. Density and
timing apply to **Full update** mode; **Single flip** isolates one impact.
**Volume** changes listening level separately. Audio is approximately level
matched with peak headroom; this is not a perceptual loudness guarantee.

- **Play / Stop:** audition the current sound; Space also plays/stops.
- **Loop + gap:** repeat with a 600 ms pause so updates remain distinct.
- **Randomness locked:** repeat the same pattern while adjusting parameters.
  Unlock to generate a new pattern on each play or adjustment. **New pattern**
  changes the seed even while locked.
- **Store B as A:** preserve your current settings and seed as a reference.
  **Listening: A/B** or Tab switches between that reference and your edits.
  Both use the current listening mode and volume. Editing a slider returns to B.
- **Reset Loose Clatter:** restore the starting parameters in B.
- **Save preset:** type a name, then Enter. Backspace edits; Escape cancels.
  Existing names are protected from overwriting.
- **Load preset:** use Up/Down to choose a saved preset, then Enter to load and
  audition. Parameters, seed, listening mode, and volume are restored.
- **Export WAV:** save the selected A/B sound at the current listening volume,
  plus a JSON preset alongside it. Files go in `workshop_presets/` next to the
  scripts. WAV files remain excluded from Git.
- **Q / Escape:** quit (Escape closes a dialog first).

The waveform and peak indicator show the current generated audio. If no audio
output is available, preset editing and WAV export still work. This workshop
saves reusable JSON presets. Load one into the sign with `--sound-preset` as
shown below.

### Use a workshop preset on the sign

Save a preset in the workshop (for example, `my-clatter`), then run:

```sh
.venv/bin/python main.py --sound-preset workshop_presets/my-clatter.json
```

The sign automatically loads every valid JSON preset in `workshop_presets/`
at startup. Run `.venv/bin/python main.py` and use Up/Down: the five built-in
sounds come first, then your workshop presets from **6** onward in filename
order. The label shows `CUSTOM: filename` and the total number of sounds.
Press G if the labels are hidden. Restart after saving new workshop presets.

The optional `--sound-preset` flag selects that preset immediately; it can also
load a JSON file outside the presets folder. M still mutes/unmutes. Invalid
automatically discovered files are skipped with a warning; an invalid explicitly
requested preset produces an error.

The sign uses the saved brightness, noise/body balance, pitch, decay, volume,
and seed to generate twelve click variations. Each click follows a visible
letter flip. Workshop density, timing irregularity, and full-update mode do
not control the sign's animation; use **Single flip** in the workshop to hear
the individual impact you are transferring. The first generated variation
matches that preview. Preset edits take effect when you restart the sign.
Quote the path if it contains spaces. WAV export is not needed.

For a headless preview: `.venv/bin/python sound_workshop.py --snapshot /tmp/workshop.png`.
Run checks with `.venv/bin/python -m unittest discover -s tests -v`.

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
In the default **1Word** mode, the letters in **THIS IS NOT A** stay still. Spaces use matching blank tiles,
including the same centre seam and hinges.
The display starts with **SIGN**, then randomly selects four-letter dictionary
nouns beginning with consonants, holding each finished word for 2.8 seconds. Every word appears once per
shuffled cycle, without an immediate repeat when a new cycle starts. Letters flip through the alphabet with
staggered starts. In **2Word** mode, the first word alternates **THIS / THAT**
after each noun change has finished: the noun flips first, then THIS/THAT.
** IS NOT A ** and all blank tiles stay fixed.
Only changing letters in THIS/THAT flip, using the selected sound.
In 2Word, the noun settles, waits 1 second, then THIS/THAT flips.
Once THIS/THAT settles, another 1-second pause precedes the next noun.
1Word retains its 2.8-second hold.

Press **1** for 1Word or **2** for 2Word. A switch waits for any active
transition to finish, and while paused it waits for resume. Returning to 1Word
flips THAT back to THIS before continuing. You can also start in 2Word:

```sh
.venv/bin/python main.py --mode 2Word
```

**3Word** adds a random NOT / blank choice alongside THIS/THAT. After the noun
settles and the 1-second pause ends, THIS/THAT flips and NOT's three tiles
start their transition at the same time if their state changes. Each cycle
independently chooses NOT or three blanks with equal probability; consecutive
cycles can keep the same state. Blank tiles retain their seams and hinges.
The next 1-second pause starts only once both groups have settled.

Press **3** or launch with `.venv/bin/python main.py --mode 3Word`.
Returning to 1Word or 2Word restores NOT; returning to 1Word also restores THIS.
Mode switches continue to wait for the current cycle and for pause to end.


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
| 1 / 2 / 3 / 4 | Select 1Word / 2Word / 3Word / 4Word mode |
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

## Next steps

- Consider how this would work if we were to communicate with a real flip dot board.

### Hardware reference

- Video: [How a Split-Flap Display Works — scottbez1](https://www.youtube.com/watch?v=UAQJJAQSg_g).
- Project: [scottbez1/splitflap](https://github.com/scottbez1/splitflap).
- Integration example: [Chainlink Python demo and software](https://github.com/scottbez1/splitflap/tree/master/software/chainlink).

This reference uses split-flap letter modules, matching our current visual
design. A flip-dot board instead forms letters from a matrix of individual
discs and would need a bitmap font and a different hardware driver.

The splitflap repository includes mechanical designs, electronics, and ESP32
firmware. Its Chainlink driver handles six modules per board; the firmware
supports USB serial control and sensor-based calibration. The Python demo
sends changing words to a connected display. See its
[serial protocol documentation](https://github.com/scottbez1/splitflap#serial-protocol)
before implementing an adapter.

Proposed integration outline (not implemented):

1. Confirm the hardware version, character set, controller, and power needs.
2. Keep noun selection separate from output, with a screen renderer and a
   hardware adapter receiving the same target word.
3. Prototype four physical modules for the changing word, using the reference
   Python demo before connecting our own selection logic.
4. Send target characters and let the controller handle motor movement;
   wait for completion and handle faults or reconnects before the next word.
5. Extend to the full phrase, keeping the prefix and blank spaces fixed.
   Our layout has 18 positions including spaces; alternatively, use static
   matching tiles for the prefix and four motorized modules for the final word.
6. Tune the pauses and transitions to the hardware, then test sustained use.
   Use the mechanisms' natural sound when running the physical display.

## 4Word mode

Press **4**, or run `.venv/bin/python main.py --mode 4Word`.
THIS/THAT keeps alternating. Each update independently selects:

- **30%:** `THIS/THAT MUST BE A CAT` (a three-letter noun).
- **35%:** `THIS/THAT IS NOT A SIGN` (a four-letter noun).
- **35%:** `THIS/THAT IS     A SIGN` (a four-letter noun, with NOT blank).

The 70% ordinary branch retains the 50/50 NOT-versus-blank choice. These are
probabilities, not fixed quotas. The noun changes first; after it settles and
a 1-second pause, THIS/THAT and the middle phrase start flipping together.
The next noun waits until the full phrase settles, plus another second.
When leaving MUST BE A for a four-letter noun, the middle phrase changes first
and settles before the noun flips. This also applies when leaving mode 4, so
MUST BE A never remains visible over a four-letter noun.

Both layouts occupy 18 physical tiles. The three-letter noun aligns to the
right, leaving its preceding tile blank so MUST BE A fits without resizing.
The 331 three-letter nouns use the same noun, consonant, article and approximate
countability rules as the four-letter pool. Each pool shuffles independently
without repeats until exhausted. Source candidates and a filter audit are in
`data/three_letter_noun_candidates.txt` and `data/three_letter_noun_filter_audit.csv`.
To rebuild on macOS, run `python scripts/filter_nouns.py /path/to/wordnet.zip 3`.
Returning to modes 1–3 restores the IS NOT A layout and a four-letter noun;
1Word also restores THIS. No mode change interrupts an active cycle.
