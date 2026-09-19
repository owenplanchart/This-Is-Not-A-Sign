# Project handoff: This Is Not A Sign

Read this first in a new chat, then inspect only files relevant to the next request.
This is a working project, not a request to rebuild it. README.md has fuller usage.

## Location and environment

- Project: `/Users/owenplanchart/Developer/Python/split flap sign`
- Previously named `flipChart`; the folder was renamed. Some UI labels still say flipChart.
- Python 3.9 virtual environment: `.venv`. Dependencies: Pygame, NumPy, SciPy.
- Use `.venv/bin/python` explicitly. The macOS system Python lacks SciPy.
- The rename required fixing activation paths and pip launchers. Old terminal/editor sessions may still refer to the previous path; reactivate or reselect the interpreter.
- In the prior chat, sandbox write access still pointed at the OLD folder after renaming. Writes in the new folder required tool escalation. Respect the new chat's actual permissions.

```sh
cd "/Users/owenplanchart/Developer/Python/split flap sign"
.venv/bin/python main.py
.venv/bin/python main.py --mode 4Word
.venv/bin/python sound_workshop.py
.venv/bin/python main.py --sound-preset workshop_presets/my-clatter1.json
.venv/bin/python -m unittest discover -s tests -v
```

## User preferences and Git state

- User likes incremental implementation and visual/audio iteration. Explain changes briefly.
- Do not push without a new request: user explicitly asked to commit locally and not push.
- Never add WAVs or `.venv` to Git. `.gitignore` excludes WAVs case-insensitively, the venv, Python caches, and `.DS_Store`.
- Remote: `https://github.com/owenplanchart/This-Is-Not-A-Sign.git`, branch `main`.
- Initial commit `3c0f403` was pushed. Subsequent commits remain local:
  - `79a3821` Document hardware references and integration next steps
  - `7369abb` Add interactive sound workshop and automatic sign preset loading
  - `868e44a` Add phrase animation modes and filtered three-letter nouns (current HEAD)
- Working tree was clean before creating this handoff. This file is newly created, not committed.
- Local Git author: `owenplanchart <owenplanchart@users.noreply.github.com>`.

## The sign

Python/Pygame artwork, 1200 x 420 window, 18 equal split-flap tiles in a single row.
Dark housing, cream letters, centre seams and hinges. Spaces are matching blank tiles.
Although the initial request used “flip discs,” the on-screen mechanism is split-flap letters.
Initial phrase: `THIS IS NOT A SIGN`. Physical position count must remain 18.

Controls:
- 1 / 2 / 3 / 4: choose mode; active mode is shown in the upper label.
- Right: advance once the current sequence is complete and not paused.
- Space: pause/resume; stops active clicks.
- Up / Down: cycle sound options, preview selected sound.
- M: mute/unmute.
- G: hide/show ALL labels, controls, and status text; sign remains visible.
- Q or Escape: quit.
- CLI: `--mode 1Word|2Word|3Word|4Word`, `--sound-preset JSON`, `--snapshot PATH`.

### Mode rules

1. **1Word:** only the final four-letter noun changes. THIS IS NOT A remains fixed. Hold 2.8 seconds after settlement.
2. **2Word:** final noun flips, settles, waits 1 second; THIS/THAT alternates, settles, waits 1 second; repeat. Initial extra letter delay was removed; the first changing letter starts immediately when scheduled. Unchanged T/H remain still.
3. **3Word:** same sequential timing as 2Word. At the THIS/THAT stage, independently choose NOT or three blanks with 50/50 probability. NOT starts flipping alongside THIS/THAT when its state changes. Repeated choices may leave NOT unchanged. Wait for both groups to finish before the next 1-second pause.
4. **4Word:** THIS/THAT still alternates. Each cycle chooses:
   - 30%: `THIS/THAT MUST BE A CAT` — three-letter noun.
   - 35%: `THIS/THAT IS NOT A SIGN` — four-letter noun.
   - 35%: `THIS/THAT IS     A SIGN` — four-letter noun with NOT blank.
   The 70% ordinary branch retains the 50/50 NOT/blank choice. These are independent probabilities, not quotas.
   Three-letter nouns occupy the rightmost three tiles; the preceding noun tile is blank so MUST BE A fits the same 18-tile board.
   Normally noun first, then 1-second pause, then first/middle phrase together, then settle and 1 second.
   **Critical invariant:** MUST BE A must NEVER remain visible with a fourth noun letter, even during animation. When leaving MUST BE A, change/settle the middle phrase BEFORE starting a four-letter noun. Mode exit uses the same protection.

