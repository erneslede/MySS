# Simulación combinada de colas
# Activa o desactiva cada característica con los flags de configuración:
#   CON_AUSENCIAS_SERVIDOR  -> servidor que sale y regresa (problema 2)
#   CON_ABANDONO            -> clientes que abandonan la cola (problema 3)
#   CON_PRIORIDAD           -> dos tipos de clientes A (alta) y B (baja) (problema 4)
#   CON_ZONA_SEGURIDAD      -> zona de tránsito entre cola y PS (problema 5)
# Cualquier combinación de flags es válida.

import pandas as pd
import random
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

HORA_INICIO = datetime(2024, 1, 1, 8, 0, 0)   # inicio de simulación: 08:00:00
DURACION    = timedelta(hours=3)               # horizonte de simulación
T_MAX       = HORA_INICIO + DURACION

# Flags de características — True/False
CON_AUSENCIAS_SERVIDOR = True
CON_ABANDONO           = True
CON_PRIORIDAD          = False
CON_ZONA_SEGURIDAD     = False
# Tiempos de llegada — en segundos
# Si CON_PRIORIDAD = False se usa TLL, si = True se usan TLL_A y TLL_B
TLL_MIN,   TLL_MAX   = 60, 60
TLL_A_MIN, TLL_A_MAX = 60, 60   # llegadas tipo A (alta prioridad)
TLL_B_MIN, TLL_B_MAX = 60, 60   # llegadas tipo B (baja prioridad)

# Tiempo de servicio — en segundos
TS_MIN,  TS_MAX  = 40, 60

# Ausencias del servidor (CON_AUSENCIAS_SERVIDOR) — en segundos
TTRAB_MIN, TTRAB_MAX = 300, 300   # tiempo que trabaja antes de salir
TDES_MIN,  TDES_MAX  = 30, 30   # tiempo que dura la ausencia

# Abandono (CON_ABANDONO) — en segundos
# Para espera fija poner ambos iguales, ej: TESP_MIN = TESP_MAX = 20
TESP_MIN, TESP_MAX = 180, 180     # tiempo máximo de espera en cola

# Zona de seguridad (CON_ZONA_SEGURIDAD) — en segundos
TZONA_MIN, TZONA_MAX = 60, 60    # tiempo de tránsito cola -> PS

# =============================================================================
# GENERADORES
# =============================================================================

def gen_tll():    return timedelta(seconds=random.uniform(TLL_MIN,   TLL_MAX))
def gen_tll_A():  return timedelta(seconds=random.uniform(TLL_A_MIN, TLL_A_MAX))
def gen_tll_B():  return timedelta(seconds=random.uniform(TLL_B_MIN, TLL_B_MAX))
def gen_ts():     return timedelta(seconds=random.uniform(TS_MIN,    TS_MAX))
def gen_ttrab():  return timedelta(seconds=random.uniform(TTRAB_MIN, TTRAB_MAX))
def gen_tdes():   return timedelta(seconds=random.uniform(TDES_MIN,  TDES_MAX))
def gen_tesp():   return timedelta(seconds=random.uniform(TESP_MIN,  TESP_MAX))
def gen_tzona():  return timedelta(seconds=random.uniform(TZONA_MIN, TZONA_MAX))

# =============================================================================
# VARIABLES DE ESTADO
# =============================================================================

t_actual          = HORA_INICIO
estado_servidor   = 1       # 0 = libre, 1 = ocupado
estado_zona       = 0       # 0 = libre, 1 = ocupado  (zona de seguridad)
servidor_presente = False    # para ausencias

# Cola única o dos colas según prioridad
# Cada entrada es (hora_llegada, hora_abandono) si CON_ABANDONO, si no (hora_llegada,)
# Para prioridad: cola_A y cola_B. Para cola única: cola_A, cola_B queda vacía.
cola_A = []   # alta prioridad (o única cola si no hay prioridad)
cola_B = []   # baja prioridad

# Para ausencias: tiempo de servicio que quedaba pendiente al salir el servidor
tiempo_restante_servicio = timedelta(0)

