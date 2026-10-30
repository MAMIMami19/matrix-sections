#!/usr/bin/env python3
"""Assemble expanded catalogs from poster results. Merge with existing, update manifest."""
import json, os, glob

WORK = os.path.dirname(os.path.abspath(__file__))

# Load all poster results
all_posters = []
for f in glob.glob(os.path.join(WORK, 'posters_*.json')):
    try:
        all_posters.extend(json.load(open(f)))
    except Exception as e:
        print(f'WARN: could not read {f}: {e}')

print(f'Loaded {len(all_posters)} poster results')
ok = [p for p in all_posters if p.get('poster_path')]
print(f'With poster_path: {len(ok)}, null: {len(all_posters)-len(ok)}')

# Group by catalog
from collections import defaultdict
by_catalog = defaultdict(list)
for p in ok:
    # Verify poster URL returns 200 (spot check via HEAD)
    by_catalog[p['catalog']].append(p)

# Catalog file mapping and names
CATALOG_INFO = {
    'mx_netflix_series': ('catalog/series/mx_netflix_series.json', 'series'),
    'mx_netflix_movie': ('catalog/movie/mx_netflix_movie.json', 'movie'),
    'mx_disney_series': ('catalog/series/mx_disney_series.json', 'series'),
    'mx_hbo_series': ('catalog/series/mx_hbo_series.json', 'series'),
    'mx_hbo_movie': ('catalog/movie/mx_hbo_movie.json', 'movie'),
    'mx_apple_series': ('catalog/series/mx_apple_series.json', 'series'),
    'mx_prime_series': ('catalog/series/mx_prime_series.json', 'series'),
    'mx_paramount_series': ('catalog/series/mx_paramount_series.json', 'series'),
    'mx_paramount_movie': ('catalog/movie/mx_paramount_movie.json', 'movie'),
    'mx_mbc_series': ('catalog/series/mx_mbc_series.json', 'series'),
    'mx_crunchyroll_series': ('catalog/series/mx_crunchyroll_series.json', 'series'),
    'mx_hulu_series': ('catalog/series/mx_hulu_series.json', 'series'),
    'mx_peacock_series': ('catalog/series/mx_peacock_series.json', 'series'),
    'mx_sony_movie': ('catalog/movie/mx_sony_movie.json', 'movie'),
    'mx_universal_movie': ('catalog/movie/mx_universal_movie.json', 'movie'),
    'mx_warner_movie': ('catalog/movie/mx_warner_movie.json', 'movie'),
    'mx_yango_series': ('catalog/series/mx_yango_series.json', 'series'),
    'mx_watchit_series': ('catalog/series/mx_watchit_series.json', 'series'),
    'mx_watchit_movie': ('catalog/movie/mx_watchit_movie.json', 'movie'),
}

import urllib.request
def head_ok(url, timeout=15):
    req = urllib.request.Request(url, method='HEAD', headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status == 200
    except Exception:
        return False

from concurrent.futures import ThreadPoolExecutor
# Verify all poster URLs with HEAD
print('Verifying poster URLs (HEAD)...')
def verify(p):
    url = f"https://image.tmdb.org/t/p/w500{p['poster_path']}"
    return p, head_ok(url)

verified = []
with ThreadPoolExecutor(max_workers=10) as ex:
    futs = [ex.submit(verify, p) for p in ok]
    for i, fut in enumerate(futs):
        p, is_ok = fut.result()
        if is_ok:
            verified.append(p)
        if (i+1) % 50 == 0:
            print(f'  {i+1}/{len(ok)}')

print(f'Posters verified 200: {len(verified)}/{len(ok)}')

# Group verified by catalog
by_cat = defaultdict(list)
for p in verified:
    by_cat[p['catalog']].append(p)

# Write catalogs (merge with existing)
for catalog_id, (path, ctype) in CATALOG_INFO.items():
    full_path = os.path.join(WORK, path)
    existing = []
    existing_ids = set()
    if os.path.exists(full_path):
        d = json.load(open(full_path))
        existing = d.get('metas', [])
        existing_ids = set(m['id'] for m in existing)
    
    new_metas = []
    for p in by_cat.get(catalog_id, []):
        tid = f"tmdb:{p['tmdb']}"
        if tid in existing_ids:
            continue
        new_metas.append({
            'id': tid,
            'type': ctype,
            'name': p['name'],
            'poster': f"https://image.tmdb.org/t/p/w500{p['poster_path']}",
            'description': '',
            'genres': [],
            'releaseInfo': str(p['year']),
        })
        existing_ids.add(tid)
    
    all_metas = existing + new_metas
    os.makedirs(os.path.dirname(full_path), exist_ok=True)
    json.dump({'metas': all_metas}, open(full_path, 'w'), ensure_ascii=False, indent=1)
    print(f'{catalog_id}: {len(existing)} existing + {len(new_metas)} new = {len(all_metas)} total')

print('\nDone. Now update manifest manually and push.')