Mode switches wait for active sequences and pause to finish. Returning to modes 1–3 restores the ordinary middle layout and a four-letter noun if needed. Returning to 1Word also restores THIS; leaving 3Word for 1Word/2Word restores NOT.

## Word rules and datasets

- Four-letter pool: **1,163** entries. Three-letter pool: **331** entries.
- Random shuffle bags; every entry is used before a fresh cycle, with no immediate repeat across the boundary. Pools shuffle independently. SIGN is treated as already used at startup.
- Must have a noun sense; may ALSO be a verb/adjective (PLAY, COLD, HOLD can qualify).
- Exclude initial A/E/I/O/U; retain Y.
- Apply conservative heuristics for singular countable nouns compatible with “a ___”: suspected plurals, substance-only senses, proper-name senses, and silent-H exceptions excluded. HERB excluded because article varies by dialect.
- Source: lowercase macOS `/usr/share/dict/web2` entries intersected with WordNet 3.0 nouns.
- WordNet does NOT provide a direct countability tag. Rules infer from glosses, noun categories/ancestors, and plural exceptions. False positives/negatives remain; manual curation is a future step explicitly agreed with user.
- Original four-letter consonant-initial noun candidates: 1,754. Three-letter candidates: 474.
- `data/four_letter_words.txt`, `data/three_letter_words.txt`: active offline pools.
- Candidate files and CSV decision audits retained in `data/` for reversible curation.
- `data/SOURCE.txt`, `data/WORDNET_LICENSE.txt`: provenance and attribution.
- `scripts/filter_nouns.py /path/to/wordnet.zip [3|4]`: rebuild; defaults to 4. Three-letter regeneration currently also reads macOS web2.
- WordNet archive was downloaded to `/tmp/flipchart-wordnet.zip`; temporary file, may disappear. URL recorded in SOURCE.txt.

## Audio history and current system

Several early mathematical metallic presets sounded too high-pitched, tonal, or droney to the user. They were replaced, not retained as selectable presets.
The better approach uses ultra-short 5–15 ms white-noise/plastic impacts mixed with low-frequency housing sine, aggressive exponential decay, and jittered clustered onsets for a full wipe.
User preferred “Loose Clatter” (previously fifth). It is now first/default, with four plastic variations:
1. Loose Clatter (original)
2. Plastic Snap
3. Plastic Clack
4. Hollow Plastic
5. Hard Plastic
New plastic variants play about 2.4 dB louder than the original in the sign.

`generate_flip_dot.py`: standalone NumPy/SciPy math-to-array generator; no playback library in generation. Produces normalized 44.1 kHz mono 16-bit WAV.
- `--preset`, `--seed`, `--duration` (1.5–2.5), `--flips` (100–300), `--output`.
- `--audition`: separate WAVs and a 14-second five-preset comparison with 1-second gaps.
- Listen on macOS: `afplay flip_dot_audition.wav`.
- Replaying a WAV always repeats that recording; regenerating varies pattern; presets change sound character.

### Interactive workshop

