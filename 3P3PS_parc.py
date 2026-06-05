# Simulación combinada de colas — MULTI-PUESTO (3 puestos de servicio)
#
# Flags heredados de simulacion_combinada:
#   CON_AUSENCIAS_SERVIDOR  -> cada puesto tiene su propio ciclo trabajo/descanso
#   CON_ABANDONO            -> tiempo máx. de espera aleatorio por cliente
#   CON_PRIORIDAD           -> cola A (alta) y cola B (baja) globales
#   CON_ZONA_SEGURIDAD      -> zona de tránsito antes del primer puesto disponible
#
# Flags nuevos — elegir exactamente uno:
#   MODALIDAD_INDEPENDIENTE -> 3 colas + 3 puestos independientes (cliente elige al azar)
#   MODALIDAD_PARALELO      -> 1 cola + 3 puestos en paralelo (va al primer libre)
#   MODALIDAD_SERIE         -> 1 cola + 3 puestos en serie (cliente pasa por los 3)

import random
from datetime import datetime, timedelta

# =============================================================================
# CONFIGURACIÓN
# =============================================================================

HORA_INICIO = datetime(2024, 1, 1, 8, 0, 0)
DURACION    = timedelta(hours=3)
T_MAX       = HORA_INICIO + DURACION

N_PUESTOS   = 3   # número de puestos de servicio

# Flags heredados
CON_AUSENCIAS_SERVIDOR = False
CON_ABANDONO           = True
CON_PRIORIDAD          = False
CON_ZONA_SEGURIDAD     = False

# Flags de modalidad — activar exactamente uno
MODALIDAD_INDEPENDIENTE = False
MODALIDAD_PARALELO      = False
MODALIDAD_SERIE         = True

# Tiempos de llegada — en segundos
TLL_MIN,   TLL_MAX   = 40, 60
TLL_A_MIN, TLL_A_MAX = 40, 60
TLL_B_MIN, TLL_B_MAX = 60, 90

# Tiempo de servicio — en segundos (independiente por puesto)
# Cada entrada corresponde a un puesto: [PS1, PS2, PS3, ...]
# Si se agregan puestos (N_PUESTOS > 3), extender estas listas en consecuencia
TS_MIN = [300, 900]
TS_MAX = [360, 1200]

# Ausencias — en segundos (independiente por puesto)
# Cada entrada corresponde a un puesto: [PS1, PS2, PS3, ...]
# Si se agregan puestos (N_PUESTOS > 3), extender estas listas en consecuencia
TTRAB_MIN = [120, 150, 180]   # tiempo de trabajo antes de salir, por puesto
TTRAB_MAX = [180, 210, 240]
TDES_MIN  = [ 30,  20,  40]   # duración de la ausencia, por puesto
TDES_MAX  = [ 60,  40,  60]

# Abandono — en segundos (aleatorio por cliente)
TESP_MIN, TESP_MAX = 60, 180

# Capacidad máxima de la cola global (None = sin límite)
# Cuando la cola está llena, el cliente es rechazado/bloqueado
CAP_COLA = 10

# =============================================================================
# GENERADORES
# =============================================================================

def gen_tll():   return timedelta(seconds=random.uniform(TLL_MIN,   TLL_MAX))
def gen_tll_A(): return timedelta(seconds=random.uniform(TLL_A_MIN, TLL_A_MAX))
def gen_tll_B(): return timedelta(seconds=random.uniform(TLL_B_MIN, TLL_B_MAX))
def gen_ts(p):   return timedelta(seconds=random.uniform(TS_MIN[p],  TS_MAX[p]))
def gen_ttrab(p): return timedelta(seconds=random.uniform(TTRAB_MIN[p], TTRAB_MAX[p]))
def gen_tdes(p):  return timedelta(seconds=random.uniform(TDES_MIN[p],  TDES_MAX[p]))
def gen_tesp():  return timedelta(seconds=random.uniform(TESP_MIN,  TESP_MAX))
def gen_tzona(): return timedelta(seconds=random.uniform(TZONA_MIN, TZONA_MAX))

