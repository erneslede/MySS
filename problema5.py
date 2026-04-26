# Problema 5 con tiempos aleatorios


import pandas as pd
import random

# Vector inicial
t_actual = 0
t_max = 500
estado_ps = 0               # 0 = libre, 1 = ocupado
estado_zona = 0             # 0 = libre, 1 = ocupado
clientes_en_cola = []       # lista de hora_llegada de cada cliente en cola
prox_llegada = random.uniform(30, 60)
prox_llegada_ps = float('inf')   # cuando el cliente en zona llega al PS
prox_fin_servicio = float('inf')

# Funciones generadoras de tiempos
def tiempo_llegada():
    return random.uniform(30, 60)
def tiempo_zona():           # tiempo de tránsito zona de seguridad -> PS
    return random.uniform(5, 15)
def tiempo_servicio():
    return random.uniform(20, 50)

# Lista de resultados
resultados = []

while t_actual < t_max:
    siguiente_evento = min(prox_llegada, prox_llegada_ps, prox_fin_servicio)

    if siguiente_evento >= t_max:
        break

    t_actual = siguiente_evento

    if siguiente_evento == prox_llegada_ps:
        tipo_evento = "llegada_ps"
    elif siguiente_evento == prox_fin_servicio:
        tipo_evento = "fin_servicio"
    else:
        tipo_evento = "llegada"

    # ── LLEGADA AL SISTEMA ────────────────────────────────────────────────────
    if tipo_evento == "llegada":
        prox_llegada = t_actual + tiempo_llegada()

        if estado_ps == 0 and estado_zona == 0:
            # Ingreso directo a la zona de seguridad
            estado_zona = 1
            prox_llegada_ps = t_actual + tiempo_zona()
            resultados.append([round(t_actual,1), "Llegada", len(clientes_en_cola), estado_ps, estado_zona])
        else:
            # Va a la cola
            clientes_en_cola.append(t_actual)
            resultados.append([round(t_actual,1), "Llegada", len(clientes_en_cola), estado_ps, estado_zona])

    # ── LLEGADA AL PS ─────────────────────────────────────────────────────────
    elif tipo_evento == "llegada_ps":
        estado_ps = 1
        estado_zona = 0
        prox_llegada_ps = float('inf')
        prox_fin_servicio = t_actual + tiempo_servicio()
        resultados.append([round(t_actual,1), "Llegada al PS", len(clientes_en_cola), estado_ps, estado_zona])

    # ── FIN DE SERVICIO ───────────────────────────────────────────────────────
    elif tipo_evento == "fin_servicio":
        estado_ps = 0
        estado_zona = 0
        prox_fin_servicio = float('inf')
        resultados.append([round(t_actual,1), "Fin de servicio", len(clientes_en_cola), estado_ps, estado_zona])

        if clientes_en_cola:
            clientes_en_cola.pop(0)
            estado_zona = 1
            prox_llegada_ps = t_actual + tiempo_zona()
            resultados.append([round(t_actual,1), "Ingreso a zona", len(clientes_en_cola), estado_ps, estado_zona])

# Crear tabla con pandas
df = pd.DataFrame(resultados, columns=["Tiempo", "Evento", "Clientes en cola", "Estado PS", "Estado Zona"])
print(df.to_string(index=False))