"""A four-letter departure board. Run with: python3 main.py"""

import argparse
import math
import os
import random
import time

from sound import FlipSound
from word_pool import WordPool


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--snapshot', metavar='PATH', help='save a still and exit')
    parser.add_argument('--sound-preset', metavar='JSON', help='load a sound workshop preset')
    args = parser.parse_args()
    if args.snapshot:
        os.environ['SDL_VIDEODRIVER'] = 'dummy'

    import pygame

    pygame.mixer.pre_init(44100, -16, 2, 512)
    pygame.init()
    try:
        flip_sound = FlipSound(pygame, enabled=not args.snapshot, workshop_preset=args.sound_preset)
    except (OSError, ValueError, TypeError, KeyError) as error:
        pygame.quit()
        parser.error(f'Could not load sound preset: {error}')
    screen = pygame.display.set_mode((1200, 420))
    pygame.display.set_caption('flipChart — THIS IS NOT A SIGN')
    clock = pygame.time.Clock()
    word_pool = WordPool()
    alphabet = 'ABCDEFGHIJKLMNOPQRSTUVWXYZ'
    ink = (226, 221, 201)
    font = pygame.font.SysFont('Helvetica Neue,Helvetica,Arial', 54, bold=True)
    small = pygame.font.SysFont('Helvetica Neue,Helvetica,Arial', 16)
    label = pygame.font.SysFont('Helvetica Neue,Helvetica,Arial', 13)
    tile_w, tile_h = 50, 100
    tile_pitch = tile_w + 10
    face_cache = {}

    def face(letter):
        if letter not in face_cache:
            surface = pygame.Surface((tile_w, tile_h))
            surface.fill((29, 32, 31))
            pygame.draw.rect(surface, (35, 38, 36), (0, 0, tile_w, tile_h // 2))
            glyph = font.render(letter, True, ink)
            surface.blit(glyph, glyph.get_rect(center=(tile_w // 2, tile_h // 2 - 2)))
            face_cache[letter] = surface
        return face_cache[letter]

    class Tile:
        def __init__(self, letter):
            self.letter = letter
            self.steps = []
            self.start = 0
            self.duration = .095

        def turn_to(self, target, now, column):
            distance = (alphabet.index(target) - alphabet.index(self.letter)) % 26
            if distance == 0:
                distance = 26
            self.steps = [alphabet[(alphabet.index(self.letter) + i) % 26]
                          for i in range(1, distance + 1)]
            self.start = now + column * .14 + random.uniform(0, .04)

        def draw(self, x, y, now):
            while self.steps and now >= self.start + self.duration:
                self.letter = self.steps.pop(0)
                self.start += self.duration
                if not paused:
                    flip_sound.click()
            old = face(self.letter)
            pygame.draw.rect(screen, (7, 9, 9), (x - 5, y - 5, tile_w + 10, tile_h + 14), border_radius=7)
            if not self.steps or now < self.start:
                screen.blit(old, (x, y))
            else:
                new = face(self.steps[0])
                half = tile_h // 2
                progress = (now - self.start) / self.duration
                screen.blit(new, (x, y), (0, 0, tile_w, half))
                screen.blit(old, (x, y + half), (0, half, tile_w, half))
                if progress < .5:
                    height = max(1, round(half * math.cos(progress * math.pi)))
                    flap = pygame.transform.smoothscale(old.subsurface((0, 0, tile_w, half)), (tile_w, height))
                    position = (x, y + half - height)
                else:
                    height = max(1, round(-half * math.cos(progress * math.pi)))
                    flap = pygame.transform.smoothscale(new.subsurface((0, half, tile_w, half)), (tile_w, height))
                    position = (x, y + half)
                shade = pygame.Surface(flap.get_size(), pygame.SRCALPHA)
                shade.fill((0, 0, 0, int(85 * math.sin(progress * math.pi))))
                flap.blit(shade, (0, 0))
                screen.blit(flap, position)
            pygame.draw.line(screen, (8, 10, 9), (x, y + tile_h // 2), (x + tile_w, y + tile_h // 2), 3)
            for hinge_x in (x + 3, x + tile_w - 7):
                pygame.draw.rect(screen, (76, 77, 69), (hinge_x, y + tile_h // 2 - 6, 4, 12), border_radius=2)
            pygame.draw.rect(screen, (52, 55, 50), (x, y, tile_w, tile_h), width=1, border_radius=3)

    # All letters share one tile renderer; only the final four get transitions.
    fixed_tiles = []
    cursor_x = 65
    for character in 'THIS IS NOT A ':
        fixed_tiles.append((Tile(character), cursor_x))
        cursor_x += tile_pitch
    moving_x = cursor_x
    tiles = [Tile(c) for c in 'SIGN']
    now = 0.0
    next_change = 2.8
    paused = False
    show_gui = True
    last_time = time.perf_counter()
    running = True

    def advance():
        nonlocal next_change
        if any(tile.steps for tile in tiles):
            return
        target_word = word_pool.next_word()
        for column, (tile, character) in enumerate(zip(tiles, target_word)):
            tile.turn_to(character, now, column)
        next_change = float('inf')

    while running:
        current_time = time.perf_counter()
        delta = min(current_time - last_time, .1)
        last_time = current_time
        if not paused:
            now += delta
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_q):
                    running = False
                elif event.key == pygame.K_g:
                    show_gui = not show_gui
                elif event.key == pygame.K_SPACE:
                    paused = not paused
                    if paused:
                        flip_sound.stop()
                elif event.key == pygame.K_m:
                    flip_sound.toggle()
                elif event.key == pygame.K_UP:
                    flip_sound.select(-1)
                elif event.key == pygame.K_DOWN:
                    flip_sound.select(1)
                elif event.key == pygame.K_RIGHT and not paused:
                    advance()
        if now >= next_change:
            advance()

        screen.fill((17, 23, 23))
        for row in range(420):
            light = int(5 * max(0, 1 - abs(row - 210) / 230))
            pygame.draw.line(screen, (17 + light, 23 + light, 23 + light), (0, row), (1200, row))
        if show_gui:
            screen.blit(label.render('F L I P C H A R T   /   N o .  0 1', True, (143, 150, 140)), (40, 60))
        pygame.draw.rect(screen, (10, 14, 14), (32, 144, 1136, 162), border_radius=18)
        pygame.draw.rect(screen, (57, 62, 56), (32, 134, 1136, 162), border_radius=16)
        pygame.draw.rect(screen, (39, 44, 40), (35, 137, 1130, 156), border_radius=14)
        pygame.draw.rect(screen, (19, 23, 21), (49, 150, 1102, 130), border_radius=8)
        for sx in (43, 1157):
            for sy in (147, 283):
                pygame.draw.circle(screen, (83, 88, 77), (sx, sy), 3)
                pygame.draw.line(screen, (27, 31, 28), (sx - 2, sy), (sx + 2, sy))
        for tile, x in fixed_tiles:
            tile.draw(x, 163, now)
        for column, tile in enumerate(tiles):
            tile.draw(moving_x + column * tile_pitch, 163, now)
        if next_change == float('inf') and not any(tile.steps for tile in tiles):
            next_change = now + 2.8
        if show_gui:
            footer = 'SPACE  pause / resume     RIGHT  next word     UP / DOWN  sound     M  mute     G  GUI     Q / ESC  quit'
            screen.blit(small.render(footer, True, (130, 140, 131)), (40, 340))
            audio_status = label.render(flip_sound.status, True, (130, 140, 131))
            screen.blit(audio_status, (40, 375))
            status = 'PAUSED' if paused else f'{len(word_pool.words):,} NOUNS. RANDOM ORDER.'
            rendered = label.render(status, True, (158, 164, 146))
            screen.blit(rendered, (1160 - rendered.get_width(), 60))
        pygame.display.flip()
        if args.snapshot:
            pygame.image.save(screen, args.snapshot)
            running = False
        clock.tick(60)
    pygame.quit()


if __name__ == '__main__':
    main()
