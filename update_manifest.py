#!/usr/bin/env python3
"""Update manifest.json: add new catalogs in reverse-alpha platform order, bump version."""
import json, os
WORK = os.path.dirname(os.path.abspath(__file__))
mp = os.path.join(WORK, 'manifest.json')
d = json.load(open(mp))

# New catalogs to add: (id, type, name)
new_cats = [
    ('mx_peacock_series', 'series', 'أعمال Peacock الأصلية'),
    ('mx_paramount_movie', 'movie', 'أعمال Paramount الأصلية'),
    ('mx_netflix_movie', 'movie', 'أعمال Netflix الأصلية'),
    ('mx_mbc_series', 'series', 'أعمال MBC الأصلية'),
    ('mx_hulu_series', 'series', 'أعمال Hulu الأصلية'),
]

existing_ids = set(c['id'] for c in d['catalogs'])
# Build new catalog entries
new_entries = []
for cid, ctype, name in new_cats:
    if cid not in existing_ids:
        new_entries.append({'id': cid, 'type': ctype, 'name': name, 'extra': []})

# Insert in reverse-alpha order. Current platform block order (after top10):
# yango, watchit_s, watchit_m, warner_m, universal_m, sony_m, prime_s, paramount_s, netflix_s, hbo_s, hbo_m, disney_s, crunchyroll_s, apple_s
# Target insertions:
# - mx_peacock_series after mx_prime_series
# - mx_paramount_movie after mx_paramount_series
# - mx_netflix_movie after mx_netflix_series
# - mx_mbc_series after mx_netflix_movie (before mx_hulu_series)
# - mx_hulu_series after mx_mbc_series (before mx_hbo_series)

order_map = {cid: {'id': cid, 'type': ct, 'name': nm, 'extra': []} for cid, ct, nm in new_cats}
result = []
for c in d['catalogs']:
    result.append(c)
    cid = c['id']
    if cid == 'mx_prime_series' and 'mx_peacock_series' in order_map:
        result.append(order_map.pop('mx_peacock_series'))
    elif cid == 'mx_paramount_series' and 'mx_paramount_movie' in order_map:
        result.append(order_map.pop('mx_paramount_movie'))
    elif cid == 'mx_netflix_series' and 'mx_netflix_movie' in order_map:
        result.append(order_map.pop('mx_netflix_movie'))
        if 'mx_mbc_series' in order_map:
            result.append(order_map.pop('mx_mbc_series'))
        if 'mx_hulu_series' in order_map:
            result.append(order_map.pop('mx_hulu_series'))

# Any leftovers (shouldn't happen) append before first non-platform
for e in order_map.values():
    result.append(e)

d['catalogs'] = result
# Bump version 1.2.2 -> 1.3.0
d['version'] = '1.3.0'

json.dump(d, open(mp, 'w'), ensure_ascii=False, indent=2)
print('Manifest updated to v1.3.0')
for c in d['catalogs']:
    if any(x in c['id'] for x in ('peacock','paramount_movie','netflix_movie','mbc','hulu')):
        print(' ', c['type'], c['id'], '|', c['name'])
print('Total catalogs:', len(d['catalogs']))
