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
    parser.add_argument('--mode', choices=('1Word', '2Word', '3Word', '4Word'), default='1Word', help='select phrase animation mode (1Word through 4Word)')
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
    short_word_pool = WordPool(word_length=3, initial=None)
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

        def turn_to(self, target, now, column, cycle_unchanged=True):
            wheel = alphabet + ' ' if ' ' in (target, self.letter) else alphabet
            distance = (wheel.index(target) - wheel.index(self.letter)) % len(wheel)
            if distance == 0:
                if not cycle_unchanged:
                    return
                distance = len(wheel)
            self.steps = [wheel[(wheel.index(self.letter) + i) % len(wheel)]
                          for i in range(1, distance + 1)]
            self.start = now + column * .14 + (random.uniform(0, .04) if column else 0)

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

    # THIS/THAT moves in 2Word and 3Word; NOT/blanks also moves in 3Word.
    fixed_tiles = []
    cursor_x = 65
    for character in 'THIS IS NOT A ':
        fixed_tiles.append((Tile(character), cursor_x))
        cursor_x += tile_pitch
    moving_x = cursor_x
    prefix_tiles = [tile for tile, _ in fixed_tiles[:4]]
    not_tiles = [tile for tile, _ in fixed_tiles[8:11]]
    middle_tiles = [tile for tile, _ in fixed_tiles[4:]]
    tiles = [Tile(c) for c in 'SIGN']
    mode = requested_mode = args.mode
    prefix_word = 'THIS'
    pending_prefix = None
    pending_middle = None
    pending_noun = None
    pending_prefix_at = None
    now = 0.0
    next_change = 1.0 if mode != '1Word' else 2.8
    paused = False
    show_gui = True
    last_time = time.perf_counter()
    running = True

    def moving():
        return pending_prefix is not None or pending_noun is not None or any(tile.steps for tile in prefix_tiles + middle_tiles + tiles)

    def change_prefix(target):
        nonlocal prefix_word
        prefix_word = target
        changed = [(tile, character) for tile, character in zip(prefix_tiles, target)
                   if tile.letter != character]
        for column, (tile, character) in enumerate(changed):
            tile.turn_to(character, now, column, cycle_unchanged=False)

    def change_not(target):
        changed = [(tile, character) for tile, character in zip(not_tiles, target)
                   if tile.letter != character]
        for column, (tile, character) in enumerate(changed):
            tile.turn_to(character, now, column, cycle_unchanged=False)

    def change_middle(target):
        changed = [(tile, character) for tile, character in zip(middle_tiles, target)
                   if tile.letter != character]
        for column, (tile, character) in enumerate(changed):
            tile.turn_to(character, now, column, cycle_unchanged=False)

    def start_noun(target):
        for column, (tile, character) in enumerate(zip(tiles, target)):
            tile.turn_to(character, now, column, cycle_unchanged=character != ' ')

    def advance():
        nonlocal next_change, pending_prefix, pending_prefix_at, pending_middle, pending_noun
        if moving():
            return
        if mode != '1Word':
            pending_prefix = 'THAT' if prefix_word == 'THIS' else 'THIS'
            pending_prefix_at = None
        if mode == '4Word':
            if random.random() < .30:
                target_word = ' ' + short_word_pool.next_word()
                pending_middle = ' MUST BE A'
            else:
                target_word = word_pool.next_word()
                pending_middle = ' IS ' + random.choice(('NOT', '   ')) + ' A '
        else:
            target_word = word_pool.next_word()
            pending_middle = None
        if ''.join(tile.letter for tile in middle_tiles) == ' MUST BE A' and target_word[0] != ' ':
            # Remove MUST before exposing a fourth noun letter, including while flipping.
            change_middle(pending_middle)
            pending_noun = target_word
        else:
            start_noun(target_word)
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
                elif event.key in (pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4):
                    requested_mode = {pygame.K_1: '1Word', pygame.K_2: '2Word', pygame.K_3: '3Word', pygame.K_4: '4Word'}[event.key]
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
        # Apply mode switches between transitions, and defer them while paused.
        if not paused and not moving() and requested_mode != mode:
            previous_mode = mode
            mode = requested_mode
            next_change = now + (1.0 if mode != '1Word' else 2.8)
            if previous_mode == '4Word' and mode != '4Word':
                change_middle(' IS NOT A ')
                if tiles[0].letter == ' ':
                    pending_noun = word_pool.next_word()
                if moving():
                    next_change = float('inf')
            elif mode not in ('3Word', '4Word'):
                change_not('NOT')
                if moving():
                    next_change = float('inf')
            if mode == '1Word' and prefix_word != 'THIS':
                change_prefix('THIS')
                next_change = float('inf')
        if not paused and now >= next_change:
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
        if not paused and pending_noun is not None and not any(tile.steps for tile in prefix_tiles + middle_tiles):
            start_noun(pending_noun)
            pending_noun = None
        if not paused and pending_noun is None and pending_prefix is not None and not any(tile.steps for tile in tiles):
            if pending_prefix_at is None:
                pending_prefix_at = now + 1.0
            elif now >= pending_prefix_at:
                change_prefix(pending_prefix)
                if mode == '3Word':
                    change_not(random.choice(('NOT', '   ')))
                elif mode == '4Word':
                    change_middle(pending_middle)
                    pending_middle = None
                pending_prefix = None
                pending_prefix_at = None
        if next_change == float('inf') and not moving():
            next_change = now + (1.0 if mode != '1Word' else 2.8)
        if show_gui:
            footer = 'SPACE  pause     RIGHT  next     1 / 2 / 3 / 4  mode     UP / DOWN  sound     M  mute     G  GUI     Q / ESC  quit'
            screen.blit(small.render(footer, True, (130, 140, 131)), (40, 340))
            audio_status = label.render(flip_sound.status, True, (130, 140, 131))
            screen.blit(audio_status, (40, 375))
            status = 'PAUSED' if paused else f'{len(word_pool.words):,} NOUNS. RANDOM ORDER.'
            if mode == '4Word' and not paused:
                status = f'{len(word_pool.words):,} FOUR-LETTER / {len(short_word_pool.words):,} THREE-LETTER NOUNS'
            status = f'{mode}  |  {status}'
            if requested_mode != mode:
                status += f'  |  next: {requested_mode}'
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
