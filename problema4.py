import pandas as pd
import random

# Parámetros
t_actual = 0
t_max = 500
estado_servidor = 0  # 0 = libre, 1 = ocupado
cola_A = []
cola_B = []

# Generadores de tiempos con distribución uniforme
def tiempo_llegada_A():
    return random.uniform(30, 60)  # llegadas A entre 30 y 60 segundos
def tiempo_llegada_B():
    return random.uniform(40, 80)  # llegadas B entre 40 y 80 segundos
def tiempo_servicio():
    return random.uniform(20, 50)  # servicio entre 20 y 50 segundos

# Inicialización de próximos eventos
prox_llegada_A = tiempo_llegada_A()
prox_llegada_B = tiempo_llegada_B()
prox_fin_servicio = float('inf')

# Lista de resultados
resultados = []

while t_actual < t_max:
     # Seleccionar próximo evento
    siguiente_evento = min(prox_llegada_A, prox_fin_servicio, prox_llegada_B)

    if siguiente_evento >= t_max:
        break

    t_actual = siguiente_evento

    # determinar tipo de evento comparando valores, no con == sobre t_actual (evita fallo por floats y da prioridad correcta)
    if siguiente_evento == prox_llegada_A:
        tipo_evento = "llegada_A"
    elif siguiente_evento == prox_fin_servicio:
        tipo_evento = "fin_servicio"
    else:
        tipo_evento = "llegada_B"

    if tipo_evento == "llegada_A":
        prox_llegada_A = t_actual + tiempo_llegada_A()
        if estado_servidor == 0:
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
        else:
            cola_A.append(t_actual)
        resultados.append([round(t_actual,1), "Llegada A", len(cola_A), len(cola_B), estado_servidor])

    elif tipo_evento == "llegada_B":
        prox_llegada_B = t_actual + tiempo_llegada_B()
        if estado_servidor == 0 and not cola_A:  # solo si no hay A esperando
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
        else:
            cola_B.append(t_actual)
        resultados.append([round(t_actual,1), "Llegada B", len(cola_A), len(cola_B), estado_servidor])

    elif tipo_evento == "fin_servicio":
        estado_servidor = 0
        prox_fin_servicio = float('inf')
        resultados.append([round(t_actual,1), "Fin de Servicio",  len(cola_A), len(cola_B), estado_servidor])
        if cola_A:  # prioridad a clientes A
            cola_A.pop(0)
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
            resultados.append([round(t_actual,1), "Reocupación cliente A", len(cola_A), len(cola_B), estado_servidor])
        elif cola_B:
            cola_B.pop(0)
            estado_servidor = 1
            prox_fin_servicio = t_actual + tiempo_servicio()
            resultados.append([round(t_actual,1), "Reocupación cliente B", len(cola_A), len(cola_B), estado_servidor])

# Crear tabla con pandas
df = pd.DataFrame(resultados, columns=["Tiempo", "Evento", "Clientes A en cola", "Clientes B en cola", "Estado del servidor"])
print(df.to_string(index=False))
