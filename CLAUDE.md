> **Nota**: Forma parte de `segundo-cerebro/`. Las reservas entran via buzon (`00-buzon/`). Ver [CLAUDE.md raiz](../../CLAUDE.md) para el flujo completo.

# CSJ Airbnb — Documentacion del Proyecto

## Objetivo

Control y analisis del apartamento de alquiler turistico en Colonia de Sant Jordi (Mallorca), alquilado a traves de Airbnb desde 2015. Foco en maximizar ingresos manteniendo calidad (Superhost) y subida gradual de precio medio sin impactar reviews.

---

## Contexto

- **Propiedad**: Ramon y Cajal 14, Colonia de Sant Jordi, Mallorca
- **Propietario**: Dani (Daniel Roig), 100%
- **Plataforma**: Airbnb (unica)
- **Licencia turistica**: ETVPL/136 (NRUA: ESFCTU00000700800108051200000000000000000ETVPL/136)
- **Historico**: desde 2015 (primeras reservas), operativo completo desde 2016
- **Perfil**: apartamento pequeno, buena ocupacion 12 meses, objetivo Superhost permanente
- **Estrategia de precio**: subida gradual del PM sin perjudicar valoraciones
- **Estancia minima**: 3 noches (ocasionalmente 2 si queda hueco)

---

## Hipoteca CSJ

- **Entidad**: Cajamar (3058)
- **Prestamo**: ES08 3058 4564 1816 4901 3043
- **Cuenta**: ES70 3058 4564 1327 2001 3325 (cuenta CSJ)
- **Capital inicial**: 109.000 EUR
- **Capital pendiente**: ~58.945 EUR
- **Tipo fijo**: 2,95%
- **Cuota mensual**: 456,28 EUR (194,15 amortizacion + 262,13 intereses)
- **Apertura**: 01/02/2024
- **Vencimiento**: 01/02/2054

---

## Arquitectura — 0 dependencias externas

Todo el sistema funciona con 3 ficheros JSON locales. **No hay llamadas API, no hay Google Sheet, no hay conexion a internet.**

```
FUENTES DE DATOS
════════════════
_reservas.json  (488 reservas, 2015-2027)
    → Ingresos, ocupacion, PM, pace, lead time, costes, beneficio neto
    → Enriquecido con booking_date, checkin, confirmation_code (90% cobertura)
    → Se actualiza cuando llega PDF de reserva al buzon

_reviews.json   (343 evaluaciones)
    → Puntuaciones, subcategorias, Superhost trimestral
    → Se actualiza con cada nuevo export de Airbnb

_visitas.json   (94 meses de page views)
    → Conversion: visitas al listing + reservas por fecha de venta
    → Dani actualiza 1x/mes desde panel Airbnb

GENERACION
══════════
python visualizar.py  →  dashboard.html

EXPORT AIRBNB (01-datos/raw/)
═════════════════════════════
28 ficheros JSON del export personal de Airbnb (solicitado 19/03/2026)
Fuente para enriquecer _reservas.json y crear _reviews.json
```

### Google Sheet — ARCHIVO MUERTO

El Google Sheet (`1BEa1m5InTFUDzvvILcDafwC3mRn7b6GkLYnq0eAMvXg`) queda como historico. **No se consulta, no se actualiza, no se necesita.**

---

## Flujo operativo

### 1. Nueva reserva

1. Dani deja PDF de reserva en `00-buzon/entrante/`
2. Claude extrae datos del PDF
3. Verificar si la reserva ya existe en `_reservas.json`
4. Si cruza meses: calcular prorrateo (2 registros, el sin `code` es continuacion)
5. Anadir a `_reservas.json`
6. Ejecutar `python visualizar.py` para regenerar dashboard
7. Mover PDF a `00-buzon/procesado/`, registrar en log

### 2. Actualizar visitas (1x/mes)

1. Dani entra al panel de Airbnb → Rendimiento → Visitas
2. Edita `_visitas.json`, anade la linea del mes: `"2026-03": 750`
3. Ejecuta `python visualizar.py`

### 3. Actualizar reviews (cuando haya nuevo export)

1. Solicitar export de datos personales en Airbnb
2. Extraer a `01-datos/raw/`
3. Claude procesa y actualiza `_reviews.json`
4. Claude enriquece `_reservas.json` con nuevas reservas/fechas

### 4. Regenerar dashboard

```bash
python visualizar.py
```

Lee los 3 JSON locales. Genera `dashboard.html`. Sin conexion a internet.

---

## Estructura de _reservas.json

```json
{
  "year": 2026, "month": 1,
  "code": "HMB4F3M2PX",
  "guest": "Nombre",
  "checkin": "2026-01-05",
  "nights": 7,
  "pm": 57.46,
  "cleaning": 60.0,
  "total": 463.22,
  "confirmation_code": "HMB4F3M2PX",
  "booking_date": "2025-11-20"
}
```

