# Simulación combinada de colas
# Activa o desactiva cada característica con los flags de configuración:
#   CON_AUSENCIAS_SERVIDOR  -> servidor que sale y regresa (problema 2)
#   CON_ABANDONO            -> clientes que abandonan la cola (problema 3)
#   CON_PRIORIDAD           -> dos tipos de clientes A (alta) y B (baja) (problema 4)
#   CON_ZONA_SEGURIDAD      -> zona de tránsito entre cola y PS (problema 5)
# Cualquier combinación de flags es válida.

import pandas as pd
import random

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

T_MAX = 1000

# Flags de características — True/False
CON_AUSENCIAS_SERVIDOR = False
CON_ABANDONO           = True
CON_PRIORIDAD          = False
CON_ZONA_SEGURIDAD     = True

# Tiempos de llegada
# Si CON_PRIORIDAD = False se usa TLL, si = True se usan TLL_A y TLL_B
TLL_MIN,   TLL_MAX   = 20, 40
TLL_A_MIN, TLL_A_MAX = 20, 40   # llegadas tipo A (alta prioridad)
TLL_B_MIN, TLL_B_MAX = 30, 60   # llegadas tipo B (baja prioridad)

# Tiempo de servicio
TS_MIN,  TS_MAX  = 30, 60

# Ausencias del servidor (CON_AUSENCIAS_SERVIDOR)
TTRAB_MIN, TTRAB_MAX = 40, 60   # tiempo que trabaja antes de salir
TDES_MIN,  TDES_MAX  = 20, 40   # tiempo que dura la ausencia

# Abandono (CON_ABANDONO)
# Para espera fija poner ambos iguales, ej: TESP_MIN = TESP_MAX = 20
TESP_MIN, TESP_MAX = 10, 50     # tiempo máximo de espera en cola

# Zona de seguridad (CON_ZONA_SEGURIDAD)
TZONA_MIN, TZONA_MAX = 5, 15    # tiempo de tránsito cola -> PS

# =============================================================================
# GENERADORES
# =============================================================================

def gen_tll():    return random.uniform(TLL_MIN,   TLL_MAX)
def gen_tll_A():  return random.uniform(TLL_A_MIN, TLL_A_MAX)
def gen_tll_B():  return random.uniform(TLL_B_MIN, TLL_B_MAX)
def gen_ts():     return random.uniform(TS_MIN,    TS_MAX)
def gen_ttrab():  return random.uniform(TTRAB_MIN, TTRAB_MAX)
def gen_tdes():   return random.uniform(TDES_MIN,  TDES_MAX)
def gen_tesp():   return random.uniform(TESP_MIN,  TESP_MAX)
def gen_tzona():  return random.uniform(TZONA_MIN, TZONA_MAX)

# =============================================================================
# VARIABLES DE ESTADO
# =============================================================================

t_actual          = 0
estado_servidor   = 0       # 0 = libre, 1 = ocupado
estado_zona       = 0       # 0 = libre, 1 = ocupado  (zona de seguridad)
servidor_presente = True    # para ausencias

# Cola única o dos colas según prioridad
# Cada entrada es (hora_llegada, hora_abandono) si CON_ABANDONO, si no (hora_llegada,)
# Para prioridad: cola_A y cola_B. Para cola única: cola_A, cola_B queda vacía.
cola_A = []   # alta prioridad (o única cola si no hay prioridad)
cola_B = []   # baja prioridad

# Para ausencias: tiempo de servicio que quedaba pendiente al salir el servidor
tiempo_restante_servicio = 0

# =============================================================================
# INICIALIZACIÓN DE EVENTOS
# =============================================================================

INF = float('inf')

prox_llegada_A       = gen_tll_A() if CON_PRIORIDAD else gen_tll()
prox_llegada_B       = gen_tll_B() if CON_PRIORIDAD else INF
prox_fin_servicio    = INF
prox_llegada_ps      = INF   # zona de seguridad: cuando el cliente llega al PS
prox_salida_servidor = gen_ttrab() if CON_AUSENCIAS_SERVIDOR else INF
prox_regreso_servidor= INF

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def nueva_entrada_cola(t):
    """Devuelve la tupla que se guarda en cola según si hay abandono o no."""
    if CON_ABANDONO:
        return (t, t + gen_tesp())
    return (t,)

