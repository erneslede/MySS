# Problema 3 con tiempos aleatorios y abandonos corregidos

import pandas as pd
import random

# Vector inicial
t_actual = 0
t_max = 1000
estado_servidor = 0  # 0 = libre, 1 = ocupado
clientes_en_cola = []  # guardamos (hora_llegada, hora_abandono)
prox_llegada = random.uniform(30, 60)  # llegada inicial entre 30 y 60 segundos
prox_fin_servicio = float('inf')

# Tiempo máximo de espera antes de abandono
tiempo_max_espera = 5

# Funciones generadoras de tiempos
def tiempo_llegada():
    return random.uniform(30, 60)  # llegadas entre 30 y 60 segundos
def tiempo_servicio():
    return random.uniform(20, 50)  # servicio entre 20 y 50 segundos

# Lista de resultados
resultados = []

while t_actual < t_max:
    # Calcular próximo abandono (el más cercano de la cola)
    prox_abandono = float('inf')
    if clientes_en_cola:
        prox_abandono = min([abandono for _, abandono in clientes_en_cola])

    # Seleccionar próximo evento
    siguiente_evento = min(prox_llegada, prox_fin_servicio, prox_abandono)
    t_actual = siguiente_evento

    if t_actual == prox_llegada:
        prox_llegada = t_actual + tiempo_llegada()
        if estado_servidor == 0:
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
        else:
            # Guardamos hora de llegada y hora de abandono
            clientes_en_cola.append((t_actual, t_actual + tiempo_max_espera))
        resultados.append([round(t_actual,1), "Llegada", len(clientes_en_cola), estado_servidor])

    elif t_actual == prox_fin_servicio:
        estado_servidor = 0
        resultados.append([round(t_actual,1), "Fin de Servicio", len(clientes_en_cola), estado_servidor])
        if clientes_en_cola:
            llegada_cliente, abandono_cliente = clientes_en_cola.pop(0)
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
            resultados.append([round(t_actual,1), "Reocupación", len(clientes_en_cola), estado_servidor])
        else:
            estado_servidor = 0
            prox_fin_servicio = float('inf')

    elif t_actual == prox_abandono:
        # Eliminamos el cliente cuyo abandono coincide con t_actual
        for i, (llegada, abandono) in enumerate(clientes_en_cola):
            if abandono == t_actual:
                clientes_en_cola.pop(i)
                break
        resultados.append([round(t_actual,1), "Abandono", len(clientes_en_cola), estado_servidor])

# Crear tabla con pandas
df = pd.DataFrame(resultados, columns=["Tiempo", "Evento", "Clientes en cola", "Estado del servidor"])
print(df.to_string(index=False))