# =============================================================================
# ESTADO DE CADA PUESTO
# Cada puesto p (0,1,2) tiene:
#   estado[p]          : 0=libre, 1=ocupado
#   presente[p]        : True/False (ausencias)
#   prox_fin[p]        : próximo fin de servicio
#   prox_salida[p]     : próxima salida del servidor
#   prox_regreso[p]    : próximo regreso del servidor
#   trest[p]           : tiempo restante de servicio interrumpido
# =============================================================================

INF = datetime.max

estado   = [0]       * N_PUESTOS
presente = [True]    * N_PUESTOS
prox_fin = [INF]     * N_PUESTOS
trest    = [timedelta(0)] * N_PUESTOS

if CON_AUSENCIAS_SERVIDOR:
    prox_salida  = [HORA_INICIO + gen_ttrab(p) for p in range(N_PUESTOS)]
    prox_regreso = [INF] * N_PUESTOS
else:
    prox_salida  = [INF] * N_PUESTOS
    prox_regreso = [INF] * N_PUESTOS

# Zona de seguridad: solo para PARALELO y SERIE (una zona compartida)
estado_zona  = 0
prox_zona_ps = INF   # cuando el cliente en zona llega al puesto destino
zona_destino = -1    # puesto al que se dirige el cliente en zona

# =============================================================================
# COLAS
# Modalidad independiente: cola_ind[p] por puesto
# Modalidad paralelo/serie: cola_A y cola_B globales
# Cada entrada: (hora_llegada, hora_abandono) si CON_ABANDONO, si no (hora_llegada,)
# =============================================================================

cola_A   = []
cola_B   = []
cola_ind = [[] for _ in range(N_PUESTOS)]   # solo para MODALIDAD_INDEPENDIENTE

# En MODALIDAD_SERIE: cola de espera entre puestos consecutivos
# cola_serie[p] = clientes esperando para entrar al puesto p (p=1,2 entre puestos)
cola_serie = [[] for _ in range(N_PUESTOS)]

# =============================================================================
# EVENTOS DE LLEGADA
# =============================================================================

t_actual     = HORA_INICIO
prox_llegada_A = HORA_INICIO + (gen_tll_A() if CON_PRIORIDAD else gen_tll())
prox_llegada_B = HORA_INICIO + gen_tll_B() if CON_PRIORIDAD else INF

# =============================================================================
# CONTADORES
# =============================================================================

total_atendidos  = 0   # clientes que completaron todos los puestos requeridos
total_abandonos  = 0
total_rechazados = 0   # clientes bloqueados por cola llena
resultados       = []

# =============================================================================
# FUNCIONES AUXILIARES
# =============================================================================

def fmt(t):
    return t.strftime("%H:%M:%S") if t != INF else "*"

def nueva_entrada(t):
    if CON_ABANDONO:
        return (t, t + gen_tesp())
    return (t,)

def proximo_ab(cola):
    if not CON_ABANDONO or not cola:
        return INF
    return min(e[1] for e in cola)

def eliminar_ab(cola, t_ab):
    for i, e in enumerate(cola):
        if e[1] == t_ab:
            cola.pop(i)
            return True
    return False

def puesto_libre_disponible():
    """Devuelve índice del primer puesto libre y con servidor presente, o -1."""
    for p in range(N_PUESTOS):
        if estado[p] == 0 and presente[p]:
            return p
    return -1

def iniciar_en_puesto(p, t):
    """Arranca el servicio en el puesto p en el instante t."""
    global estado_zona, prox_zona_ps, zona_destino
    estado[p] = 1
    if MODALIDAD_SERIE and p == 0 and CON_ZONA_SEGURIDAD:
        # La zona solo aplica antes del primer puesto en serie
        estado_zona  = 1
        prox_zona_ps = t + gen_tzona()
        zona_destino = 0
        estado[p]    = 0   # aún no llegó, espera en zona
    elif not MODALIDAD_SERIE and CON_ZONA_SEGURIDAD:
        # Paralelo: zona compartida antes de cualquier puesto
        estado_zona  = 1
        prox_zona_ps = t + gen_tzona()
        zona_destino = p
        estado[p]    = 0
    else:
        prox_fin[p] = t + gen_ts(p)

