#!/usr/bin/env python3
# -*- coding: utf-8 -*-

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, asdict
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from openpyxl import Workbook
from openpyxl.styles import Font, PatternFill
from openpyxl.utils import get_column_letter


DEFAULT_TODAY = date.today()
DEFAULT_END = date(DEFAULT_TODAY.year, 12, 31)

_ROOT = Path(__file__).parent.parent
_DEFAULT_INPUT = str(_ROOT / "datos" / "reservas.json")
_DEFAULT_XLSX = str(_ROOT / "output" / "pricing_output.xlsx")
_DEFAULT_JSON = str(_ROOT / "output" / "pricing_output.json")

# Configuración general
PACE_DEFAULT = 1.00  # 1.10 si ingresos > histórico, 1.00 si igual, 0.90 si por debajo
LOOKBACK_YEARS = 5
MIN_VALID_PM = 15.0
MAX_VALID_PM = 500.0

# Descuento semanal comercial (estancias >= 7 noches)
WEEKLY_DISCOUNT = 0.05

# Descuento tarifa NRF (no reembolsable) vs base reembolsable
NRF_DISCOUNT = 0.10

# Factores por duración del hueco
GAP_FACTORS: Dict[int, float] = {
    1: 0.65,
    2: 0.80,
    3: 0.90,
    4: 0.95,
}

# Colores Excel
HEADER_FILL = PatternFill("solid", fgColor="D9EAF7")
INFO_FILL = PatternFill("solid", fgColor="EDEDED")
AGGRESSIVE_FILL = PatternFill("solid", fgColor="FDE9D9")
BALANCED_FILL = PatternFill("solid", fgColor="FFF2CC")
PREMIUM_FILL = PatternFill("solid", fgColor="E2F0D9")


@dataclass
class Reservation:
    guest: str
    checkin: date
    checkout: date
    nights: int
    pm: float
    status: str
    booking_date: Optional[date]
    year: int
    month: int
    confirmation_code: str
    rate_type: Optional[str]  # "refundable" | "nrf" | None (histórico sin dato)

    @property
    def occupied_nights(self) -> List[date]:
        return [self.checkin + timedelta(days=i) for i in range(self.nights)]


@dataclass
class Gap:
    start_date: date
    end_date: date
    nights: int

    @property
    def month_key(self) -> str:
        return month_key_for_date(self.start_date)


@dataclass
class GapPricing:
    start_date: str
    end_date: str
    nights: int
    month_bucket: str
    p25: float
    p50: float
    p75: float
    f_gap: float
    f_leadtime: float
    f_pace: float
    raw_price: float
    recommended_price: float
    min_price: float
    max_price: float
    weekly_price_after_discount_5pct: Optional[float]
    refundable_price: float
    strategy: str
    review_date_30d: Optional[str]
    review_date_15d: Optional[str]
    review_date_7d: Optional[str]
    next_action: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="RMS determinista para CSJ.")
    parser.add_argument("--input", default=_DEFAULT_INPUT, help="Ruta al reservas.json")
    parser.add_argument("--today", default=DEFAULT_TODAY.isoformat(), help="Fecha de referencia YYYY-MM-DD")
    parser.add_argument("--end", default=DEFAULT_END.isoformat(), help="Fecha final YYYY-MM-DD")
    parser.add_argument("--pace", type=float, default=PACE_DEFAULT, help="Factor de pace: 1.10 / 1.00 / 0.90")
    parser.add_argument("--lookback-years", type=int, default=LOOKBACK_YEARS, help="Años históricos a usar para percentiles")
    parser.add_argument("--xlsx", default=_DEFAULT_XLSX, help="Ruta del Excel de salida")
    parser.add_argument("--json", default=_DEFAULT_JSON, help="Ruta del JSON de salida")
    return parser.parse_args()


def parse_date(value: str) -> Optional[date]:
    if not value:
        return None
    return datetime.strptime(value, "%Y-%m-%d").date()


def month_key_for_date(d: date) -> str:
    if d.month == 12 and d.day >= 20:
        return "12x"
    return f"{d.month:02d}"


def month_label(month_key: str) -> str:
    labels = {
        "01": "Enero",
        "02": "Febrero",
        "03": "Marzo",
        "04": "Abril",
        "05": "Mayo",
        "06": "Junio",
        "07": "Julio",
        "08": "Agosto",
        "09": "Septiembre",
        "10": "Octubre",
        "11": "Noviembre",
        "12": "Diciembre (1-19)",
        "12x": "Diciembre (20-31)",
    }
    return labels[month_key]


