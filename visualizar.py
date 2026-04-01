#!/usr/bin/env python3
"""
CSJ Airbnb — Dashboard Ejecutivo CEO
HTML interactivo con Chart.js + filtros.
Todos los datos desde ficheros locales: _reservas.json, _reviews.json, _visitas.json.
0 dependencias externas.
"""

import json
import os
import calendar
from datetime import datetime

MESES = ["Ene", "Feb", "Mar", "Abr", "May", "Jun", "Jul", "Ago", "Sep", "Oct", "Nov", "Dic"]

PALETTE = {
    2015: "#6b7280", 2016: "#9ca3af", 2017: "#a78bfa", 2018: "#c084fc",
    2019: "#f472b6", 2020: "#ef4444", 2021: "#fb923c", 2022: "#fbbf24",
    2023: "#34d399", 2024: "#22d3ee", 2025: "#3b82f6", 2026: "#8b5cf6",
    2027: "#f59e0b",
}


def load_reservas():
    """Carga _reservas.json y calcula ingresos, ocupación y PM mensuales por año."""
    path = os.path.join(os.path.dirname(__file__), "_reservas.json")
    with open(path, "r", encoding="utf-8") as f:
        reservas = json.load(f)

    # Validación: filtrar entradas imposibles
    before = len(reservas)
    reservas = [r for r in reservas if 0 < r["nights"] <= 31 or r["total"] > 0]
    if len(reservas) < before:
        print(f"  AVISO: {before - len(reservas)} entradas filtradas por datos imposibles")

    # Acumular por (año, mes): total ingresos, noches, total sin limpieza
    from collections import defaultdict
    acc = defaultdict(lambda: {"total": 0, "nights": 0, "total_sin_limp": 0, "count": 0})
    for r in reservas:
        key = (r["year"], r["month"])
        acc[key]["total"] += r["total"]
        acc[key]["nights"] += r["nights"]
        acc[key]["total_sin_limp"] += r["total"] - r["cleaning"]
        acc[key]["count"] += 1

    years = sorted(set(k[0] for k in acc))
    ing, ocu, pm = {}, {}, {}
    for y in years:
        ing[y] = []
        ocu[y] = []
        pm[y] = []
        for m in range(1, 13):
            d = acc.get((y, m))
            days = calendar.monthrange(y, m)[1]
            if d and d["total"] > 0:
                ing[y].append(round(d["total"], 2))
                ocu[y].append(round(d["nights"] / days, 4))  # fracción 0-1
                pm[y].append(round(d["total_sin_limp"] / d["nights"], 2) if d["nights"] > 0 else 0)
            else:
                ing[y].append(0)
                ocu[y].append(0)
                pm[y].append(0)

    return ing, ocu, pm, reservas


def load_reviews():
    """Carga _reviews.json y calcula medias por subcategoría."""
    path = os.path.join(os.path.dirname(__file__), "_reviews.json")
    with open(path, "r", encoding="utf-8") as f:
        reviews = json.load(f)

    cats = ["llegada", "limpieza", "veracidad", "comunicacion", "ubicacion", "calidad"]
    CAT_DISPLAY = {
        "llegada": "Llegada", "limpieza": "Limpieza", "veracidad": "Veracidad",
        "comunicacion": "Comunicación", "ubicacion": "Ubicación", "calidad": "Calidad"
    }

    def avg_cat(revs, cat):
        vs = [r[cat] for r in revs if r.get(cat) and r[cat] > 0]
        return round(sum(vs) / len(vs), 2) if vs else 0

    def avg_general(revs):
        vs = [r["rating"] for r in revs if r.get("rating") and r["rating"] > 0]
        return round(sum(vs) / len(vs), 2) if vs else 0

    result = {"global": {}, "12m": {}, "3m": {}}
    # All reviews
    result["global"]["General"] = avg_general(reviews)
    result["global"]["n"] = len(reviews)
    for c in cats:
        result["global"][CAT_DISPLAY[c]] = avg_cat(reviews, c)

    # Last 12 months
    from datetime import datetime, timedelta
    now = datetime.now()
    r12 = [r for r in reviews if r["date"] >= (now - timedelta(days=365)).strftime("%Y-%m-%d")]
    result["12m"]["General"] = avg_general(r12)
    result["12m"]["n"] = len(r12)
    for c in cats:
        result["12m"][CAT_DISPLAY[c]] = avg_cat(r12, c)

    # Last 3 months
    r3 = [r for r in reviews if r["date"] >= (now - timedelta(days=90)).strftime("%Y-%m-%d")]
    result["3m"]["General"] = avg_general(r3)
    result["3m"]["n"] = len(r3)
    for c in cats:
        result["3m"][CAT_DISPLAY[c]] = avg_cat(r3, c)

    return result, reviews


def load_visitas():
    """Carga _visitas.json con page views del listing por mes."""
    path = os.path.join(os.path.dirname(__file__), "_visitas.json")
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)



def J(o):
    return json.dumps(o, ensure_ascii=False)


