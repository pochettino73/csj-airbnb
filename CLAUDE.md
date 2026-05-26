> **Proyecto**: CSJ — Airbnb Colonia de Sant Jordi. Ruta: `C:\Users\droig\Proyectos\CSJ\`. Buzón de entrada: `CSJ/buzon/entrante/`.

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
- **Dashboard publico**: https://pochettino73.github.io/csj-airbnb/dashboard.html

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
ESTRUCTURA DEL PROYECTO
═══════════════════════
CSJ/
├── dashboard.html         Dashboard ejecutivo (raíz — requerido por GitHub Pages)
├── CLAUDE.md
├── datos/
│   ├── reservas.json      588 reservas (2015-2027) — fuente de verdad
│   ├── reviews.json       346 evaluaciones — puntuaciones y Superhost
│   ├── visitas.json       meses de page views
│   └── raw/               28 ficheros JSON del export Airbnb (19/03/2026)
├── scripts/
│   ├── visualizar.py      Genera dashboard.html desde los 3 JSON
│   ├── auditar_dashboard.py  Auditoría económica — EJECUTAR antes de git push
│   ├── validar.py         Valida reservas.json (se ejecuta automáticamente)
│   ├── pricing.py         RMS determinista — genera output/pricing_output.xlsx
│   └── utils/             Scripts de debug (no operativos)
├── output/
│   ├── pricing_output.xlsx
│   ├── pricing_output.json
│   ├── auditoria_dashboard.xlsx  Último informe de auditoría
│   ├── auditoria_dashboard.json  Último informe de auditoría (JSON)
│   └── audit_baseline.json       Snapshot de métricas validadas (auto-generado)
└── buzon/
    ├── entrante/          Dani deja PDFs aquí
    └── procesado/YYYY/MM/

GENERACION
══════════
python scripts/auditar_dashboard.py  →  verificar 0 CRÍTICOs
python scripts/visualizar.py         →  dashboard.html  →  git push  →  GitHub Pages
python scripts/pricing.py            →  output/pricing_output.xlsx
```

### Google Sheet — ARCHIVO MUERTO

El Google Sheet (`1BEa1m5InTFUDzvvILcDafwC3mRn7b6GkLYnq0eAMvXg`) queda como historico. **No se consulta, no se actualiza, no se necesita.**

---

## Flujo operativo

### 1. Nueva reserva

1. Dani deja PDF de reserva en `buzon/entrante/`
2. Claude extrae datos del PDF
3. Verificar si la reserva ya existe en `datos/reservas.json`
4. Si cruza meses: calcular prorrateo (2 registros, el sin `code` es continuacion)
5. Anadir a `datos/reservas.json`
6. Ejecutar `python scripts/visualizar.py` para regenerar dashboard (valida automáticamente)
7. `git commit && git push` para actualizar GitHub Pages
8. Mover PDF a `buzon/procesado/YYYY/MM/`

### 2. Actualizar visitas (1x/mes)

1. Dani entra al panel de Airbnb → Rendimiento → Visitas
2. Edita `datos/visitas.json`, anade la linea del mes: `"2026-03": 750`
3. Ejecuta `python scripts/visualizar.py`
4. `git commit && git push`

### 3a. Añadir review individual (cuando Dani lo comunica)

1. Localizar la reserva en `datos/reservas.json` por `confirmation_code`
2. Añadir entrada al final de `datos/reviews.json` con la estructura de reviews recientes (date, rating, comment="", private_feedback="", language, bookable_id=null, reviewer_id=null, confirmation_code, general, llegada, limpieza, veracidad, comunicacion, ubicacion, calidad)
3. Ejecutar `python scripts/visualizar.py`
4. `git add datos/reviews.json dashboard.html && git commit && git push`

> Claude ejecuta los pasos 3 y 4 directamente sin pedir a Dani que lo haga.

### 3b. Actualizar reviews (cuando haya nuevo export)

1. Solicitar export de datos personales en Airbnb
2. Extraer a `datos/raw/`
3. Claude procesa y actualiza `datos/reviews.json`
4. Claude enriquece `datos/reservas.json` con nuevas reservas/fechas
5. Regenerar dashboard y push

### 4. Regenerar dashboard

```bash
python scripts/visualizar.py
git add datos/reservas.json dashboard.html && git commit -m "..." && git push
```

Lee los 3 JSON en `datos/`. Genera `dashboard.html`. Push publica en GitHub Pages.

---

## Estructura de datos/reservas.json

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
- **`confirmation_code`**: codigo Airbnb (solo ~3/ano tienen match del export)
- **`rate_type`**: (opcional, solo nuevas reservas) `"refundable"` | `"nrf"`. Histórico sin dato = None. pricing.py normaliza los PMs NRF a equivalente flexible dividiendo por (1 - 0.10).
- **Reservas entre meses**: se prorratean como 2 registros (el que no tiene `code` es la continuacion)

## Estructura de datos/visitas.json

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

### Publicacion

- **Repo**: `pochettino73/csj-airbnb` (publico)
- **URL**: https://pochettino73.github.io/csj-airbnb/dashboard.html
- **Responsive**: optimizado para movil y desktop

### 5 KPIs dinamicos

Filtros: ano y1 vs y2, periodo Anual / A fecha.

| KPI | Descripcion |
|-----|-------------|
| Ingresos | Ingresos brutos del periodo + comparativa vs y2 |
| Ocupacion | % ocupacion del periodo + comparativa vs y2 |
| PM por temporada | 3 valores horizontales: Alta / Media / Baja con deltas |
| Pace | Delta % vendido a misma fecha vs y2 |
| Rating | Nota global del proximo trimestre Superhost + pendientes + simulacion |

### Bandas estacionales PM

| Banda | Periodo |
|-------|---------|
| Alta | 15 jun — 15 sep |
| Media | 1 abr — 14 jun + 16 sep — 31 oct |
| Baja | 1 nov — 31 mar |

### Colores de graficas

Sistema de colores semántico: cada variable tiene un color fijo en todos los gráficos. La distinción entre años se hace con opacidad y línea discontinua, no cambiando el color.

