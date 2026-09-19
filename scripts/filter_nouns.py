"""Conservative 'a ___' heuristic; WordNet does not encode countability.

Usage: python scripts/filter_nouns.py /path/to/wordnet.zip
Keeps candidates and writes an audit so later curation is reversible.
"""
import csv
from functools import lru_cache
from pathlib import Path
import re
import sys
from zipfile import ZipFile

ROOT = Path(__file__).resolve().parents[1]


def main(archive):
    with ZipFile(archive) as z:
        lines = z.read('wordnet/data.noun').decode().splitlines()
        exceptions = {line.split()[0] for line in z.read('wordnet/noun.exc').decode().splitlines()}
    records, by_word = {}, {}
    for line in lines:
        if not line or not line[0].isdigit():
            continue
        raw, gloss = line.split('|', 1)
        fields = raw.split()
        count = int(fields[3], 16)
        lemmas = fields[4:4 + 2 * count:2]
        pos = 4 + 2 * count
        pointers = [fields[i:i+4] for i in range(pos+1, pos+1+4*int(fields[pos]), 4)]
        records[fields[0]] = (int(fields[1]), gloss.strip(), pointers)
        for word in lemmas:
            if word.islower():
                by_word.setdefault(word, []).append(fields[0])

    @lru_cache(None)
    def substance(synset):
        lex, _, pointers = records[synset]
        if lex == 27 or synset in {'00019613', '00020090'}:
            return True
        return any(substance(target) for kind, target, pos, _ in pointers
                   if kind == '@' and pos == 'n')

    candidates = (ROOT / 'data/noun_candidates.txt').read_text().splitlines()
    kept, audit = [], []
    for upper in candidates:
        word = upper.lower()
        senses = by_word.get(word, [])
        reason, evidence = '', ''
        if word[0] in 'aeiou' or word in {'hour', 'heir', 'herb'}:
            reason = 'requires an, or pronunciation varies by dialect'
        elif (word in exceptions and word not in {'deer', 'fish'}) or word in {
            'dice', 'data', 'magi', 'kine', 'feet', 'teeth', 'men', 'women',
        }:
            reason = 'irregular plural form'
        elif word.endswith('s') and not word.endswith(('ss', 'us')) and word not in {'lens', 'bias', 'gas'}:
            reason = 'possible plural or plural-only form'
        else:
            for sid in senses:
                lex, gloss, pointers = records[sid]
                definition = gloss.split(';')[0]
                if any(p[0] == '@i' for p in pointers) or substance(sid):
                    continue
                if re.search(r'\b(plural|genus|genera|family of|collectively)\b', definition):
                    continue
                if re.match(r'^(a |an |one |someone |somebody |a person )', definition) or (
                    lex == 5 and not re.match(r'^(any of|small .*s\b)', definition)):
                    evidence = sid + ': ' + definition
                    break
            if not evidence:
                reason = 'no clear singular countable sense (heuristic)'
        if not reason:
            kept.append(upper)
        audit.append((upper, 'exclude' if reason else 'keep', reason or evidence))
    (ROOT / 'data/four_letter_words.txt').write_text('\n'.join(kept) + '\n')
    with (ROOT / 'data/noun_filter_audit.csv').open('w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(('word', 'decision', 'reason_or_evidence'))
        writer.writerows(audit)
    print(f'Kept {len(kept)} of {len(candidates)} candidates; saved audit CSV.')


if __name__ == '__main__':
    main(sys.argv[1])
