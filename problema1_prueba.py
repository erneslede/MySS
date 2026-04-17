# Problema 1 con tiempos constantes y salida en varias líneas

# Vector inicial
t_actual = 0
t_max = 500
estado_servidor = 0
clientes_en_cola = 0
prox_llegada =  45
prox_fin_servicio = float('inf') #no hay nadie siendo atendido - lo seteo como infinito para que no sea elegido

while t_actual < t_max:
    # Comparo cuál es el menor valor y lo elijo porque ocurre primero
    if prox_llegada < prox_fin_servicio:
        t_actual = prox_llegada
        prox_llegada = t_actual + 45 #programo la PRÓXIMA llegada
        if estado_servidor == 0:
            estado_servidor = 1
            prox_fin_servicio = t_actual + 40
        else:
            clientes_en_cola += 1
        print(f"[T{t_actual}] Evento: Llegada. Cola: {clientes_en_cola}, Servidor: {estado_servidor}")
        print("--------------------------------------------")
    elif prox_fin_servicio < prox_llegada:
        t_actual = prox_fin_servicio
        if clientes_en_cola > 0:
            clientes_en_cola -= 1
            prox_fin_servicio = t_actual + 40
        elif clientes_en_cola == 0:
            estado_servidor = 0
            prox_fin_servicio = float('inf')
        print(f"[T{t_actual}] Evento: Fin de Servicio. Cola: {clientes_en_cola}, Servidor: {estado_servidor}")
        print("--------------------------------------------")

print("-- Simulación finalizada --")