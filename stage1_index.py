#!/usr/bin/env python3
"""Expand platform catalogs with verified TMDB titles. Stage 1: build ID index + define candidates."""
import gzip, json, re, unicodedata, os

WORK = os.path.dirname(os.path.abspath(__file__))

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    s = re.sub(r'\s+', ' ', s).strip()
    return s

def load_index(path, title_key):
    idx = {}
    with gzip.open(path, 'rt', encoding='utf-8') as f:
        for line in f:
            try:
                d = json.loads(line)
            except Exception:
                continue
            t = d.get(title_key) or ''
            if not t:
                continue
            key = norm(t)
            if not key:
                continue
            idx.setdefault(key, []).append((d['id'], d.get('popularity', 0)))
    # sort each bucket by popularity desc
    for k in idx:
        idx[k].sort(key=lambda x: -x[1])
    return idx

print('Loading TV index...', flush=True)
TV = load_index(os.path.join(WORK, 'tv_ids.json.gz'), 'original_name')
print('TV titles:', len(TV), flush=True)
print('Loading movie index...', flush=True)
MV = load_index(os.path.join(WORK, 'movie_ids.json.gz'), 'original_title')
print('Movie titles:', len(MV), flush=True)

import pickle
with open(os.path.join(WORK, 'idx_tv.pkl'), 'wb') as f:
    pickle.dump(TV, f)
with open(os.path.join(WORK, 'idx_mv.pkl'), 'wb') as f:
    pickle.dump(MV, f)
print('Indexes saved.')