- **`total`**: ingreso neto (tras comision Airbnb 3%+IVA, incluye limpieza)
- **`booking_date`**: fecha de venta (cuando se hizo la reserva)
- **`checkin`**: fecha de estancia (cuando entra el huesped)
- **`confirmation_code`**: codigo Airbnb (90% cobertura, 10% sin match del export)
- **Reservas entre meses**: se prorratean como 2 registros (el que no tiene `code` es la continuacion)

## Estructura de _visitas.json

```json
{
  "2024-01": 320,
  "2024-02": 410,
  "2026-03": 750
}
```

Clave = `YYYY-MM`, valor = numero de page views del listing en ese mes.

---

## Costes

### Costes fijos mensuales (ref. 2024)

| Concepto | EUR/mes | Notas |
|----------|---------|-------|
| Hipoteca | 456,28 | Cajamar, tipo fijo 2,95% |
| Endesa (electricidad) | 90,00 | |
| Telefono y WIFI | 80,00 | |
| Comunidad de vecinos | 50,00 | No domiciliado |
| Seguro Banc Sabadell | 25,00 | |
| Hidrobal (agua) | 25,00 | |
| IBI | 16,67 | ~200 EUR/ano |
| Basuras | 14,58 | ~175 EUR/ano |
| **Total fijos** | **757,53** | |

### Costes variables

| Concepto | Importe | Frecuencia |
|----------|---------|------------|
| Limpieza (Tania) | 30 EUR/reserva | Por reserva (Dani paga 30, cobra 60 al cliente) |
| Amenities | ~10 EUR/reserva | Por reserva |

### Modelo de costes en el dashboard

```python
COSTE_RESERVA = 40  # EUR/reserva (30 Tania + 10 amenities)
COSTES_FIJOS = {2015: 6000, ..., 2024: 9090, 2025: 9090, ...}
costes_ano = COSTES_FIJOS[ano] + 40 * n_reservas
```

- Los 60 EUR de limpieza se cobran al cliente y ya estan en el ingreso neto
- El coste real para Dani son 30 EUR (lo que paga a Tania) + 10 EUR amenities

---

## Dashboard ejecutivo

### 5 KPIs dinamicos

Con filtros (ano y1 vs y2, periodo Anual/YTD/6m/3m):
- Beneficio neto + margen % + comparativa (responde a filtro periodo)
- Ingresos brutos + comparativa (responde a filtro periodo)
- Ocupacion + comparativa (responde a filtro periodo)
- PM temporada alta jun-ago + comparativa (fijo, no depende del periodo)
- Pace vs LY: delta % vendido a misma fecha (responde a filtro periodo)

### Secciones

**S1 — Ingresos y rentabilidad:**
- Ingresos mensuales comparativa (banda historica min/max/media)
- Evolucion anual ingresos (media historica)
- Beneficio neto anual (barras + linea ingreso bruto)
- Costes vs ingresos (% coste/ingreso)
- Estacionalidad ingresos (radar y1 vs y2)

**S2 — Ocupacion:**
- Ocupacion mensual comparativa (banda historica)
- Evolucion anual ocupacion (media historica)
- Tabla visual ocupacion por ano (semaforo verde/amarillo/rojo)

**S3 — Precio Medio:**
- PM mensual comparativa (banda historica)
- Evolucion anual PM (media historica)
- PM por banda estacional: Alta/Media/Baja

**S4 — Resumen combinado:** Ingresos + Ocupacion + PM por ano (doble eje)

**S5 — Conversion:** Tasa conversion anual (CVR%) + Visitas y reservas mensuales (fecha de venta)

**S6 — Ritmo de ventas:**
- Pace Report: OTB y1 vs y2 por mes (a misma fecha)
- Lead Time: distribucion por ventana (<7d, 7-30d, 30-90d, >90d) + PM por ventana
- Lead Time medio por ano (tendencia de antelacion)

**S7 — Evaluaciones y Superhost:**
- Puntuaciones por ano (y1 vs y2, todas las subcategorias)
- Radar de evaluaciones (y1 vs y2)
- Timeline Superhost trimestral (rating + n reviews + umbral 4.8)

---

## Superhost

Airbnb evalua trimestralmente (1 ene, 1 abr, 1 jul, 1 oct) con ventana de 365 dias. Criterios:
- Rating medio >= 4.8
- >= 10 estancias/ano (o 3 estancias + 100 noches)
- Tasa de cancelacion < 1%
- Tasa de respuesta >= 90%

El dashboard muestra el tracking trimestral con rating y numero de reviews por periodo.

---

## Pendiente / Mejoras

- [ ] GitHub Pages para acceder al dashboard desde movil/desktop
- [ ] Retomar control de gastos reales (no se actualiza desde 2024)
- [ ] Finanzas compartidas con Ester (subdominio `compartido/`)
- [x] 0 dependencias externas (3 JSON locales, sin API)
- [x] Export Airbnb procesado: _reservas.json enriquecido + _reviews.json creado
- [x] Dashboard con pace report, lead time, Superhost tracking
- [x] _reservas.json como fuente de verdad (488 reservas, totales ajustados)

---

*Documento actualizado el 20/03/2026*