def lead_time_factor(days_to_checkin: int) -> float:
    if days_to_checkin > 60:
        return 1.05
    if 30 <= days_to_checkin <= 60:
        return 1.00
    if 15 <= days_to_checkin < 30:
        return 0.95
    if 7 <= days_to_checkin < 15:
        return 0.90
    return 0.80


def gap_factor(nights: int) -> float:
    return GAP_FACTORS.get(nights, 1.00)


def percentile_linear(sorted_values: List[float], p: float) -> float:
    if not sorted_values:
        raise ValueError("No hay datos para calcular percentiles.")
    if len(sorted_values) == 1:
        return float(sorted_values[0])
    pos = (len(sorted_values) - 1) * p
    low = int(pos)
    high = min(low + 1, len(sorted_values) - 1)
    frac = pos - low
    return sorted_values[low] * (1 - frac) + sorted_values[high] * frac


def load_reservations(path: Path) -> List[Reservation]:
    with path.open("r", encoding="utf-8") as f:
        data = json.load(f)

    reservations: List[Reservation] = []
    for row in data:
        status = str(row.get("status", "confirmed"))
        checkin = parse_date(str(row.get("checkin", "")))
        nights = int(row.get("nights", 0) or 0)
        pm = float(row.get("pm", 0) or 0)
        booking_date = parse_date(str(row.get("booking_date", "")))
        year = int(row.get("year", 0) or 0)
        month = int(row.get("month", 0) or 0)
        rate_type = row.get("rate_type") or None  # None = histórico sin dato

        if not checkin or nights <= 0:
            continue

        # Normalizar PM a equivalente flexible para percentiles homogéneos
        pm_flex = pm
        if rate_type == "nrf" and pm > 0:
            pm_flex = round(pm / (1 - NRF_DISCOUNT), 2)

        checkout = checkin + timedelta(days=nights)

        reservations.append(
            Reservation(
                guest=str(row.get("guest", "")),
                checkin=checkin,
                checkout=checkout,
                nights=nights,
                pm=pm_flex,  # PM normalizado a flexible
                status=status,
                booking_date=booking_date,
                year=year,
                month=month,
                confirmation_code=str(row.get("confirmation_code", "")),
                rate_type=rate_type,
            )
        )
    return reservations


def filter_confirmed_with_valid_pm(
    reservations: List[Reservation],
    today: date,
    lookback_years: int,
) -> List[Reservation]:
    start_year = today.year - lookback_years
    valid = []
    for r in reservations:
        if r.status != "confirmed":
            continue
        if r.checkin.year < start_year or r.checkin.year > today.year:
            continue
        if not (MIN_VALID_PM <= r.pm <= MAX_VALID_PM):
            continue
        if r.nights >= 28:
            continue
        valid.append(r)
    return valid


def compute_month_percentiles(
    reservations: List[Reservation],
) -> Dict[str, Dict[str, float]]:
    buckets: Dict[str, List[float]] = {
        "01": [], "02": [], "03": [], "04": [], "05": [], "06": [],
        "07": [], "08": [], "09": [], "10": [], "11": [], "12": [], "12x": []
    }

    for r in reservations:
        key = month_key_for_date(r.checkin)
        buckets[key].append(r.pm)

    percentiles: Dict[str, Dict[str, float]] = {}
    for key, values in buckets.items():
        if not values:
            continue
        values_sorted = sorted(values)
        percentiles[key] = {
            "count": float(len(values_sorted)),
            "p25": round(percentile_linear(values_sorted, 0.25), 2),
            "p50": round(percentile_linear(values_sorted, 0.50), 2),
            "p75": round(percentile_linear(values_sorted, 0.75), 2),
            "min": round(min(values_sorted), 2),
            "max": round(max(values_sorted), 2),
        }
    return percentiles


def occupied_dates(
    reservations: List[Reservation],
    start: date,
    end: date,
) -> set[date]:
    occupied: set[date] = set()
    for r in reservations:
        if r.status != "confirmed":
            continue
        for night in r.occupied_nights:
            if start <= night <= end:
                occupied.add(night)
    return occupied


def detect_gaps(occupied: set[date], start: date, end: date) -> List[Gap]:
    gaps: List[Gap] = []
    current = start
    gap_start: Optional[date] = None

    while current <= end:
        free = current not in occupied
        if free and gap_start is None:
            gap_start = current
        elif not free and gap_start is not None:
            gaps.append(Gap(gap_start, current, (current - gap_start).days))
            gap_start = None
        current += timedelta(days=1)

    if gap_start is not None:
        final_end = end + timedelta(days=1)
        gaps.append(Gap(gap_start, final_end, (final_end - gap_start).days))

    return gaps


