import json
from datetime import date, timedelta
from collections import Counter

with open('datos/reviews.json', encoding='utf-8') as f:
    reviews = json.load(f)
with open('datos/reservas.json', encoding='utf-8') as f:
    reservas = json.load(f)

win_start = date(2025, 7, 1)
win_end   = date(2026, 6, 30)

# Reviews en ventana
rev_in_window = []
for r in reviews:
    try:
        d = date.fromisoformat(r['date'])
        if win_start <= d <= win_end:
            g = r.get('general') or r.get('rating')
            rev_in_window.append({
                'date': d,
                'rating': g,
                'code': r.get('confirmation_code', ''),
                'guest': r.get('guest', ''),
                'comment': (r.get('comment') or '')[:50]
            })
    except:
        pass

# Estancias confirmadas (no continuaciones) con checkout en ventana
stays = []
for res in reservas:
    if res.get('status') != 'confirmed':
        continue
    if res.get('is_continuation'):
        continue
    try:
        ci = date.fromisoformat(res['checkin'])
        n  = res.get('nights', 0)
        co = ci + timedelta(days=n)
        if win_start <= co <= win_end + timedelta(days=14):
            stays.append({
                'checkout': co,
                'code': res.get('confirmation_code') or res.get('code', ''),
                'guest': res.get('guest', ''),
                'nights': n
            })
    except:
        pass

stays.sort(key=lambda x: x['checkout'])

# Cruce: codigo primero, luego fecha +-10 dias
used_reviews = set()
matched = []

for s in stays:
    found = None
    for i, r in enumerate(rev_in_window):
        if i in used_reviews:
            continue
        if s['code'] and r['code'] and s['code'] == r['code']:
            found = (i, r, 'codigo')
            break
    if not found:
        for i, r in enumerate(rev_in_window):
            if i in used_reviews:
                continue
            if abs((r['date'] - s['checkout']).days) <= 10:
                found = (i, r, 'fecha')
                break
    if found:
        used_reviews.add(found[0])
        matched.append({
            'checkout': s['checkout'],
            'guest': s['guest'],
            'code': s['code'],
            'rating': found[1]['rating'],
            'rev_date': found[1]['date'],
            'match': found[2]
        })
    else:
        matched.append({
            'checkout': s['checkout'],
            'guest': s['guest'],
            'code': s['code'],
            'rating': None,
            'rev_date': None,
            'match': 'SIN REVIEW'
        })

print('ESTANCIAS EN VENTANA (checkout jul25-jun26)')
print('=' * 75)
print(f"{'Checkout':<12} {'R':>2}  {'Match':<8}  {'Huesped':<30}  Codigo")
print('-' * 75)
for m in matched:
    r = str(m['rating']) if m['rating'] else '-'
    rv = str(m['rev_date']) if m['rev_date'] else ''
    g = m['guest'].encode('ascii', 'replace').decode('ascii')
    print(f"{str(m['checkout']):<12} {r:>2}  {m['match']:<8}  {g:<30}  {m['code']}")

print()
print('REVIEWS SIN ESTANCIA ASOCIADA:')
huerfanas = [(i, r) for i, r in enumerate(rev_in_window) if i not in used_reviews]
if huerfanas:
    for i, r in huerfanas:
        print(f"  {r['date']}  {r['rating']}  {r['guest']:<25}  {r['code']}  {r['comment']}")
else:
    print('  Ninguna')

print()
total_ratings = [m['rating'] for m in matched if m['rating']]
n = len(total_ratings)
s = sum(total_ratings)
print(f'Reviews con rating: {n}  |  Suma: {s}  |  Media: {s/n:.4f}')
c = Counter(total_ratings)
for k in sorted(c, reverse=True):
    print(f'  {k} estrellas: {c[k]}')
