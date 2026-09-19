import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

from dataclasses import replace
from pathlib import Path
import tempfile
import unittest

import numpy as np
import pygame
from scipy.io import wavfile

from workshop_audio import CONTROLS, Settings, load_preset, save_preset, synthesize
from sound_workshop import Workshop


class AudioTests(unittest.TestCase):
    def test_deterministic_and_new_patterns(self):
        a = synthesize(Settings(), seed=42)
        np.testing.assert_array_equal(a, synthesize(Settings(), seed=42))
        self.assertFalse(np.array_equal(a, synthesize(Settings(), seed=43)))

    def test_controls_change_audio_with_headroom(self):
        baseline = synthesize(Settings())
        for field, _, low, high, _, _ in CONTROLS:
            for value in (low, high):
                with self.subTest(field=field, value=value):
                    result = synthesize(replace(Settings(), **{field: value}))
                    self.assertFalse(np.array_equal(baseline, result))
                    self.assertEqual(result.dtype, np.int16)
                    self.assertEqual(len(result), 88200)
                    self.assertLessEqual(np.max(np.abs(result.astype(float))), 29491)
                    self.assertEqual(result[0], 0)
                    self.assertEqual(result[-1], 0)

    def test_single_ignores_schedule_controls(self):
        a = synthesize(Settings(), 'single')
        b = synthesize(replace(Settings(), density=100, jitter=0), 'single')
        np.testing.assert_array_equal(a, b)
        self.assertTrue(.005 <= len(a)/44100 <= .015)

    def test_preset_roundtrip_and_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / 'test.json'
            settings = replace(Settings(), pitch=310, decay=2.2)
            save_preset(path, settings, 20, 'single', .7)
            self.assertEqual(load_preset(path), (settings, 20, 'single', .7))
            path.write_text('{"version": 100}')
            with self.assertRaises(ValueError):
                load_preset(path)
        with self.assertRaises(ValueError):
            synthesize(replace(Settings(), pitch=float('nan')))


class WorkshopTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.app = Workshop(self.tmp.name)
        self.app.draw()

    def tearDown(self):
        self.app.stop()
        pygame.quit()
        self.tmp.cleanup()

    def test_slider_ab_save_load_export(self):
        app = self.app
        original = app.pcm.copy()
        app.action('capture')
        rect = app.slider_rect(2)
        app.event(pygame.event.Event(pygame.MOUSEBUTTONDOWN, button=1, pos=(rect.right, rect.centery)))
        app.event(pygame.event.Event(pygame.MOUSEBUTTONUP, button=1, pos=(rect.right, rect.centery)))
        edited = app.pcm.copy()
        self.assertFalse(np.array_equal(original, edited))
        app.action('compare')
        np.testing.assert_array_equal(original, app.pcm)
        app.action('compare')
        np.testing.assert_array_equal(edited, app.pcm)
        app.action('save')
        app.filename = 'test-preset'
        app.confirm_modal()
        self.assertIsNone(app.modal)
        app.action('reset')
        app.action('load')
        app.confirm_modal()
        np.testing.assert_array_equal(edited, app.pcm)
        app.action('export')
        path = next(Path(self.tmp.name).glob('*.wav'))
        rate, audio = wavfile.read(path)
        self.assertEqual(rate, 44100)
        np.testing.assert_array_equal(audio, np.rint(app.pcm.astype(float)*app.volume).astype(np.int16))
        app.action('loop')
        self.assertTrue(app.loop)
        self.assertIsNotNone(app.next_play)
        app.action('stop')
        self.assertFalse(app.loop)
        self.assertIsNone(app.next_play)

    def test_missing_audio_and_modal_errors(self):
        pygame.mixer.quit()
        app = Workshop(self.tmp.name)
        # Explicitly disable the mixer after initialization to test fallback.
        pygame.mixer.quit()
        app.regenerate()
        self.assertIsNone(app.sound)
        app.play()
        app.action('save')
        app.filename = '../invalid'
        app.confirm_modal()
        self.assertEqual(app.modal, 'save')
        self.assertFalse(list(Path(self.tmp.name).glob('*.json')))
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_ESCAPE))
        self.assertIsNone(app.modal)
        app.event(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
        self.assertFalse(app.running)


if __name__ == '__main__':
    unittest.main()