# =============================================================================
# CONTADORES
# =============================================================================

HORA_UNA_HORA          = HORA_INICIO + timedelta(hours=2)

abandonos_primera_hora = 0    # a) abandonos dentro de la primera hora
atendidos_segundo_desc = 0    # b) clientes atendidos al inicio del 2do descanso
num_descansos          = 0    # cantidad de descansos iniciados
respuesta_b_registrada = False
total_atendidos = 0
total_abandonos = 0

# =============================================================================
# INICIALIZACIÓN DE EVENTOS
# =============================================================================

INF = datetime.max

prox_llegada_A       = HORA_INICIO + (gen_tll_A() if CON_PRIORIDAD else gen_tll())
prox_llegada_B       = HORA_INICIO + gen_tll_B() if CON_PRIORIDAD else INF
prox_fin_servicio    = INF
prox_llegada_ps      = INF   # zona de seguridad: cuando el cliente llega al PS
prox_salida_servidor = HORA_INICIO + gen_ttrab() if CON_AUSENCIAS_SERVIDOR else INF
prox_regreso_servidor= INF

# Ajuste por vector inicial
if CON_AUSENCIAS_SERVIDOR and not servidor_presente:
    prox_regreso_servidor = HORA_INICIO + gen_tdes()
    prox_salida_servidor  = INF

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

def cargar_cola_inicial(n_clientes, segundos_esperados):
    """
    Carga n_clientes en cola_A con hora_llegada = HORA_INICIO - segundos_esperados,
    de modo que al arrancar cada cliente ya lleva ese tiempo esperando en cola.
    Si CON_ABANDONO está activo, calcula hora_abandono desde hora_llegada con gen_tesp().
    """
    hora_llegada = HORA_INICIO - timedelta(seconds=segundos_esperados)
    for _ in range(n_clientes):
        if CON_ABANDONO:
            cola_A.append((hora_llegada, hora_llegada + gen_tesp()))
        else:
            cola_A.append((hora_llegada,))
    # si el servidor está libre, arranca con el primer cliente de la cola
    global estado_servidor, prox_fin_servicio, estado_zona, prox_llegada_ps
    if estado_servidor == 0 and hay_cola():
        cola_A.pop(0)
        if CON_ZONA_SEGURIDAD:
            estado_zona     = 1
            prox_llegada_ps = HORA_INICIO + gen_tzona()
        else:
            estado_servidor   = 1
            prox_fin_servicio = HORA_INICIO + gen_ts()

# Vector inicial: 100 clientes, todos llevan 10 segundos esperando
# cargar_cola_inicial(n_clientes=100, segundos_esperados=10)

def fmt(t):
    """Formatea un datetime como HH:MM:SS para la tabla."""
    return t.strftime("%H:%M:%S")

# =============================================================================
# LISTA DE RESULTADOS Y COLUMNAS
# =============================================================================

resultados = []

def registrar(t, evento):
    """Registra el estado completo del sistema en el momento del evento."""
    if not servidor_presente:
        ps_str = "[X]"
    elif estado_servidor == 1:
        ps_str = "[O]"
    else:
        ps_str = "[ ]"
        
    # Estructura del gráfico para que soporte la cola grande
    total_cola = len(cola_A) + len(cola_B)
    if total_cola > 8:
        graf = f"{ps_str} " + "O " * 6 + f"... (+{total_cola - 6})"
    else:
        graf = ps_str + (" O" * total_cola if total_cola > 0 else "")

    est_srv_num = 1 if estado_servidor == 1 else 0
    srv_pres_num = 1 if servidor_presente else 0

    fila = [
        fmt(t),
        fmt(prox_llegada_A) if prox_llegada_A != INF else "*",
        fmt(prox_fin_servicio) if prox_fin_servicio != INF else "*",
        evento,
        len(cola_A), #Se puede sumar len(cola_B) si activamos prioridad
        est_srv_num,
        srv_pres_num
    ]
    # Si tenemos zona de seguridad activa, guardamos su estado numérico
    if CON_ZONA_SEGURIDAD:
        fila.append(1 if estado_zona == 1 else 0)
        
    fila.append(graf)
    resultados.append(fila)