def siguiente_de_cola_global():
    """Cola A tiene prioridad sobre B (globales)."""
    if cola_A:
        return cola_A, "A"
    if cola_B:
        return cola_B, "B"
    return None, None

def cola_llena():
    """Devuelve True si la cola global alcanzó la capacidad máxima."""
    if CAP_COLA is None:
        return False
    return (len(cola_A) + len(cola_B)) >= CAP_COLA

def hay_cola_global():
    return bool(cola_A) or bool(cola_B)

def grafico():
    """Representación ASCII del estado actual."""
    partes = []
    for p in range(N_PUESTOS):
        if not presente[p]:
            partes.append(f"PS{p+1}[X]")
        elif estado[p] == 1:
            partes.append(f"PS{p+1}[O]")
        else:
            partes.append(f"PS{p+1}[ ]")
    total_cola = sum(len(c) for c in [cola_A, cola_B] + cola_ind + cola_serie)
    cola_str = " O" * min(total_cola, 6)
    if total_cola > 6:
        cola_str += f"...(+{total_cola-6})"
    return " ".join(partes) + cola_str

def registrar(t, evento):
    fila = [
        fmt(t),
        evento,
    ]
    # Estado de cada puesto
    for p in range(N_PUESTOS):
        fila.append(estado[p])
        if CON_AUSENCIAS_SERVIDOR:
            fila.append(1 if presente[p] else 0)
    # Colas
    if MODALIDAD_INDEPENDIENTE:
        for p in range(N_PUESTOS):
            fila.append(len(cola_ind[p]))
    else:
        fila.append(len(cola_A))
        if CON_PRIORIDAD:
            fila.append(len(cola_B))
        if MODALIDAD_SERIE:
            for p in range(1, N_PUESTOS):
                fila.append(len(cola_serie[p]))
    if CON_ZONA_SEGURIDAD and not MODALIDAD_INDEPENDIENTE:
        fila.append(estado_zona)
    fila.append(grafico())
    resultados.append(fila)

# =============================================================================
# LOOP PRINCIPAL
# =============================================================================

registrar(t_actual, "---VECTOR INICIAL---")