def choose_strategy(nights: int, recommended: float, p25: float, p50: float, p75: float) -> str:
    if nights <= 2:
        return "agresiva"
    midpoint_low = (p25 + p50) / 2
    midpoint_high = (p50 + p75) / 2
    if recommended <= midpoint_low:
        return "agresiva"
    if recommended >= midpoint_high:
        return "premium"
    return "equilibrada"


def clamp_price(raw: float, nights: int, p25: float, p75: float) -> float:
    lower = p25 * 0.90 if nights == 1 else p25
    return max(lower, min(raw, p75))


def compute_review_dates(today: date, start_date: date) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
    d30 = start_date - timedelta(days=30)
    d15 = start_date - timedelta(days=15)
    d7 = start_date - timedelta(days=7)

    v30 = d30.isoformat() if d30 >= today else None
    v15 = d15.isoformat() if d15 >= today else None
    v7 = d7.isoformat() if d7 >= today else None

    if v30:
        action = f"Revisar el {v30}; si no se vende, bajar 5%"
    elif v15:
        action = f"Revisar el {v15}; si no se vende, bajar 5–10%"
    elif v7:
        action = f"Revisar el {v7}; si no se vende, precio agresivo"
    else:
        action = "Hueco cercano; revisar a diario"
    return v30, v15, v7, action


def price_gaps(
    gaps: List[Gap],
    percentiles: Dict[str, Dict[str, float]],
    today: date,
    pace_factor: float,
) -> List[GapPricing]:
    results: List[GapPricing] = []
    for gap in gaps:
        key = gap.month_key
        if key not in percentiles:
            # si no hay bucket, se intenta el bucket "normal" del mes
            fallback = f"{gap.start_date.month:02d}"
            if fallback not in percentiles:
                continue
            key = fallback

        pct = percentiles[key]
        p25 = pct["p25"]
        p50 = pct["p50"]
        p75 = pct["p75"]

        f_gap = gap_factor(gap.nights)
        days_to_checkin = (gap.start_date - today).days
        f_lead = lead_time_factor(days_to_checkin)
        raw = p50 * f_gap * f_lead * pace_factor
        recommended = round(clamp_price(raw, gap.nights, p25, p75), 2)

        min_price = round(max(p25 * (0.90 if gap.nights == 1 else 1.00), recommended - 5), 2)
        max_anchor = p50 if gap.nights <= 2 else p75
        max_price = round(min(max_anchor, recommended + 8), 2)

        weekly = round(recommended * 7 * (1 - WEEKLY_DISCOUNT), 2) if gap.nights >= 7 else None
        refundable = round(recommended * (1 - NRF_DISCOUNT), 2)
        strategy = choose_strategy(gap.nights, recommended, p25, p50, p75)
        r30, r15, r7, action = compute_review_dates(today, gap.start_date)

        results.append(
            GapPricing(
                start_date=gap.start_date.isoformat(),
                end_date=gap.end_date.isoformat(),
                nights=gap.nights,
                month_bucket=month_label(key),
                p25=p25,
                p50=p50,
                p75=p75,
                f_gap=round(f_gap, 2),
                f_leadtime=round(f_lead, 2),
                f_pace=round(pace_factor, 2),
                raw_price=round(raw, 2),
                recommended_price=recommended,
                min_price=min_price,
                max_price=max_price,
                weekly_price_after_discount_5pct=weekly,
                refundable_price=refundable,
                strategy=strategy,
                review_date_30d=r30,
                review_date_15d=r15,
                review_date_7d=r7,
                next_action=action,
            )
        )
    results.sort(key=lambda x: x.start_date)
    return results


def autosize_worksheet(ws) -> None:
    for col_cells in ws.columns:
        max_length = 0
        col_letter = get_column_letter(col_cells[0].column)
        for cell in col_cells:
            value = "" if cell.value is None else str(cell.value)
            max_length = max(max_length, len(value))
        ws.column_dimensions[col_letter].width = min(max_length + 2, 40)


