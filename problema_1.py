"""Problema No. 1: Los clientes llegan uno a uno a intervalos de tiempo 
aleatorios para recibir servicio uno a uno en el mismo orden de llegada. Los 
tiempos de prestación del servicio son también aleatorios. El servidor no 
abandona nunca el puesto de servicio. 
Si al llegar un cliente al sistema el puesto de servicio esta ocupado ese cliente 
deberá hacer cola para aguardar que se le preste el servicio. Al terminar de 
prestarse el servicio a un cliente el próximo lo reemplaza en el puesto de 
servicio en forma instantánea. 
Eventos. 
1) Llegada de un cliente al sistema. 
2) Fin de servicio. 
Variables de estado. 
1) Estado de ocupado o libre del puesto de servicio. 
2) Cantidad de clientes en cola. 
Generadores. 
1. Generador de tiempo de llegada de un cliente al sistema:  tLL = 45” 
(cte). 
2. Generador de tiempo de servicio: tS = 40” (cte)  """

# Inicializacion
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