while t_actual < T_MAX:

    # Recolectar todos los eventos posibles
    candidatos = [prox_llegada_A, prox_llegada_B]
    candidatos += prox_fin
    candidatos += prox_salida
    candidatos += prox_regreso
    if CON_ZONA_SEGURIDAD and not MODALIDAD_INDEPENDIENTE:
        candidatos.append(prox_zona_ps)

    # Abandonos
    if MODALIDAD_INDEPENDIENTE:
        for p in range(N_PUESTOS):
            candidatos.append(proximo_ab(cola_ind[p]))
    else:
        candidatos.append(proximo_ab(cola_A))
        candidatos.append(proximo_ab(cola_B))
        if MODALIDAD_SERIE:
            for p in range(1, N_PUESTOS):
                candidatos.append(proximo_ab(cola_serie[p]))

    sig = min(candidatos)

    if sig >= T_MAX:
        break

    t_actual = sig

    # ── Determinar tipo de evento ─────────────────────────────────────────────

    # Abandonos globales
    ab_A = proximo_ab(cola_A)
    ab_B = proximo_ab(cola_B)
    ab_ind = [proximo_ab(cola_ind[p]) for p in range(N_PUESTOS)]
    ab_ser = [proximo_ab(cola_serie[p]) for p in range(1, N_PUESTOS)]

    if MODALIDAD_INDEPENDIENTE:
        ab_min_ind = min(ab_ind)
    else:
        ab_min_ind = INF

    ab_global = min(ab_A, ab_B)
    ab_serie_min = min(ab_ser) if MODALIDAD_SERIE else INF
    ab_min = min(ab_global, ab_min_ind, ab_serie_min)

    # Fin de servicio más cercano
    fin_min = min(prox_fin)
    fin_p   = prox_fin.index(fin_min) if fin_min != INF else -1

    # Salida/regreso más cercano
    sal_min = min(prox_salida)
    sal_p   = prox_salida.index(sal_min) if sal_min != INF else -1
    reg_min = min(prox_regreso)
    reg_p   = prox_regreso.index(reg_min) if reg_min != INF else -1

    # Prioridad: abandono > fin_servicio > salida > regreso > zona > llegada
    if   sig == ab_min:       tipo = "abandono"
    elif sig == fin_min:      tipo = "fin_servicio"
    elif sig == sal_min:      tipo = "salida_servidor"
    elif sig == reg_min:      tipo = "regreso_servidor"
    elif sig == prox_zona_ps: tipo = "llegada_ps"
    elif sig == prox_llegada_A: tipo = "llegada_A"
    else:                     tipo = "llegada_B"

    # ── LLEGADA ───────────────────────────────────────────────────────────────
    if tipo in ("llegada_A", "llegada_B"):
        es_A = (tipo == "llegada_A")
        if es_A:
            prox_llegada_A = t_actual + (gen_tll_A() if CON_PRIORIDAD else gen_tll())
        else:
            prox_llegada_B = t_actual + gen_tll_B()

        etiqueta = ("Llegada A" if CON_PRIORIDAD else "Llegada") if es_A else "Llegada B"

        if MODALIDAD_INDEPENDIENTE:
            # Elige puesto al azar entre los disponibles; si ninguno, elige cola al azar
            libres = [p for p in range(N_PUESTOS) if estado[p] == 0 and presente[p]]
            if libres:
                p = random.choice(libres)
                iniciar_en_puesto(p, t_actual)
            else:
                p = random.randint(0, N_PUESTOS - 1)
                cola_ind[p].append(nueva_entrada(t_actual))
            registrar(t_actual, etiqueta)

        elif MODALIDAD_PARALELO:
            p = puesto_libre_disponible()
            if p >= 0 and (not CON_ZONA_SEGURIDAD or estado_zona == 0):
                iniciar_en_puesto(p, t_actual)
            elif cola_llena():
                total_rechazados += 1
                registrar(t_actual, f"{etiqueta} — RECHAZADO (cola llena)")
                continue
            else:
                (cola_A if es_A else cola_B).append(nueva_entrada(t_actual))
            registrar(t_actual, etiqueta)

        elif MODALIDAD_SERIE:
            # El cliente entra al puesto 0 si está libre
            if estado[0] == 0 and presente[0] \
                    and (not CON_ZONA_SEGURIDAD or estado_zona == 0):
                iniciar_en_puesto(0, t_actual)
            elif cola_llena():
                total_rechazados += 1
                registrar(t_actual, f"{etiqueta} — RECHAZADO (cola llena)")
                continue
            else:
                (cola_A if es_A else cola_B).append(nueva_entrada(t_actual))
            registrar(t_actual, etiqueta)

    # ── LLEGADA AL PS (zona de seguridad) ─────────────────────────────────────
    elif tipo == "llegada_ps":
        p = zona_destino
        estado_zona  = 0
        prox_zona_ps = INF
        zona_destino = -1
        estado[p]    = 1
        prox_fin[p]  = t_actual + gen_ts(p)
        registrar(t_actual, f"Llega a PS{p+1} (zona)")

    # ── FIN DE SERVICIO ───────────────────────────────────────────────────────
    elif tipo == "fin_servicio":
        p = fin_p
        prox_fin[p]  = INF
        estado[p]    = 0

        if MODALIDAD_SERIE and p < N_PUESTOS - 1:
            # El cliente pasa al siguiente puesto (o su cola de espera)
            sig_p = p + 1
            registrar(t_actual, f"Fin PS{p+1} → espera PS{sig_p+1}")
            if estado[sig_p] == 0 and presente[sig_p]:
                estado[sig_p]    = 1
                prox_fin[sig_p]  = t_actual + gen_ts(sig_p)
                registrar(t_actual, f"Inicia PS{sig_p+1}")
            else:
                cola_serie[sig_p].append(nueva_entrada(t_actual))
        else:
            # Cliente completó todos los puestos requeridos
            total_atendidos += 1
            registrar(t_actual, f"Fin Servicio PS{p+1}")

        # Intentar tomar siguiente de la cola correspondiente
        if MODALIDAD_INDEPENDIENTE:
            if cola_ind[p] and presente[p]:
                cola_ind[p].pop(0)
                iniciar_en_puesto(p, t_actual)
                registrar(t_actual, f"Reocupación PS{p+1}")
        elif MODALIDAD_PARALELO:
            cola_sig, tipo_sig = siguiente_de_cola_global()
            if cola_sig is not None and presente[p] \
                    and (not CON_ZONA_SEGURIDAD or estado_zona == 0):
                cola_sig.pop(0)
                iniciar_en_puesto(p, t_actual)
                registrar(t_actual, f"Reocupación PS{p+1}")
        elif MODALIDAD_SERIE:
            # Tomar de cola_serie si hay, sino de cola global para puesto 0
            if p == 0:
                cola_sig, _ = siguiente_de_cola_global()
                if cola_sig is not None and presente[0] \
                        and (not CON_ZONA_SEGURIDAD or estado_zona == 0):
                    cola_sig.pop(0)
                    iniciar_en_puesto(0, t_actual)
                    registrar(t_actual, "Reocupación PS1")
            else:
                if cola_serie[p] and presente[p]:
                    cola_serie[p].pop(0)
                    estado[p]   = 1
                    prox_fin[p] = t_actual + gen_ts(p)
                    registrar(t_actual, f"Reocupación PS{p+1}")

    # ── SALIDA DEL SERVIDOR ───────────────────────────────────────────────────
    elif tipo == "salida_servidor":
        p = sal_p
        presente[p] = False
        if estado[p] == 1 and prox_fin[p] != INF:
            trest[p]    = prox_fin[p] - t_actual
            prox_fin[p] = INF
        estado[p]        = 0
        prox_regreso[p]  = t_actual + gen_tdes(p)
        prox_salida[p]   = INF
        registrar(t_actual, f"Salida Servidor PS{p+1}")

    # ── REGRESO DEL SERVIDOR ──────────────────────────────────────────────────
    elif tipo == "regreso_servidor":
        p = reg_p
        presente[p]     = True
        prox_salida[p]  = t_actual + gen_ttrab(p)
        prox_regreso[p] = INF

        if trest[p] > timedelta(0):
            estado[p]   = 1
            prox_fin[p] = t_actual + trest[p]
            trest[p]    = timedelta(0)
            registrar(t_actual, f"Regreso Servidor PS{p+1} (retoma)")
        else:
            registrar(t_actual, f"Regreso Servidor PS{p+1}")
            # Intentar tomar de la cola
            if MODALIDAD_INDEPENDIENTE:
                if cola_ind[p]:
                    cola_ind[p].pop(0)
                    iniciar_en_puesto(p, t_actual)
                    registrar(t_actual, f"Reocupación PS{p+1}")
            elif MODALIDAD_PARALELO:
                cola_sig, _ = siguiente_de_cola_global()
                if cola_sig is not None \
                        and (not CON_ZONA_SEGURIDAD or estado_zona == 0):
                    cola_sig.pop(0)
                    iniciar_en_puesto(p, t_actual)
                    registrar(t_actual, f"Reocupación PS{p+1}")
            elif MODALIDAD_SERIE:
                if p == 0:
                    cola_sig, _ = siguiente_de_cola_global()
                    if cola_sig is not None \
                            and (not CON_ZONA_SEGURIDAD or estado_zona == 0):
                        cola_sig.pop(0)
                        iniciar_en_puesto(0, t_actual)
                        registrar(t_actual, "Reocupación PS1")
                else:
                    if cola_serie[p]:
                        cola_serie[p].pop(0)
                        estado[p]   = 1
                        prox_fin[p] = t_actual + gen_ts(p)
                        registrar(t_actual, f"Reocupación PS{p+1}")

    # ── ABANDONO ──────────────────────────────────────────────────────────────
    elif tipo == "abandono":
        total_abandonos += 1
        if MODALIDAD_INDEPENDIENTE:
            for p in range(N_PUESTOS):
                if ab_ind[p] == sig:
                    eliminar_ab(cola_ind[p], sig)
                    registrar(t_actual, f"Abandono cola PS{p+1}")
                    break
        elif MODALIDAD_SERIE and sig == ab_serie_min:
            for p in range(1, N_PUESTOS):
                if proximo_ab(cola_serie[p]) == sig:
                    eliminar_ab(cola_serie[p], sig)
                    registrar(t_actual, f"Abandono cola PS{p+1} (serie)")
                    break
        else:
            if ab_A <= ab_B:
                eliminar_ab(cola_A, ab_A)
                registrar(t_actual, "Abandono A" if CON_PRIORIDAD else "Abandono")
            else:
                eliminar_ab(cola_B, ab_B)
                registrar(t_actual, "Abandono B")

