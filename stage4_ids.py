#!/usr/bin/env python3
"""Match all candidates to TMDB IDs via export. Save ID map."""
import pickle, re, unicodedata, os, sys, json
WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = s.lower(); s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

with open(os.path.join(WORK, 'idx_tv.pkl'), 'rb') as f: TV = pickle.load(f)
with open(os.path.join(WORK, 'idx_mv.pkl'), 'rb') as f: MV = pickle.load(f)

def find_id(hint, display, ctype):
    idx = TV if ctype == 'series' else MV
    for t in (hint, display):
        k = norm(t)
        if k in idx and idx[k]: return idx[k][0][0], idx[k][0][1]
    d2 = re.sub(r'\s*\(.*?\)\s*', ' ', display)
    k = norm(d2)
    if k in idx and idx[k]: return idx[k][0][0], idx[k][0][1]
    # try without leading "the "
    for t in (hint, display):
        k = norm(t)
        if k.startswith('the '):
            k2 = k[4:]
            if k2 in idx and idx[k2]: return idx[k2][0][0], idx[k2][0][1]
    return None, None

# import all candidate lists
import candidates as C
all_lists = {
    'NETFLIX_SERIES': ('series', C.NETFLIX_SERIES),
    'NETFLIX_MOVIES': ('movie', C.NETFLIX_MOVIES),
    'DISNEY_SERIES': ('series', C.DISNEY_SERIES),
    'HBO_SERIES': ('series', C.HBO_SERIES),
    'HBO_MOVIES': ('movie', C.HBO_MOVIES),
    'APPLE_SERIES': ('series', C.APPLE_SERIES),
    'PRIME_SERIES': ('series', C.PRIME_SERIES),
    'PARAMOUNT_SERIES': ('series', C.PARAMOUNT_SERIES),
    'PARAMOUNT_MOVIES': ('movie', C.PARAMOUNT_MOVIES),
    'MBC_SERIES': ('series', C.MBC_SERIES),
}

# Batch 2 lists (to be added)
BATCH2 = {}

idmap = {}
nomatch = []
for listname, (ctype, cands) in all_lists.items():
    for (name, hint, year) in cands:
        tid, pop = find_id(hint, name, ctype)
        if tid:
            idmap[f'{listname}::{name}'] = {'tmdb': tid, 'type': ctype, 'year': year, 'name': name, 'pop': pop}
        else:
            nomatch.append(f'{listname} :: {name} ({hint})')

with open(os.path.join(WORK, 'idmap.json'), 'w') as f:
    json.dump(idmap, f, indent=1)
print(f'Matched: {len(idmap)}, No match: {len(nomatch)}')
for x in nomatch[:40]:
    print('  NO:', x)
