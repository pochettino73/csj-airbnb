import json, sys
from datetime import date
sys.stdout.reconfigure(encoding='utf-8')

with open('datos/reservas.json', encoding='utf-8') as f:
    data = json.load(f)

conf = [r for r in data if r.get('status') != 'cancelled']
canc_2026 = [r for r in data if r.get('status') == 'cancelled'
             and r.get('year', 0) == 2026
             and r.get('impacto', 0) > 0]
canc_2025 = [r for r in data if r.get('status') == 'cancelled'
             and r.get('year', 0) == 2025
             and r.get('impacto', 0) > 0]

print('=== CANCELACIONES 2025 ===')
for r in sorted(canc_2025, key=lambda x: x.get('checkin', '')):
    print(f"  {r.get('checkin',''):12}  {r.get('nights',0):2d}n  {r.get('impacto',0):8.2f} EUR  {r.get('guest','')}")
tot_2025 = sum(r.get('impacto', 0) for r in canc_2025)
n_2025 = sum(r.get('nights', 0) for r in canc_2025)
print(f"  TOTAL: {len(canc_2025)} cancelaciones  |  {n_2025}n perdidas  |  {tot_2025:.2f} EUR impacto")

print()
print('=== CANCELACIONES 2026 (todas) ===')
for r in sorted(canc_2026, key=lambda x: x.get('checkin', '')):
    print(f"  {r.get('checkin',''):12}  {r.get('nights',0):2d}n  {r.get('impacto',0):8.2f} EUR  {r.get('guest','')}")
tot_2026 = sum(r.get('impacto', 0) for r in canc_2026)
n_2026 = sum(r.get('nights', 0) for r in canc_2026)
print(f"  TOTAL: {len(canc_2026)} cancelaciones  |  {n_2026}n perdidas  |  {tot_2026:.2f} EUR impacto")

print()
print('=== JUNIO 2026 — estado actual ===')
jun = [r for r in conf if r.get('year') == 2026 and r.get('month') == 6]
for r in sorted(jun, key=lambda x: x.get('checkin', '')):
    print(f"  {r.get('checkin',''):12}  {r.get('nights',0):2d}n  {r.get('total',0):8.2f} EUR  {r.get('guest','')}")
print(f"  => {sum(r.get('nights',0) for r in jun)}n / 30 dias = {sum(r.get('nights',0) for r in jun)/30*100:.0f}% ocupacion  |  {sum(r.get('total',0) for r in jun):.2f} EUR")

print()
print('=== JULIO 2026 — estado actual ===')
jul = [r for r in conf if r.get('year') == 2026 and r.get('month') == 7]
for r in sorted(jul, key=lambda x: x.get('checkin', '')):
    print(f"  {r.get('checkin',''):12}  {r.get('nights',0):2d}n  {r.get('total',0):8.2f} EUR  {r.get('guest','')}")
print(f"  => {sum(r.get('nights',0) for r in jul)}n / 31 dias = {sum(r.get('nights',0) for r in jul)/31*100:.0f}% ocupacion  |  {sum(r.get('total',0) for r in jul):.2f} EUR")

# Historico Jun-Jul para comparar
print()
print('=== REFERENCIA HISTORICA Jun+Jul (2022-2025) ===')
for yr in [2022, 2023, 2024, 2025]:
    jun_h = [r for r in conf if r.get('year') == yr and r.get('month') == 6]
    jul_h = [r for r in conf if r.get('year') == yr and r.get('month') == 7]
    ing = sum(r.get('total',0) for r in jun_h+jul_h)
    n = sum(r.get('nights',0) for r in jun_h+jul_h)
    print(f"  {yr}:  Jun+Jul {n:2d}n  {ing:.2f} EUR")