# =============================================================================
# TABLA DE RESULTADOS
# =============================================================================

modalidad_str = ("INDEPENDIENTE" if MODALIDAD_INDEPENDIENTE
                 else "PARALELO" if MODALIDAD_PARALELO
                 else "SERIE")

headers = ["Hora", "Evento"]
anchos  = [10, 42]

for p in range(N_PUESTOS):
    headers.append(f"PS{p+1}")
    anchos.append(5)
    if CON_AUSENCIAS_SERVIDOR:
        headers.append(f"Pres{p+1}")
        anchos.append(6)

if MODALIDAD_INDEPENDIENTE:
    for p in range(N_PUESTOS):
        headers.append(f"Cola{p+1}")
        anchos.append(7)
else:
    headers.append("Cola A" if CON_PRIORIDAD else "Cola")
    anchos.append(7)
    if CON_PRIORIDAD:
        headers.append("Cola B")
        anchos.append(7)
    if MODALIDAD_SERIE:
        for p in range(1, N_PUESTOS):
            headers.append(f"C→PS{p+1}")
            anchos.append(7)

if CON_ZONA_SEGURIDAD and not MODALIDAD_INDEPENDIENTE:
    headers.append("Zona")
    anchos.append(5)

headers.append("Gráfico")
anchos.append(35)

