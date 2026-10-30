#!/usr/bin/env python3
"""Stage 3: match candidates to TMDB IDs, verify via Cinemeta, check posters."""
import pickle, json, re, unicodedata, os, sys, time
import urllib.request
from concurrent.futures import ThreadPoolExecutor, as_completed

WORK = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, WORK)
from candidates import CATALOG_JOBS

def norm(s):
    s = unicodedata.normalize('NFKD', s).encode('ascii', 'ignore').decode('ascii')
    s = s.lower()
    s = re.sub(r'[^a-z0-9 ]', ' ', s)
    return re.sub(r'\s+', ' ', s).strip()

with open(os.path.join(WORK, 'idx_tv.pkl'), 'rb') as f:
    TV = pickle.load(f)
with open(os.path.join(WORK, 'idx_mv.pkl'), 'rb') as f:
    MV = pickle.load(f)

def find_id(title_hint, display, ctype):
    idx = TV if ctype == 'series' else MV
    for t in (title_hint, display):
        key = norm(t)
        if key in idx and idx[key]:
            return idx[key][0][0]  # highest popularity
    # fallback: try display without parentheticals
    d2 = re.sub(r'\s*\(.*?\)\s*', ' ', display)
    key = norm(d2)
    if key in idx and idx[key]:
        return idx[key][0][0]
    return None

def fetch(url, timeout=25):
    req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0'})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return r.status, r.read()
    except Exception as e:
        return 0, b''

def verify_one(job):
    cid, ctype, name, hint, year = job
    tid = find_id(hint, name, ctype)
    if not tid:
        return (cid, name, 'NO_ID_MATCH')
    meta_url = f'https://v3-cinemeta.strem.io/meta/{ctype}/tmdb:{tid}.json'
    st, body = fetch(meta_url)
    if st != 200:
        return (cid, name, f'CINEMETA_{st}')
    try:
        meta = json.loads(body)['meta']
    except Exception:
        return (cid, name, 'CINEMETA_PARSE')
    if meta.get('type') != ctype:
        return (cid, name, f'TYPE_MISMATCH:{meta.get("type")}')
    poster = meta.get('poster') or ''
    if not poster or 'image.tmdb.org' not in poster:
        return (cid, name, 'NO_POSTER')
    pst, _ = fetch(poster, timeout=20)
    if pst != 200:
        return (cid, name, f'POSTER_{pst}')
    # year sanity: allow +-1
    ri = str(meta.get('releaseInfo') or '')
    m = re.search(r'(19|20)\d{2}', ri)
    if m and abs(int(m.group(0)) - year) > 1:
        return (cid, name, f'YEAR_MISMATCH:{m.group(0)}vs{year}')
    return (cid, name, 'OK', {
        'id': f'tmdb:{tid}',
        'type': ctype,
        'name': meta.get('name') or name,
        'poster': poster,
        'description': (meta.get('description') or '')[:400],
        'genres': [],
        'releaseInfo': ri or str(year),
    })

# Build job list
jobs = []
job_meta = {}
for cid, ctype, cands, path, is_new in CATALOG_JOBS:
    for (name, hint, year) in cands:
        key = (cid, name)
        jobs.append((cid, ctype, name, hint, year))
        job_meta[key] = (ctype, path, is_new)

print(f'{len(jobs)} candidates to verify...', flush=True)
results = {}
fails = {}
with ThreadPoolExecutor(max_workers=12) as ex:
    futs = {ex.submit(verify_one, j): j for j in jobs}
    done = 0
    for fut in as_completed(futs):
        r = fut.result()
        done += 1
        if done % 50 == 0:
            print(f'  {done}/{len(jobs)}', flush=True)
        if r[2] == 'OK':
            results[(r[0], r[1])] = r[3]
        else:
            fails.setdefault(r[2], []).append(f'{r[0]} :: {r[1]}')

print('\n=== FAILURES ===')
for k, v in sorted(fails.items()):
    print(f'{k}: {len(v)}')
    for x in v[:8]:
        print('   ', x)

# Save verified per catalog
out = {}
for (cid, name), item in results.items():
    out.setdefault(cid, []).append(item)
with open(os.path.join(WORK, 'verified.json'), 'w') as f:
    json.dump(out, f, ensure_ascii=False, indent=1)
print('\n=== VERIFIED COUNTS ===')
for cid, ctype, cands, path, is_new in CATALOG_JOBS:
    print(f'{cid}: {len(out.get(cid, []))} / {len(cands)}')