def proximo_abandono(cola):
    """Devuelve el tiempo de abandono más cercano de una cola, o INF."""
    if not CON_ABANDONO or not cola:
        return INF
    return min(entry[1] for entry in cola)

def pop_cliente(cola):
    """Saca el primer cliente de la cola y devuelve su tupla."""
    return cola.pop(0)

def eliminar_abandono(cola, t_abandono):
    """Elimina de la cola el cliente cuya hora de abandono coincide con t_abandono."""
    for i, entry in enumerate(cola):
        if entry[1] == t_abandono:
            cola.pop(i)
            return True
    return False

def iniciar_servicio(t):
    """Programa el fin de servicio o el ingreso a zona según configuración."""
    global estado_zona, prox_llegada_ps, prox_fin_servicio
    if CON_ZONA_SEGURIDAD:
        estado_zona     = 1
        prox_llegada_ps = t + gen_tzona()
    else:
        estado_servidor_ocupar()
        prox_fin_servicio = t + gen_ts()

def estado_servidor_ocupar():
    global estado_servidor
    estado_servidor = 1

def hay_cola():
    return bool(cola_A) or bool(cola_B)

def siguiente_de_cola():
    """Devuelve de qué cola sale el próximo cliente respetando prioridad."""
    if cola_A:
        return cola_A, "A"
    if cola_B:
        return cola_B, "B"
    return None, None

# =============================================================================
# LISTA DE RESULTADOS Y COLUMNAS
# =============================================================================

resultados = []

def registrar(t, evento):
    """Registra el estado completo del sistema en el momento del evento."""
    fila = [round(t, 1), evento, len(cola_A)]
    if CON_PRIORIDAD:
        fila.append(len(cola_B))
    fila.append(estado_servidor)
    if CON_AUSENCIAS_SERVIDOR:
        fila.append(servidor_presente)
    if CON_ZONA_SEGURIDAD:
        fila.append(estado_zona)
    resultados.append(fila)

# =============================================================================
# LOOP PRINCIPAL
# =============================================================================