| Variable | Color | Hex | Constante JS |
|----------|-------|-----|-------------|
| Ingresos | Azul | `#3b82f6` | `COL_ING` |
| Ocupación | Cian | `#22d3ee` | `COL_OCU` |
| ADR / PM | Amarillo | `#facc15` | `COL_ADR` |
| Visitas | Violeta | `#a78bfa` | `COL_VIS` |
| Reservas | Verde | `#22c55e` | `COL_RES` |
| Cancelaciones | Rojo | `#ef4444` | `COL_CANC` |

- **y1** (año principal): color sólido, línea continua, grosor 3
- **y2** (año comparativa): mismo color + `70` (opacidad ~44%), línea discontinua `[5,5]`, grosor 1.5
- **Banda histórica** (min/max): gris semitransparente

Las constantes se definen al inicio del bloque JS de `visualizar.py` y se usan en todas las funciones de chart.

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
- Timeline Superhost trimestral (rating + n reviews + umbral 4.8, recortado al proximo trimestre)
- Proximo trimestre: selector de trimestres futuros, rating actual, distribucion de notas, simulacion de reviews necesarias, reviews pendientes

---

## Superhost

Airbnb evalua trimestralmente (1 ene, 1 abr, 1 jul, 1 oct) con ventana de 365 dias.

### Ventanas de evaluacion — notacion de negocio (T1-T4)

El dashboard usa notacion de negocio (T1=Jan-Mar, T2=Apr-Jun, T3=Jul-Sep, T4=Oct-Dec), NO la notacion de Airbnb (Q1-Q4). El mapeo es:

| Label dashboard | Fecha evaluacion Airbnb | Ventana | Trimestre de negocio |
|-----------------|------------------------|---------|----------------------|
| Y-T1 | 1 abril Y | 1 abr Y-1 — 31 mar Y | Ene-Mar de Y |
| Y-T2 | 1 julio Y | 1 jul Y-1 — 30 jun Y | Abr-Jun de Y |
| Y-T3 | 1 octubre Y | 1 oct Y-1 — 30 sep Y | Jul-Sep de Y |
| (Y-1)-T4 | 1 enero Y | 1 ene Y-1 — 31 dic Y-1 | Oct-Dic de Y-1 |

### Implementacion en visualizar.py

```python
t_map = {1: 4, 2: 1, 3: 2, 4: 3}   # Airbnb q -> T de negocio
t_year = {1: y-1, 2: y, 3: y, 4: y}  # ajuste de año
```

- `FUTURE_SH`: incluye el trimestre cuya eval_date >= hoy (4 entradas: T_actual_completado + T_activo + T3 + T4)
- `shIdx = 1`: tab activo por defecto = T2 (el siguiente a evaluar, el que necesita seguimiento)
- `FUTURE_SH[0]` = T1 (recien cerrado, visible como referencia historica)
- El chart timeline muestra los ultimos 4 trimestres (`slice(-4)`), con `autoSkip:false`
- La tarjeta de Rating en el menu superior usa `FUTURE_SH[1]` (T2 activo)
- El chart corta en `FUTURE_SH[1].label` (T2), no en NEXT_SH (T1)

### Criterios

- Rating medio >= 4.8
- >= 10 estancias/ano (o 3 estancias + 100 noches)
- Tasa de cancelacion < 1%
- Tasa de respuesta >= 90%

---

## Cambios aplicados 2026-04-21

### Sección 8 — Cancelaciones (nueva)

Se añadió campo `status` al JSON de reservas (`"confirmed"` / `"cancelled"`) para separar los dos universos de análisis. Las reservas sin `status` se tratan como `confirmed` por defecto.

A las cancelaciones se les añadió campo `impacto` (estimación del precio perdido) y `total` (penalización cobrada por Airbnb). La lógica de recuperación (`recovery()`) calcula el solapamiento en días entre la cancelación y reservas confirmadas posteriores en las mismas fechas, estimando el ingreso que se recuperó.

**Modelo de cálculo por cancelación:**
- `perdido` = `impacto` + `total`
- `recuperado` = ingreso prorateado de reservas confirmadas que ocuparon esas fechas
- `neto` = `perdido` − `total` − `recuperado`

**3 gráficas en S8:**
- C22: Tasa de cancelación anual (confirmadas vs canceladas, % tasa)
- C23: Impacto económico (perdido / recuperado / neto por año en EUR)
- C24: Lead time comparado (días de antelación al reservar: confirmadas vs canceladas)

**KPI en cabecera:** Card "Cancelaciones Y1" con nº cancelaciones y tasa %.

---

## Cambios aplicados 2026-04-21 (sesión tarde)

### Corrección crítica: reservas faltantes en _reservas.json

El export de datos de Airbnb (19/03/2026) **no incluye todas las reservas como host**. Al cruzar el JSON contra el panel de Airbnb → Reservas, se detectaron 11 reservas confirmadas ausentes y 2 registros con datos cruzados.

**11 reservas añadidas:**
HMKEA23BY9, HM5RJ9QHXS, HMZKC8PCKM, HMFJ8S23WT, HMAZFDQRF3, HMQMWE3HM4, HMNKEKCM4M, HMHM4FQMHK, HMHXK9AFY5, HMHS3SRTMF, HMB4YS98MZ

Las que cruzan mes (HMNKEKCM4M jun→jul, HMHM4FQMHK jul→ago) se añadieron como 2 registros cada una.

**2 registros corregidos:**
- HMTPSMQXSS: tenía datos de Lia Piedra (7n, 827€) → corregido a Susan Schimmeyer (5n, 636.04€, 12-17 jul)
- HMNWSFKKZK: tenía datos de Vasile Cumatrenco en 2 registros → corregido a Lia Piedra Prieto (7n, 826.85€, 21-28 jul, registro único)

**Lección aprendida:** el export personal de Airbnb no es fiable como fuente completa de reservas host. La fuente de verdad es el panel Airbnb → Reservas. Cada vez que haya dudas sobre huecos, contrastar con el panel.

---

## Cambios aplicados 2026-04-23

### Corrección prorrateos cross-month (histórico + 2026)

Se detectaron 5 registros con noches mal prorateadas (el registro principal tenía el total de noches en lugar de solo las noches del mes de checkin):