`sound_workshop.py` provides a separate 1080 x 830 Pygame window.
`workshop_audio.py` handles pure synthesis, settings, JSON validation/persistence.
Six sliders: brightness, noise/body balance, body pitch (100–500 Hz), decay (.3–4 ms), density (100–300), timing irregularity (0–35 ms). Separate volume slider.
- Single flip / Full update listening modes; Play/Stop; looping with 600 ms gap.
- Slider release regenerates and auditions. Volume is independent of synthesis.
- Locked randomness makes comparisons reproducible; New pattern changes seed. Unlocked playback/edits generate fresh seeds.
- Store B as A; Tab or A/B button compares reference to edits. Editing returns to B.
- Reset Loose Clatter, save/load named JSON presets, export WAV + JSON.
- Save dialog: type name, Backspace edits, Enter confirms, Escape cancels. No overwrite.
- Load dialog: Up/Down and Enter.
- Waveform and peak indicator. Approximate RMS matching capped at .9 peak; NOT a perceptual loudness guarantee.
- JSON saves settings, seed, mode, volume, format version 1.
- Export reproduces the selected buffer at current listening volume.
- Output folder: `workshop_presets/`. Q/Escape quit, Space playback, Tab A/B.

### Workshop → sign integration

The sign discovers valid `workshop_presets/*.json` at startup, sorted by filename, and appends them after the five built-ins. Invalid discovered presets warn and skip; invalid explicitly requested presets fail with a readable CLI error.
Currently committed presets:
- 6/7 CUSTOM: my-clatter1
- 7/7 CUSTOM: my-clatter2

`--sound-preset PATH` selects that preset immediately, including files outside the folder. No flag is necessary for discovery. Restart after saving/editing presets.
Custom sounds use brightness/noise/pitch/decay/volume/seed to precompute 12 click variations. First variation matches workshop Single flip synthesis; others derive from successive seeds.
Workshop density, jitter and full-wipe mode do not drive the sign: click timing follows visible tile landings. Mute and Up/Down continue to work. No WAV required.
Audio comparisons were NUMERICAL, not subjective listening: compare PCM arrays; allow one-unit 16-bit rounding during SDL mono-to-stereo conversion. Do not claim sounds were listened to or acoustically validated.

## Files and verification

- `main.py`: Pygame tiles, UI, mode/timing state, noun selection, sound hooks. Tile animation state currently lives inside main().
- `sound.py`: built-in/custom sound banks, discovery, playback and mute.
- `word_pool.py`: filtered pool loading for lengths 3/4, shuffle/no-repeat behavior.
- `generate_flip_dot.py`, `workshop_audio.py`, `sound_workshop.py`: described above.
- `tests/test_workshop.py`: synthesis, presets, A/B/UI/export/fallback checks.
- `tests/test_sign_preset.py`: discovery, custom PCM match, CLI failures, selection.
- `tests/test_sign_modes.py`: real app loop with accelerated clock/dummy SDL; sequential timing, pause/mode changes, synchronized NOT, probability branch boundary, MUST/three-letter invariant.
- Latest full run: **13 tests passed**, `git diff --check` clean before last commit.
- Tests use dummy audio/video; no claim of audible QA.
- Screenshots: `main.py --snapshot /tmp/sign.png`; `sound_workshop.py --snapshot /tmp/workshop.png`.
- Some tools could not read host PNG paths despite files existing. Fallback used shell base64 output forwarded as an image for visual inspection.

## Future hardware reference (outline only)

README Next steps: consider controlling a real board. No hardware adapter implemented.
- Video: https://www.youtube.com/watch?v=UAQJJAQSg_g — How a Split-Flap Display Works.
- Repo: https://github.com/scottbez1/splitflap
- Python demo: https://github.com/scottbez1/splitflap/tree/master/software/chainlink
- ESP32/USB serial split-flap modules closely match this visual design. Chainlink supports six modules per driver board. Inspect current protocol/docs before implementation.
- First milestone: four physical letters driven by Python; keep word selection independent of renderer/hardware output. Later extend to 18 positions, or static matching prefix tiles plus moving word modules.
- True flip-dot hardware is different: letters are bitmap disc grids and need another renderer/driver. Natural mechanism sound would replace synthesized audio on physical hardware.

## Current handoff

The user asked for this compaction file to start a fresh chat with less context.
All feature work through the MUST/three-letter transition fix is committed locally
at 868e44a. No unfinished feature is currently requested. Do not push or start new
work merely from this handoff; await the user's next instruction.