plantilla = " ".join([f"{{:<{a}}}" for a in anchos])

print(f"\n{'='*sum(anchos)}")
print(f"  SIMULACIÓN MULTI-PUESTO — MODALIDAD: {modalidad_str}  |  N_PUESTOS: {N_PUESTOS}")
print(f"{'='*sum(anchos)}")
print(plantilla.format(*headers))
print("-" * sum(anchos))
for fila in resultados:
    print(plantilla.format(*[str(e) for e in fila]))
print("=" * sum(anchos))

# =============================================================================
# RESULTADOS TOTALES
# =============================================================================

total_ingresados = total_atendidos + total_abandonos
print()
print("=" * 55)
print("   RESULTADOS TOTALES")
print("=" * 55)
print(f"   Modalidad:                          {modalidad_str}")
print(f"   Capacidad máxima de cola:           {CAP_COLA if CAP_COLA else 'Sin límite'}")
print(f"   Total de clientes atendidos:        {total_atendidos}")
print(f"   Total de abandonos:                 {total_abandonos}")
print(f"   Total de rechazados (cola llena):   {total_rechazados}")
if total_ingresados > 0:
    print(f"   Total ingresados al sistema:        {total_ingresados}")
    print(f"   % atendidos:                        {total_atendidos/total_ingresados*100:.1f}%")
    print(f"   % abandonos:                        {total_abandonos/total_ingresados*100:.1f}%")
    print(f"   Relación atendidos/abandonos:       {total_atendidos}/{total_abandonos}")
    if total_abandonos > 0:
        print(f"   Por cada abandono se atendieron:    {total_atendidos/total_abandonos:.2f} clientes")
print("=" * 55)