# =============================================================================
# LOOP PRINCIPAL
# =============================================================================

registrar(t_actual, "---VECTOR INICIAL---") # Imprime los valores del vector inicial como un evento

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
    elif siguiente_evento == prox_fin_servicio:      tipo_evento = "fin_servicio"
    elif siguiente_evento == prox_salida_servidor:   tipo_evento = "salida_servidor"
    elif siguiente_evento == prox_regreso_servidor:  tipo_evento = "regreso_servidor"
    elif siguiente_evento == prox_llegada_ps:        tipo_evento = "llegada_ps"
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
        total_atendidos += 1
        estado_servidor   = 0
        estado_zona       = 0
        prox_fin_servicio = INF
        if not respuesta_b_registrada:
            atendidos_segundo_desc += 1
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
        num_descansos += 1
        if num_descansos == 2 and not respuesta_b_registrada:
            respuesta_b_registrada = True
        registrar(t_actual, "Salida del Servidor")

    # ── REGRESO DEL SERVIDOR ──────────────────────────────────────────────────
    elif tipo_evento == "regreso_servidor":
        servidor_presente    = True
        prox_salida_servidor = t_actual + gen_ttrab()
        prox_regreso_servidor= INF

        if tiempo_restante_servicio > timedelta(0):
            estado_servidor          = 1
            prox_fin_servicio        = t_actual + tiempo_restante_servicio
            tiempo_restante_servicio = timedelta(0)
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
        total_abandonos += 1
        if prox_abandono_A <= prox_abandono_B:
            eliminar_abandono(cola_A, prox_abandono_A)
            registrar(t_actual, "Abandono A" if CON_PRIORIDAD else "Abandono")
        else:
            eliminar_abandono(cola_B, prox_abandono_B)
            registrar(t_actual, "Abandono B")
        if t_actual <= HORA_UNA_HORA:
            abandonos_primera_hora += 1

# =============================================================================
# TABLA DE RESULTADOS
# =============================================================================

headers = [
    "Hora", 
    "Próxima llegada", 
    "Próximo fin de servicio", 
    "Evento", 
    "Clientes en cola", 
    "Estado servidor", 
    "Servidor presente"
]
if CON_ZONA_SEGURIDAD:
    headers.append("Zona seg.")
headers.append("Gráfico")

# Definimos los anchos fijos de cada columna para que NADA se mueva
# Los números representan la cantidad de caracteres que reservamos para cada columna
anchos = [10, 18, 26, 38, 18, 17, 18]
if CON_ZONA_SEGURIDAD:
    anchos.append(11)
anchos.append(20) # Ancho para el gráfico

plantilla = " ".join([f"{{:<{a}}}" for a in anchos])

print("\n" + "=" * sum(anchos))
# Imprimir encabezados
print(plantilla.format(*headers))
print("-" * sum(anchos))

# Imprimir cada fila perfectamente alineada
for fila in resultados:
    # Convertimos todos los elementos a string para el formateador
    fila_str = [str(elemento) for elemento in fila]
    print(plantilla.format(*fila_str))

print("=" * sum(anchos))    

# =============================================================================
# RESPUESTAS
# =============================================================================

print()
print("=" * 55)
print("   RESPUESTAS")
print("=" * 55)
print(f"   a) Abandonos en la primera hora")
print(f"      ({fmt(HORA_INICIO)} - {fmt(HORA_UNA_HORA)}): {abandonos_primera_hora} cliente/s")
print()
if respuesta_b_registrada:
    print(f"   b) Clientes atendidos al inicio del 2do descanso: {atendidos_segundo_desc}")
else:
    print(f"   b) El 2do descanso no ocurrió en el horizonte de simulación")
print("=" * 55)

print()
print("=" * 55)
print("   RESULTADOS TOTALES")
print("=" * 55)
print(f"   Total de clientes/piezas atendidos: {total_atendidos}")
print(f"   Total de abandonos: {total_abandonos}")
print("=" * 55)