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
│   ├── validar.py         Valida reservas.json (se ejecuta automáticamente)
│   ├── pricing.py         RMS determinista — genera output/pricing_output.xlsx
│   └── utils/             Scripts de debug (no operativos)
├── output/
│   ├── pricing_output.xlsx
│   └── pricing_output.json
└── buzon/
    ├── entrante/          Dani deja PDFs aquí
    └── procesado/YYYY/MM/

GENERACION
══════════
python scripts/visualizar.py  →  dashboard.html  →  git push  →  GitHub Pages
python scripts/pricing.py     →  output/pricing_output.xlsx
python scripts/validar.py     →  validación standalone
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

### 3. Actualizar reviews (cuando haya nuevo export)

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

- **y1** (ano principal): azul `#3b82f6`
- **y2** (ano comparativa): naranja `#f97316`
- **Media historica**: ambar/dorado `rgba(251,191,36,0.7)`
- **Banda historica** (min/max): gris semitransparente

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

*Documento actualizado el 27/04/2026*