def build(data, ing, ocu, pm, rev):
    reservas = data.get("reservas", [])
    visitas_raw = data.get("visitas", {})
    now = datetime.now()
    cy, cm = now.year, now.month

    active = sorted([y for y in ing if sum(ing[y]) > 0])

    # All data as JSON for JS
    all_ing = {str(y): ing[y] for y in active}
    all_ocu = {str(y): [round(v * 100, 2) for v in ocu.get(y, [0]*12)] for y in active}
    all_pm = {str(y): [round(v, 2) for v in pm.get(y, [0]*12)] for y in active}

    ann_ing = {str(y): round(sum(ing[y])) for y in active}
    ann_ocu = {str(y): round(sum(v for v in ocu[y] if v > 0) / max(1, sum(1 for v in ocu[y] if v > 0)) * 100, 1) for y in active}
    ann_pm = {str(y): round(sum(v for v in pm.get(y, [0]*12) if v > 0) / max(1, sum(1 for v in pm.get(y, [0]*12) if v > 0)), 1) for y in active}

    # Resumen from local data (replaces Sheet "Resumen" tab)
    res_y = [str(y) for y in active]
    res_i = [ann_ing[str(y)] for y in active]
    res_o = [ann_ocu[str(y)] for y in active]
    res_p = [ann_pm[str(y)] for y in active]

    palette = {str(y): PALETTE.get(y, "#94a3b8") for y in active}

    # Band — Ingresos
    hmin, hmax, havg = [], [], []
    for m in range(12):
        vs = [ing[y][m] for y in ing if y < cy and ing[y][m] > 0]
        hmin.append(round(min(vs), 0) if vs else 0)
        hmax.append(round(max(vs), 0) if vs else 0)
        havg.append(round(sum(vs)/len(vs), 0) if vs else 0)

    # Band — Ocupación
    hmin_ocu, hmax_ocu, havg_ocu = [], [], []
    for m in range(12):
        vs = [ocu[y][m]*100 for y in ocu if y < cy and ocu[y][m] > 0]
        hmin_ocu.append(round(min(vs), 1) if vs else 0)
        hmax_ocu.append(round(max(vs), 1) if vs else 0)
        havg_ocu.append(round(sum(vs)/len(vs), 1) if vs else 0)

    # Band — PM
    hmin_pm, hmax_pm, havg_pm = [], [], []
    for m in range(12):
        vs = [pm[y][m] for y in pm if y < cy and pm[y][m] > 0]
        hmin_pm.append(round(min(vs), 1) if vs else 0)
        hmax_pm.append(round(max(vs), 1) if vs else 0)
        havg_pm.append(round(sum(vs)/len(vs), 1) if vs else 0)

    # === CONVERSIÓN (visitas desde _visitas.json + reservas desde booking_date) ===
    # Identificar prorated children para no contarlas como reservas separadas
    _pror = set()
    for i in range(len(reservas)):
        r = reservas[i]
        g = r['guest'].strip() if r.get('guest') else ''
        if not g:
            continue
        ym = r['year'] * 12 + r['month']
        for j in range(max(0, i - 5), i):
            p = reservas[j]
            pg = p['guest'].strip() if p.get('guest') else ''
            if pg == g and p['year'] * 12 + p['month'] == ym - 1:
                _pror.add(i)
                break

    conv_years = sorted(set(y for y in active if y >= 2018))
    conv_data = {}
    for y in conv_years:
        sy = str(y)
        c_visitas, c_reservas = [], []
        for m in range(1, 13):
            vk = f"{y}-{m:02d}"
            c_visitas.append(visitas_raw.get(vk, 0))
            # Reservas por fecha de venta (booking_date), excluir prorated
            n_res = sum(1 for idx, r in enumerate(reservas)
                        if r.get('booking_date')
                        and int(r['booking_date'][:4]) == y
                        and int(r['booking_date'][5:7]) == m
                        and idx not in _pror)
            c_reservas.append(n_res)
        conv_data[sy] = {"v": c_visitas, "r": c_reservas}

    conv_ann = {}
    for sy in conv_data:
        tv = sum(conv_data[sy]["v"])
        tr = sum(conv_data[sy]["r"])
        cvr = round(tr / tv * 100, 2) if tv > 0 else 0
        conv_ann[sy] = {"v": tv, "r": tr, "cvr": cvr}

    # === COSTES Y BENEFICIO NETO ===
    # Costes estimados por año — TODO: reemplazar con datos reales de pestañas Gastos
    COSTE_RESERVA = 40  # EUR/reserva (30€ Tania + 10€ amenities/desgaste)
    COSTES_FIJOS = {
        2015: 6000, 2016: 6000, 2017: 6500, 2018: 7000, 2019: 7200,
        2020: 7200, 2021: 7500, 2022: 8000, 2023: 8500, 2024: 9090,
        2025: 9090, 2026: 9090, 2027: 9090,
    }
    # Contar reservas por año desde _reservas.json (solo las que tienen code, evitar prorrateos duplicados)
    reservas_por_anyo = {}
    for r in reservas:
        y = r["year"]
        reservas_por_anyo.setdefault(y, 0)
        if r.get("code"):  # solo contar la reserva principal, no la parte prorrateada
            reservas_por_anyo[y] += 1

    costes_ann = {}
    neto_ann = {}
    for y in active:
        sy = str(y)
        ingreso = sum(ing[y])
        fijos = COSTES_FIJOS.get(y, 9090)
        n_reservas = reservas_por_anyo.get(y, 0)
        if n_reservas == 0:
            n_reservas = max(1, round(sum(ocu[y]) * 365 / 5))
        total_costes = fijos + n_reservas * COSTE_RESERVA
        costes_ann[sy] = round(total_costes)
        neto_ann[sy] = round(ingreso - total_costes)

    # === PM POR BANDA ESTACIONAL ===
    # Alta: 15/6 al 15/9 — Media: 1/4 al 15/6 y 15/9 al 31/10 — Baja: 1/11 al 31/3
    def get_banda(checkin_str):
        """Devuelve 'alta', 'media' o 'baja' según la fecha de checkin."""
        mm, dd = int(checkin_str[5:7]), int(checkin_str[8:10])
        # Alta: 15 jun - 15 sep
        if (mm == 6 and dd >= 15) or mm in (7, 8) or (mm == 9 and dd <= 15):
            return "alta"
        # Baja: 1 nov - 31 mar
        if mm in (11, 12, 1, 2, 3):
            return "baja"
        # Media: 1 abr - 14 jun y 16 sep - 31 oct
        return "media"

    pm_banda = {}
    for y in active:
        sy = str(y)
        bandas = {"alta": [], "media": [], "baja": []}
        for r in reservas:
            if r["year"] != y or r["nights"] <= 0 or r["total"] <= 0:
                continue
            ci = r.get("checkin")
            pm_r = (r["total"] - r["cleaning"]) / r["nights"] if r["nights"] > 0 else 0
            if ci and pm_r > 0:
                banda = get_banda(ci)
                bandas[banda].append(pm_r)
            elif not ci and pm_r > 0:
                # Sin checkin: asignar por mes (fallback)
                m = r["month"]
                if m in (7, 8):
                    bandas["alta"].append(pm_r)
                elif m in (11, 12, 1, 2, 3):
                    bandas["baja"].append(pm_r)
                else:
                    bandas["media"].append(pm_r)
        pm_banda[sy] = {
            b: round(sum(vs)/len(vs), 1) if vs else 0
            for b, vs in bandas.items()
        }

    # === PACE REPORT (On The Books vs LY) ===
    from datetime import date, timedelta
    today_d = date.today()

    pace_otb = {}   # {str(y): [12]}  — revenue booked by equivalent date
    pace_final = {}  # {str(y): [12]} — total final revenue

    for y in active:
        sy = str(y)
        try:
            cutoff = today_d.replace(year=y)
        except ValueError:
            cutoff = today_d.replace(year=y, day=28)
        cutoff_str = cutoff.strftime("%Y-%m-%d")

        otb, final = [], []
        for m in range(1, 13):
            mr = [r for r in reservas if r['year'] == y and r['month'] == m]
            final.append(round(sum(r['total'] for r in mr), 2))
            otb_v = sum(r['total'] for r in mr
                        if r.get('booking_date') and r['booking_date'] <= cutoff_str)
            otb_v += sum(r['total'] for r in mr if not r.get('booking_date'))
            otb.append(round(otb_v, 2))
        pace_otb[sy] = otb
        pace_final[sy] = final

    # === LEAD TIME ===
    lt_buckets_def = [("<7d", 0, 7), ("7-30d", 7, 30), ("30-90d", 30, 90), (">90d", 90, 9999)]
    lt_bucket_data = {b[0]: [] for b in lt_buckets_def}
    lt_by_year_raw = {}

    for r in reservas:
        if not r.get('booking_date') or not r.get('checkin'):
            continue
        try:
            bd = date.fromisoformat(r['booking_date'])
            ci = date.fromisoformat(r['checkin'])
        except Exception:
            continue
        lt = (ci - bd).days
        if lt < 0 or r['nights'] <= 0:
            continue
        pm_n = (r['total'] - r['cleaning']) / r['nights']
        for bname, blo, bhi in lt_buckets_def:
            if blo <= lt < bhi:
                lt_bucket_data[bname].append({"lt": lt, "pm": pm_n, "total": r['total']})
                break
        lt_by_year_raw.setdefault(str(r['year']), []).append(lt)

    lt_summary = {}
    for bname in [b[0] for b in lt_buckets_def]:
        entries = lt_bucket_data[bname]
        if entries:
            lt_summary[bname] = {
                "n": len(entries),
                "avg_pm": round(sum(e['pm'] for e in entries) / len(entries), 2),
                "avg_lt": round(sum(e['lt'] for e in entries) / len(entries), 1),
                "pct_rev": round(sum(e['total'] for e in entries), 0),
            }
        else:
            lt_summary[bname] = {"n": 0, "avg_pm": 0, "avg_lt": 0, "pct_rev": 0}

    lt_avg_year = {}
    for sy, lts in lt_by_year_raw.items():
        lt_avg_year[sy] = round(sum(lts) / len(lts), 1) if lts else 0

    rg = rev.get("global", {})
    cats = ["General", "Llegada", "Limpieza", "Veracidad", "Comunicación", "Ubicación", "Calidad"]
    cats_sub = ["Llegada", "Limpieza", "Veracidad", "Comunicación", "Ubicación", "Calidad"]
    cats_key = ["llegada", "limpieza", "veracidad", "comunicacion", "ubicacion", "calidad"]

    # Superhost assessment periods (quarterly, rolling 365d)
    # Q1 check: Jan 1 (reviews from Jan 1 LY to Dec 31)
    # Q2 check: Apr 1 (reviews from Apr 1 LY to Mar 31)
    # Q3 check: Jul 1 (reviews from Jul 1 LY to Jun 30)
    # Q4 check: Oct 1 (reviews from Oct 1 LY to Sep 30)
    reviews_list = data.get("reviews_list", [])
    superhost_quarters = {}  # {"2026-Q1": {rating, n, ...}}
    sh_checks = []
    for y in range(2018, cy + 2):
        # Q1: 1 ene Y-1 → 31 dic Y-1 (end year = Y-1)
        # Q2: 1 abr Y-1 → 31 mar Y  (end year = Y)
        # Q3: 1 jul Y-1 → 30 jun Y  (end year = Y)
        # Q4: 1 oct Y-1 → 30 sep Y  (end year = Y)
        for q, (sm, sd, ey_offset, em, ed) in enumerate([
            (1, 1, -1, 12, 31), (4, 1, 0, 3, 31), (7, 1, 0, 6, 30), (10, 1, 0, 9, 30)
        ], 1):
            start = f"{y-1}-{sm:02d}-{sd:02d}"
            end = f"{y+ey_offset}-{em:02d}-{ed:02d}"
            t_map = {1: 4, 2: 1, 3: 2, 4: 3}
            t_year = {1: y-1, 2: y, 3: y, 4: y}
            label = f"{t_year[q]}-T{t_map[q]}"
            qrevs = [r for r in reviews_list if start <= r["date"] <= end]
            if not qrevs:
                continue
            ratings = [r["rating"] for r in qrevs if r.get("rating") and r["rating"] > 0]
            avg_r = round(sum(ratings) / len(ratings), 2) if ratings else 0
            superhost_quarters[label] = {
                "n": len(qrevs), "rating": avg_r,
                "superhost": avg_r >= 4.8 and len(qrevs) >= 3,
            }
            sh_checks.append(label)

    # === REVISIONES SUPERHOST FUTURAS ===
    today_str = now.strftime("%Y-%m-%d")
    from collections import Counter
    from datetime import datetime as dt2
    future_sh = []  # list of future quarter assessments
    for y in range(cy, cy + 2):
        for q, (sm, sd, ey_offset, em, ed) in enumerate([
            (1, 1, -1, 12, 31), (4, 1, 0, 3, 31), (7, 1, 0, 6, 30), (10, 1, 0, 9, 30)
        ], 1):
            eval_date = f"{y}-{[1,4,7,10][q-1]:02d}-01"
            if eval_date > today_str and len(future_sh) < 4:
                start_w = f"{y-1}-{sm:02d}-{sd:02d}"
                end_w = f"{y+ey_offset}-{em:02d}-{ed:02d}"
                t_map_w = {1: 4, 2: 1, 3: 2, 4: 3}
                t_year_w = {1: y-1, 2: y, 3: y, 4: y}
                label_w = f"{t_year_w[q]}-T{t_map_w[q]}"
                qrevs_w = [r for r in reviews_list if start_w <= r["date"] <= end_w]
                ratings_w = [r["rating"] for r in qrevs_w if r.get("rating") and r["rating"] > 0]
                total_pts = sum(ratings_w)
                n_rev = len(ratings_w)
                avg_now = round(total_pts / n_rev, 4) if n_rev else 0
                gap = round(4.8 * n_rev - total_pts, 1)
                dist_w = Counter(ratings_w)
                needed_5 = 0
                test_pts, test_n = total_pts, n_rev
                while test_n > 0 and test_pts / test_n < 4.8:
                    test_pts += 5
                    test_n += 1
                    needed_5 += 1
                    if needed_5 > 50:
                        break
                bad_revs = []
                for r in qrevs_w:
                    if r.get("rating") and r["rating"] < 5:
                        bad_revs.append({
                            "date": r["date"],
                            "rating": r["rating"],
                            "comment": (r.get("comment") or "")[:100],
                        })
                bad_revs.sort(key=lambda x: x["rating"])
                # Reservas en la ventana que ya hicieron checkout pero no dejaron review
                from datetime import timedelta
                review_dates = set(r["date"] for r in qrevs_w)
                stays_in_window = []
                for r in reservas:
                    ci = r.get("checkin")
                    if not ci or not r.get("code"):
                        continue
                    co_date = (dt2.strptime(ci, "%Y-%m-%d") + timedelta(days=r["nights"])).strftime("%Y-%m-%d")
                    # Stay falls in window if checkout is within window period
                    if start_w <= co_date <= end_w and co_date <= today_str:
                        stays_in_window.append({"guest": r.get("guest", "?"), "checkin": ci, "nights": r["nights"], "checkout": co_date})
                # Estimated pending = stays - reviews (approximate, not exact match)
                pending_reviews = max(0, len(stays_in_window) - n_rev)

                eval_dt = dt2.strptime(eval_date, "%Y-%m-%d")
                days_left = (eval_dt - now).days
                future_sh.append({
                    "label": label_w,
                    "eval_date": eval_date,
                    "days_left": days_left,
                    "window": f"{start_w} → {end_w}",
                    "n": n_rev,
                    "total_pts": total_pts,
                    "rating": round(avg_now, 2),
                    "rating_exact": round(avg_now, 4),
                    "gap": gap,
                    "needed_5": needed_5,
                    "is_super": avg_now >= 4.8,
                    "dist": {str(k): v for k, v in dist_w.items()},
                    "bad_reviews": bad_revs[:10],
                    "pending": pending_reviews,
                    "if_pending_5": round((total_pts + 5 * pending_reviews) / (n_rev + pending_reviews), 4) if pending_reviews > 0 and n_rev > 0 else avg_now,
                })
    next_sh = future_sh[0] if future_sh else None

    rev_by_year = {}
    for y in active:
        sy = str(y)
        yr = [r for r in reviews_list if r["date"][:4] == sy]
        if not yr:
            rev_by_year[sy] = {"General": 0, "n": 0}
            for ck in cats_key:
                rev_by_year[sy][ck] = 0
            continue
        gen = [r["rating"] for r in yr if r.get("rating") and r["rating"] > 0]
        rev_by_year[sy] = {
            "General": round(sum(gen) / len(gen), 2) if gen else 0,
            "n": len(yr),
        }
        for ck in cats_key:
            vs = [r[ck] for r in yr if r.get(ck) and r[ck] > 0]
            rev_by_year[sy][ck] = round(sum(vs) / len(vs), 2) if vs else 0

    # Review cards (global)
    rcards = ""
    for c in cats:
        v = rg.get(c, 0)
        col = "#22c55e" if v >= 4.8 else "#f59e0b" if v >= 4.5 else "#ef4444"
        rcards += f'<div class="rv"><div class="rs" style="color:{col}">{v:.2f}</div><div class="rl">{c}</div></div>'

    html = f"""<!DOCTYPE html>
<html lang="es">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>CSJ Airbnb — CEO Dashboard</title>
<script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.1/dist/chart.umd.min.js"></script>
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
:root {{ --bg:#0f172a; --c:#1e293b; --b:#334155; --t:#f1f5f9; --m:#94a3b8; --a:#3b82f6; --g:#22c55e; --r:#ef4444; }}
* {{ margin:0;padding:0;box-sizing:border-box; }}
body {{ font-family:'Inter',sans-serif; background:var(--bg); color:var(--t); padding:20px 24px; max-width:100%; overflow-x:hidden; }}

/* Header + Filters */
.top {{ display:flex; justify-content:space-between; align-items:center; flex-wrap:wrap; gap:12px; margin-bottom:20px; padding-bottom:16px; border-bottom:1px solid var(--b); }}
.top h1 {{ font-size:24px; font-weight:800; }} .top h1 span {{ color:var(--a); }}
.top .sub {{ color:var(--m); font-size:12px; }}
.filters {{ display:flex; gap:8px; align-items:center; flex-wrap:wrap; }}
.filters label {{ color:var(--m); font-size:11px; font-weight:600; text-transform:uppercase; letter-spacing:.5px; }}
.filters select, .filters button {{
  background:var(--c); color:var(--t); border:1px solid var(--b); border-radius:8px;
  padding:6px 12px; font-size:12px; font-family:inherit; cursor:pointer;
}}
.filters select:focus, .filters button:hover {{ border-color:var(--a); outline:none; }}
.filters button.active {{ background:var(--a); border-color:var(--a); }}

/* KPIs */
.kpis {{ display:grid; grid-template-columns:repeat(5,1fr); gap:14px; margin-bottom:16px; }}
.kpi {{ background:var(--c); border:1px solid var(--b); border-radius:10px; padding:16px; }}
.kpi:hover {{ border-color:var(--a); }}
.kpi .lbl {{ font-size:10px; font-weight:600; color:var(--m); text-transform:uppercase; letter-spacing:.5px; margin-bottom:5px; }}
.kpi .val {{ font-size:28px; font-weight:700; letter-spacing:-0.5px; }}
.kpi .chg {{ font-size:11px; font-weight:600; margin-top:2px; }}
.kpi .chg.up {{ color:var(--g); }} .kpi .chg.down {{ color:var(--r); }}
.kpi .det {{ font-size:9px; color:var(--m); margin-top:1px; }}
.kpi .hist {{ font-size:9px; color:var(--m); margin-top:3px; border-top:1px solid var(--b); padding-top:3px; }}
@media(max-width:900px) {{ .kpis {{ grid-template-columns:repeat(2,1fr); }} }}
@media(max-width:500px) {{ .kpis {{ grid-template-columns:1fr; }} }}
@media(max-width:600px) {{
  body {{ padding:10px 8px; }}
  .top h1 {{ font-size:18px; }}
  .kpi .val {{ font-size:22px; }}
  .sh {{ font-size:15px; margin:20px 0 8px 0; }}
  .cd {{ padding:12px; }}
  .cd h3 {{ font-size:12px; }}
  .ch.xl {{ height:260px; }} .ch.lg {{ height:240px; }} .ch.md {{ height:220px; }} .ch.sm {{ height:180px; }}
  .filters {{ gap:4px; }}
  .filters select, .filters button {{ padding:5px 8px; font-size:11px; }}
  .spark-table {{ font-size:9px; }}
  .spark-table th, .spark-table td {{ padding:2px 3px; }}
}}

/* Cards */
.row {{ display:grid; gap:16px; margin-bottom:20px; }}
.r2 {{ grid-template-columns:1fr 1fr; }} .r1 {{ grid-template-columns:1fr; }} .r3 {{ grid-template-columns:1fr 1fr 1fr; }}
@media(max-width:900px) {{ .r2,.r3 {{ grid-template-columns:1fr; }} }}
.cd {{ background:var(--c); border:1px solid var(--b); border-radius:10px; padding:18px; }}
.cd h3 {{ font-size:14px; font-weight:600; margin-bottom:2px; }}
.cd .s {{ font-size:10px; color:var(--m); margin-bottom:12px; }}
.ch {{ position:relative; width:100%; }}
.ch.xl {{ height:380px; }} .ch.lg {{ height:320px; }} .ch.md {{ height:280px; }} .ch.sm {{ height:220px; }}

/* Section headers */
.sh {{ font-size:18px; font-weight:700; margin:28px 0 12px 0; padding-top:16px; border-top:1px solid var(--b); }}
.sh span {{ color:var(--a); font-weight:400; font-size:12px; margin-left:8px; }}

/* Heatmap reimagined as sparkline table */
.spark-table {{ width:100%; border-collapse:collapse; font-size:11px; }}
.spark-table th {{ color:var(--m); font-size:9px; font-weight:600; text-transform:uppercase; padding:4px 6px; text-align:center; }}
.spark-table td {{ padding:4px 6px; text-align:center; }}
.spark-table .yr {{ color:var(--m); font-weight:600; text-align:left; white-space:nowrap; }}
.spark-table .bar {{ height:20px; border-radius:3px; display:inline-block; vertical-align:middle; }}

/* Reviews */
.rvs {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(90px,1fr)); gap:8px; }}
.rv {{ text-align:center; padding:10px 4px; background:rgba(59,130,246,0.06); border-radius:6px; }}
.rv .rs {{ font-size:20px; font-weight:700; }}
.rv .rl {{ font-size:9px; color:var(--m); margin-top:2px; }}

.ft {{ text-align:center; color:var(--m); font-size:9px; margin-top:24px; padding-top:12px; border-top:1px solid var(--b); }}
</style>
</head>
<body>

<div class="top">
  <div>
    <h1>CSJ <span>Airbnb</span></h1>
    <div class="sub">Colonia de Sant Jordi, Mallorca &mdash; {now.strftime("%d/%m/%Y %H:%M")}</div>
  </div>
  <div class="filters">
    <label>Comparar:</label>
    <select id="fYear1">
      {"".join(f'<option value="{y}" {"selected" if y==cy else ""}>{y}</option>' for y in reversed(active))}
    </select>
    <span style="color:var(--m)">vs</span>
    <select id="fYear2">
      {"".join(f'<option value="{y}" {"selected" if y==cy-1 else ""}>{y}</option>' for y in reversed(active))}
    </select>
    <label style="margin-left:12px">Periodo:</label>
    <button class="period-btn active" data-months="12">Anual</button>
    <button class="period-btn" data-months="{cm}">A fecha</button>
  </div>
</div>

<div class="kpis" id="kpiContainer"></div>

<!-- ============================================ -->
<!-- SECTION 1: INGRESOS Y RENTABILIDAD          -->
<!-- ============================================ -->
<div class="sh">Ingresos y rentabilidad <span>Revenue &amp; Profitability</span></div>
<div class="row r2">
  <div class="cd">
    <h3>Ingresos mensuales &mdash; comparativa</h3>
    <div class="s">A&ntilde;os seleccionados + banda hist&oacute;rica (min/max)</div>
    <div class="ch xl"><canvas id="c1"></canvas></div>
  </div>
  <div class="cd">
    <h3>Evoluci&oacute;n anual de ingresos</h3>
    <div class="s">Total por a&ntilde;o con media hist&oacute;rica</div>
    <div class="ch xl"><canvas id="c2"></canvas></div>
  </div>
</div>
<div class="row r2">
  <div class="cd">
    <h3>Beneficio neto anual</h3>
    <div class="s">Ingresos &minus; costes estimados por a&ntilde;o</div>
    <div class="ch lg"><canvas id="c12"></canvas></div>
  </div>
  <div class="cd">
    <h3>Costes vs ingresos</h3>
    <div class="s">Costes totales estimados vs ingreso bruto &mdash; % coste/ingreso</div>
    <div class="ch lg"><canvas id="c13"></canvas></div>
  </div>
</div>
<div class="row r1">
  <div class="cd">
    <h3>Estacionalidad &mdash; Ingresos</h3>
    <div class="s">Distribuci&oacute;n mensual comparativa entre a&ntilde;os seleccionados</div>
    <div class="ch lg"><canvas id="c9"></canvas></div>
  </div>
</div>

<!-- ============================================ -->
<!-- SECTION 2: OCUPACIÓN                         -->
<!-- ============================================ -->
<div class="sh">Ocupaci&oacute;n <span>Occupancy</span></div>
<div class="row r2">
  <div class="cd">
    <h3>Ocupaci&oacute;n mensual &mdash; comparativa</h3>
    <div class="s">A&ntilde;os seleccionados + banda hist&oacute;rica (min/max)</div>
    <div class="ch xl"><canvas id="c3"></canvas></div>
  </div>
  <div class="cd">
    <h3>Evoluci&oacute;n anual de ocupaci&oacute;n</h3>
    <div class="s">Media anual con media hist&oacute;rica</div>
    <div class="ch xl"><canvas id="c4"></canvas></div>
  </div>
</div>
<div class="row r1">
  <div class="cd">
    <h3>Ocupaci&oacute;n mensual por a&ntilde;o</h3>
    <div class="s">Barras proporcionales &mdash; verde (&gt;80%), amarillo (50-80%), rojo (&lt;50%)</div>
    <div id="sparktable" style="margin-top:8px; overflow-x:auto;"></div>
  </div>
</div>

<!-- ============================================ -->
<!-- SECTION 3: PRECIO MEDIO                      -->
<!-- ============================================ -->
<div class="sh">Precio Medio <span>ADR</span></div>
<div class="row r2">
  <div class="cd">
    <h3>PM mensual &mdash; comparativa</h3>
    <div class="s">A&ntilde;os seleccionados + banda hist&oacute;rica (min/max)</div>
    <div class="ch xl"><canvas id="c5"></canvas></div>
  </div>
  <div class="cd">
    <h3>Evoluci&oacute;n anual de PM</h3>
    <div class="s">Media anual con media hist&oacute;rica</div>
    <div class="ch xl"><canvas id="c6"></canvas></div>
  </div>
</div>
<div class="row r1">
  <div class="cd">
    <h3>PM por banda estacional</h3>
    <div class="s">Alta (15jun-15sep) / Media (1abr-14jun, 16sep-31oct) / Baja (1nov-31mar) &mdash; &euro;/noche</div>
    <div class="ch lg"><canvas id="c14"></canvas></div>
  </div>
</div>

<!-- ============================================ -->
<!-- SECTION 4: RESUMEN COMBINADO                 -->
<!-- ============================================ -->
<div class="sh">Resumen <span>Combined</span></div>
<div class="row r1">
  <div class="cd">
    <h3>Ingresos, Ocupaci&oacute;n y PM por a&ntilde;o</h3>
    <div class="s">Barras = Ingresos (eje izdo) &mdash; L&iacute;neas = Ocupaci&oacute;n % y PM &euro;/noche (eje dcho)</div>
    <div class="ch xl"><canvas id="c7"></canvas></div>
  </div>
</div>

<!-- ============================================ -->
<!-- SECTION 5: CONVERSIÓN                        -->
<!-- ============================================ -->
<div class="sh">Conversi&oacute;n <span>Funnel</span></div>
<div class="row r2">
  <div class="cd">
    <h3>Tasa de conversi&oacute;n anual</h3>
    <div class="s">Reservas creadas / Visitas al listing &mdash; desde 2018</div>
    <div class="ch lg"><canvas id="c15"></canvas></div>
  </div>
  <div class="cd">
    <h3>Visitas y reservas mensuales (fecha de venta)</h3>
    <div class="s">Cu&aacute;ndo se reserv&oacute;, no cu&aacute;ndo se aloja &mdash; barras=visitas al listing, l&iacute;nea=reservas creadas</div>
    <div class="ch lg"><canvas id="c16"></canvas></div>
  </div>
</div>

<!-- ============================================ -->
<!-- SECTION 6: PACE & LEAD TIME                   -->
<!-- ============================================ -->
<div class="sh">Ritmo de ventas <span>Pace &amp; Lead Time</span></div>
<div class="row r2">
  <div class="cd">
    <h3>Pace Report &mdash; On The Books</h3>
    <div class="s">Ingresos vendidos a fecha equivalente: &iquest;voy por delante o por detr&aacute;s vs a&ntilde;o anterior?</div>
    <div class="ch xl"><canvas id="c17"></canvas></div>
  </div>
  <div class="cd">
    <h3>Lead Time &mdash; Antelaci&oacute;n de reserva</h3>
    <div class="s">D&iacute;as entre reserva y check-in &mdash; &iquest;qu&eacute; ventana genera m&aacute;s valor?</div>
    <div class="ch xl"><canvas id="c18"></canvas></div>
  </div>
</div>
<div class="row r1">
  <div class="cd">
    <h3>Lead Time medio por a&ntilde;o</h3>
    <div class="s">Evoluci&oacute;n: &iquest;los hu&eacute;spedes reservan con m&aacute;s o menos antelaci&oacute;n?</div>
    <div class="ch lg"><canvas id="c19"></canvas></div>
  </div>
</div>

<!-- ============================================ -->
<!-- SECTION 7: EVALUACIONES                      -->
<!-- ============================================ -->
<div class="sh">Evaluaciones <span>Reviews &amp; Superhost</span></div>
<div class="row r1">
  <div class="cd" id="nextShPanel"></div>
</div>
<div class="row r2">
  <div class="cd">
    <h3>Radar de evaluaciones</h3>
    <div class="s">Subcategor&iacute;as comparadas (escala 4-5)</div>
    <div class="ch md"><canvas id="c10"></canvas></div>
  </div>
  <div class="cd">
    <h3>Superhost &mdash; Historial trimestral</h3>
    <div class="s">Rating medio por trimestre Airbnb (ventana 365d). Verde = Superhost &mdash; Rojo = por debajo de 4.8</div>
    <div class="ch lg"><canvas id="c21"></canvas></div>
  </div>
</div>

<div class="ft">CSJ Airbnb CEO Dashboard &mdash; visualizar.py &mdash; {now.strftime("%d/%m/%Y")}</div>

<script>
Chart.defaults.color='#94a3b8';
Chart.defaults.borderColor='#334155';
Chart.defaults.font.family="'Inter',sans-serif";

const M={J(MESES)};
const GC='rgba(51,65,85,0.5)';
const PALETTE={J(palette)};
const ALL_ING={J(all_ing)};
const ALL_OCU={J(all_ocu)};
const ALL_PM={J(all_pm)};
const ANN_ING={J(ann_ing)};
const ANN_OCU={J(ann_ocu)};
const ANN_PM={J(ann_pm)};
const ACTIVE={J([str(y) for y in active])};
const HMIN={J(hmin)};
const HMAX={J(hmax)};
const HAVG={J(havg)};
const HMIN_OCU={J(hmin_ocu)};
const HMAX_OCU={J(hmax_ocu)};
const HAVG_OCU={J(havg_ocu)};
const HMIN_PM={J(hmin_pm)};
const HMAX_PM={J(hmax_pm)};
const HAVG_PM={J(havg_pm)};
const RES_Y={J(res_y)};
const RES_I={J(res_i)};
const RES_O={J(res_o)};
const RES_P={J(res_p)};
const COSTES_ANN={J(costes_ann)};
const NETO_ANN={J(neto_ann)};
const PM_BANDA={J(pm_banda)};
const CONV_DATA={J({str(y): conv_data[str(y)] for y in conv_years if str(y) in conv_data})};
const CONV_ANN={J(conv_ann)};
const PACE_OTB={J(pace_otb)};
const PACE_FINAL={J(pace_final)};
const LT_SUMMARY={J(lt_summary)};
const LT_AVG_YEAR={J(lt_avg_year)};
const REV_BY_YEAR={J(rev_by_year)};
const CATS_SUB={J(cats_sub)};
const CATS_KEY={J(cats_key)};
const SH_DATA={J(superhost_quarters)};
const SH_CHECKS={J(sh_checks)};
const NEXT_SH={J(next_sh)};
const FUTURE_SH={J(future_sh)};

// Globals
let charts = {{}};
let y1 = '{cy}', y2 = '{cy-1}', period = 12;

function getYears() {{ return [y1, y2]; }}

// === KPIs dinámicos ===
function drawKPIs() {{
  const ct = document.getElementById('kpiContainer');
  const d1 = ALL_ING[y1] || Array(12).fill(0);
  const d2 = ALL_ING[y2] || Array(12).fill(0);
  const o1 = ALL_OCU[y1] || Array(12).fill(0);
  const o2 = ALL_OCU[y2] || Array(12).fill(0);
  const p1 = ALL_PM[y1] || Array(12).fill(0);
  const p2 = ALL_PM[y2] || Array(12).fill(0);

  const sum = (a,n) => a.slice(0,n).reduce((s,v)=>s+v,0);
  const avg = (a,n) => {{ const vs=a.slice(0,n).filter(v=>v>0); return vs.length ? vs.reduce((s,v)=>s+v,0)/vs.length : 0; }};
  const pct = (a,b) => b ? ((a-b)/b*100) : 0;
  const fmt = (v,dec=0) => v.toLocaleString('es-ES',{{maximumFractionDigits:dec,minimumFractionDigits:dec}});

  const ing1 = sum(d1,period), ing2 = sum(d2,period);
  const ocu1 = avg(o1,period), ocu2 = avg(o2,period);

  // PM temporada alta (jun=5, jul=6, ago=7) — siempre fijo, no depende del filtro
  const pmAlta = (a) => {{ const vs=[a[5],a[6],a[7]].filter(v=>v>0); return vs.length?vs.reduce((s,v)=>s+v,0)/vs.length:0; }};
  const pm1 = pmAlta(p1), pm2 = pmAlta(p2);

  // Beneficio neto prorrateado al periodo
  const costesAnn1 = COSTES_ANN[y1] || 0;
  const costesAnn2 = COSTES_ANN[y2] || 0;
  const costesPeriod1 = Math.round(costesAnn1 * period / 12);
  const costesPeriod2 = Math.round(costesAnn2 * period / 12);
  const neto1 = Math.round(ing1 - costesPeriod1);
  const neto2 = Math.round(ing2 - costesPeriod2);
  const margen1 = ing1 > 0 ? Math.round((ing1 - costesPeriod1) / ing1 * 100) : 0;

  const periodLabel = period === 12 ? 'anual' : period+'m';
  const pmLabel = period <= 3 ? 'PM' : period <= 7 ? 'PM' : 'PM';

  function card(label, val, chg, det, histLine) {{
    const cls = chg >= 0 ? 'up' : 'down';
    const arr = chg >= 0 ? '&#9650;' : '&#9660;';
    const chgStr = isFinite(chg) && chg !== 0 ? '<div class="chg '+cls+'">'+arr+' '+Math.abs(chg).toFixed(1)+'% vs '+y2+'</div>' : '';
    const histStr = histLine ? '<div class="hist">'+histLine+'</div>' : '';
    return '<div class="kpi"><div class="lbl">'+label+'</div><div class="val">'+val+'</div>'+chgStr+'<div class="det">'+det+'</div>'+histStr+'</div>';
  }}

  let h = '';
  h += card('Ingresos '+periodLabel+' '+y1, fmt(ing1)+'€', pct(ing1,ing2),
    y2+': '+fmt(ing2)+'€', '');
  h += card('Ocupaci&oacute;n '+periodLabel+' '+y1, ocu1.toFixed(1)+'%', pct(ocu1,ocu2),
    y2+': '+ocu2.toFixed(1)+'%', '');
  // PM medio global
  const pmAvg = (a) => {{ const vs=a.filter(v=>v>0); return vs.length?vs.reduce((s,v)=>s+v,0)/vs.length:0; }};
  const pmGlobal1 = pmAvg(p1), pmGlobal2 = pmAvg(p2);
  const pmB1 = PM_BANDA[y1] || {{alta:0,media:0,baja:0}};
  const pmB2 = PM_BANDA[y2] || {{alta:0,media:0,baja:0}};
  const pmChg = pct(pmGlobal1, pmGlobal2);
  const pmCls = pmChg >= 0 ? 'up' : 'down';
  const pmArr = pmChg >= 0 ? '&#9650;' : '&#9660;';
  const pmChgStr = isFinite(pmChg) && pmChg !== 0 ? '<div class="chg '+pmCls+'">'+pmArr+' '+Math.abs(pmChg).toFixed(1)+'% vs '+y2+'</div>' : '';
  function pmBlock(label, col, v1, v2) {{
    const d = v2 > 0 ? ((v1-v2)/v2*100) : 0;
    const dc = d >= 0 ? '#22c55e' : '#ef4444';
    const sign = d >= 0 ? '+' : '';
    const dStr = v2 > 0 ? '<div style="font-size:10px;color:'+dc+'">'+sign+d.toFixed(0)+'%</div>' : '';
    return '<div style="flex:1;text-align:center">'
      +'<div style="font-size:20px;font-weight:700;color:'+col+'">'+v1.toFixed(0)+'€</div>'
      +'<div style="font-size:9px;color:var(--m);margin:2px 0">'+label+'</div>'
      +dStr
      +'</div>';
  }}
  h += '<div class="kpi"><div class="lbl">PM '+y1+'</div>'
    +'<div style="display:flex;gap:2px;margin-top:8px">'
    +pmBlock('Alta','#ef4444',pmB1.alta,pmB2.alta)
    +'<div style="border-left:1px solid var(--b)"></div>'
    +pmBlock('Media','#f59e0b',pmB1.media,pmB2.media)
    +'<div style="border-left:1px solid var(--b)"></div>'
    +pmBlock('Baja','#3b82f6',pmB1.baja,pmB2.baja)
    +'</div></div>';

  // Pace KPI
  const otb1 = (PACE_OTB[y1]||Array(12).fill(0)).slice(0,period).reduce((a,b)=>a+b,0);
  const otb2 = (PACE_OTB[y2]||Array(12).fill(0)).slice(0,period).reduce((a,b)=>a+b,0);
  const fin2Total = (PACE_FINAL[y2]||Array(12).fill(0)).slice(0,period).reduce((a,b)=>a+b,0);
  const paceDelta = otb2 > 0 ? ((otb1 - otb2) / otb2 * 100) : 0;
  const paceSign = paceDelta >= 0 ? '+' : '';
  const paceCol = paceDelta >= 0 ? 'var(--g)' : 'var(--r)';
  const paceCapt = fin2Total > 0 ? Math.round(otb1/fin2Total*100) : 0;
  h += '<div class="kpi"><div class="lbl">Pace vs '+y2+'</div><div class="val" style="color:'+paceCol+'">'+paceSign+paceDelta.toFixed(1)+'%</div><div class="det">'+fmt(otb1)+'€ vs '+fmt(otb2)+'€ a misma fecha</div><div class="hist">'+paceCapt+'% del total final '+y2+' ('+fmt(fin2Total)+'€)</div></div>';

  // Rating Superhost — próximo trimestre
  const shd = FUTURE_SH && FUTURE_SH.length ? FUTURE_SH[0] : null;
  if(shd) {{
    const shCol = shd.is_super ? '#22c55e' : '#ef4444';
    const shIcon = shd.is_super ? '&#x2705;' : '&#x26A0;&#xFE0F;';
    const shStatus = shd.is_super ? 'Superhost' : 'En riesgo';
    const shDiff = (shd.rating_exact - 4.8).toFixed(2);
    const shSign = shd.rating_exact >= 4.8 ? '+' : '';
    const pendTxt = shd.pending > 0 ? '<div style="font-size:9px;color:var(--m);margin-top:3px;border-top:1px solid var(--b);padding-top:3px">'+shd.pending+' pendientes &rarr; si 5&#9733;: <b style="color:'+(shd.if_pending_5>=4.8?'#22c55e':'#f59e0b')+'">'+shd.if_pending_5.toFixed(2)+'</b></div>' : '';
    h += '<div class="kpi"><div class="lbl">Rating '+shd.label+'</div><div class="val" style="color:'+shCol+'">'+shd.rating_exact.toFixed(2)+'</div><div class="chg" style="color:'+shCol+'">'+shIcon+' '+shStatus+'</div><div class="det">'+shSign+shDiff+' vs 4.80 &mdash; '+shd.n+' reviews</div><div class="hist">Eval: '+shd.eval_date+' ('+shd.days_left+'d)</div>'+pendTxt+'</div>';
  }}

  ct.innerHTML = h;
}}

const COL_Y1 = '#3b82f6';  // azul fuerte — año principal
const COL_Y2 = '#f97316';  // naranja — año comparación
function makeDatasetLine(year, data, isPrimary) {{
  const col = isPrimary ? COL_Y1 : COL_Y2;
  return {{
    label: year,
    data: data,
    borderColor: col,
    borderWidth: isPrimary ? 3 : 2,
    pointRadius: isPrimary ? 4 : 2,
    pointBackgroundColor: col,
    tension: 0.3,
    fill: false,
  }};
}}

// === Banda histórica (reutilizable) ===
function bandDatasets(hmax, hmin, havg, n) {{
  return [
    {{ label:'Rango hist.', data:hmax.slice(0,n), borderColor:'transparent', backgroundColor:'rgba(251,191,36,0.08)', fill:'+1', pointRadius:0, pointHitRadius:0, order:10 }},
    {{ label:'_min', data:hmin.slice(0,n), borderColor:'transparent', backgroundColor:'transparent', fill:false, pointRadius:0, pointHitRadius:0, order:10 }},
    {{ label:'Media hist.', data:havg.slice(0,n), borderColor:'rgba(251,191,36,0.7)', borderDash:[6,3], borderWidth:2, pointRadius:0, pointHitRadius:0, fill:false, order:9 }},
  ];
}}
function bandLegendFilter(item) {{ return item.text && item.text !== '_min'; }}

// === C1: Ingresos mensuales comparativa + banda ===
function drawC1() {{
  if(charts.c1) charts.c1.destroy();
  const labels = M.slice(0, period);
  charts.c1 = new Chart(document.getElementById('c1'), {{
    type:'line',
    data: {{
      labels,
      datasets: [
        ...bandDatasets(HMAX, HMIN, HAVG, period),
        makeDatasetLine(y2, (ALL_ING[y2]||Array(12).fill(0)).slice(0,period), false),
        makeDatasetLine(y1, (ALL_ING[y1]||Array(12).fill(0)).slice(0,period), true),
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,padding:12,font:{{size:10}},filter:bandLegendFilter}}}}, tooltip:{{filter:t=>t.dataset.label!=='_min',callbacks:{{label:c=>c.dataset.label+': '+c.parsed.y.toLocaleString('es-ES',{{maximumFractionDigits:0}})+'€'}}}} }},
      scales:{{ y:{{ticks:{{callback:v=>v.toLocaleString('es-ES')+'€'}},grid:{{color:GC}}}}, x:{{grid:{{display:false}}}} }}
    }}
  }});
}}

// === C2: Ingresos anuales ===
function drawC2() {{
  if(charts.c2) charts.c2.destroy();
  const yrs = ACTIVE;
  const vals = yrs.map(y => ANN_ING[y]||0);
  const cols = yrs.map(y => (y===y1||y===y2) ? PALETTE[y] : 'rgba(148,163,184,0.3)');
  const avgI = vals.filter(v=>v>0);
  const meanI = avgI.length ? avgI.reduce((a,b)=>a+b,0)/avgI.length : 0;
  charts.c2 = new Chart(document.getElementById('c2'), {{
    type:'bar',
    data: {{ labels:yrs, datasets:[
      {{ data:vals, backgroundColor:cols, borderRadius:6, borderSkipped:false }},
      {{ label:'Media: '+meanI.toLocaleString('es-ES',{{maximumFractionDigits:0}})+'€', data:Array(yrs.length).fill(meanI), type:'line', borderColor:'rgba(251,191,36,0.6)', borderDash:[6,4], borderWidth:1.5, pointRadius:0, fill:false }}
    ] }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}},filter:i=>i.text&&i.text.startsWith('Media')}}}}, tooltip:{{callbacks:{{label:c=>c.parsed.y.toLocaleString('es-ES',{{maximumFractionDigits:0}})+'€'}}}} }},
      scales:{{ y:{{ticks:{{callback:v=>(v/1000).toFixed(0)+'k€'}},grid:{{color:GC}}}}, x:{{grid:{{display:false}}}} }}
    }}
  }});
}}

// === C3: Ocupación mensual ===
function drawC3() {{
  if(charts.c3) charts.c3.destroy();
  const labels = M.slice(0,period);
  charts.c3 = new Chart(document.getElementById('c3'), {{
    type:'line',
    data: {{
      labels,
      datasets: [
        ...bandDatasets(HMAX_OCU, HMIN_OCU, HAVG_OCU, period),
        makeDatasetLine(y2, (ALL_OCU[y2]||Array(12).fill(0)).slice(0,period), false),
        makeDatasetLine(y1, (ALL_OCU[y1]||Array(12).fill(0)).slice(0,period), true),
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,padding:12,font:{{size:10}},filter:bandLegendFilter}}}}, tooltip:{{filter:t=>t.dataset.label!=='_min',callbacks:{{label:c=>c.dataset.label+': '+c.parsed.y.toFixed(1)+'%'}}}} }},
      scales:{{ y:{{max:100,ticks:{{callback:v=>v+'%'}},grid:{{color:GC}}}}, x:{{grid:{{display:false}}}} }}
    }}
  }});
}}

// === C4: Ocupación anual ===
function drawC4() {{
  if(charts.c4) charts.c4.destroy();
  const yrs = ACTIVE;
  const vals = yrs.map(y => ANN_OCU[y]||0);
  const cols = yrs.map(y => (y===y1||y===y2) ? PALETTE[y] : 'rgba(148,163,184,0.3)');
  const avgO = vals.filter(v=>v>0);
  const meanO = avgO.length ? avgO.reduce((a,b)=>a+b,0)/avgO.length : 0;
  charts.c4 = new Chart(document.getElementById('c4'), {{
    type:'bar',
    data: {{ labels:yrs, datasets:[
      {{ data:vals, backgroundColor:cols, borderRadius:6, borderSkipped:false }},
      {{ label:'Media: '+meanO.toFixed(1)+'%', data:Array(yrs.length).fill(meanO), type:'line', borderColor:'rgba(251,191,36,0.6)', borderDash:[6,4], borderWidth:1.5, pointRadius:0, fill:false }}
    ] }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}},filter:i=>i.text&&i.text.startsWith('Media')}}}}, tooltip:{{callbacks:{{label:c=>c.parsed.y.toFixed(1)+'%'}}}} }},
      scales:{{ y:{{max:100,ticks:{{callback:v=>v+'%'}},grid:{{color:GC}}}}, x:{{grid:{{display:false}}}} }}
    }}
  }});
}}

// === C5: PM mensual ===
function drawC5() {{
  if(charts.c5) charts.c5.destroy();
  const labels = M.slice(0,period);
  charts.c5 = new Chart(document.getElementById('c5'), {{
    type:'line',
    data: {{
      labels,
      datasets: [
        ...bandDatasets(HMAX_PM, HMIN_PM, HAVG_PM, period),
        makeDatasetLine(y2, (ALL_PM[y2]||Array(12).fill(0)).slice(0,period), false),
        makeDatasetLine(y1, (ALL_PM[y1]||Array(12).fill(0)).slice(0,period), true),
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,padding:12,font:{{size:10}},filter:bandLegendFilter}}}}, tooltip:{{filter:t=>t.dataset.label!=='_min',callbacks:{{label:c=>c.dataset.label+': '+c.parsed.y.toFixed(1)+'€'}}}} }},
      scales:{{ y:{{ticks:{{callback:v=>v+'€'}},grid:{{color:GC}}}}, x:{{grid:{{display:false}}}} }}
    }}
  }});
}}

// === C6: PM anual ===
function drawC6() {{
  if(charts.c6) charts.c6.destroy();
  const yrs = ACTIVE;
  const vals = yrs.map(y => ANN_PM[y]||0);
  const cols = yrs.map(y => (y===y1||y===y2) ? PALETTE[y] : 'rgba(148,163,184,0.3)');
  const avgP = vals.filter(v=>v>0);
  const meanP = avgP.length ? avgP.reduce((a,b)=>a+b,0)/avgP.length : 0;
  charts.c6 = new Chart(document.getElementById('c6'), {{
    type:'bar',
    data: {{ labels:yrs, datasets:[
      {{ data:vals, backgroundColor:cols, borderRadius:6, borderSkipped:false }},
      {{ label:'Media: '+meanP.toFixed(1)+'€', data:Array(yrs.length).fill(meanP), type:'line', borderColor:'rgba(251,191,36,0.6)', borderDash:[6,4], borderWidth:1.5, pointRadius:0, fill:false }}
    ] }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}},filter:i=>i.text&&i.text.startsWith('Media')}}}}, tooltip:{{callbacks:{{label:c=>c.parsed.y.toFixed(1)+'€/noche'}}}} }},
      scales:{{ y:{{ticks:{{callback:v=>v+'€'}},grid:{{color:GC}}}}, x:{{grid:{{display:false}}}} }}
    }}
  }});
}}

// === C7: Resumen combinado ===
function drawC7() {{
  if(charts.c7) charts.c7.destroy();
  charts.c7 = new Chart(document.getElementById('c7'), {{
    type:'bar',
    data: {{
      labels: RES_Y,
      datasets: [
        {{ label:'Ingresos (€)', data:RES_I, backgroundColor:'rgba(59,130,246,0.6)', borderRadius:6, borderSkipped:false, yAxisID:'y', order:2 }},
        {{ label:'Ocupación (%)', data:RES_O, type:'line', borderColor:'#22c55e', borderWidth:2.5, pointRadius:4, pointBackgroundColor:'#22c55e', tension:0.3, fill:false, yAxisID:'y1', order:1 }},
        {{ label:'PM (€/noche)', data:RES_P, type:'line', borderColor:'#f59e0b', borderWidth:2.5, pointRadius:4, pointBackgroundColor:'#f59e0b', tension:0.3, fill:false, yAxisID:'y1', order:0 }},
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins: {{
        legend:{{position:'top',labels:{{usePointStyle:true,padding:14}}}},
        tooltip:{{ callbacks:{{ label:function(c){{
          if(c.dataset.yAxisID==='y') return c.dataset.label+': '+c.parsed.y.toLocaleString('es-ES',{{maximumFractionDigits:0}})+'€';
          if(c.dataset.label.includes('Ocu')) return c.dataset.label+': '+c.parsed.y.toFixed(1)+'%';
          return c.dataset.label+': '+c.parsed.y.toFixed(1)+'€';
        }} }} }}
      }},
      scales: {{
        y: {{ position:'left', title:{{display:true,text:'Ingresos €',color:'#60a5fa'}}, ticks:{{callback:v=>(v/1000).toFixed(0)+'k€',color:'#60a5fa'}}, grid:{{color:GC}} }},
        y1: {{ position:'right', title:{{display:true,text:'Ocupación % / PM €',color:'#94a3b8'}}, ticks:{{color:'#94a3b8'}}, grid:{{drawOnChartArea:false}}, min:0, max:100 }},
        x: {{ grid:{{display:false}} }}
      }}
    }}
  }});
}}

// === C8: RevPAR ===
// === C9: Radar estacionalidad y1 vs y2 ===
function drawC9() {{
  if(charts.c9) charts.c9.destroy();
  charts.c9 = new Chart(document.getElementById('c9'), {{
    type:'radar',
    data: {{
      labels:M,
      datasets: [
        {{ label:y1, data:ALL_ING[y1]||Array(12).fill(0), borderColor:PALETTE[y1], backgroundColor:PALETTE[y1]+'22', borderWidth:2, pointRadius:3, pointBackgroundColor:PALETTE[y1] }},
        {{ label:y2, data:ALL_ING[y2]||Array(12).fill(0), borderColor:PALETTE[y2], backgroundColor:PALETTE[y2]+'11', borderWidth:1.5, borderDash:[4,4], pointRadius:2, pointBackgroundColor:PALETTE[y2] }},
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true}}}} }},
      scales:{{ r:{{ beginAtZero:true, ticks:{{display:false}}, grid:{{color:GC}}, pointLabels:{{font:{{size:10}}}} }} }}
    }}
  }});
}}

// === Spark table (occupancy visual) ===
function drawSpark() {{
  const ct = document.getElementById('sparktable');
  let h = '<table class="spark-table"><thead><tr><th></th>';
  M.forEach(m => h += '<th>'+m+'</th>');
  h += '<th>Media</th></tr></thead><tbody>';
  ACTIVE.slice().reverse().forEach(y => {{
    const d = ALL_OCU[y] || Array(12).fill(0);
    const avg = d.filter(v=>v>0);
    const mean = avg.length ? (avg.reduce((a,b)=>a+b,0)/avg.length).toFixed(1) : '0';
    h += '<tr><td class="yr" style="color:'+PALETTE[y]+'">'+y+'</td>';
    d.forEach(v => {{
      const w = Math.max(v, 0);
      const col = v >= 80 ? '#22c55e' : v >= 50 ? '#eab308' : v > 0 ? '#ef4444' : '#1e293b';
      h += '<td><div class="bar" style="width:'+w+'%;background:'+col+'">&nbsp;</div></td>';
    }});
    h += '<td style="font-weight:600;color:'+(parseFloat(mean)>=80?'#22c55e':parseFloat(mean)>=50?'#eab308':'#ef4444')+'">'+mean+'%</td>';
    h += '</tr>';
  }});
  h += '</tbody></table>';
  ct.innerHTML = h;
}}

// === Review cards by year ===
let shIdx = 0;
function drawNextSH(idx) {{
  if(idx !== undefined) shIdx = idx;
  const ct = document.getElementById('nextShPanel');
  if(!FUTURE_SH || !FUTURE_SH.length) {{ ct.innerHTML = '<p style="color:var(--m)">Sin datos</p>'; return; }}
  const d = FUTURE_SH[shIdx];

  // Quarter selector buttons
  let hBtns = '<div style="display:flex;gap:6px;margin-bottom:12px">';
  FUTURE_SH.forEach((q,i) => {{
    const active = i === shIdx;
    const bgc = active ? (q.is_super ? '#22c55e' : '#ef4444') : 'var(--c)';
    const bdc = active ? bgc : 'var(--b)';
    const txc = active ? '#fff' : 'var(--t)';
    hBtns += '<button onclick="drawNextSH('+i+')" style="background:'+bgc+';color:'+txc+';border:1px solid '+bdc+';border-radius:8px;padding:6px 14px;font-size:12px;font-family:inherit;cursor:pointer;font-weight:'+(active?'700':'400')+'">'+q.label+'</button>';
  }});
  hBtns += '</div>';
  const col = d.is_super ? '#22c55e' : '#ef4444';
  const icon = d.is_super ? '&#x2705;' : '&#x26A0;&#xFE0F;';
  const statusTxt = d.is_super ? 'SUPERHOST' : 'EN RIESGO';
  const gap = d.gap;
  const dist = d.dist || {{}};

  let h = hBtns;
  h += '<h3>Revisi&oacute;n Superhost &mdash; '+d.label+'</h3>';
  h += '<div class="s">Evaluaci&oacute;n: '+d.eval_date+' (faltan '+d.days_left+' d&iacute;as) &mdash; Ventana: '+d.window+'</div>';

  // Main rating display
  h += '<div style="display:flex;align-items:center;gap:24px;margin:16px 0;flex-wrap:wrap">';
  h += '<div style="text-align:center"><div style="font-size:48px;font-weight:800;color:'+col+'">'+d.rating_exact.toFixed(2)+'</div>';
  h += '<div style="font-size:13px;font-weight:600;color:'+col+'">'+icon+' '+statusTxt+'</div></div>';

  // Stats
  h += '<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;flex:1;min-width:250px">';
  h += '<div style="background:rgba(59,130,246,0.08);border-radius:8px;padding:12px;text-align:center"><div style="font-size:24px;font-weight:700">'+d.n+'</div><div style="font-size:10px;color:var(--m)">Reviews</div></div>';
  h += '<div style="background:rgba(59,130,246,0.08);border-radius:8px;padding:12px;text-align:center"><div style="font-size:24px;font-weight:700">'+d.total_pts+'</div><div style="font-size:10px;color:var(--m)">Puntos totales</div></div>';
  // Pending reviews
  const pend = d.pending || 0;
  h += '<div style="background:rgba(251,191,36,0.1);border-radius:8px;padding:12px;text-align:center"><div style="font-size:24px;font-weight:700;color:#f59e0b">'+pend+'</div><div style="font-size:10px;color:#f59e0b">Pendientes evaluar</div></div>';

  if(!d.is_super) {{
    h += '<div style="background:rgba(239,68,68,0.1);border-radius:8px;padding:12px;text-align:center"><div style="font-size:24px;font-weight:700;color:#ef4444">'+d.needed_5+'</div><div style="font-size:10px;color:#ef4444">Reviews 5&#9733; necesarias</div></div>';
  }} else {{
    const margin = (d.rating_exact - 4.8).toFixed(2);
    h += '<div style="background:rgba(34,197,94,0.1);border-radius:8px;padding:12px;text-align:center"><div style="font-size:24px;font-weight:700;color:#22c55e">+'+margin+'</div><div style="font-size:10px;color:#22c55e">Margen sobre 4.80</div></div>';
  }}
  h += '</div></div>';

  // Pending simulation
  if(pend > 0) {{
    const pend5 = (d.total_pts + 5 * pend) / (d.n + pend);
    const pend4 = (d.total_pts + 4 * pend) / (d.n + pend);
    const pendMix = (d.total_pts + 5 * Math.ceil(pend*0.8) + 4 * Math.floor(pend*0.2)) / (d.n + pend);
    h += '<div style="margin:8px 0;padding:10px;background:rgba(251,191,36,0.06);border:1px solid rgba(251,191,36,0.2);border-radius:8px">';
    h += '<div style="font-size:11px;font-weight:600;color:#f59e0b;margin-bottom:4px">SI LAS '+pend+' PENDIENTES EVAL&Uacute;AN:</div>';
    h += '<div style="font-size:11px;color:var(--t);margin:2px 0">'+(pend5>=4.8?'&#x2705;':'&#x274C;')+' Todas 5&#9733; &rarr; <b>'+pend5.toFixed(4)+'</b></div>';
    h += '<div style="font-size:11px;color:var(--t);margin:2px 0">'+(pendMix>=4.8?'&#x2705;':'&#x274C;')+' 80% de 5&#9733; + 20% de 4&#9733; &rarr; <b>'+pendMix.toFixed(4)+'</b></div>';
    h += '<div style="font-size:11px;color:var(--t);margin:2px 0">'+(pend4>=4.8?'&#x2705;':'&#x274C;')+' Todas 4&#9733; &rarr; <b>'+pend4.toFixed(4)+'</b></div>';
    h += '</div>';
  }}

  // Distribution bar
  const stars = [5,4,3,2,1];
  const total = stars.reduce((s,k) => s + (dist[k]||0), 0);
  h += '<div style="margin:12px 0"><div style="font-size:11px;font-weight:600;color:var(--m);margin-bottom:6px">DISTRIBUCI&Oacute;N</div>';
  const barCols = {{5:'#22c55e',4:'#84cc16',3:'#f59e0b',2:'#f97316',1:'#ef4444'}};
  stars.forEach(s => {{
    const cnt = dist[s] || 0;
    const pctW = total > 0 ? (cnt/total*100) : 0;
    h += '<div style="display:flex;align-items:center;gap:8px;margin:3px 0">';
    h += '<div style="width:20px;font-size:11px;font-weight:600;text-align:right">'+s+'&#9733;</div>';
    h += '<div style="flex:1;background:var(--b);border-radius:4px;height:14px;overflow:hidden"><div style="width:'+pctW+'%;height:100%;background:'+barCols[s]+';border-radius:4px"></div></div>';
    h += '<div style="width:30px;font-size:11px;color:var(--m);text-align:right">'+cnt+'</div>';
    h += '</div>';
  }});
  h += '</div>';

  // Bad reviews
  const bad = d.bad_reviews || [];
  if(bad.length > 0) {{
    h += '<div style="margin-top:12px"><div style="font-size:11px;font-weight:600;color:var(--m);margin-bottom:6px">REVIEWS QUE PENALIZAN (< 5&#9733;)</div>';
    h += '<div style="max-height:200px;overflow-y:auto">';
    bad.forEach(r => {{
      const rc = r.rating <= 3 ? '#ef4444' : '#f59e0b';
      h += '<div style="display:flex;gap:8px;padding:6px 0;border-bottom:1px solid var(--b);font-size:11px">';
      h += '<div style="white-space:nowrap;color:var(--m)">'+r.date+'</div>';
      h += '<div style="font-weight:700;color:'+rc+'">'+r.rating+'&#9733;</div>';
      h += '<div style="color:var(--m);overflow:hidden;text-overflow:ellipsis;white-space:nowrap">'+r.comment+'</div>';
      h += '</div>';
    }});
    h += '</div></div>';
  }}

  // Simulation
  if(!d.is_super) {{
    h += '<div style="margin-top:12px;padding:12px;background:rgba(239,68,68,0.06);border:1px solid rgba(239,68,68,0.2);border-radius:8px">';
    h += '<div style="font-size:11px;font-weight:600;color:#ef4444;margin-bottom:6px">&#x1F4CA; SIMULACI&Oacute;N</div>';
    for(let extra = 1; extra <= 5; extra++) {{
      const newAvg = (d.total_pts + 5*extra) / (d.n + extra);
      const ok = newAvg >= 4.8;
      const ic = ok ? '&#x2705;' : '&#x274C;';
      h += '<div style="font-size:11px;color:var(--t);margin:2px 0">'+ic+' +'+extra+' review(s) de 5&#9733; &rarr; <b>'+newAvg.toFixed(4)+'</b></div>';
    }}
    h += '</div>';
  }}

  ct.innerHTML = h;
}}

// === C10: Reviews radar y1 vs y2 ===
function drawC10() {{
  if(charts.c10) charts.c10.destroy();
  const r1 = REV_BY_YEAR[y1] || {{}};
  const r2 = REV_BY_YEAR[y2] || {{}};
  const d1 = CATS_KEY.map(c => r1[c] || 0);
  const d2 = CATS_KEY.map(c => r2[c] || 0);
  const ds = [
    {{ label:y1, data:d1, borderColor:PALETTE[y1], backgroundColor:(PALETTE[y1]||'#3b82f6')+'22', borderWidth:2, pointRadius:4, pointBackgroundColor:PALETTE[y1] }},
  ];
  if (d2.some(v => v > 0)) {{
    ds.push({{ label:y2, data:d2, borderColor:PALETTE[y2], backgroundColor:(PALETTE[y2]||'#94a3b8')+'11', borderWidth:1.5, borderDash:[4,4], pointRadius:3, pointBackgroundColor:PALETTE[y2] }});
  }}
  charts.c10 = new Chart(document.getElementById('c10'), {{
    type:'radar',
    data: {{ labels:CATS_SUB, datasets:ds }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}}}}}} }},
      scales:{{ r:{{ min:4, max:5, ticks:{{stepSize:0.2,font:{{size:9}}}}, grid:{{color:GC}}, pointLabels:{{font:{{size:10}}}} }} }}
    }}
  }});
}}

// === C12: Beneficio neto anual ===
function drawC12() {{
  if(charts.c12) charts.c12.destroy();
  const yrs = ACTIVE.filter(y => NETO_ANN[y] !== undefined);
  const vals = yrs.map(y => NETO_ANN[y]);
  const cols = vals.map((v,i) => v >= 0 ? '#22c55e' : '#ef4444');
  const ingVals = yrs.map(y => ANN_ING[y]||0);
  charts.c12 = new Chart(document.getElementById('c12'), {{
    type:'bar',
    data: {{ labels:yrs, datasets:[
      {{ label:'Beneficio neto', data:vals, backgroundColor:cols, borderRadius:6, borderSkipped:false }},
      {{ label:'Ingreso bruto', data:ingVals, type:'line', borderColor:'rgba(148,163,184,0.4)', borderDash:[6,4], borderWidth:1.5, pointRadius:3, pointBackgroundColor:'rgba(148,163,184,0.6)', fill:false }},
    ] }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}}}}}}, tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.parsed.y.toLocaleString('es-ES',{{maximumFractionDigits:0}})+'€'}}}} }},
      scales:{{ y:{{ticks:{{callback:v=>(v/1000).toFixed(0)+'k€'}},grid:{{color:GC}}}}, x:{{grid:{{display:false}}}} }}
    }}
  }});
}}

// === C13: Costes vs ingresos ===
function drawC13() {{
  if(charts.c13) charts.c13.destroy();
  const yrs = ACTIVE.filter(y => COSTES_ANN[y] !== undefined);
  const costes = yrs.map(y => COSTES_ANN[y]);
  const ingresos = yrs.map(y => ANN_ING[y]||0);
  const pctCoste = yrs.map((y,i) => ingresos[i] > 1000 ? Math.round(costes[i]/ingresos[i]*100) : null);
  charts.c13 = new Chart(document.getElementById('c13'), {{
    type:'bar',
    data: {{ labels:yrs, datasets:[
      {{ label:'Costes', data:costes, backgroundColor:'#ef4444aa', borderRadius:6, borderSkipped:false }},
      {{ label:'Ingresos', data:ingresos, backgroundColor:'rgba(59,130,246,0.3)', borderColor:'#3b82f6', borderWidth:1.5, borderRadius:6, borderSkipped:false }},
      {{ label:'% coste/ingreso', data:pctCoste, type:'line', borderColor:'#f59e0b', borderWidth:2, pointRadius:3, pointBackgroundColor:'#f59e0b', tension:0.3, fill:false, yAxisID:'y1' }},
    ] }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins: {{
        legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}}}}}},
        tooltip:{{callbacks:{{
          label:function(c) {{
            if(c.dataset.yAxisID==='y1') return c.dataset.label+': '+c.parsed.y+'%';
            return c.dataset.label+': '+c.parsed.y.toLocaleString('es-ES',{{maximumFractionDigits:0}})+'€';
          }}
        }}}}
      }},
      scales: {{
        y: {{ ticks:{{callback:v=>(v/1000).toFixed(0)+'k€'}}, grid:{{color:GC}} }},
        y1: {{ position:'right', title:{{display:true,text:'% coste/ingreso',color:'#f59e0b'}}, ticks:{{callback:v=>v+'%',color:'#f59e0b'}}, grid:{{drawOnChartArea:false}}, min:0 }},
        x: {{ grid:{{display:false}} }}
      }}
    }}
  }});
}}

// === C14: PM por banda estacional ===
function drawC14() {{
  if(charts.c14) charts.c14.destroy();
  const yrs = ACTIVE.filter(y => PM_BANDA[y] && (PM_BANDA[y].alta > 0 || PM_BANDA[y].media > 0 || PM_BANDA[y].baja > 0));
  charts.c14 = new Chart(document.getElementById('c14'), {{
    type:'bar',
    data: {{ labels:yrs, datasets:[
      {{ label:'Alta (15jun-15sep)', data:yrs.map(y=>PM_BANDA[y].alta), backgroundColor:'#ef4444cc', borderRadius:6, borderSkipped:false }},
      {{ label:'Media (abr-jun,sep-oct)', data:yrs.map(y=>PM_BANDA[y].media), backgroundColor:'#f59e0bcc', borderRadius:6, borderSkipped:false }},
      {{ label:'Baja (nov-mar)', data:yrs.map(y=>PM_BANDA[y].baja), backgroundColor:'#3b82f6cc', borderRadius:6, borderSkipped:false }},
    ] }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}}}}}}, tooltip:{{callbacks:{{label:c=>c.dataset.label+': '+c.parsed.y.toFixed(1)+'€/noche'}}}} }},
      scales:{{ y:{{ticks:{{callback:v=>v+'€'}},grid:{{color:GC}}}}, x:{{grid:{{display:false}}}} }}
    }}
  }});
}}

// === C15: Tasa de conversión anual ===
function drawC15() {{
  if(charts.c15) charts.c15.destroy();
  const cyrs = Object.keys(CONV_ANN).sort();
  const cvrs = cyrs.map(y => CONV_ANN[y].cvr);
  const reservas = cyrs.map(y => CONV_ANN[y].r);
  charts.c15 = new Chart(document.getElementById('c15'), {{
    type:'bar',
    data: {{ labels:cyrs, datasets:[
      {{ label:'CVR %', data:cvrs, backgroundColor:cyrs.map(y=>(y===y1||y===y2)?PALETTE[y]||'#3b82f6':'rgba(148,163,184,0.3)'), borderRadius:6, borderSkipped:false, yAxisID:'y' }},
      {{ label:'Reservas', data:reservas, type:'line', borderColor:'#22c55e', borderWidth:2, pointRadius:3, pointBackgroundColor:'#22c55e', tension:0.3, fill:false, yAxisID:'y1' }},
    ] }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}}}}}}, tooltip:{{callbacks:{{label:c=>c.dataset.yAxisID==='y'?c.parsed.y.toFixed(2)+'%':c.parsed.y+' reservas'}}}} }},
      scales: {{
        y: {{ position:'left', title:{{display:true,text:'CVR %',color:'#60a5fa'}}, ticks:{{callback:v=>v.toFixed(1)+'%',color:'#60a5fa'}}, grid:{{color:GC}} }},
        y1: {{ position:'right', title:{{display:true,text:'Reservas',color:'#22c55e'}}, ticks:{{color:'#22c55e'}}, grid:{{drawOnChartArea:false}} }},
        x: {{ grid:{{display:false}} }}
      }}
    }}
  }});
}}

// === C16: Visitas y reservas mensuales ===
function drawC16() {{
  if(charts.c16) charts.c16.destroy();
  const labels = M.slice(0,period);
  const ds = [];
  [y1, y2].forEach((y,idx) => {{
    const cd = CONV_DATA[y];
    if (!cd) return;
    const alpha = idx === 0 ? 'b3' : '55';
    ds.push({{ label:'Visitas '+y, data:cd.v.slice(0,period), backgroundColor:(PALETTE[y]||'#94a3b8')+alpha, borderRadius:4, yAxisID:'y', order:2+idx }});
    ds.push({{ label:'Reservas '+y, data:cd.r.slice(0,period), type:'line', borderColor:idx===0?'#22c55e':'#22c55e88', borderWidth:idx===0?2.5:1.5, borderDash:idx===0?[]:[5,5], pointRadius:idx===0?3:2, pointBackgroundColor:idx===0?'#22c55e':'#22c55e88', tension:0.3, fill:false, yAxisID:'y1', order:idx }});
  }});
  charts.c16 = new Chart(document.getElementById('c16'), {{
    type:'bar',
    data: {{ labels, datasets:ds }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}}}}}}, tooltip:{{}} }},
      scales: {{
        y: {{ position:'left', title:{{display:true,text:'Visitas',color:'#60a5fa'}}, ticks:{{color:'#60a5fa'}}, grid:{{color:GC}} }},
        y1: {{ position:'right', title:{{display:true,text:'Reservas',color:'#22c55e'}}, ticks:{{color:'#22c55e',stepSize:1}}, grid:{{drawOnChartArea:false}} }},
        x: {{ grid:{{display:false}} }}
      }}
    }}
  }});
}}

// === C17: Pace Report — OTB by month ===
function drawC17() {{
  if(charts.c17) charts.c17.destroy();
  const labels = M.slice(0,period);
  const otb1 = (PACE_OTB[y1]||Array(12).fill(0)).slice(0,period);
  const otb2 = (PACE_OTB[y2]||Array(12).fill(0)).slice(0,period);
  const fin2 = (PACE_FINAL[y2]||Array(12).fill(0)).slice(0,period);
  // Delta % per month
  const delta = otb1.map((v,i) => otb2[i] > 0 ? ((v - otb2[i]) / otb2[i] * 100).toFixed(1) : '—');
  charts.c17 = new Chart(document.getElementById('c17'), {{
    type:'bar',
    data: {{
      labels,
      datasets: [
        {{ label:'OTB '+y1, data:otb1, backgroundColor:PALETTE[y1]+'cc', borderRadius:6, borderSkipped:false }},
        {{ label:'OTB '+y2+' (misma fecha)', data:otb2, backgroundColor:PALETTE[y2]+'88', borderRadius:6, borderSkipped:false }},
        {{ label:'Final '+y2, data:fin2, type:'line', borderColor:'rgba(148,163,184,0.5)', borderDash:[6,4], borderWidth:1.5, pointRadius:3, pointBackgroundColor:'rgba(148,163,184,0.6)', fill:false }},
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins: {{
        legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}}}}}},
        tooltip:{{callbacks:{{
          afterBody: function(items) {{
            const i = items[0].dataIndex;
            return delta[i] !== '—' ? '\\n\\u0394 vs '+y2+': '+(parseFloat(delta[i])>=0?'+':'')+delta[i]+'%' : '';
          }},
          label:c=>c.dataset.label+': '+c.parsed.y.toLocaleString('es-ES',{{maximumFractionDigits:0}})+'€'
        }}}}
      }},
      scales: {{
        y:{{ticks:{{callback:v=>(v/1000).toFixed(0)+'k€'}},grid:{{color:GC}}}},
        x:{{grid:{{display:false}}}}
      }}
    }}
  }});
}}

// === C18: Lead Time distribution + PM ===
function drawC18() {{
  if(charts.c18) charts.c18.destroy();
  const buckets = ['<7d','7-30d','30-90d','>90d'];
  const bucketLabels = ['< 7 días','7-30 días','30-90 días','> 90 días'];
  const counts = buckets.map(b => LT_SUMMARY[b].n);
  const pms = buckets.map(b => LT_SUMMARY[b].avg_pm);
  const total = counts.reduce((a,b)=>a+b,0);
  const pcts = counts.map(c => total > 0 ? Math.round(c/total*100) : 0);
  charts.c18 = new Chart(document.getElementById('c18'), {{
    type:'bar',
    data: {{
      labels: bucketLabels,
      datasets: [
        {{ label:'Reservas', data:counts, backgroundColor:['#ef4444cc','#f59e0bcc','#22c55ecc','#3b82f6cc'], borderRadius:6, borderSkipped:false, yAxisID:'y' }},
        {{ label:'PM €/noche', data:pms, type:'line', borderColor:'#f59e0b', borderWidth:2.5, pointRadius:5, pointBackgroundColor:'#f59e0b', tension:0.3, fill:false, yAxisID:'y1' }},
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins: {{
        legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}}}}}},
        tooltip:{{callbacks:{{
          label:function(c) {{
            if(c.dataset.yAxisID==='y') return c.parsed.y+' reservas ('+pcts[c.dataIndex]+'%)';
            return 'PM: '+c.parsed.y.toFixed(1)+'€/noche';
          }}
        }}}}
      }},
      scales: {{
        y: {{ position:'left', title:{{display:true,text:'Reservas',color:'#60a5fa'}}, ticks:{{color:'#60a5fa'}}, grid:{{color:GC}} }},
        y1: {{ position:'right', title:{{display:true,text:'PM €/noche',color:'#f59e0b'}}, ticks:{{color:'#f59e0b',callback:v=>v+'€'}}, grid:{{drawOnChartArea:false}} }},
        x: {{ grid:{{display:false}} }}
      }}
    }}
  }});
}}

// === C19: Lead Time trend by year ===
function drawC19() {{
  if(charts.c19) charts.c19.destroy();
  const yrs = ACTIVE.filter(y => LT_AVG_YEAR[y] && LT_AVG_YEAR[y] > 0);
  const vals = yrs.map(y => LT_AVG_YEAR[y]);
  const cols = yrs.map(y => (y===y1||y===y2) ? PALETTE[y] : 'rgba(148,163,184,0.3)');
  const avgLT = vals.filter(v=>v>0);
  const meanLT = avgLT.length ? avgLT.reduce((a,b)=>a+b,0)/avgLT.length : 0;
  charts.c19 = new Chart(document.getElementById('c19'), {{
    type:'bar',
    data: {{ labels:yrs, datasets:[
      {{ data:vals, backgroundColor:cols, borderRadius:6, borderSkipped:false }},
      {{ label:'Media: '+meanLT.toFixed(0)+' días', data:Array(yrs.length).fill(meanLT), type:'line', borderColor:'rgba(251,191,36,0.6)', borderDash:[6,4], borderWidth:1.5, pointRadius:0, fill:false }}
    ] }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      plugins:{{ legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}},filter:i=>i.text&&i.text.startsWith('Media')}}}}, tooltip:{{callbacks:{{label:c=>c.parsed.y.toFixed(0)+' días de media'}}}} }},
      scales:{{ y:{{title:{{display:true,text:'Días'}},grid:{{color:GC}}}}, x:{{grid:{{display:false}}}} }}
    }}
  }});
}}



// === C21: Superhost timeline ===
function drawC21() {{
  if(charts.c21) charts.c21.destroy();
  const nextQ = NEXT_SH ? NEXT_SH.label : null;
  const cutIdx = nextQ ? SH_CHECKS.indexOf(nextQ) : SH_CHECKS.length - 1;
  const allLabels = SH_CHECKS.slice(0, cutIdx + 1);
  const labels = allLabels.slice(-12);
  const ratings = labels.map(q => SH_DATA[q] ? SH_DATA[q].rating : null);
  const counts = labels.map(q => SH_DATA[q] ? SH_DATA[q].n : 0);
  const isSH = labels.map(q => SH_DATA[q] ? SH_DATA[q].superhost : false);
  const ptColors = ratings.map((v,i) => v === null ? 'transparent' : (isSH[i] ? '#22c55e' : '#ef4444'));
  const ptBorder = ratings.map((v,i) => v === null ? 'transparent' : (isSH[i] ? '#16a34a' : '#dc2626'));
  charts.c21 = new Chart(document.getElementById('c21'), {{
    type:'line',
    data: {{
      labels,
      datasets: [
        {{
          label:'Rating medio (365d)',
          data:ratings,
          borderColor:'#3b82f6',
          borderWidth:2.5,
          pointRadius:6,
          pointHoverRadius:8,
          pointBackgroundColor:ptColors,
          pointBorderColor:ptBorder,
          pointBorderWidth:2,
          tension:0.3,
          fill:false,
          spanGaps:true,
        }},
        {{
          label:'Umbral Superhost (4.8)',
          data:Array(labels.length).fill(4.8),
          borderColor:'rgba(239,68,68,0.5)',
          borderDash:[8,4],
          borderWidth:2,
          pointRadius:0,
          fill:{{target:'end',above:'transparent',below:'rgba(239,68,68,0.08)'}},
        }},
      ]
    }},
    options: {{
      responsive:true, maintainAspectRatio:false,
      interaction:{{mode:'index',intersect:false}},
      plugins: {{
        legend:{{position:'top',labels:{{usePointStyle:true,font:{{size:10}}}}}},
        tooltip:{{callbacks:{{
          title: function(items) {{
            const i = items[0].dataIndex;
            const q = labels[i];
            return q + (isSH[i] ? ' \\u2705 SUPERHOST' : ' \\u274c No Superhost');
          }},
          label:function(c) {{
            if(c.dataset.label.includes('Umbral')) return '';
            const i = c.dataIndex;
            const r = ratings[i];
            const n = counts[i];
            if(r===null) return '';
            const diff = (r - 4.8).toFixed(2);
            const sign = r >= 4.8 ? '+' : '';
            return ['Rating: ' + r.toFixed(2) + ' (' + sign + diff + ' vs 4.8)', 'Reviews: ' + n + ' (min 3)'];
          }}
        }}}}
      }},
      scales: {{
        y: {{
          min:4.0, max:5.0,
          ticks:{{stepSize:0.1,color:'#94a3b8',callback:v=>v.toFixed(1)}},
          grid:{{color: function(ctx) {{ return ctx.tick.value === 4.8 ? 'rgba(239,68,68,0.3)' : GC; }} }}
        }},
        x: {{ ticks:{{font:{{size:9}},maxRotation:45}}, grid:{{display:false}} }}
      }}
    }}
  }});
}}

// === DRAW ALL ===
function drawAll() {{
  drawKPIs(); drawC1(); drawC2(); drawC3(); drawC4(); drawC5(); drawC6(); drawC7(); drawC9(); drawSpark(); drawNextSH(); drawC10(); drawC12(); drawC13(); drawC14(); drawC15(); drawC16(); drawC17(); drawC18(); drawC19(); drawC21();
}}
drawAll();

// === FILTER HANDLERS ===
document.getElementById('fYear1').addEventListener('change', e => {{ y1 = e.target.value; drawAll(); }});
document.getElementById('fYear2').addEventListener('change', e => {{ y2 = e.target.value; drawAll(); }});
document.querySelectorAll('.period-btn').forEach(btn => {{
  btn.addEventListener('click', () => {{
    document.querySelectorAll('.period-btn').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    period = parseInt(btn.dataset.months);
    drawKPIs(); drawC1(); drawC3(); drawC5(); drawC9(); drawC16(); drawC17();
  }});
}});
</script>
</body>
</html>"""
    return html


def main():
    print("Cargando datos locales...")
    ing, ocu, pm, reservas = load_reservas()
    rev, reviews_list = load_reviews()
    visitas = load_visitas()
    data = {"reservas": reservas, "reviews_list": reviews_list, "visitas": visitas}
    html = build(data, ing, ocu, pm, rev)
    out = os.path.join(os.path.dirname(__file__), "dashboard.html")
    with open(out, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"\nDashboard: {out}")


if __name__ == "__main__":
    main()
