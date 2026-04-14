'''Igual al problema nro. 1, pero el servidor trabaja durante 
intervalos de tiempo aleatorios y entre ellos descansa durante intervalos de 
tiempo también aleatorios. (trabaja unos minutos, descansa unos minutos, 
trabaja otros minutos, descansa otros minutos, etc). 
 
Eventos. 
1)  Llegada de un cliente al sistema 
2)  Fin del servicio. 
3)  Salida del servidor. 
4)  Llegada del servidor. 
 
Variables de estado. 
1)  Estado de ocupado o libre del puesto de servicio. 
2)  Cantidad de clientes en cola. 
3)  Presencia o ausencia del servidor.'''

import random
# def t_aleatorio(min, max):
#     t_aleatorio = 

# Inicializacion
t_actual = 0
t_max = 500
estado_servidor = 0
servidor_presente = True
prox_salida_servidor = float('inf') #inicia trabajando - lo seteo como infinito para que no sea elegido
clientes_en_cola = 0
prox_llegada =  45
prox_fin_servicio = float('inf') #no hay nadie siendo atendido - lo seteo como infinito para que no sea elegido
t_descanso = random()
t_trabajo = random()
while t_actual < t_max:
    comienzo_descanso = random(random,random)
    fin_descanso = random(random,random)
    # Comparo cuál es el menor valor y lo elijo porque ocurre primero
    if prox_llegada < prox_fin_servicio:
        t_actual = prox_llegada
        prox_llegada = t_actual + 45 # calculo la PRÓXIMA llegada
        if servidor_presente and estado_servidor == 0:
            estado_servidor = 1
            prox_fin_servicio = t_actual + t_trabajo
        else:
            clientes_en_cola += 1
        print(f"[T{t_actual}, T_Trabajo{t_trabajo}] Evento: Llegada. Cola: {clientes_en_cola}, Servidor: {estado_servidor}")
        print("--------------------------------------------")
    elif prox_fin_servicio < prox_llegada:
        if servidor_presente:
            t_actual = prox_fin_servicio
            if clientes_en_cola > 0:
                clientes_en_cola -= 1
                prox_fin_servicio = t_actual + t_trabajo
            elif clientes_en_cola == 0:
                estado_servidor = 0
                prox_fin_servicio = float('inf')
        else:
            prox_fin_servicio = t_actual + t_trabajo + t_descanso
    print(f"[T{t_actual}] Evento: Fin de Servicio. Cola: {clientes_en_cola}, Servidor: {estado_servidor}")
    print("--------------------------------------------")
    elif t_descanso < t_actual:



print("-- Simulación finalizada --")