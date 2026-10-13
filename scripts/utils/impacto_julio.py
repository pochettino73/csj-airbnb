import json, sys
sys.stdout.reconfigure(encoding='utf-8')

with open('datos/reservas.json', encoding='utf-8') as f:
    data = json.load(f)

jul_conf = [r for r in data if r.get('year')==2026 and r.get('month')==7 and r.get('status')!='cancelled']

# Escenario original: sin Hannah ni Britta, con Darya
orig = [r for r in jul_conf if r.get('code') not in ('HMKQFE28R9', 'HM8T2PNRSC')]
darya = {'guest': 'Darya Kramar (cancelada)', 'checkin': '2026-07-01', 'nights': 9, 'total': 999.59, 'pm': 105.07}
orig_full = sorted(orig + [darya], key=lambda x: x.get('checkin', ''))

print('ESCENARIO ORIGINAL (sin cancelacion):')
for r in orig_full:
    marker = '  [CANC]' if 'cancelada' in r.get('guest','') else ''
    print(f"  {r.get('checkin',''):12}  {r.get('nights'):2d}n  {r.get('total',0):8.2f} EUR  {r.get('guest','')}{marker}")
t_orig = sum(r.get('total', 0) for r in orig_full)
n_orig = sum(r.get('nights', 0) for r in orig_full)
print(f'  TOTAL: {n_orig}n  |  {t_orig:.2f} EUR')

print()
print('ESTADO ACTUAL (cancelacion + nuevas reservas):')
for r in sorted(jul_conf, key=lambda x: x.get('checkin', '')):
    new = ' [NUEVA]' if r.get('code') in ('HMKQFE28R9', 'HM8T2PNRSC') else ''
    print(f"  {r.get('checkin',''):12}  {r.get('nights'):2d}n  {r.get('total',0):8.2f} EUR  {r.get('guest','')}{new}")
t_act = sum(r.get('total', 0) for r in jul_conf)
n_act = sum(r.get('nights', 0) for r in jul_conf)
print(f'  TOTAL: {n_act}n  |  {t_act:.2f} EUR')

print()
print('IMPACTO NETO:')
print(f'  Ingresos:  {t_orig:.2f} -> {t_act:.2f} EUR  ({t_act-t_orig:+.2f} EUR)')
print(f'  Noches:    {n_orig} -> {n_act}n  ({n_act-n_orig:+d}n)')
print(f'  Huecos pendientes: Jul 1-2 + Jul 28-30 = 4n potencial ~ +420 EUR')
