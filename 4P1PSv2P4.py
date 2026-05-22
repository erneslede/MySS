# Simulación de taller de carpintería — 3 etapas en serie
# Un carpintero procesa 6 sillas a través de:
#   Etapa 1: Armado    (30–40 min cada silla)
#   Etapa 2: Lijado    (10–20 min cada silla)
#   Etapa 3: Lustrado  ( 5–30 min cada silla)
# Cada etapa es un servidor; la salida de uno es la entrada del siguiente.

import random
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

HORA_INICIO    = datetime(2024, 1, 1, 8, 0, 0)   # inicio: 08:00:00
DURACION    = timedelta(hours=3)               # horizonte de simulación
T_MAX       = HORA_INICIO + DURACION
N_SILLAS       = 6                                # piezas a procesar

# Tiempos de cada etapa — en minutos
T_ARMADO_MIN,   T_ARMADO_MAX   = 30, 40
T_LIJADO_MIN,   T_LIJADO_MAX   = 10, 20
T_LUSTRADO_MIN, T_LUSTRADO_MAX =  5, 30

# =============================================================================
# GENERADORES
# =============================================================================

def gen_armado():   return timedelta(minutes=random.uniform(T_ARMADO_MIN,   T_ARMADO_MAX))
def gen_lijado():   return timedelta(minutes=random.uniform(T_LIJADO_MIN,   T_LIJADO_MAX))
def gen_lustrado(): return timedelta(minutes=random.uniform(T_LUSTRADO_MIN, T_LUSTRADO_MAX))

# =============================================================================
# VARIABLES DE ESTADO
# =============================================================================

t_actual = HORA_INICIO

# Estado de cada servidor: 0 = libre, 1 = ocupado
estado_armado   = 0
estado_lijado   = 0
estado_lustrado = 0

# Colas de cada etapa — cada entrada es el número de silla (1..N_SILLAS)
cola_armado   = list(range(1, N_SILLAS + 1))   # todas las sillas esperan al inicio
cola_lijado   = []
cola_lustrado = []

# Contadores de terminadas
total_terminadas = 0

# =============================================================================
# CONTADORES
# =============================================================================

sillas_terminadas = []   # lista con hora de finalización de cada silla

# =============================================================================
# INICIALIZACIÓN DE EVENTOS
# =============================================================================

INF = datetime.max

prox_fin_armado   = INF
prox_fin_lijado   = INF
prox_fin_lustrado = INF

# Al arrancar: si hay sillas en cola y el servidor está libre, arrancar
def intentar_iniciar(cola, estado_actual, gen_tiempo, t):
    """Intenta iniciar el servicio en una etapa. Devuelve (nuevo_estado, prox_fin)."""
    if estado_actual == 0 and cola:
        cola.pop(0)
        return 1, t + gen_tiempo()
    return estado_actual, INF

# Arrancar cada etapa con la primera silla disponible
estado_armado,   prox_fin_armado   = intentar_iniciar(cola_armado,   estado_armado,   gen_armado,   HORA_INICIO)
estado_lijado,   prox_fin_lijado   = intentar_iniciar(cola_lijado,   estado_lijado,   gen_lijado,   HORA_INICIO)
estado_lustrado, prox_fin_lustrado = intentar_iniciar(cola_lustrado, estado_lustrado, gen_lustrado, HORA_INICIO)

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def fmt(t):
    """Formatea datetime como HH:MM:SS."""
    return t.strftime("%H:%M:%S")

def fmt_inf(t):
    """Muestra * si es INF."""
    return "*" if t == INF else fmt(t)

# =============================================================================
# TABLA DE RESULTADOS
# =============================================================================

resultados = []

def registrar(t, evento):
    """Registra el estado completo del sistema."""

    def srv_str(estado):
        return "[O]" if estado == 1 else "[ ]"

    # Gráfico simplificado: cada etapa con su estado y cola
    graf = (
        f"ARM:{srv_str(estado_armado)}{'O'*len(cola_armado)}  "
        f"LIJ:{srv_str(estado_lijado)}{'O'*len(cola_lijado)}  "
        f"LUS:{srv_str(estado_lustrado)}{'O'*len(cola_lustrado)}"
    )

    fila = [
        fmt(t),
        fmt_inf(prox_fin_armado),
        fmt_inf(prox_fin_lijado),
        fmt_inf(prox_fin_lustrado),
        evento,
        len(cola_armado),
        len(cola_lijado),
        len(cola_lustrado),
        estado_armado,
        estado_lijado,
        estado_lustrado,
        total_terminadas,
        graf,
    ]
    resultados.append(fila)

# =============================================================================
# VECTOR INICIAL
# =============================================================================

registrar(t_actual, "---VECTOR INICIAL---")

# =============================================================================
# LOOP PRINCIPAL
# =============================================================================

