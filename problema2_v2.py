# Problema 2 con tiempos reales

import random
import pandas as pd
from datetime import datetime, timedelta

# Configuración de turno: 4 horas
inicio_turno = datetime(2026, 4, 17, 9, 0, 0)  # fecha y hora de inicio (ejemplo: 17/04/2026 09:00)
fin_turno = inicio_turno + timedelta(hours=4)

# Estado inicial
t_actual = inicio_turno
estado_servidor = 0  # 0 = libre, 1 = ocupado
servidor_presente = True
clientes_en_cola = 0
tiempo_restante_servicio = 0

# Generadores de tiempos uniformes (en minutos)
def tiempo_llegada():
    return random.uniform(10, 20)  # intervalo entre llegadas
def tiempo_servicio():
    return random.uniform(15, 25)  # duración del servicio
def tiempo_trabajo():
    return random.uniform(40, 60)  # intervalo de trabajo del servidor
def tiempo_descanso():
    return random.uniform(20, 40)  # intervalo de descanso del servidor

# Inicialización de eventos
prox_llegada = t_actual + timedelta(minutes=tiempo_llegada())
prox_fin_servicio = fin_turno + timedelta(days=1)  # infinito simulado
prox_salida_servidor = t_actual + timedelta(minutes=tiempo_trabajo())
prox_regreso_servidor = fin_turno + timedelta(days=1)

# Matriz de resultados
resultados = []

while t_actual < fin_turno:
    # Seleccionar próximo evento
    siguiente_evento = min(prox_llegada, prox_fin_servicio, prox_salida_servidor, prox_regreso_servidor)

    if siguiente_evento >= fin_turno:
        break

    t_actual = siguiente_evento

    # determinar tipo de evento comparando valores, no con == sobre t_actual (evita fallo por floats y da prioridad correcta)
    if siguiente_evento == prox_salida_servidor:
        tipo_evento = "salida_servidor"
    elif siguiente_evento == prox_fin_servicio:
        tipo_evento = "fin_servicio"
    elif siguiente_evento == prox_regreso_servidor:
        tipo_evento = "regreso_servidor"
    else:
        tipo_evento = "llegada"

    if tipo_evento == "llegada":
        prox_llegada = t_actual + timedelta(minutes=tiempo_llegada())
        if servidor_presente and estado_servidor == 0:
            estado_servidor = 1
            prox_fin_servicio = t_actual + timedelta(minutes=tiempo_servicio())
        else:
            clientes_en_cola += 1
        resultados.append([t_actual.strftime("%H:%M:%S"), "Llegada", clientes_en_cola, estado_servidor, servidor_presente])

    elif tipo_evento == "fin_servicio":
        estado_servidor = 0
        prox_fin_servicio = fin_turno + timedelta(days=1)
        resultados.append([t_actual.strftime("%H:%M:%S"), "Fin de Servicio", clientes_en_cola, estado_servidor, servidor_presente])
        if servidor_presente:
            if clientes_en_cola > 0:
                clientes_en_cola -= 1
                estado_servidor = 1
                prox_fin_servicio = t_actual + timedelta(minutes=tiempo_servicio())
                resultados.append([t_actual.strftime("%H:%M:%S"), "Reocupación", clientes_en_cola, estado_servidor, servidor_presente])

    elif tipo_evento == "salida_servidor":
        servidor_presente = False
        if estado_servidor == 1 and prox_fin_servicio != fin_turno + timedelta(days=1):
            # Guardamos cuánto faltaba del servicio
            tiempo_restante_servicio = (prox_fin_servicio - t_actual).total_seconds() / 60
            prox_fin_servicio = fin_turno + timedelta(days=1)
        estado_servidor = 0
        prox_regreso_servidor = t_actual + timedelta(minutes=tiempo_descanso())
        prox_salida_servidor = fin_turno + timedelta(days=1)
        resultados.append([t_actual.strftime("%H:%M:%S"), "Salida del Servidor", clientes_en_cola, estado_servidor, servidor_presente])

    elif tipo_evento == "regreso_servidor":
        servidor_presente = True
        if tiempo_restante_servicio > 0:
            estado_servidor = 1
            prox_fin_servicio = t_actual + timedelta(minutes=tiempo_restante_servicio)
            tiempo_restante_servicio = 0
        elif clientes_en_cola > 0:
            clientes_en_cola -= 1
            estado_servidor = 1
            prox_fin_servicio = t_actual + timedelta(minutes=tiempo_servicio())
        else:
            estado_servidor = 0
            prox_fin_servicio = fin_turno + timedelta(days=1)
        prox_salida_servidor = t_actual + timedelta(minutes=tiempo_trabajo())
        prox_regreso_servidor = fin_turno + timedelta(days=1)
        resultados.append([t_actual.strftime("%H:%M:%S"), "Regreso del Servidor", clientes_en_cola, estado_servidor, servidor_presente])

# Mostrar tabla con pandas
df = pd.DataFrame(resultados, columns=["Hora", "Evento", "Clientes en cola", "Estado del servidor", "Servidor presente"])
print(df.to_string(index=False))