- HMNKEKCM4M (Darya Kramar, jun→jul 2026): nights 10→1 en junio
- HMHM4FQMHK (Vasile Cumatrenco, jul→ago 2026): nights 8→2 en julio
- Lisanne Vladisavljevic (sep→oct 2021): nights 9→2 en septiembre + continuación oct añadida (7n)
- Mireille Heronneau (oct→nov 2021): nights 5→2 en octubre + continuación nov añadida (3n)
- Elisabeth Liwadas Kreutz (may→jun 2022): nights 7→5 en mayo + continuación jun añadida (2n)

**Regla:** el registro principal solo lleva las noches que caen en su mes. El total (€) va íntegro en el primer mes. La continuación (code='') lleva las noches del segundo mes y total=0.

### Reserva añadida: Arthur Schaber (HMZRBPTXRS)

Reserva no incluida en el export de Airbnb. Añadida manualmente tras validar huecos:
- Feb 26 → Mar 2 de 2026 (4 noches, 217.41€, 1 adulto)
- Registro Feb: year=2026, month=2, nights=3, total=217.41
- Continuación Mar: year=2026, month=3, nights=1, total=0

### validar.py — nuevo script de validación automática

Creado `validar.py` e integrado en `visualizar.py`. Se ejecuta automáticamente en cada `python visualizar.py`. Si hay errores, aborta antes de generar el dashboard.

**Checks implementados:**
1. Campos obligatorios (year, month, nights, total)
2. Cross-month mal prorateado (noches > días restantes del mes)
3. Continuaciones huérfanas (code='' + total=0 sin registro principal en mes anterior)
4. Ocupación >100% en cualquier mes
5. Confirmadas con total=0 que no son continuaciones
6. PM outlier (<15€ o >500€/noche según campo pm)
7. Cancelaciones sin campo impacto
8. Reviews con reservation_id desconocido

**Total registros tras sesión:** 588 (502 confirmadas, 86 canceladas), 346 reviews.

### Eliminadas gráficas C12 y C13

Se eliminaron del dashboard las gráficas de Beneficio Neto y Costes vs Ingresos por no aportar valor operativo.

---

## Cambios aplicados 2026-04-23 (sesión tarde)

### Reorganización de carpetas

Estructura simplificada y semántica:
- `datos/` — reservas.json, reviews.json, visitas.json, raw/
- `scripts/` — visualizar.py, validar.py, pricing.py, utils/
- `output/` — pricing_output.xlsx, pricing_output.json
- `buzon/` — entrante/, procesado/YYYY/MM/
- `dashboard.html` permanece en raíz (requerido por GitHub Pages)

Scripts migrados a `scripts/` con paths actualizados:
- `validar.py`: usa `Path(__file__).parent.parent` para localizar `datos/`
- `visualizar.py`: constantes `_ROOT` y `_DATOS` resuelven rutas desde la posición del script
- `pricing.py`: `_ROOT`, `_DEFAULT_INPUT`, `_DEFAULT_XLSX`, `_DEFAULT_JSON` como defaults dinámicos

**Comando actualizado:** `python scripts/visualizar.py` (antes `python visualizar.py`)

### auditar_dashboard.py — nuevo script de auditoría de métricas

Creado `scripts/auditar_dashboard.py` e integrado en `visualizar.py` (se ejecuta tras validar.py). Calcula métricas de forma independiente y las compara con las fórmulas del dashboard.

**Flujo completo:** `validar.py` (datos) → `auditar_dashboard.py` (métricas) → generación dashboard

**Errores BLOQUEANTES** (impiden generación del dashboard):
- Reservas solapadas activas (checkout en el futuro)
- Ocupación > 100% en cualquier mes
- Cross-month mal prorateado
- Tests unitarios de casos documentados fallidos

**AVISOS** (no bloquean):
- PM mensual distorsionado por bug cross-month del dashboard (conocido, pendiente fix)
- Inconsistencias históricas de PM (registros pre-2021 sin cleaning almacenado)
- Solapes históricos (ambas reservas ya cerradas)
- Pace con registros sin booking_date

**Umbrales PM:** AVISO si delta > 5%, ERROR solo si delta > 15% en año actual sin cross-month

**Tests unitarios incluidos (T1-T6):**
- T1: HMNKEKCM4M Darya Kramar (jun→jul 2026) — nights=1 en jun, continuación en jul, PM distorsionado
- T2: HMHM4FQMHK Vasile Cumatrenco (jul→ago 2026) — nights=2 en jul
- T3: HMZRBPTXRS Arthur Schaber (feb→mar 2026) — nights=3 en feb
- T4: Lisanne Vladisavljevic (sep 2021) — nights=2
- T5: Mireille Heronneau (oct 2021) — nights=2
- T6: Elisabeth Liwadas Kreutz (may 2022) — nights=5

### Reserva añadida: Sophie Metais (HMBB8ASH5P)

- May 31 → Jun 3 de 2026 (3 noches, 282€ total neto, rate_type="nrf")
- PM NRF = 94€/noche (Airbnb); PM flexible normalizado = 104.44€
- Registro único (no cross-month)

---

## Sistema de validación de datos

### Validación automática — validar.py

Se ejecuta automáticamente cada vez que se lanza `python scripts/visualizar.py`. Si detecta **errores**, aborta y no genera el dashboard. Si detecta **avisos**, los muestra pero continúa.

También se puede lanzar standalone: `python scripts/validar.py`

#### Checks que provocan ERROR (bloquean la generación del dashboard)

| # | Qué detecta | Ejemplo |
|---|-------------|---------|
| 1 | **Campos obligatorios ausentes** — falta year, month, nights o total | Registro sin `total` |
| 2 | **Cross-month mal prorateado** — el registro principal tiene más noches de las que caben en su mes | Reserva con checkin 30-jun y nights=10 cuando solo quedan 1 noche en junio |
| 4 | **Ocupación imposible** — la suma de noches confirmadas en un mes supera los días del mes | Mes de 30 días con 32 noches vendidas |

#### Checks que generan AVISO (no bloquean)

