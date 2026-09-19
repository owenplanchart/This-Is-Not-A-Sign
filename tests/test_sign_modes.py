import os
os.environ['SDL_VIDEODRIVER'] = 'dummy'
os.environ['SDL_AUDIODRIVER'] = 'dummy'

import inspect
from itertools import count
import unittest
from unittest.mock import patch

import pygame
import main


class SignModeTests(unittest.TestCase):
    def test_four_word_branches_layout_and_return(self):
        ticks = count()
        state = {'frames': 0, 'seen': [], 'last_prefix': 'THIS', 'restoring': False}

        def frame():
            local = inspect.currentframe().f_back.f_locals
            state['frames'] += 1
            if state['frames'] > 900:
                self.fail(f'4Word sequence stalled: {state}')
            noun_moving = any(t.steps for t in local['tiles'])
            middle_moving = any(t.steps for t in local['middle_tiles'])
            prefix_moving = any(t.steps for t in local['prefix_tiles'])
            if local['mode'] == '4Word':
                self.assertFalse(noun_moving and (middle_moving or prefix_moving))
            if ''.join(t.letter for t in local['middle_tiles']) == ' MUST BE A':
                self.assertEqual(local['tiles'][0].letter, ' ')
                self.assertFalse(local['tiles'][0].steps, 'Fourth noun tile must stay blank under MUST')
            if local['moving']():
                return
            phrase = ''.join(t.letter for t, _ in local['fixed_tiles']) + ''.join(t.letter for t in local['tiles'])
            self.assertEqual(len(phrase), 18)
            if state['restoring']:
                if local['mode'] == '1Word':
                    self.assertEqual(phrase[:14], 'THIS IS NOT A ')
                    self.assertIn(phrase[14:], local['word_pool'].words)
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
                return
            if phrase[:4] != state['last_prefix']:
                state['last_prefix'] = phrase[:4]
                index = len(state['seen'])
                if index in (0, 3):
                    self.assertEqual(phrase[4:15], ' MUST BE A ')
                    self.assertIn(phrase[15:], local['short_word_pool'].words)
                    pygame.image.save(local['screen'], '/tmp/sign-4word-must.png')
                else:
                    self.assertEqual(phrase[4:14], ' IS NOT A ' if index == 1 else ' IS     A ')
                    self.assertIn(phrase[14:], local['word_pool'].words)
                state['seen'].append(phrase)
                if index == 3:
                    state['restoring'] = True
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_1))

        try:
            with patch('sys.argv', ['main.py', '--mode', '4Word']), \
                 patch.object(main.time, 'perf_counter', side_effect=lambda: next(ticks) * .1), \
                 patch.object(main.random, 'random', side_effect=[.299999, .30, .99, .0]), \
                 patch.object(main.random, 'choice', side_effect=['NOT', '   ']), \
                 patch.object(pygame.time, 'Clock') as clock, \
                 patch.object(pygame.display, 'flip', new=frame):
                clock.return_value.tick.return_value = 0
                main.main()
            self.assertEqual(len(state['seen']), 4)
        finally:
            pygame.quit()

    def test_three_word_blank_return_and_restore(self):
        ticks = count()
        state = {'frames': 0, 'phase': 'blank', 'starts': 0}

        def frame():
            local = inspect.currentframe().f_back.f_locals
            state['frames'] += 1
            if state['frames'] > 700:
                self.fail(f'3Word sequence stalled: {state}')
            noun_moving = any(t.steps for t in local['tiles'])
            not_moving = any(t.steps for t in local['not_tiles'])
            prefix_moving = any(t.steps for t in local['prefix_tiles'])
            self.assertFalse(noun_moving and (not_moving or prefix_moving))
            for i in (4, 5, 6, 7, 11, 12, 13):
                self.assertFalse(local['fixed_tiles'][i][0].steps)
            if local['mode'] == '3Word' and not_moving and not state.get('was_not_moving', False):
                self.assertTrue(prefix_moving)
                prefix_start = min(t.start for t in local['prefix_tiles'] if t.steps)
                not_start = min(t.start for t in local['not_tiles'] if t.steps)
                self.assertAlmostEqual(prefix_start, not_start)
                state['starts'] += 1
            state['was_not_moving'] = not_moving
            text = ''.join(t.letter for t in local['not_tiles'])
            settled = not local['moving']()
            if settled:
                if state['phase'] == 'blank' and text == '   ':
                    state['phase'] = 'return'
                elif state['phase'] == 'return' and text == 'NOT':
                    state['phase'] = 'blank-again'
                elif state['phase'] == 'blank-again' and text == '   ':
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_2))
                    state['phase'] = 'restore'
                elif state['phase'] == 'restore' and local['mode'] == '2Word':
                    self.assertEqual(text, 'NOT')
                    state['phase'] = 'done'
                    pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q))
                    pygame.image.save(local['screen'], '/tmp/sign-3word-restored.png')
            if state['phase'] == 'return' and text == '   ' and settled:
                pygame.image.save(local['screen'], '/tmp/sign-3word-blank.png')

        try:
            with patch('sys.argv', ['main.py', '--mode', '3Word']), \
                 patch.object(main.time, 'perf_counter', side_effect=lambda: next(ticks) * .1), \
                 patch.object(main.random, 'choice', side_effect=['   ', 'NOT', '   ']), \
                 patch.object(pygame.time, 'Clock') as clock, \
                 patch.object(pygame.display, 'flip', new=frame):
                clock.return_value.tick.return_value = 0
                main.main()
            self.assertEqual(state['phase'], 'done')
            self.assertEqual(state['starts'], 3)
        finally:
            pygame.quit()

    def test_two_word_alternates_then_switches_back_while_paused(self):
        ticks = count()
        state = {'frames': 0, 'phase': 'that', 'seen': [], 'paused_frames': 0, 'noun_first': False, 'prefix_after': False}

        def key(value):
            pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=value))

        def frame():
            local = inspect.currentframe().f_back.f_locals
            state['frames'] += 1
            if state['frames'] > 500:
                self.fail(f'Mode sequence stalled: {state}')
            self.assertTrue(all(not tile.steps for tile, _ in local['fixed_tiles'][4:]))
            noun_moving = any(tile.steps for tile in local['tiles'])
            prefix_moving = any(tile.steps for tile in local['prefix_tiles'])
            self.assertFalse(noun_moving and prefix_moving, 'Words must flip sequentially')
            if local['pending_prefix'] is not None and noun_moving:
                state['noun_first'] = True
                self.assertFalse(prefix_moving)
            if prefix_moving and local['mode'] == '2Word':
                self.assertTrue(state['noun_first'])
                state['prefix_after'] = True
            if local['pending_prefix_at'] is not None:
                self.assertFalse(noun_moving or prefix_moving)
                if 'prefix_due' not in state:
                    self.assertAlmostEqual(local['pending_prefix_at'] - local['now'], 1.0)
                    state['prefix_due'] = local['pending_prefix_at']
            elif prefix_moving and 'prefix_due' in state:
                self.assertGreaterEqual(local['now'], state.pop('prefix_due'))
            if local['mode'] == '2Word' and not local['moving']():
                if state.get('was_moving', False):
                    self.assertAlmostEqual(local['next_change'] - local['now'], 1.0)
            state['was_moving'] = local['moving']()
            prefix = ''.join(tile.letter for tile in local['prefix_tiles'])
            settled = not local['moving']()
            phase = state['phase']
            if phase == 'that' and settled and prefix == 'THAT':
                state['seen'].append(prefix)
                state['phase'] = 'this'
            elif phase == 'this' and settled and prefix == 'THIS':
                state['seen'].append(prefix)
                state['phase'] = 'switch'
            elif phase == 'switch' and local['moving']() and local['prefix_word'] == 'THAT':
                key(pygame.K_SPACE)
                key(pygame.K_1)
                state['phase'] = 'paused'
            elif phase == 'paused':
                self.assertTrue(local['paused'])
                self.assertEqual(local['mode'], '2Word')
                self.assertEqual(local['requested_mode'], '1Word')
                state['paused_frames'] += 1
                if state['paused_frames'] == 3:
                    key(pygame.K_SPACE)
                    state['phase'] = 'restore'
            elif phase == 'restore' and local['mode'] == '1Word' and settled:
                self.assertEqual(prefix, 'THIS')
                state['phase'] = 'oneword'
                key(pygame.K_RIGHT)
            elif phase == 'oneword' and local['moving']():
                self.assertEqual(prefix, 'THIS')
                self.assertTrue(all(not tile.steps for tile in local['prefix_tiles']))
                state['phase'] = 'done'
                key(pygame.K_q)

        try:
            with patch('sys.argv', ['main.py', '--mode', '2Word']), \
                 patch.object(main.time, 'perf_counter', side_effect=lambda: next(ticks) * .1), \
                 patch.object(pygame.time, 'Clock') as clock, \
                 patch.object(pygame.display, 'flip', new=frame):
                clock.return_value.tick.return_value = 0
                main.main()
            self.assertEqual(state['phase'], 'done')
            self.assertEqual(state['seen'], ['THAT', 'THIS'])
            self.assertTrue(state['noun_first'] and state['prefix_after'])
        finally:
            pygame.quit()


if __name__ == '__main__':
    unittest.main()