while t_actual < T_MAX:

    siguiente_evento = min(prox_fin_armado, prox_fin_lijado, prox_fin_lustrado)

    if siguiente_evento == INF:
        break   # no hay más eventos posibles (no debería ocurrir)

    t_actual = siguiente_evento

    # ── Determinar tipo de evento ─────────────────────────────────────────────
    # En caso de empate: lustrado > lijado > armado (prioridad a etapas finales)
    if   siguiente_evento == prox_fin_lustrado: tipo_evento = "fin_lustrado"
    elif siguiente_evento == prox_fin_lijado:   tipo_evento = "fin_lijado"
    else:                                       tipo_evento = "fin_armado"

    # ── FIN DE ARMADO ─────────────────────────────────────────────────────────
    if tipo_evento == "fin_armado":
        estado_armado   = 0
        prox_fin_armado = INF
        cola_lijado.append("silla")          # pieza pasa a la siguiente cola
        registrar(t_actual, "Fin Armado → entra a cola Lijado")

        # Intentar iniciar la siguiente silla en armado
        if cola_armado:
            cola_armado.pop(0)
            estado_armado   = 1
            prox_fin_armado = t_actual + gen_armado()
            registrar(t_actual, "Reocupación Armado")

        # Intentar iniciar lijado si estaba libre
        if estado_lijado == 0 and cola_lijado:
            cola_lijado.pop(0)
            estado_lijado   = 1
            prox_fin_lijado = t_actual + gen_lijado()
            registrar(t_actual, "Inicio Lijado")

    # ── FIN DE LIJADO ─────────────────────────────────────────────────────────
    elif tipo_evento == "fin_lijado":
        estado_lijado   = 0
        prox_fin_lijado = INF
        cola_lustrado.append("silla")        # pieza pasa a la siguiente cola
        registrar(t_actual, "Fin Lijado → entra a cola Lustrado")

        # Intentar iniciar la siguiente silla en lijado
        if cola_lijado:
            cola_lijado.pop(0)
            estado_lijado   = 1
            prox_fin_lijado = t_actual + gen_lijado()
            registrar(t_actual, "Reocupación Lijado")

        # Intentar iniciar lustrado si estaba libre
        if estado_lustrado == 0 and cola_lustrado:
            cola_lustrado.pop(0)
            estado_lustrado   = 1
            prox_fin_lustrado = t_actual + gen_lustrado()
            registrar(t_actual, "Inicio Lustrado")

    # ── FIN DE LUSTRADO ───────────────────────────────────────────────────────
    elif tipo_evento == "fin_lustrado":
        estado_lustrado   = 0
        prox_fin_lustrado = INF
        total_terminadas += 1
        sillas_terminadas.append(t_actual)
        registrar(t_actual, f"Fin Lustrado → Silla {total_terminadas} TERMINADA")

        # Intentar iniciar la siguiente silla en lustrado
        if cola_lustrado:
            cola_lustrado.pop(0)
            estado_lustrado   = 1
            prox_fin_lustrado = t_actual + gen_lustrado()
            registrar(t_actual, "Reocupación Lustrado")

# =============================================================================
# TABLA DE RESULTADOS
# =============================================================================

headers = [
    "Hora",
    "Fin Armado",
    "Fin Lijado",
    "Fin Lustrado",
    "Evento",
    "Cola ARM",
    "Cola LIJ",
    "Cola LUS",
    "Srv ARM",
    "Srv LIJ",
    "Srv LUS",
    "Terminadas",
    "Gráfico",
]

anchos = [10, 12, 12, 14, 42, 10, 10, 10, 9, 9, 9, 11, 40]
plantilla = " ".join([f"{{:<{a}}}" for a in anchos])

separador = "=" * sum(anchos)
print("\n" + separador)
print(plantilla.format(*headers))
print("-" * sum(anchos))

for fila in resultados:
    print(plantilla.format(*[str(e) for e in fila]))

print(separador)

# =============================================================================
# RESULTADOS FINALES
# =============================================================================

duracion_total = sillas_terminadas[-1] - HORA_INICIO if sillas_terminadas else timedelta(0)
horas  = int(duracion_total.total_seconds() // 3600)
minutos = int((duracion_total.total_seconds() % 3600) // 60)
segundos = int(duracion_total.total_seconds() % 60)

print()
print("=" * 55)
print("   RESULTADOS FINALES")
print("=" * 55)
print(f"   Sillas procesadas: {total_terminadas} / {N_SILLAS}")
print(f"   Inicio:            {fmt(HORA_INICIO)}")
print(f"   Última silla:      {fmt(sillas_terminadas[-1]) if sillas_terminadas else '-'}")
print(f"   Duración total:    {horas:02d}h {minutos:02d}m {segundos:02d}s")
print()
print("   Detalle por silla:")
for i, t in enumerate(sillas_terminadas, 1):
    delta = t - HORA_INICIO
    m = int(delta.total_seconds() // 60)
    s = int(delta.total_seconds() % 60)
    print(f"   Silla {i}: terminada a las {fmt(t)}  ({m}m {s:02d}s desde inicio)")
print("=" * 55)