| # | Qué detecta | Ejemplo |
|---|-------------|---------|
| 3 | **Continuación huérfana** — registro sin code y total=0 sin registro principal en mes anterior | Continuación de julio sin reserva principal en junio |
| 5 | **Reserva confirmada con total=0** que no es continuación | Reserva con code pero sin ingreso |
| 6 | **PM outlier** — precio/noche fuera de rango (< 15€ o > 500€) según campo `pm` almacenado | PM=3€ o PM=600€ |
| 7 | **Cancelación sin campo `impacto`** | Cancelación sin estimación de ingreso perdido |
| 8 | **Review con reservation_id desconocido** — el código no existe en reservas.json | Review huérfana |

### Reglas de integridad para reservas cross-month

Cuando una reserva cruza de un mes al siguiente se crean **2 registros**:

| Campo | Registro principal (mes checkin) | Continuación (mes siguiente) |
|-------|----------------------------------|------------------------------|
| `code` | Código Airbnb (ej. HMXXX) | Vacío `""` |
| `year` / `month` | Mes del checkin | Mes siguiente |
| `nights` | Solo las noches que caen en su mes | Las noches del mes siguiente |
| `total` | Ingreso íntegro de la reserva | `0` |
| `pm` | PM real calculado sobre el total de noches | `0` |
| `cleaning` | 60€ | `0` |

**Por qué así:** el ingreso se cobra de una vez y se asigna al mes de entrada. Las noches se prorratean para que la ocupación mensual sea correcta.

### Limitación conocida: PM distorsionado en meses con reservas cross-month

**Problema:** el dashboard calcula el PM mensual como `(total - cleaning) / nights` sumando todos los registros del mes. Para meses donde entra la parte principal de una reserva cross-month (con el ingreso íntegro pero pocas noches), el PM aparece artificialmente alto.

**Ejemplo real (junio 2026):** Darya Kramar tiene 1 noche en junio y 9 en julio, con 1.110€ íntegros en junio. El dashboard muestra PM junio 2026 = **115€/noche** cuando el PM real ponderado es **81€/noche**.

**Impacto:** solo afecta a meses con reservas cross-month. El campo `pm` almacenado en cada registro es siempre correcto (refleja el precio real por noche sobre la estancia completa). Los ingresos totales y la ocupación no están afectados.

**Estado:** bug conocido, pendiente de corregir en visualizar.py (usar campo `pm` ponderado por noches en lugar de `total/nights`).

### Qué NO controla el validador automático

- Que el precio sea razonable para la temporada (lo hace pricing.py con percentiles)
- Que el nombre del huésped sea correcto (se verifica manualmente contra el PDF)
- Que el booking_date sea correcto (se extrae del PDF)
- La distorsión del PM mensual en el dashboard por reservas cross-month (bug conocido arriba)
- Que todas las reservas del panel Airbnb estén en el JSON — el export de Airbnb no es fiable, hay que contrastar manualmente con el panel Airbnb → Reservas cuando haya dudas

---

## Pendiente / Mejoras

- [ ] Retomar control de gastos reales (no se actualiza desde 2024)
- [ ] Corregir PM mensual en dashboard para reservas cross-month (usar campo `pm` ponderado) — auditoria_dashboard.py lo detecta como AVISO
- [x] GitHub Pages activo: https://pochettino73.github.io/csj-airbnb/dashboard.html
- [x] 0 dependencias externas (3 JSON locales, sin API)
- [x] Export Airbnb procesado: reservas.json enriquecido + reviews.json creado
- [x] Dashboard con pace report, lead time, Superhost tracking
- [x] reservas.json como fuente de verdad (588 registros, totales ajustados)
- [x] Dashboard responsive (movil + desktop)
- [x] Carpetas simplificadas (sin subcarpetas vacias)
- [x] validar.py integrado en visualizar.py — validación automática en cada generación
- [x] auditar_dashboard.py — auditoría de métricas independiente (10 checks, tests unitarios)
- [x] Carpetas reorganizadas: datos/, scripts/, output/, buzon/
- [x] pricing.py con RMS determinista + columna Precio_NRF_-10% + WEEKLY_DISCOUNT

---

---

## Cambios aplicados 2026-04-27

### Auditoría reforzada — severidades revisadas

Se actualizaron los umbrales de `auditar_dashboard.py` para clasificar incidencias por impacto real:

**CRÍTICO (blocking=True):**
- PM mensual delta > 10%
- PM temporada delta > 10%
- Pace: diferencia absoluta > 100€ en año actual o futuro
- Solapes en año actual o futuro
- year/month inconsistente con checkin (salvo continuaciones cross-month)

**AVISO (blocking=False):**
- PM delta 5-10%
- Incidencias históricas (solapes pre-año-actual, pace histórico)
- Registros sin booking_date en años pasados

**Resumen ejecutivo** añadido al output de la auditoría: nº OK / AVISOS / CRÍTICOS y estado BLOQUEADO / OK para generar.

### Bug PM cross-month corregido en visualizar.py

La fórmula de PM mensual y por temporada se corrigió en `visualizar.py`:

- **Antes (bug):** `PM = sum(total - cleaning) / sum(nights)` por mes → distorsionado por reservas cross-month
- **Ahora (correcto):** `PM = sum(pm * nights) / sum(nights)` usando campo `pm` almacenado, ponderado por noches, excluyendo continuaciones

La misma corrección aplica a PM por banda estacional y lead time.

`calc_pm_dashboard` en `auditar_dashboard.py` también actualizado para replicar la nueva fórmula. La sección PM_Mensual del Excel queda como regression test (delta debe ser siempre ~0).

### Correcciones de datos históricos

- **Código '9'** (2017-06-30, 1 noche): year/month corregido de julio a junio (checkin el último día del mes, estaba archivado en el mes siguiente)
- **Código '8'** (2018-04-30, 1 noche): year/month corregido de mayo a abril

### booking_date de Terry Lutz completado manualmente