def write_workbook(
    xlsx_path: Path,
    gaps: List[GapPricing],
    percentiles: Dict[str, Dict[str, float]],
    log_row: Dict[str, str],
) -> None:
    wb = Workbook()

    # Hoja huecos
    ws = wb.active
    ws.title = "Huecos"
    headers = [
        "Inicio", "Fin", "Noches", "Mes", "P25", "P50", "P75",
        "F_gap", "F_leadtime", "F_pace", "Precio_bruto", "Precio_flexible",
        "Precio_NRF_-10%", "Min", "Max", "Precio_7n_-5%", "Estrategia",
        "Revisión_30d", "Revisión_15d", "Revisión_7d", "Próxima_acción"
    ]
    ws.append(headers)
    for cell in ws[1]:
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL

    for row in gaps:
        ws.append([
            row.start_date, row.end_date, row.nights, row.month_bucket,
            row.p25, row.p50, row.p75, row.f_gap, row.f_leadtime, row.f_pace,
            row.raw_price, row.recommended_price, row.refundable_price,
            row.min_price, row.max_price,
            row.weekly_price_after_discount_5pct, row.strategy,
            row.review_date_30d, row.review_date_15d, row.review_date_7d, row.next_action
        ])

    for r in range(2, ws.max_row + 1):
        strategy = ws.cell(r, 16).value
        fill = None
        if strategy == "agresiva":
            fill = AGGRESSIVE_FILL
        elif strategy == "equilibrada":
            fill = BALANCED_FILL
        elif strategy == "premium":
            fill = PREMIUM_FILL
        if fill:
            for c in range(1, ws.max_column + 1):
                ws.cell(r, c).fill = fill

    autosize_worksheet(ws)
    ws.freeze_panes = "A2"

    # Hoja percentiles
    wp = wb.create_sheet("Percentiles")
    wp.append(["Bucket", "P25", "P50", "P75", "Min", "Max", "N"])
    for cell in wp[1]:
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL

    for key in ["01", "02", "03", "04", "05", "06", "07", "08", "09", "10", "11", "12", "12x"]:
        if key in percentiles:
            p = percentiles[key]
            wp.append([
                month_label(key), p["p25"], p["p50"], p["p75"], p["min"], p["max"], int(p["count"])
            ])

    autosize_worksheet(wp)
    wp.freeze_panes = "A2"

    # Hoja parámetros
    wc = wb.create_sheet("Parametros")
    wc.append(["Parámetro", "Valor"])
    for cell in wc[1]:
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL
    params = [
        ("Fuente", "datos/reservas.json"),
        ("Solo status=confirmed", "Sí"),
        ("Fecha de cálculo", log_row["today"]),
        ("Fecha final", log_row["end"]),
        ("Lookback years", log_row["lookback_years"]),
        ("Pace factor", log_row["pace"]),
        ("Descuento semanal", f"{int(WEEKLY_DISCOUNT * 100)}%"),
        ("Regla 1 noche", "Puede caer hasta 10% por debajo de P25"),
        ("Regla 2+ noches", "No bajar de P25 ni subir de P75"),
    ]
    for row in params:
        wc.append(row)
    autosize_worksheet(wc)

    # Hoja log
    wl = wb.create_sheet("Log")
    wl.append(["Timestamp", "Today", "End", "LookbackYears", "Pace", "HuecosDetectados", "Observaciones"])
    for cell in wl[1]:
        cell.font = Font(bold=True)
        cell.fill = HEADER_FILL
    wl.append([
        log_row["timestamp"],
        log_row["today"],
        log_row["end"],
        log_row["lookback_years"],
        log_row["pace"],
        log_row["gaps_detected"],
        log_row["notes"],
    ])
    autosize_worksheet(wl)

    wb.save(xlsx_path)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    xlsx_path = Path(args.xlsx)
    json_path = Path(args.json)

    today = parse_date(args.today)
    end = parse_date(args.end)
    if today is None or end is None:
        raise ValueError("Las fechas deben estar en formato YYYY-MM-DD.")
    if end < today:
        raise ValueError("La fecha final no puede ser anterior a la fecha de hoy.")

    reservations = load_reservations(input_path)
    valid_for_percentiles = filter_confirmed_with_valid_pm(reservations, today, args.lookback_years)
    percentiles = compute_month_percentiles(valid_for_percentiles)

    occupied = occupied_dates(reservations, today, end)
    gaps = detect_gaps(occupied, today, end)
    priced = price_gaps(gaps, percentiles, today, args.pace)

    with json_path.open("w", encoding="utf-8") as f:
        json.dump([asdict(x) for x in priced], f, ensure_ascii=False, indent=2)

    log_row = {
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "today": today.isoformat(),
        "end": end.isoformat(),
        "lookback_years": str(args.lookback_years),
        "pace": str(args.pace),
        "gaps_detected": str(len(priced)),
        "notes": "Percentiles recalculados automáticamente desde datos/reservas.json (confirmed, pm válido).",
    }
    write_workbook(xlsx_path, priced, percentiles, log_row)

    print(f"Excel generado: {xlsx_path.resolve()}")
    print(f"JSON generado: {json_path.resolve()}")
    print(f"Huecos detectados: {len(priced)}")
    print()
    for row in priced:
        print(
            f"{row.start_date} -> {row.end_date} | "
            f"{row.nights} noches | "
            f"{row.recommended_price:.2f} EUR/noche | "
            f"{row.strategy} | "
            f"rango {row.min_price:.2f}-{row.max_price:.2f}"
        )


if __name__ == "__main__":
    main()
