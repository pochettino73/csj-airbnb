#!/usr/bin/env python3
"""
CSJ — Validador de datos
Se ejecuta automáticamente desde visualizar.py.
También se puede lanzar standalone: python validar.py
"""

import json
import os
import sys
import calendar
from datetime import datetime, date

ROOT = os.path.dirname(os.path.dirname(__file__))  # CSJ/
BASE = os.path.join(ROOT, "datos")


def _p(msg):
    """Print seguro en terminales con encoding limitado (ej. cp1252)."""
    print(msg.encode(sys.stdout.encoding or "utf-8", errors="replace").decode(sys.stdout.encoding or "utf-8"))


def _load(fname):
    with open(os.path.join(BASE, fname), encoding="utf-8") as f:
        return json.load(f)


def validar(verbose=True):
    errors = []
    warnings = []

    try:
        reservas = _load("reservas.json")
    except Exception as e:
        errors.append(f"No se puede leer reservas.json: {e}")
        return errors, warnings

    try:
        reviews = _load("reviews.json")
    except Exception as e:
        warnings.append(f"No se puede leer reviews.json: {e}")
        reviews = []

    confirmed = [r for r in reservas if r.get("status", "confirmed") == "confirmed"]
    cancelled = [r for r in reservas if r.get("status") == "cancelled"]

    # ── 1. CAMPOS OBLIGATORIOS ────────────────────────────────────────────────
    required = ["year", "month", "nights", "total"]
    for i, r in enumerate(reservas):
        for campo in required:
            if campo not in r:
                errors.append(f"Registro #{i} falta campo '{campo}': {r.get('code','sin code')} {r.get('guest','')}")

    # ── 2. CROSS-MONTH: prorrateo de noches ───────────────────────────────────
    for r in confirmed:
        if not r.get("checkin"):
            continue
        try:
            ci = datetime.strptime(r["checkin"], "%Y-%m-%d").date()
        except ValueError:
            errors.append(f"Fecha checkin inválida: {r.get('code','?')} {r.get('checkin')}")
            continue

        dias_mes = calendar.monthrange(ci.year, ci.month)[1]
        noches_restantes = dias_mes - ci.day + 1
        nights = r.get("nights", 0)

        if nights > noches_restantes and r.get("code"):
            # Es cross-month y el registro principal tiene más noches de las que caben
            errors.append(
                f"Cross-month mal prorateado: {r.get('code')} {r.get('guest','')} "
                f"checkin={r['checkin']} nights={nights} "
                f"(max en {ci.strftime('%b')}: {noches_restantes})"
            )

    # ── 3. CONTINUACIONES HUÉRFANAS ───────────────────────────────────────────
    # Solo las que tienen total=0 son continuaciones cross-month reales
    continuaciones = [r for r in confirmed if not r.get("code") and r.get("total", 0) == 0]

    for r in continuaciones:
        guest = r.get("guest", "")
        # Buscar registro principal con mismo guest en el mes anterior
        y, m = r.get("year"), r.get("month")
        mes_ant = (y - 1, 12) if m == 1 else (y, m - 1)
        tiene_principal = any(
            p.get("guest") == guest and p.get("code")
            and p.get("year") == mes_ant[0] and p.get("month") == mes_ant[1]
            for p in confirmed
        )
        if not tiene_principal:
            warnings.append(
                f"Continuacion sin registro principal: {guest} "
                f"{y}-{m:02d} checkin={r.get('checkin','?')}"
            )

    # ── 4. OCUPACIÓN > 100% ───────────────────────────────────────────────────
    from collections import defaultdict
    noches_mes = defaultdict(int)
    for r in confirmed:
        noches_mes[(r["year"], r["month"])] += r.get("nights", 0)

    for (y, m), n in noches_mes.items():
        dias = calendar.monthrange(y, m)[1]
        if n > dias:
            errors.append(
                f"Ocupación imposible: {y}-{m:02d} tiene {n} noches "
                f"en un mes de {dias} días ({n/dias*100:.0f}%)"
            )

    # ── 5. INGRESOS: confirmadas sin total y no son continuaciones ────────────
    for r in confirmed:
        if r.get("total", 0) == 0 and r.get("code"):
            warnings.append(
                f"Reserva confirmada con total=0: {r.get('code')} "
                f"{r.get('guest','')} {r.get('checkin','')}"
            )

    # ── 6. PM: outliers usando campo pm almacenado (< 20€ o > 500€ por noche) ─
    for r in confirmed:
        if not r.get("code"):
            continue  # continuaciones no tienen PM propio
        pm = r.get("pm", 0)
        if pm > 0 and (pm < 15 or pm > 500):
            warnings.append(
                f"PM outlier: {r.get('code')} {r.get('guest','')} "
                f"{r.get('checkin','')} PM={pm:.0f}/noche"
            )

    # ── 7. CANCELACIONES: estructura correcta ─────────────────────────────────
    for r in cancelled:
        if "impacto" not in r:
            warnings.append(
                f"Cancelación sin campo 'impacto': {r.get('code','?')} "
                f"{r.get('guest','')} {r.get('checkin','')}"
            )
        # Las canceladas no deben sumar noches al calendario
        noches_mes[(r["year"], r["month"])]  # solo verificar que existe

    # ── 8. REVIEWS: reservation_id referencia reserva existente ──────────────
    if reviews:
        codes = {r.get("code") for r in reservas if r.get("code")}
        for rv in reviews:
            rid = rv.get("reservation_id") or rv.get("code")
            if rid and rid not in codes:
                warnings.append(f"Review con reservation_id desconocido: {rid}")

    # ── RESUMEN ───────────────────────────────────────────────────────────────
    if verbose:
        total_r = len(reservas)
        total_conf = len(confirmed)
        total_canc = len(cancelled)
        total_rev = len(reviews)

        _p(f"\n{'='*50}")
        _p(f"  VALIDACION CSJ")
        _p(f"{'='*50}")
        _p(f"  Reservas: {total_r} ({total_conf} confirmadas, {total_canc} canceladas)")
        _p(f"  Reviews:  {total_rev}")
        if errors:
            _p(f"\n  ERRORES ({len(errors)}):")
            for e in errors:
                _p(f"    [X] {e}")
        if warnings:
            _p(f"\n  AVISOS ({len(warnings)}):")
            for w in warnings:
                _p(f"    [!] {w}")
        if not errors and not warnings:
            _p(f"\n  [OK] Todo correcto")
        _p(f"{'='*50}\n")

    return errors, warnings


if __name__ == "__main__":
    import sys
    errors, warnings = validar(verbose=True)
    sys.exit(1 if errors else 0)