- **Reserva:** Terry Lutz, checkin 2026-03-28, 16 noches en total (4 en marzo, 12 en abril)
- **booking_date añadido:** `2025-08-19`
- **Fuente:** panel Airbnb → Reservas, consultado manualmente por Dani el 27/04/2026
- **Registros afectados:** los dos registros de Terry Lutz en 2026 (month=3 y month=4)
- **Impacto:** resolvió los 2 CRÍTICOS de Pace (OTB 2026-03 y OTB 2026-04 tenían D>100€ por ausencia de booking_date)

### Estado de auditoría tras sesión (mañana)

```
OK:        145
AVISOS:     43  (solapes históricos + pace histórico + lead time)
CRÍTICOS:    0
Estado:    OK para generar
```

---

## Cambios aplicados 2026-04-27 (sesión tarde)

### Terry Lutz — datos completados (HMF8YAQAKN)

- **code:** `HMF8YAQAKN` añadido al registro principal (month=3)
- **Formato cross-month corregido:** income íntegro en marzo (total=977.89, cleaning=60.0); continuación abril con total=0, cleaning=0
- **rate_type:** `"refundable"` añadido (política Flexible confirmada en PDF)
- **PDF:** procesado y movido a `buzon/procesado/2026/03/`

### booking_date estimado en 27 registros históricos

Todos los registros confirmados con code pero sin `booking_date` recibieron fecha estimada: `checkin - 4 meses` (o `1º del mes - 4 meses` para los 7 sin checkin). Cubre registros de 2015 a 2019.

### KPIs del dashboard — comparativa "misma fecha" en todas las tarjetas

Todas las tarjetas de KPI usan ahora el corte por `booking_date` para comparar y1 vs y2 a mismo día:

**Nuevas funciones en `visualizar.py`:**
- `calc_cancelaciones_ytd(reservas_all, today)` — tasa de cancelación filtrada a mismo día del año anterior
- `calc_pm_ytd(reservas_all, today)` — PM ponderado por noches de estancias vendidas hasta misma fecha

**Nuevo objeto `TOTALES` en JS:** ingresos, ocupación, cancelaciones y PM del año completo de y2, mostrado como "Total final y2" en cada tarjeta.

**Cambios por tarjeta:**
| Tarjeta | Antes | Ahora |
|---------|-------|-------|
| Ventas | ✓ ya usaba booking_date | + histLine "Total final y2" desde TOTALES |
| Ocupación | ✓ ya usaba booking_date | + histLine "Total final y2: X% (Y noches)" |
| Cancelaciones | comparaba vs año completo y2 | misma fecha + signo corregido (pct(tasa1,tasa2)) + histLine "Total final y2" |
| PM medio | media de meses con datos | ponderado por noches vía PM_YTD + histLine "Total final y2" |

### PM anual (gráfico evolución) — criterio operativa 12 meses

`ANN_PM` cambiado de media de meses activos a `sum(pm_mensual) / 12`, coherente con el spreadsheet histórico y con la realidad de operativa 12 meses. Meses sin reservas cuentan como €0, no se excluyen.

2022 no tiene campo `pm` almacenado → usa media mensual como fallback.

### Estado de auditoría tras sesión tarde

```
OK:        145
AVISOS:     22  (solapes históricos + pace histórico + lead time)
CRÍTICOS:    0
Estado:    OK para generar
```

---

## Cambios aplicados 2026-05-22

### Nueva reserva: Hermann Henkel (HME3NT9TKP)

- Check-in 14/09/2026, 6 noches, 676,52€, booking_date 2026-05-22
- Temporada media (sep), huésped alemán

### Nueva review: Stef Wallace (HM5RJ9QHXS)

- Date 2026-05-21, rating general 4, subcategorías: llegada=5, limpieza=4, veracidad=4, comunicación=5, ubicación=4, calidad=4

### Visitas abril 2026

- 1.226 visitas añadidas a `datos/visitas.json`

### pricing.py — RMS completamente reescrito

El sistema de Revenue Management anterior usaba reglas rígidas (`nights ≤ 2 → agresiva`). El nuevo sistema es multifactor, basado en zonas de percentiles, completamente auditable.

**Estrategias:**

| Estrategia | Zona percentil | Color Excel |
|------------|---------------|-------------|
| Ocupación | P25–P40 | Rojo (FDE9D9) |
| Equilibrio | P45–P60 | Amarillo (FFF2CC) |
| Rentabilidad | P65–P75 | Morado (E8DAEF) |

**Lógica de asignación:**
- **Ocupación**: hueco corto (≤3n) AND (lead<21d OR pace<0.97 OR temporada baja OR occ_futura<35%)
- **Rentabilidad**: pos_score≥3 OR (temporada alta AND buena antelación AND (pace fuerte OR occ alta))
- **Equilibrio**: caso por defecto

**Microajustes dentro de la zona** (posición inicial = punto medio):
- Lead <10d: −20% | <21d: −10% | >60d: +15%
- Pace >1.07: +20% | >1.02: +10% | <0.93: −15% | <0.97: −8%
- Noches ≤2: −10% | ≤3: −5%
- Occ ≥70%: +10% | <30%: −10%
- Tensión Rentabilidad (score≥3): hasta +13% sobre P75

**Suelo**: P25 (×0.90 para estancias de 1 noche)
**Techo**: P75 × 1.13

**CLI:** `python scripts/pricing.py` — pace se auto-calcula si no se pasa `--pace`

**Output:** 24 columnas en Excel incluyendo Estrategia, Zona objetivo, Precio base zona, Ajuste RMS, Precio final Flex, Precio NRF (−10%), Precio 7n (−5%), Motivo RMS, Suelo, Techo.

**pricing_output.json** es leído por `visualizar.py` para poblar el bloque Huecos y Pricing del dashboard.

### Dashboard — Revenue Decision Cockpit

Refactoring completo del dashboard. De 22 visualizaciones a 14 elementos (11 charts + 3 bloques nuevos).

**Nueva arquitectura — 7 secciones:**

| # | Sección | Contenido |
|---|---------|-----------|
| 1 | Ritmo de ventas | C17+ Pace + ADR (doble eje) |
| 2 | Huecos y Pricing | Tabla desde pricing_output.json — riesgo, acción, gap mercado |
| 3 | Posicionamiento | Mini-form MPI con localStorage |
| 4 | Ingresos | C1 (mensual) + C7+ (anual ingresos+ADR) |
| 5 | Ocupación y PM | C3 + C5 + C14 + C6 + sparktable |
| 6 | Conversión | Lead KPI inline + C15 + C16 |
| 7 | Salud | Superhost panel + C21 + C22+ |