while t_actual < T_MAX:

    # Calcular próximos abandonos en ambas colas
    prox_abandono_A = proximo_abandono(cola_A)
    prox_abandono_B = proximo_abandono(cola_B)
    prox_abandono   = min(prox_abandono_A, prox_abandono_B)

    siguiente_evento = min(
        prox_llegada_A,
        prox_llegada_B,
        prox_fin_servicio,
        prox_llegada_ps,
        prox_salida_servidor,
        prox_regreso_servidor,
        prox_abandono
    )

    if siguiente_evento >= T_MAX:
        break

    t_actual = siguiente_evento

    # Determinar tipo de evento (orden de prioridad ante empates)
    if   siguiente_evento == prox_abandono:          tipo_evento = "abandono"
    elif siguiente_evento == prox_salida_servidor:   tipo_evento = "salida_servidor"
    elif siguiente_evento == prox_regreso_servidor:  tipo_evento = "regreso_servidor"
    elif siguiente_evento == prox_llegada_ps:        tipo_evento = "llegada_ps"
    elif siguiente_evento == prox_fin_servicio:      tipo_evento = "fin_servicio"
    elif siguiente_evento == prox_llegada_A:         tipo_evento = "llegada_A"
    else:                                            tipo_evento = "llegada_B"

    # ── LLEGADA (tipo A o única) ──────────────────────────────────────────────
    if tipo_evento == "llegada_A":
        prox_llegada_A = t_actual + (gen_tll_A() if CON_PRIORIDAD else gen_tll())
        if estado_servidor == 0 and (not CON_ZONA_SEGURIDAD or estado_zona == 0) \
                and (not CON_AUSENCIAS_SERVIDOR or servidor_presente):
            estado_servidor_ocupar()
            iniciar_servicio(t_actual)
        else:
            cola_A.append(nueva_entrada_cola(t_actual))
        registrar(t_actual, "Llegada A" if CON_PRIORIDAD else "Llegada")

    # ── LLEGADA tipo B ────────────────────────────────────────────────────────
    elif tipo_evento == "llegada_B":
        prox_llegada_B = t_actual + gen_tll_B()
        if estado_servidor == 0 and not cola_A \
                and (not CON_ZONA_SEGURIDAD or estado_zona == 0) \
                and (not CON_AUSENCIAS_SERVIDOR or servidor_presente):
            estado_servidor_ocupar()
            iniciar_servicio(t_actual)
        else:
            cola_B.append(nueva_entrada_cola(t_actual))
        registrar(t_actual, "Llegada B")

    # ── LLEGADA AL PS (zona de seguridad) ─────────────────────────────────────
    elif tipo_evento == "llegada_ps":
        estado_zona       = 0
        estado_servidor   = 1
        prox_llegada_ps   = INF
        prox_fin_servicio = t_actual + gen_ts()
        registrar(t_actual, "Llegada al PS")

    # ── FIN DE SERVICIO ───────────────────────────────────────────────────────
    elif tipo_evento == "fin_servicio":
        estado_servidor   = 0
        estado_zona       = 0
        prox_fin_servicio = INF
        registrar(t_actual, "Fin de Servicio")

        cola_sig, tipo_sig = siguiente_de_cola()
        if cola_sig is not None and (not CON_AUSENCIAS_SERVIDOR or servidor_presente):
            pop_cliente(cola_sig)
            estado_servidor_ocupar()
            iniciar_servicio(t_actual)
            registrar(t_actual, f"Reocupación{'  cliente ' + tipo_sig if CON_PRIORIDAD else ''}")
        elif not hay_cola():
            estado_servidor = 0

    # ── SALIDA DEL SERVIDOR ───────────────────────────────────────────────────
    elif tipo_evento == "salida_servidor":
        servidor_presente = False
        if estado_servidor == 1 and prox_fin_servicio != INF:
            tiempo_restante_servicio = prox_fin_servicio - t_actual
            prox_fin_servicio        = INF
        estado_servidor       = 0
        prox_regreso_servidor = t_actual + gen_tdes()
        prox_salida_servidor  = INF
        registrar(t_actual, "Salida del Servidor")

    # ── REGRESO DEL SERVIDOR ──────────────────────────────────────────────────
    elif tipo_evento == "regreso_servidor":
        servidor_presente    = True
        prox_salida_servidor = t_actual + gen_ttrab()
        prox_regreso_servidor= INF

        if tiempo_restante_servicio > 0:
            estado_servidor          = 1
            prox_fin_servicio        = t_actual + tiempo_restante_servicio
            tiempo_restante_servicio = 0
            registrar(t_actual, "Regreso del Servidor (retoma servicio)")
        else:
            registrar(t_actual, "Regreso del Servidor")
            cola_sig, tipo_sig = siguiente_de_cola()
            if cola_sig is not None:
                pop_cliente(cola_sig)
                estado_servidor_ocupar()
                iniciar_servicio(t_actual)
                registrar(t_actual, f"Reocupación{'  cliente ' + tipo_sig if CON_PRIORIDAD else ''}")

    # ── ABANDONO ──────────────────────────────────────────────────────────────
    elif tipo_evento == "abandono":
        if prox_abandono_A <= prox_abandono_B:
            eliminar_abandono(cola_A, prox_abandono_A)
            registrar(t_actual, "Abandono A" if CON_PRIORIDAD else "Abandono")
        else:
            eliminar_abandono(cola_B, prox_abandono_B)
            registrar(t_actual, "Abandono B")

# =============================================================================
# TABLA DE RESULTADOS
# =============================================================================

columnas = ["Tiempo", "Evento", "Cola A" if CON_PRIORIDAD else "Clientes en cola"]
if CON_PRIORIDAD:
    columnas.append("Cola B")
columnas.append("Estado servidor")
if CON_AUSENCIAS_SERVIDOR:
    columnas.append("Servidor presente")
if CON_ZONA_SEGURIDAD:
    columnas.append("Estado zona")

df = pd.DataFrame(resultados, columns=columnas)
print(df.to_string(index=False))