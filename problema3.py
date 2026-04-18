# Problema 3 con tiempos reales

import pandas as pd
import random

# Parámetros de la simulación
t_actual = 0
t_max = 2000
estado_servidor = 0  # 0 = libre, 1 = ocupado
clientes_en_cola = []  # guardamos hora de llegada de cada cliente
prox_llegada = random.uniform(30, 60)  # llegada inicial entre 30 y 60 segundos
prox_fin_servicio = float('inf')

# Tiempo máximo de espera antes de abandono (10 minutos = 600s)
tiempo_max_espera = 600

# Funciones generadoras de tiempos
def tiempo_llegada():
    return random.uniform(30, 60)  # llegadas entre 30 y 60 segundos
def tiempo_servicio():
    return random.uniform(20, 50)  # servicio entre 20 y 50 segundos

# Lista de resultados
resultados = []

while t_actual < t_max:
    # Calcular posibles abandonos
    prox_abandono = float('inf')
    if clientes_en_cola:
        # Verificamos si algún cliente ya superó el tiempo máximo de espera
        for llegada in clientes_en_cola:
            if t_actual - llegada >= tiempo_max_espera:
                prox_abandono = t_actual
                break

    # Seleccionar próximo evento
    siguiente_evento = min(prox_llegada, prox_fin_servicio, prox_abandono)
    t_actual = siguiente_evento

    if t_actual == prox_llegada:
        prox_llegada = t_actual + tiempo_llegada()
        if estado_servidor == 0:
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
        else:
            clientes_en_cola.append(t_actual)
        resultados.append([t_actual, "Llegada", len(clientes_en_cola), estado_servidor])

    elif t_actual == prox_fin_servicio:
        if clientes_en_cola:
            llegada_cliente = clientes_en_cola.pop(0)
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
        else:
            estado_servidor = 0
            prox_fin_servicio = float('inf')
        resultados.append([t_actual, "Fin de Servicio", len(clientes_en_cola), estado_servidor])

    elif t_actual == prox_abandono:
        # El primer cliente en cola abandona
        clientes_en_cola.pop(0)
        resultados.append([t_actual, "Abandono", len(clientes_en_cola), estado_servidor])

# Crear tabla con pandas
df = pd.DataFrame(resultados, columns=["Tiempo", "Evento", "Clientes en cola", "Estado del servidor"])
print(df.to_string(index=False))