**Eliminados (8 charts):** C2 (fusionado en C7+), C4, C8, C9, C10, C18, C19, C23, C24

**C17+ Pace + ADR:** doble eje — barras OTB (eje izquierdo) + puntos discretos ADR actual y LY (eje derecho). Tooltips enriquecidos con Δ Rev%, Δ ADR%, Δ Noches%.

**C7+ Evolución anual:** barras ingresos + línea ADR (sustituyó a C2+C7, eliminó ocupación).

**C22+ Cancelaciones:** añadida línea de tasa % en eje derecho + delta vs año anterior en tooltip.

**Bloque Huecos y Pricing:**
- Tabla generada desde `PRICING_GAPS` (pricing_output.json inyectado en dashboard)
- Columnas: Hueco · n · Temp · Estrategia · RMS · Actual (input editable) · Riesgo · Acción · vs Mkt
- Precios actuales persistidos en `localStorage` (`csj_prices`)
- Riesgo calculado client-side: nights + lead_days + future_occ_pct
- Acción automática: Subir (actual < floor×0.95) / Bajar (actual > ceiling) / Mantener

**Bloque Market Positioning:**
- 4 inputs: mi precio actual, mercado vendido, mercado disponible, presión (dropdown)
- MPI = mi precio / mercado vendido. Interpretación: <0.80 muy barato · 0.80–0.95 competitivo · 0.95–1.10 en mercado · >1.10 agresivo
- Gap vs vendido y vs disponible automáticos
- Todo persistido en `localStorage` (`csj_mkt`, `csj_my_price`)
- Actualizar también recalcula la columna "vs Mkt" en la tabla de huecos

**Lead Time mini-KPI:** sustituye C18+C19. Muestra lead medio del año seleccionado + delta % vs año anterior. Inline, sin gráfico.

**Fix:** sección Evaluaciones abre por defecto en el trimestre en curso (`shIdx = 0`), no en el siguiente.

### Estado de datos tras sesión

- **reservas.json:** 590 registros (503 confirmadas, 87 canceladas)
- **reviews.json:** 350 evaluaciones
- **Auditoría:** 0 CRÍTICOS, 22 AVISOS (todos históricos o sin booking_date)

---

---

## Cambios aplicados 2026-05-22 (sesión 2)

### Dashboard v3 — refinements completos

**Arquitectura revisada (6 secciones, Posicionamiento global eliminado):**

| # | Sección | Contenido |
|---|---------|-----------|
| 1 | Huecos y Pricing | Tabla con filas expandibles de mercado por hueco |
| 2 | Ritmo de ventas | C17 Pace + ADR (doble eje) |
| 3 | Ingresos | C1 + C7 |
| 4 | Ocupación y PM | C3 + C5 + C14 + sparktable (C6 eliminado) |
| 5 | Demanda Airbnb | Lead KPI + C15 + C16 (antes "Conversión") |
| 6 | Salud | Superhost panel + C21 + C22 |

**Cambios implementados:**

1. **Huecos expandibles con mercado por hueco** — click en fila abre panel con: Mkt vendido, Mkt disponible, Presión, Fecha revisión, Guardar. localStorage key = `csj_mkt_{start_date}`. Fila principal muestra badge MPI si hay datos. MPI thresholds: <0.80 Muy barato / 0.80-0.95 Competitivo / 0.95-1.10 En mercado / >1.10 Agresivo. Posicionamiento global (drawMarketPos/saveMkt) eliminado.

2. **Acción mejorada** — considera: actual vs floor/ceiling, MPI vs mercado, presión de mercado. Resultados: Subir / Subir + mkt / Subir (mkt) / Oportunidad / Subir leve / Mantener / Mantener* / Revisar / Bajar.

3. **6º KPI — Huecos abiertos** — muestra count + RMS medio + fecha próximo hueco. Grid KPI: 3 columnas desktop, 2 columnas tablet, 1 columna móvil.

4. **Robustez técnica** — `safeDraw(fn, name)` envuelve cada drawXXX en try/catch. `window.onerror` + `div#err-banner` muestran error JS visible. Guard Chart.js: si no carga muestra mensaje y no ejecuta charts. Inicialización segura con if/else separados para Chart.defaults y tooltip config.

5. **Sparktable tooltip** — `title` attribute en cada celda: año · mes · X% · N/D noches.

6. **Renombrado** — "Conversión" → "Demanda Airbnb".

7. **Dead code eliminado** — drawC2, drawC4, drawC9, drawC10, drawC18, drawC19, drawC23, drawC24; C6 "ADR anual" (redundante con C7); COSTES_ANN / NETO_ANN (Python + JS).

8. **Secciones reordenadas** — Huecos antes que Pace; Posicionamiento global eliminado.

**Refinements sesión 3 (9 puntos):**
- `err-banner` div añadido al HTML
- Chart.js safe init (guard si no carga)
- KPI grid: 3-col desktop, responsive
- Título: "CEO Dashboard" → "Revenue Cockpit" en header, h1 y footer
- Confirmación visual al guardar datos de mercado (botón verde + "✓ Guardado" 2.5s)
- Tooltip en celda Acción: motivo detallado por cada caso (precio bajo suelo, alto techo, MPI, presión, etc.)
- C6 "ADR anual — evolución" eliminado (cubierto por C7)
- COSTES_ANN / NETO_ANN eliminados de Python y JS
- Tooltip nativo sparktable mantenido sin cambios

**Deploy:** commit `21320f9` (v3 base) + `19097d1` (refinements).

*Documento actualizado el 22/05/2026*

---

## Cambios aplicados 2026-05-25

### Sistema de colores semántico

Reemplaza el sistema anterior (y1=azul, y2=naranja). Ver tabla en "Colores de graficas" arriba.

