import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from dataclasses import replace
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

import numpy as np
import pygame

from sound import FlipSound
from workshop_audio import Settings, save_preset, synthesize


class SignPresetTests(unittest.TestCase):
    def setUp(self):
        pygame.mixer.init(44100, -16, 2)
        self.tmp = tempfile.TemporaryDirectory()
        self.path = Path(self.tmp.name) / 'my clatter.json'
        self.settings = replace(Settings(), pitch=320, decay=2.5)
        save_preset(self.path, self.settings, 81, 'wipe', .6)

    def tearDown(self):
        pygame.quit()
        self.tmp.cleanup()

    def test_custom_matches_workshop_and_preserves_builtins(self):
        sound = FlipSound(pygame, workshop_preset=self.path, preset_dir=self.tmp.name)
        self.assertEqual(len(sound.banks), 6)
        self.assertIn('6/6  CUSTOM: my clatter', sound.status)
        expected = synthesize(self.settings, 'single', seed=81)
        stereo = pygame.sndarray.array(sound.sounds[0])
        # SDL mono-to-stereo conversion can round by one PCM unit.
        np.testing.assert_allclose(stereo[:, 0], expected, rtol=0, atol=1)
        self.assertAlmostEqual(sound.sounds[0].get_volume(), .6, delta=1/128)
        builtin = FlipSound(pygame, preset_dir=self.tmp.name)
        self.assertEqual(sound.banks[0][0].get_raw(), builtin.banks[0][0].get_raw())
        sound.select(-1)
        self.assertEqual(sound.selected, 4)
        sound.select(1)
        self.assertEqual(sound.selected, 5)
        sound.toggle()
        sound.click()
        self.assertFalse(pygame.mixer.get_busy())

    def test_silent_mode_validates_and_names_custom(self):
        sound = FlipSound(pygame, enabled=False, workshop_preset=self.path, preset_dir=self.tmp.name)
        self.assertIn('CUSTOM: my clatter', sound.status)
        self.assertEqual(sound.banks, [])
        self.path.write_text('[]')
        with self.assertRaises(ValueError):
            FlipSound(pygame, enabled=False, workshop_preset=self.path, preset_dir=self.tmp.name)

    def test_discovers_multiple_presets_without_flag(self):
        save_preset(Path(self.tmp.name) / 'second.json', Settings(), 42, 'single')
        (Path(self.tmp.name) / 'broken.json').write_text('invalid')
        with self.assertWarns(UserWarning):
            sound = FlipSound(pygame, preset_dir=self.tmp.name)
        self.assertEqual(len(sound.banks), 7)
        self.assertEqual(sound.selected, 0)
        for _ in range(5):
            sound.select(1)
        self.assertIn('6/7  CUSTOM: my clatter', sound.status)
        sound.select(1)
        self.assertIn('7/7  CUSTOM: second', sound.status)
        sound.select(1)
        self.assertEqual(sound.selected, 0)

    def test_cli_snapshot_and_bad_path(self):
        root = Path(__file__).resolve().parents[1]
        image = Path(self.tmp.name) / 'sign.png'
        result = subprocess.run([sys.executable, str(root/'main.py'), '--sound-preset', str(self.path), '--snapshot', str(image)], capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertTrue(image.exists())
        result = subprocess.run([sys.executable, str(root/'main.py'), '--sound-preset', str(self.path)+'missing'], capture_output=True, text=True)
        self.assertEqual(result.returncode, 2)
        self.assertIn('Could not load sound preset', result.stderr)
        self.assertNotIn('Traceback', result.stderr)


if __name__ == '__main__':
    unittest.main()
