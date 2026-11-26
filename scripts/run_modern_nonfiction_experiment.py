#!/usr/bin/env python3
"""Run the replacement nonfiction corpus with the existing controlled protocol."""

from __future__ import annotations

import argparse
from dataclasses import replace
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from substitution_rank.analysis import write_summary
from substitution_rank.experiment import ExperimentConfig
from substitution_rank.supplement import run_stage

CORPUS = ROOT / 'corpus/modern_nonfiction_20260926'
CONFIG = ROOT / 'configs/modern_nonfiction_20260926/nonfiction_controlled_hc.json'
TRAIN_NAMES = [
    'pg1342_pride_and_prejudice.txt', 'pg1400_great_expectations.txt',
    'pg2701_moby_dick.txt', 'pg1661_sherlock_holmes.txt',
    'pg84_frankenstein.txt', 'pg345_dracula.txt',
    'pg74_tom_sawyer.txt', 'pg1260_jane_eyre.txt',
]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--check', action='store_true', help='validate inputs without running search')
    parser.add_argument('--workers', type=int, default=4)
    parser.add_argument('--batch-size', type=int, default=50)
    parser.add_argument('--pilot-trials', type=int, default=0, help='trials per length; write to a separate pilot directory')
    args = parser.parse_args()
    if args.workers < 1 or args.batch_size < 1 or args.pilot_trials < 0:
        parser.error('workers and batch-size must be positive; pilot-trials must be non-negative')
    manifest = json.loads((CORPUS / 'corpus_manifest.json').read_text(encoding='utf-8'))
    documents = manifest['documents']
    if len(documents) != 4 or any(int(d['publication_date'][:4]) < 2020 for d in documents):
        raise ValueError('Expected four nonfiction works published after 2019')
    train = [ROOT / 'corpus/formal_minimum/train' / name for name in TRAIN_NAMES]
    test = [ROOT / d['clean_path'] for d in documents]
    for document in documents:
        for kind in ['raw', 'clean', 'letters']:
            actual = hashlib.sha256((ROOT / document[f'{kind}_path']).read_bytes()).hexdigest()
            if actual != document[f'{kind}_sha256']:
                raise ValueError(f"Corpus checksum mismatch: {document['id']} {kind}")
    for path in train:
        if not path.is_file():
            raise FileNotFoundError(path)
    config = ExperimentConfig.from_json(CONFIG)
    print(f'Validated: {len(train)} training works; {len(test)} modern nonfiction test works.', flush=True)
    if args.check:
        print('Formal plan: 100/200/500 letters, 500 trials each, 120000 effective proposals per trial.')
        return
    output_root = ROOT / 'results/modern_nonfiction_20260926'
    if args.pilot_trials:
        config = replace(config, trials_per_length=args.pilot_trials)
        output_root = output_root / f'pilot_{args.pilot_trials}'
    output = output_root / 'nonfiction_controlled_hc.csv'
    rows = run_stage(name='modern_nonfiction_controlled_hc', config=config,
                     train_paths=train, test_paths=test, output_path=output,
                     workers=args.workers, batch_size=args.batch_size, resume=True)
    expected = len(config.lengths) * config.trials_per_length
    if len(rows) != expected or len({(r['length'], r['trial']) for r in rows}) != expected:
        raise ValueError('Incomplete or duplicate trials')
    for row in rows:
        if int(row['total_proposals']) != 120000 or int(row['neutral_proposals']) != 0 or int(row['early_stopped_restarts']) != 0 or int(row['score_calls']) != 120031:
            raise ValueError('Controlled search budget invariant failed')
    write_summary(rows, output.with_suffix(''))
    print(f'Completed {len(rows)} trials: {output}')


if __name__ == '__main__':
    main()