**Implementación:**
- Constantes JS `COL_ING`, `COL_OCU`, `COL_ADR`, `COL_VIS`, `COL_RES`, `COL_CANC` al inicio del bloque JS
- Variables CSS `--col-ing`, `--col-ocu`, etc. en `:root`
- `makeDatasetLine(year, data, isPrimary, col)` recibe el color como parámetro
- Año principal: color sólido, grosor 3. Año comparativa: color + `'70'` (hex opacity), `borderDash:[5,5]`, grosor 1.5

### makeLegendLabels() — iconos de leyenda para líneas discontinuas

Helper que devuelve un objeto `labels` para Chart.js que sustituye el círculo por una línea en la leyenda cuando el dataset tiene `borderDash`. Se pasa en `options.plugins.legend.labels` de cada chart.

```javascript
function makeLegendLabels(extra) {
  return Object.assign({
    usePointStyle: true,
    font: {size: 10},
    generateLabels: function(chart) {
      const items = Chart.defaults.plugins.legend.labels.generateLabels(chart);
      items.forEach(function(item) {
        const ds = chart.data.datasets[item.datasetIndex];
        if (ds && ds.borderDash && ds.borderDash.length) { item.pointStyle = 'line'; }
      });
      return items;
    }
  }, extra || {});
}
```

### niceMax() — valores enteros en el tope del eje

`Math.max(...) * 1.35` producía decimales en el top del eje (ej. 147.555). `niceMax(v, step)` redondea hacia arriba al múltiplo de `step` (por defecto 10). Se aplica en todos los `suggestedMax` de Chart.js.

```javascript
function niceMax(v, step) { step = step || 10; return Math.ceil(v / step) * step; }
```

### pace_adr_otb — fórmula ADR correcta en Pace Report

Nueva variable Python `pace_adr_otb` que calcula el ADR mensual OTB usando `sum(pm * nights) / sum(nights)`, excluyendo la cleaning fee. Reemplaza el cálculo incorrecto anterior (`total / nights`) que inflaba el ADR por la limpieza.

- Solo cuenta reservas con `booking_date <= cutoff` (misma fecha que los bars OTB)
- Excluye continuaciones cross-month (`code='' y total=0`)
- Resultado inyectado en JS como `PACE_ADR = {str(year): [12 valores o null]}`

### Pace Report — restauración eje ADR + Cierre en canvas

**Eje y1 (ADR):** restaurado a la derecha del Pace Report. Los puntos ADR se posicionan con `y1Scale.getPixelForValue(adr)`, no a offset fijo.

**Línea Cierre año anterior:** dibujada directamente en el canvas del plugin `paceAdr` (en `afterDatasetsDraw`), centrada sobre la barra OTB del año anterior (`bx2[i]`). No es un dataset Chart.js porque Chart.js posicionaría los puntos en el centro categórico (entre las dos barras agrupadas), no sobre la barra correcta.

**Dataset fantasma para leyenda:** `{ label:'Cierre '+y2, data:Array(period).fill(null), type:'line', borderDash:[6,4], borderWidth:1.5, pointRadius:0, showLine:false }` — aparece en la leyenda con icono de línea discontinua pero no dibuja nada; el dibujo real lo hace el plugin.

### Tabla Huecos — rediseño a tarjetas numeradas

La tabla de huecos anterior tenía inputs de mercado por fila (Mkt vendido, Mkt disponible, Presión) que requerían mantenimiento manual. Eliminada completamente. Nueva tabla:

- **Layout:** tarjetas CSS grid, columnas `36px 1fr 64px 88px 56px 108px`, `column-gap:16px`
- **Por tarjeta:** número circular, fechas DD/MM/YY, badge "Xn", pill temporada (color por banda), antelación, precio RMS hero (grande, amarillo)
- **Borde izquierdo** coloreado por temporada (azul=alta, amarillo=media, slate=baja)
- **Eliminado:** toda la lógica de mercado, Riesgo, Acción, vs Mkt, inputs localStorage

### Estado de auditoría (2026-05-25)

```
OK:        146
AVISOS:     22  (solapes históricos + 6 sin booking_date + PM 2020 delta 5.7%)
CRÍTICOS:    0
Estado:    OK para generar
```

**Avisos conocidos pendientes de resolver:**
- 6 reservas sin `booking_date` (2015-09, 2024-01, 2024-07, 2024-11, 2025-01, 2025-08) — afectan al cálculo OTB del Pace Report para esos meses
- PM 2020: dashboard=66.33€ vs correcto=70.34€ (delta 5.7%) — causa pendiente de identificar
- 14 solapes históricos (reservas pre-2021, ambas cerradas, sin impacto operativo)

---

## Cambios aplicados 2026-05-25 (sesión 2) — Auditoría económica

### Duplicado eliminado: Arthur Schaber

Detectado mediante el nuevo check de duplicados: el mismo huésped tenía dos registros para feb-mar 2026.
- **Eliminados:** code='' Feb 2026 (162.75€) + code='' Mar 2026 (54.25€)
- **Conservado:** HMZRBPTXRS (217.41€ Feb + 0€ Mar)
- **Impacto:** Marzo 2026 corregido de 2153€ → 2099€

### booking_dates estimados (6 registros)

Registros sin `booking_date` estimados con la heurística `checkin - 4 meses`:

| Huésped | Mes | booking_date estimado |
|---------|-----|----------------------|
| Bernhard | 2015-09 | 2015-04-27 (del registro padre) |
| Maitane Renart | 2024-01 | 2023-09-01 |
| Lucy Rankin | 2024-07 | 2024-03-01 |
| Fabio Mora | 2024-11 | 2024-10-07 (del registro padre) |
| Isabel Jung | 2025-01 | 2024-09-01 |
| Marta Berdejo | 2025-08 | 2025-04-01 |

### Dmitry Shpak — corrección de noches

- **Checkin:** 2026-08-18 (correcto). **Checkout real:** 2026-08-25 (7n, no 8n)
- **Tiani Les** entra el mismo día (25/ago) — es cambio de día, no solapamiento
- **nights:** 8 → 7. **pm:** 105.0 → 120.0. **total:** 900€ (sin cambio, cuadra: 7×120+60=900)

### auditar_dashboard.py — auditoría económica (nuevo sistema)

