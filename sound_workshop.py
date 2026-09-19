"""Interactive sound workshop. Run: .venv/bin/python sound_workshop.py"""
import argparse
from dataclasses import replace
from datetime import datetime
from io import BytesIO
from pathlib import Path
import os
import secrets

import numpy as np
import pygame
from scipy.io import wavfile

from workshop_audio import CONTROLS, RATE, Settings, load_preset, save_preset, synthesize

ROOT = Path(__file__).resolve().parent
BG, PANEL, TEXT, MUTED, ACCENT = '#101919', '#1c2929', '#e5e8db', '#9daea7', '#dfb870'


class Workshop:
    def __init__(self, output_dir=None):
        pygame.mixer.pre_init(RATE, -16, 2, 512)
        pygame.init()
        self.screen = pygame.display.set_mode((1080, 830))
        pygame.display.set_caption('Split Flap Sign — Sound Workshop')
        self.font = pygame.font.SysFont('Helvetica Neue,Arial', 20)
        self.small = pygame.font.SysFont('Helvetica Neue,Arial', 15)
        self.large = pygame.font.SysFont('Helvetica Neue,Arial', 32, bold=True)
        self.settings, self.seed, self.mode = Settings(), 42, 'wipe'
        self.reference = (replace(self.settings), self.seed)
        self.side = 'B'
        self.locked, self.loop, self.running = True, False, True
        self.volume = .5
        self.sound = self.channel = None
        self.next_play = None
        self.drag = None
        self.buttons = {}
        self.modal = None
        self.filename = ''
        self.files, self.file_index = [], 0
        self.output_dir = Path(output_dir) if output_dir else ROOT / 'workshop_presets'
        self.message = 'Adjust a slider, then release to hear the change. Start with Play.'
        self.regenerate()

    def active(self):
        return self.reference if self.side == 'A' else (self.settings, self.seed)

    def stop(self):
        if self.channel:
            self.channel.stop()
        self.channel = None
        self.next_play = None

    def regenerate(self):
        self.stop()
        settings, seed = self.active()
        self.pcm = synthesize(settings, self.mode, seed)
        if pygame.mixer.get_init():
            buffer = BytesIO()
            wavfile.write(buffer, RATE, self.pcm)
            buffer.seek(0)
            self.sound = pygame.mixer.Sound(file=buffer)
            self.sound.set_volume(self.volume)
        else:
            self.sound = None
            self.message = 'No audio device. Presets and WAV export are still available.'

    def play(self, fresh=False):
        if fresh and not self.locked and self.side == 'B':
            self.seed = secrets.randbelow(2**32)
            self.regenerate()
        self.stop()
        if self.sound:
            self.channel = self.sound.play()
            self.next_play = pygame.time.get_ticks() + round(len(self.pcm) / RATE * 1000) + 600
        else:
            self.message = 'No audio device available. Export a WAV to listen elsewhere.'

    def audition_change(self):
        if not self.locked and self.side == 'B':
            self.seed = secrets.randbelow(2**32)
        self.regenerate()
        self.play()

    def text(self, text, x, y, font=None, color=TEXT):
        self.screen.blit((font or self.small).render(text, True, color), (x, y))

    def button(self, key, title, x, y, w, active=False):
        rect = pygame.Rect(x, y, w, 36)
        self.buttons[key] = rect
        pygame.draw.rect(self.screen, ACCENT if active else '#30403d', rect, border_radius=6)
        self.text(title, x + 12, y + 9, color=BG if active else TEXT)

    def slider_rect(self, index):
        return pygame.Rect(460, 251 + index * 58, 440, 18)

    def set_slider(self, index, x):
        self.side = 'B'
        name, _, low, high, _, _ = CONTROLS[index]
        rect = self.slider_rect(index)
        value = low + max(0, min(1, (x - rect.x) / rect.w)) * (high - low)
        setattr(self.settings, name, round(value) if name == 'density' else value)

    def action(self, key):
        if key == 'play':
            self.play(fresh=True)
        elif key == 'stop':
            self.loop = False
            self.stop()
        elif key == 'loop':
            self.loop = not self.loop
            if self.loop:
                self.play(fresh=True)
        elif key in ('single', 'wipe'):
            self.mode = key
            self.audition_change()
        elif key == 'lock':
            self.locked = not self.locked
        elif key == 'reroll':
            self.side = 'B'
            self.seed = secrets.randbelow(2**32)
            self.regenerate()
            self.play()
        elif key == 'capture':
            self.reference = (replace(self.settings), self.seed)
            self.message = 'Current B stored as reference A. Edit B, then compare with Tab.'
        elif key == 'compare':
            self.side = 'A' if self.side == 'B' else 'B'
            self.regenerate()
            self.play()
        elif key == 'reset':
            self.settings, self.seed, self.side = Settings(), 42, 'B'
            self.audition_change()
            self.message = 'B reset to the Loose Clatter starting point.'
        elif key == 'save':
            self.loop = False
            self.stop()
            self.filename = 'my-clatter'
            self.modal = 'save'
            pygame.key.start_text_input()
        elif key == 'load':
            self.loop = False
            self.stop()
            self.files = sorted(self.output_dir.glob('*.json'))
            self.file_index = 0
            if self.files:
                self.modal = 'load'
            else:
                self.message = 'No saved presets yet. Use Save preset first.'
        elif key == 'export':
            try:
                self.output_dir.mkdir(parents=True, exist_ok=True)
                stamp = datetime.now().strftime('%Y%m%d-%H%M%S-%f')
                path = self.output_dir / f'clatter-{stamp}.wav'
                # Export matches the listening volume and the selected A/B buffer.
                wavfile.write(path, RATE, np.rint(self.pcm.astype(float) * self.volume).astype(np.int16))
                settings, seed = self.active()
                save_preset(path.with_suffix('.json'), settings, seed, self.mode, self.volume)
                self.message = f'Exported {path.name} + settings to {self.output_dir.name}/'
            except (OSError, ValueError) as error:
                self.message = f'Export failed: {error}'

    def confirm_modal(self):
        try:
            if self.modal == 'save':
                name = self.filename.strip()
                if not name or any(c not in 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789-_' for c in name):
                    raise ValueError('Use letters, numbers, hyphens or underscores for the name.')
                self.output_dir.mkdir(parents=True, exist_ok=True)
                path = self.output_dir / (name + '.json')
                if path.exists():
                    raise ValueError('That preset exists. Choose a new name.')
                settings, seed = self.active()
                save_preset(path, settings, seed, self.mode, self.volume)
                self.message = f'Saved {path.name} in {self.output_dir.name}/'
            else:
                self.settings, self.seed, self.mode, self.volume = load_preset(self.files[self.file_index])
                self.side, self.locked = 'B', True
                self.regenerate()
                self.play()
                self.message = f'Loaded {self.files[self.file_index].name}'
            self.modal = None
            pygame.key.stop_text_input()
        except (OSError, ValueError, TypeError, KeyError) as error:
            self.message = str(error)

    def event(self, event):
        if event.type == pygame.QUIT:
            self.running = False
            return
        if self.modal:
            if event.type == pygame.TEXTINPUT and self.modal == 'save':
                self.filename = (self.filename + event.text)[:45]
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.modal = None
                    pygame.key.stop_text_input()
                elif event.key == pygame.K_RETURN:
                    self.confirm_modal()
                elif self.modal == 'save' and event.key == pygame.K_BACKSPACE:
                    self.filename = self.filename[:-1]
                elif self.modal == 'load' and event.key in (pygame.K_UP, pygame.K_DOWN):
                    self.file_index = (self.file_index + (1 if event.key == pygame.K_DOWN else -1)) % len(self.files)
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_q, pygame.K_ESCAPE):
                self.running = False
            elif event.key == pygame.K_SPACE:
                self.action('stop' if self.channel and self.channel.get_busy() else 'play')
            elif event.key == pygame.K_TAB:
                self.action('compare')
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            for i in range(len(CONTROLS)):
                if self.slider_rect(i).inflate(18, 22).collidepoint(event.pos):
                    self.stop()
                    self.drag = i
                    self.set_slider(i, event.pos[0])
                    return
            if pygame.Rect(782, 181, 200, 26).collidepoint(event.pos):
                self.drag = 'volume'
                self.set_volume(event.pos[0])
                return
            for key, rect in self.buttons.items():
                if rect.collidepoint(event.pos):
                    self.action(key)
                    break
        elif event.type == pygame.MOUSEMOTION and self.drag is not None:
            if self.drag == 'volume':
                self.set_volume(event.pos[0])
            else:
                self.set_slider(self.drag, event.pos[0])
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1 and self.drag is not None:
            regenerate = self.drag != 'volume'
            self.drag = None
            if regenerate:
                self.audition_change()

    def set_volume(self, x):
        self.volume = max(0, min(1, (x - 782) / 200))
        if self.sound:
            self.sound.set_volume(self.volume)

    def draw(self):
        self.screen.fill(BG)
        self.buttons.clear()
        self.text('SOUND WORKSHOP', 40, 28, self.large)
        self.text('Shape the click. Then hear the whole mechanism.', 40, 70, color=MUTED)
        self.button('single', 'Single flip', 40, 112, 120, self.mode == 'single')
        self.button('wipe', 'Full update', 170, 112, 125, self.mode == 'wipe')
        self.button('play', 'Play', 320, 112, 82)
        self.button('stop', 'Stop', 412, 112, 82)
        self.button('loop', 'Loop + gap', 504, 112, 130, self.loop)
        self.button('compare', f'Listening: {self.side}  /  switch', 658, 112, 200, self.side == 'A')
        self.button('capture', 'Store B as A', 868, 112, 170)
        self.button('lock', 'Randomness locked' if self.locked else 'Randomness varies', 40, 174, 205, self.locked)
        self.button('reroll', 'New pattern', 255, 174, 140)
        self.text(f'Seed {self.active()[1]}', 415, 185, color=MUTED)
        self.text(f'Volume {self.volume:.0%}', 660, 185)
        pygame.draw.line(self.screen, '#465750', (782, 194), (982, 194), 5)
        pygame.draw.circle(self.screen, pygame.Color(ACCENT), (round(782 + 200 * self.volume), 194), 8)
        settings = self.active()[0]
        for i, (name, title, low, high, unit, detail) in enumerate(CONTROLS):
            rect = self.slider_rect(i)
            self.text(title, 40, rect.y - 6, self.font)
            self.text(detail, 40, rect.y + 19, color=MUTED)
            value = getattr(settings, name)
            fraction = (value - low) / (high - low)
            pygame.draw.line(self.screen, '#465750', (rect.left, rect.centery), (rect.right, rect.centery), 5)
            x = round(rect.left + fraction * rect.w)
            pygame.draw.line(self.screen, pygame.Color(ACCENT), (rect.left, rect.centery), (x, rect.centery), 5)
            pygame.draw.circle(self.screen, pygame.Color(ACCENT), (x, rect.centery), 8)
            display = f'{value:.0%}' if unit == '%' else f'{value:.1f} {unit}'
            self.text(display, 925, rect.y - 1)
        pygame.draw.rect(self.screen, PANEL, (40, 612, 998, 75), border_radius=6)
        # Peak-preserving waveform envelope: narrow clicks remain visible.
        bins = np.array_split(self.pcm.astype(float) / 32767 * self.volume, 950)
        for i, section in enumerate(bins):
            if len(section):
                height = max(1, round(np.max(np.abs(section)) * 28))
                pygame.draw.line(self.screen, pygame.Color(ACCENT), (64+i, 649-height), (64+i, 649+height))
        peak = max(float(np.max(np.abs(self.pcm.astype(float)))) / 32767 * self.volume, 1e-12)
        self.text(f'{len(self.pcm)/RATE:.3f}s  |  Peak {20*np.log10(peak):.1f} dBFS  |  Level matched with peak headroom', 40, 694, color=MUTED)
        self.button('reset', 'Reset Loose Clatter', 40, 726, 195)
        self.button('save', 'Save preset', 247, 726, 140)
        self.button('load', 'Load preset', 399, 726, 140)
        self.button('export', 'Export WAV', 551, 726, 140)
        self.text('SPACE play/stop   TAB A/B   Q quit', 720, 737, color=MUTED)
        self.text(self.message[:135], 40, 786)
        if self.modal:
            pygame.draw.rect(self.screen, '#30403d', (220, 275, 640, 285), border_radius=12)
            if self.modal == 'save':
                self.text('Save selected sound', 250, 300, self.large)
                self.text('Name: ' + self.filename + '_', 250, 360, self.font)
                self.text('Type a name. Backspace to edit.', 250, 403)
            else:
                self.text('Load preset', 250, 300, self.large)
                start = max(0, self.file_index - 2)
                for row, path in enumerate(self.files[start:start+5]):
                    self.text(('> ' if start+row == self.file_index else '  ') + path.name[:58], 250, 350+row*28,
                              color=ACCENT if start+row == self.file_index else TEXT)
            self.text('ENTER confirm   ESC cancel   UP / DOWN select', 250, 519)
        pygame.display.flip()

    def run(self, snapshot=None):
        clock = pygame.time.Clock()
        while self.running:
            for event in pygame.event.get():
                self.event(event)
            if self.loop and self.drag is None and not self.modal and self.next_play is not None and pygame.time.get_ticks() >= self.next_play:
                self.play(fresh=True)
            self.draw()
            if snapshot:
                pygame.image.save(self.screen, snapshot)
                break
            clock.tick(30)
        self.stop()
        pygame.quit()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', help='render the workshop without opening a window')
    args = parser.parse_args()
    if args.snapshot:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'
        os.environ['SDL_AUDIODRIVER'] = 'dummy'
    Workshop().run(args.snapshot)


if __name__ == '__main__':
    main()
