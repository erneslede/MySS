import pandas as pd

# Parámetros de la simulación
t_actual = 0
t_max = 500
estado_servidor = 0  # 0 = libre, 1 = ocupado
clientes_en_cola = 0
prox_llegada = 45
prox_fin_servicio = float('inf')  # infinito porque no hay servicio en curso

# Lista para almacenar resultados
resultados = []

while t_actual < t_max:
    # Comparo cuál evento ocurre primero
    if prox_llegada < prox_fin_servicio:
        t_actual = prox_llegada
        prox_llegada = t_actual + 45  # programo la próxima llegada
        if estado_servidor == 0:
            estado_servidor = 1
            prox_fin_servicio = t_actual + 40
        else:
            clientes_en_cola += 1
        resultados.append([t_actual, "Llegada", clientes_en_cola, "Ocupado" if estado_servidor == 1 else "Libre"])
        
    elif prox_fin_servicio < prox_llegada:
        t_actual = prox_fin_servicio
        if clientes_en_cola > 0:
            clientes_en_cola -= 1
            prox_fin_servicio = t_actual + 40
            estado_servidor = 1
        else:
            estado_servidor = 0
            prox_fin_servicio = float('inf')
        resultados.append([t_actual, "Fin de Servicio", clientes_en_cola, "Ocupado" if estado_servidor == 1 else "Libre"])

# Crear tabla con pandas
df = pd.DataFrame(resultados, columns=["Tiempo", "Evento", "Clientes en cola", "Estado del servidor"])
print(df.to_string(index=False))