El auditor pasa de "integridad estructural" a "coherencia de negocio". Añadidos 4 nuevos checks:

**1. `audit_duplicados()`**
- Detecta dos registros del mismo huésped en el mismo mes (guest-mes duplicado) → AVISO
- Detecta código Airbnb apareciendo en más de un mes → CRÍTICO
- Detecta registro sin código ni checkin pero con ingreso → AVISO
- Solo aplica a códigos reales Airbnb: `len>=6 AND not isdigit() AND isalnum()` (evita false positives con códigos históricos numéricos)

**2. `audit_distorsion_crossmonth()`**
- Para cada reserva cross-month, calcula cuántos € corresponden económicamente al mes siguiente
- Fórmula: `distorsion = pm_eff × nights_next_month`; `pct_mes = distorsion / total_mes × 100`
- **AVISO** si distorsion >= 150€ OR pct_mes >= 15%
- **CRÍTICO** (solo reciente, no histórico) si pct_mes >= 50% AND distorsion >= 400€
- Muestra: noches en cada mes, total reserva, distorsión €, % del mes, % de noches en mes siguiente

**3. `audit_anomalias_economicas()`**
- Compara ingresos de cada mes de los últimos 2 años contra mediana histórica del mismo mes calendario
- Referencias: años con al menos 3 años válidos (excluyendo COVID 2020, excluyendo año actual y futuro)
- **AVISO** si delta >= +50% o <= -40%
- **CRÍTICO** si delta >= +100% o <= -60%
- Si cross-month explica la anomalía: baja nivel y omite si el delta residual está dentro del rango normal
- En el campo `notes`: atribuye la causa ("Distorsión cross-month: +689€") con delta ajustado

**4. `audit_proteccion_historica()`**
- Carga `output/audit_baseline.json` si existe (snapshot de métricas validadas)
- Compara ingresos y PM por mes. AVISO si delta >= 5%, CRÍTICO si >= 15%
- El baseline se guarda automáticamente al final de cada auditoría sin CRÍTICOs (`_save_baseline()`)

**Constantes añadidas:**
```python
BASELINE_PATH   = OUTPUT / "audit_baseline.json"
COVID_YEARS     = {2020}
REF_MIN_YEARS   = 3
ANOM_WARN_PCT   = 50.0   # +50% / -40% → AVISO
ANOM_CRIT_PCT   = 100.0  # +100% / -60% → CRÍTICO
CROSS_WARN_EUR  = 150
CROSS_WARN_PCT  = 15.0
CROSS_CRIT_EUR  = 400
CROSS_CRIT_PCT  = 35.0
BASELINE_WARN_PCT = 5.0
BASELINE_CRIT_PCT = 15.0
```

### Estado de auditoría tras sesión

```
OK:        147
AVISOS:     43  (solapes históricos + cross-month + anomalías 2025 + duplicados potenciales + PM 2020)
CRÍTICOS:    0
Estado:    OK para generar
```

**Baseline guardado en:** `output/audit_baseline.json` (snapshot de métricas del 2026-05-25)

**Avisos que requieren revisión de Dani:**
- Lucy Rankin 2024-07: dos registros code='' (6n/723€ con checkin + 2n/270€ sin checkin) — posibles dos estancias separadas o error de entrada

---

## Cambios aplicados 2026-05-26

### Bug crítico resuelto: dashboard en blanco

**Causa:** `let shIdx = 0` declarado dos veces en el mismo `<script>` (líneas 1017 y 1443 de `visualizar.py`). En JS moderno, re-declarar una variable `let` en el mismo scope es un SyntaxError que rompe toda la página.

**Causa secundaria:** `function drawNextSH(idx)` también estaba declarada dos veces (líneas 1444 y 1708).

**Fix aplicado en `visualizar.py`:**
- Eliminado el `let shIdx = 0;` duplicado en la línea 1443
- Eliminada la segunda declaración completa de `drawNextSH` (bloque 1707-1779, versión incompleta sin bad_reviews)
- Conservada la función completa (línea 1443→1550) con: selector de trimestres, rating, stats, simulación de pendientes, distribución de estrellas, bad_reviews expandibles, simulación cuántas reviews necesito
- Añadido guard `if(!ct) return;` a la función conservada

**Lección:** al restaurar código de una versión anterior, verificar siempre con `grep "function drawNextSH\|let shIdx"` que no haya declaraciones duplicadas.

### Chart.js movido al final del body

`<script src="chart.js">` estaba en `<head>` sin `defer` — script bloqueante que impedía renderizar nada hasta que el CDN cargara. Movido a justo antes del script inline al final de `<body>`. El HTML skeleton se renderiza inmediatamente; Chart.js carga al final.

### Funciones HTML puro desacopladas de Chart.js

`drawKPIs`, `drawSpark`, `drawHuecos` y `drawNextSH` generan HTML puro sin Chart.js. Se llaman ahora **antes** del guard `if(typeof Chart!=='undefined')`, de modo que tablas y paneles aparecen aunque Chart.js tarde o falle.

### Sparktable — fix scroll horizontal móvil

- `min-width:620px` en `.spark-table` fuerza scroll horizontal
- Wrapper `width:100%;overflow-x:auto;-webkit-overflow-scrolling:touch` envuelve la tabla
- `min-width:36px` en `th` y `td` garantiza columnas visibles
- Barras subidas de 26px a 36px de alto
- Media query móvil movida después de los estilos base para que tome precedencia

### Deploy: GitHub Actions (sustituye legacy Jekyll)

El sistema legacy de GitHub Pages fallaba silenciosamente porque Jekyll interpreta los `{{` del JS como Liquid templates, bloqueando el deploy. Solución:

1. Añadido `.nojekyll` al repo
2. Creado `.github/workflows/deploy.yml` con `actions/deploy-pages`
3. Cambiado `build_type` a `workflow` via API

**Desde ahora cada `git push` despliega en ~22 segundos via GitHub Actions.** El sistema legacy nunca más.

```yaml
# .github/workflows/deploy.yml
on: push (branch: master)
jobs: checkout → configure-pages → upload-artifact → deploy-pages
```
