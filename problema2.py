# Problema 2 con tiempos aleatorios

import random
import pandas as pd

# Vector inicial
t_actual = 0
t_max = 500
estado_servidor = 0  # 0 = libre, 1 = ocupado
servidor_presente = True
clientes_en_cola = 0
tiempo_restante_servicio = 0

# Generadores de tiempos uniformes
def tiempo_llegada():
    return random.uniform(10, 20)  # intervalo entre llegadas
def tiempo_servicio():
    return random.uniform(15, 25)  # duración del servicio
def tiempo_trabajo():
    return random.uniform(40, 60)  # intervalo de trabajo del servidor
def tiempo_descanso():
    return random.uniform(20, 40)  # intervalo de descanso del servidor

# Inicialización de eventos
prox_llegada = tiempo_llegada()
prox_fin_servicio = float('inf')
prox_salida_servidor = tiempo_trabajo()
prox_regreso_servidor = float('inf')

# Matriz de resultados
resultados = []

while t_actual < t_max:
    # Próximo evento
    prox_evento = min(prox_llegada, prox_fin_servicio, prox_salida_servidor, prox_regreso_servidor)
    t_actual = prox_evento

    if t_actual == prox_llegada:
        prox_llegada = t_actual + tiempo_llegada()
        if servidor_presente and estado_servidor == 0:
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
        else:
            clientes_en_cola += 1
        resultados.append([round(t_actual,1), "Llegada", clientes_en_cola, estado_servidor, servidor_presente])

    elif t_actual == prox_fin_servicio:
        if servidor_presente:
            if clientes_en_cola > 0:
                clientes_en_cola -= 1
                prox_fin_servicio = t_actual + tiempo_servicio()
            else:
                estado_servidor = 0
                prox_fin_servicio = float('inf')
        resultados.append([round(t_actual,1), "Fin de Servicio", clientes_en_cola, estado_servidor, servidor_presente])

    elif t_actual == prox_salida_servidor:
        servidor_presente = False
        if estado_servidor == 1 and prox_fin_servicio != float('inf'):
            # Guardamos cuánto faltaba del servicio
            tiempo_restante_servicio = prox_fin_servicio - t_actual
            prox_fin_servicio = float('inf')  # se interrumpe el servicio
        estado_servidor = 0
        prox_regreso_servidor = t_actual + tiempo_descanso()
        prox_salida_servidor = float('inf')
        resultados.append([round(t_actual,1), "Salida del Servidor", clientes_en_cola, estado_servidor, servidor_presente])

    elif t_actual == prox_regreso_servidor:
        servidor_presente = True
        if tiempo_restante_servicio > 0:
            # Retoma el servicio interrumpido
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_restante_servicio
            tiempo_restante_servicio = 0
        elif clientes_en_cola > 0:
            clientes_en_cola -= 1
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
        else:
            estado_servidor = 0
            prox_fin_servicio = float('inf')
        prox_salida_servidor = t_actual + tiempo_trabajo()
        prox_regreso_servidor = float('inf')
        resultados.append([round(t_actual,1), "Regreso del Servidor", clientes_en_cola, estado_servidor, servidor_presente])

# Convertir la matriz en tabla con pandas
df = pd.DataFrame(resultados, columns=["Tiempo", "Evento", "Clientes en cola", "Estado del servidor", "Servidor presente"])
print(df.to_string(index=False))
