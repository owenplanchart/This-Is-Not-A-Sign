"""Random dictionary words, with no repeats within a shuffled cycle."""

from pathlib import Path
import random


class WordPool:
    def __init__(self, path=None, rng=None, initial='SIGN', word_length=4):
        if word_length not in (3, 4):
            raise ValueError('Word length must be 3 or 4')
        filename = 'three_letter_words.txt' if word_length == 3 else 'four_letter_words.txt'
        path = Path(path) if path else Path(__file__).parent / 'data' / filename
        self.words = sorted({line.strip().upper() for line in path.read_text().splitlines()
                             if len(line.strip()) == word_length and line.strip().isascii()
                             and line.strip().isalpha()})
        if len(self.words) < 2:
            raise ValueError(f'The dictionary needs at least two {word_length}-letter A–Z words.')
        self.rng = rng if rng is not None else random.Random()
        self.last = initial
        self.remaining = [word for word in self.words if word != initial]
        self.rng.shuffle(self.remaining)

    def next_word(self):
        if not self.remaining:
            self.remaining = self.words.copy()
            self.rng.shuffle(self.remaining)
            # Avoid the same word on either side of a cycle boundary.
            if self.remaining[-1] == self.last:
                self.remaining[0], self.remaining[-1] = self.remaining[-1], self.remaining[0]
        self.last = self.remaining.pop()
        return self.last
