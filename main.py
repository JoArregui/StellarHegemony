import os
import time 

from clases.base import ObjetoEspacial
from clases.economia import EconomiaFaccion
# Importar todas las clases necesarias para el mapeo
from clases.estructuras import EstacionMinera, GeneradorFusionBasico, EstacionComandoOrbital
from clases.unidades import CazaLigero, CorbetaDefensiva, DroneRecoleccion, Destructor 
from clases.serializador import guardar_juego, cargar_juego
from clases.monitor_rendimiento import MonitorRendimiento

# =================================================================
#               FUNCIONES DE INTERFAZ Y COMANDOS
# =================================================================

def limpiar_pantalla():
    """Borra la pantalla de la consola según el sistema operativo."""
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_ayuda():
    """Muestra la lista de comandos disponibles."""
    print("\n--- Comandos Disponibles ---")
    print("recursos                   -> Muestra el estado actual de los recursos.")
    print("producir <Unidad>          -> Añade una unidad a la cola de producción (Ej: producir DroneRecoleccion).")
    print("ordenar <ID> <accion>      -> Asigna una nueva orden a una unidad (Ej: ordenar 3 recolectar).")
    print("salir                      -> Termina la simulación.")
    print("ayuda                      -> Muestra esta lista.")
    print("----------------------------")

def procesar_comando(motor_juego, comando):
    """Procesa un comando de texto introducido por el usuario."""
    comando = comando.strip().lower()
    partes = comando.split()
    accion = partes[0] if partes else ""
    
    faccion_terran = motor_juego.facciones.get('Terran')
    
    if accion == 'ayuda':
        mostrar_ayuda()
        return True
    
    if accion == 'recursos':
        if faccion_terran:
            print("\n--- Recursos Terran ---")
            for r, c in faccion_terran.recursos.items():
                print(f"  {r.capitalize()}: {c:.1f}")
            print(f"  Población: {faccion_terran.poblacion_actual}/{faccion_terran.poblacion_maxima}")
            print("-------------------------")
        return True
        
    if accion == 'producir':
        # --- Lógica de PRODUCIR (EXISTENTE) ---
        if len(partes) < 2:
            print("[ERROR] Uso: producir <Unidad>")
            return True
            
        nombre_unidad = partes[1]
        clase_unidad = motor_juego.UNIDAD_CLASES.get(nombre_unidad)
        
        if not clase_unidad:
            print(f"[ERROR] Unidad '{nombre_unidad}' desconocida. Pruebe 'DroneRecoleccion'.")
            return True
        
        comando_orbital = motor_juego.objetos.get(1)
        if not comando_orbital or not isinstance(comando_orbital, EstacionComandoOrbital):
            print("[ERROR] No se encuentra la Estación de Comando Orbital (ID 1) para producir unidades.")
            return True
            
        try:
            tiempo_produccion = clase_unidad.tiempo_produccion
            if not hasattr(comando_orbital, 'cola_produccion'):
                comando_orbital.cola_produccion = []
            
            comando_orbital.cola_produccion.append((nombre_unidad, tiempo_produccion))
            
            print(f"[COMANDO EXITOSO] '{nombre_unidad}' añadido a la cola de producción. Tiempo: {tiempo_produccion:.1f}s")
            
        except AttributeError:
            print(f"[ERROR] No se pudo obtener la información de tiempo de producción para {nombre_unidad}.")
            return True

        return True
    
    # --- NUEVO: ORDENAR UNIDADES ---
    if accion == 'ordenar':
        if len(partes) < 3:
            print("[ERROR] Uso: ordenar <ID> <accion> (Ej: ordenar 3 recolectar)")
            return True
            
        try:
            id_unidad = int(partes[1])
            accion_orden = partes[2]
        except ValueError:
            print("[ERROR] El ID de la unidad debe ser un número entero.")
            return True
            
        unidad = motor_juego.objetos.get(id_unidad)
        
        if not unidad or unidad.faccion != 'Terran':
            print(f"[ERROR] Unidad con ID {id_unidad} no encontrada o no pertenece a Terran.")
            return True

        if accion_orden == 'recolectar' and isinstance(unidad, DroneRecoleccion):
            
            # Buscamos la Estación Minera (ID 2) y el Comando (ID 1)
            minera = motor_juego.objetos.get(2)
            comando = motor_juego.objetos.get(1)
            
            if minera and comando:
                unidad.orden_recolectar(minera, comando)
                print(f"[COMANDO EXITOSO] Drone [{id_unidad}] reasignado: Recolectar (Minera 2 -> Comando 1).")
                return True
            else:
                print("[ERROR] No se encontraron la Estación Minera (ID 2) o Comando (ID 1) para la orden.")
                return True
                
        else:
            print(f"[ERROR] Acción '{accion_orden}' o tipo de unidad no soportados para el ID {id_unidad}.")
            return True

    if accion == 'salir':
        print("[COMANDO] Terminando simulación...")
        return 'salir'

    print(f"[ERROR] Comando desconocido: '{comando}'. Escriba 'ayuda' para ver los comandos.")
    return True


def imprimir_estado_juego(motor_juego):
    """Muestra el estado actual del juego de forma limpia en la consola."""
    limpiar_pantalla()
    
    # Solo mostramos información para la facción 'Terran'
    faccion = motor_juego.facciones.get('Terran')
    if not faccion:
        print("Error: Faccion 'Terran' no encontrada.")
        return

    # --- 1. Encabezado y Misión ---
    print("=======================================")
    print("🚀 STELLAR HEGEMONY | SIMULACIÓN 🚀")
    print(f"Tiempo total: {motor_juego.tiempo_total_simulacion:.1f}s")
    print("=======================================")
    
    recurso_mision = motor_juego.objetivo_mision['recurso'].upper()
    cantidad_r = motor_juego.objetivo_mision['cantidad_requerida']
    progreso = faccion.recursos[motor_juego.objetivo_mision['recurso']]
    
    estado_mision = "COMPLETADA" if motor_juego.mision_completada else f"{progreso:.1f}/{cantidad_r}"
    
    print(f"🎯 Misión: Recolectar {cantidad_r} de {recurso_mision} ({estado_mision})")
    print("---------------------------------------")

    # --- 2. Recursos y Población ---
    print("💰 Economía:")
    print(f"  Mineral: {faccion.recursos['mineral']:.1f} | Energía: {faccion.recursos['energia']:.1f} | Materia Rara: {faccion.recursos['materia_rara']:.1f}")
    print(f"  Población: {faccion.poblacion_actual}/{faccion.poblacion_maxima}")
    print("---------------------------------------")

    # --- 3. Unidades y Estructuras Activas ---
    print("🏭 Objetos y Estados:")
    
    # Agrupamos objetos por tipo y estado
    objetos_por_tipo = {}
    
    for obj_id, obj in motor_juego.objetos.items():
        nombre = obj.__class__.__name__
        estado = ""
        
        if hasattr(obj, 'cola_produccion') and obj.cola_produccion:
            item_prod = obj.cola_produccion[0]
            estado = f"-> Produciendo {item_prod[0]} ({item_prod[1]:.1f}s)"
        elif nombre == 'DroneRecoleccion':
            
            # --- CORRECCIÓN DE ATRIBUTO ---
            estado_drone = getattr(obj, '_estado_movimiento', 'INACTIVO') # Usamos el atributo real
            
            if estado_drone == 'MOVIENDO':
                if obj.destino_actual:
                    estado = f"-> {estado_drone} a {obj.destino_actual.nombre} ({obj.recurso_cargado} {obj.capacidad_cargada:.1f})"
                else:
                    estado = f"-> {estado_drone} (Sin destino)"
            elif estado_drone == 'RECOLECTANDO':
                if obj.destino_actual:
                    estado = f"-> {estado_drone} en {obj.destino_actual.nombre} ({obj.recurso_cargado} {obj.capacidad_cargada:.1f})"
                else:
                    estado = f"-> {estado_drone} (Sin recurso)"
            elif estado_drone == 'ENTREGANDO':
                if obj.destino_actual:
                    estado = f"-> {estado_drone} en {obj.destino_actual.nombre} ({obj.recurso_cargado} {obj.capacidad_cargada:.1f})"
                else:
                    estado = f"-> {estado_drone} (Sin base)"
            
        objetos_por_tipo.setdefault(nombre, []).append(f"  [{obj_id}] {nombre} (Vida: {obj.vida_actual:.0f}) {estado}")

    for nombre, lista in objetos_por_tipo.items():
        print(f"  > {nombre} ({len(lista)}):")
        for item in lista:
            print(item)
    print("=======================================")


class MotorJuego:
    def __init__(self):
        self.objetos = {} 
        self.facciones = {}
        self.contador_id = 0
        
        # --- Atributos de Simulación ---
        self.tiempo_total_simulacion = 0.0
        self.monitor = MonitorRendimiento() 
        
        # --- Configuración de la Misión ---
        self.objetivo_mision = {
            'recurso': 'mineral', 
            'cantidad_requerida': 120 
        }
        self.mision_completada = False

        # --- Mapeo de Clases para la Cola de Producción (USADO POR ESTRUCTURAS) ---
        self.UNIDAD_CLASES = {
            'DroneRecoleccion': DroneRecoleccion,
            'CazaLigero': CazaLigero,
            'CorbetaDefensiva': CorbetaDefensiva,
            'Destructor': Destructor,
            'EstacionMinera': EstacionMinera,
            'GeneradorFusionBasico': GeneradorFusionBasico,
        }

    def crear_objeto(self, clase_objeto, faccion_nombre, posicion):
        """Crea una instancia de un ObjetoEspacial y lo añade al juego."""
        self.contador_id += 1
        nuevo_objeto = clase_objeto(self.contador_id, faccion_nombre, posicion)
        self.objetos[self.contador_id] = nuevo_objeto
        
        if isinstance(nuevo_objeto, EstacionComandoOrbital):
            if faccion_nombre in self.facciones:
                # El comando aumenta el límite de población al ser creado.
                self.facciones[faccion_nombre].poblacion_maxima += nuevo_objeto.poblacion_maxima_incremento 

        return nuevo_objeto

    def tick_simulacion(self, delta_tiempo):
        
        # --- 0. INICIAR MONITOR ---
        self.monitor.iniciar_tick() 

        produccion_total_estructuras = {} 
        recursos_entregados_drones = {}

        # --- 1. Proceso de Estructuras (Producción y Entrenamiento) ---
        for id_objeto, objeto in list(self.objetos.items()):
            
            if isinstance(objeto, EstacionMinera) or isinstance(objeto, GeneradorFusionBasico):
                # A. Producción de recursos (Minera/Generador) - Solo llenan el almacén
                objeto.tick_simulacion_produccion() 

            if isinstance(objeto, EstacionComandoOrbital):
                 # B. Entrenamiento de unidades (Centro de Comando)
                 objeto.tick_simulacion_produccion(self, delta_tiempo) 
        
        # --- 2. Actualización de Unidades (Movimiento, Combate, Recolección) ---
        for id_objeto, objeto in list(self.objetos.items()):
            
            if hasattr(objeto, 'tick_simulacion') and objeto.vida_actual > 0:
                recursos_devueltos = objeto.tick_simulacion(self, delta_tiempo) 
                
                if recursos_devueltos: 
                    faccion_nombre = objeto.faccion
                    if faccion_nombre not in recursos_entregados_drones:
                        recursos_entregados_drones[faccion_nombre] = {'mineral': 0, 'energia': 0, 'materia_rara': 0}
                    for recurso, cantidad in recursos_devueltos.items():
                        recursos_entregados_drones[faccion_nombre][recurso] += cantidad
                        
            if objeto.vida_actual <= 0 and id_objeto in self.objetos:
                if hasattr(objeto, 'poblacion_coste') and objeto.poblacion_coste > 0:
                    self.facciones[objeto.faccion].poblacion_actual -= getattr(objeto, 'poblacion_coste', 0)
                del self.objetos[id_objeto]

        # --- 3. Aplicación de Recursos Entregados por Drones (Puntuales) ---
        for faccion_nombre, recursos in recursos_entregados_drones.items():
            if faccion_nombre in self.facciones:
                economia = self.facciones[faccion_nombre]
                for recurso, cantidad in recursos.items():
                    economia.recursos[recurso] += cantidad
        
        # --- 4. Aplicación del Costo de Mantenimiento ---
        for faccion_nombre, faccion in self.facciones.items():
            objetos_faccion = [obj for obj in self.objetos.values() if obj.faccion == faccion_nombre]
            faccion.aplicar_mantenimiento(objetos_faccion, delta_tiempo)
            
        # --- 5. Chequeo de Misión ---
        if not self.mision_completada:
            for faccion_nombre, faccion in self.facciones.items():
                recurso_mision = self.objetivo_mision['recurso']
                cantidad_requerida = self.objetivo_mision['cantidad_requerida']
                
                if faccion.recursos.get(recurso_mision, 0) >= cantidad_requerida:
                    self.mision_completada = True
                    print(f"\n[CONDICIÓN DE VICTORIA] ¡Misión completada por {faccion_nombre}!")
                    print(f"Objetivo: Alcanzar {cantidad_requerida} de {recurso_mision.upper()}.")
                    
        # --- 6. Penalización por Déficit de Recursos ---
        DANO_DEFICIT_ENERGIA = 2.0 

        for faccion_nombre, faccion in self.facciones.items():
            
            if faccion.recursos['energia'] < 0:
                
                dano_aplicar = DANO_DEFICIT_ENERGIA * delta_tiempo
                
                for id_objeto in list(self.objetos.keys()): 
                    objeto = self.objetos.get(id_objeto)
                    
                    if objeto and objeto.faccion == faccion_nombre and objeto.vida_actual > 0:
                        
                        if hasattr(objeto, 'mantenimiento_coste') and objeto.mantenimiento_coste.get('energia', 0) > 0:
                            objeto.recibir_danio(dano_aplicar)
        
        # --- 7. FINALIZAR MONITOR ---
        self.tiempo_total_simulacion += delta_tiempo
        self.monitor.finalizar_tick(self, delta_tiempo)
        
        return 


    def iniciar_juego(self, cargar=False): 
        
        if cargar:
            juego_cargado = cargar_juego()
            if juego_cargado:
                # Si se carga, reemplazamos el 'self' actual con el estado cargado
                self.__dict__.update(juego_cargado.__dict__)
                print(f"[REANUDANDO] Mineral actual: {self.facciones['Terran'].recursos['mineral']:.1f}")
                return

        # --- LÓGICA DE INICIO DE JUEGO NUEVO ---
        print("--- Iniciando Stellar Hegemony: TEST DE CARGADO Y GUARDADO ---")
        
        # --- FACCIÓN TERRAN ---
        terrana_nombre = 'Terran'
        self.facciones[terrana_nombre] = EconomiaFaccion(terrana_nombre)
        terrana = self.facciones[terrana_nombre]
        
        # Recursos iniciales para el test
        terrana.recursos = {'mineral': 100, 'energia': 500, 'materia_rara': 500} 
        
        # 1. Comando (ID 1)
        comando_t = self.crear_objeto(EstacionComandoOrbital, terrana_nombre, (0, 0, 0)) 
        
        # 2. Estación Minera (ID 2)
        minera_t = self.crear_objeto(EstacionMinera, terrana_nombre, (200, 0, 0))
        
        # 3. Drone inicial (ID 3)
        drone_t = self.crear_objeto(DroneRecoleccion, terrana_nombre, (10, 10, 10))
        terrana.poblacion_actual += drone_t.poblacion_coste
        
        # El Drone comienza a trabajar inmediatamente: Minera -> Comando
        drone_t.orden_recolectar(minera_t, comando_t)
        
        print(f"\n[MISIÓN] Recolectar {self.objetivo_mision['cantidad_requerida']} de {self.objetivo_mision['recurso'].upper()}.")
        print(f"[ECONOMÍA INICIAL] Mineral: {terrana.recursos['mineral']:.1f}")


if __name__ == "__main__":
    
    # --- Ejecutar Prueba 1: GUARDADO INICIAL ---
    print("\n\n=============== PRUEBA 1: GUARDADO INICIAL (Modo Consola) ===============")
    juego_guardado = MotorJuego()
    
    tiempo_simular_guardado = 5.0
    
    juego_guardado.iniciar_juego(cargar=False) 
    
    # Ejecutar simulación a medio camino
    tiempo_total = 0.0
    delta_tiempo = 0.1
    
    print("\n--- Simulación a medio camino (Ver la Consola) ---")
    while tiempo_total < tiempo_simular_guardado:
        juego_guardado.tick_simulacion(delta_tiempo)
        tiempo_total += delta_tiempo
        
        # DIBUJAR ESTADO EN CONSOLA
        imprimir_estado_juego(juego_guardado)
        time.sleep(0.05) # Pausa mínima para que sea legible

    print(f"\nT: {tiempo_total:.1f}s | Mineral al guardar: {juego_guardado.facciones['Terran'].recursos['mineral']:.1f}")
    guardar_juego(juego_guardado)
    
    # Añadimos una pausa al final del Guardado para ver el output de la consola
    time.sleep(1.0) 
    

    # --- Ejecutar Prueba 2: CARGADO Y VICTORIA (INTERACTIVA) ---
    print("\n\n=============== PRUEBA 2: CARGADO Y VICTORIA (Modo Interactivo) ===============")
    juego_cargado = MotorJuego()
    juego_cargado.iniciar_juego(cargar=True) 

    if not juego_cargado.mision_completada:
        
        terrana = juego_cargado.facciones['Terran']
        print(f"\n[VERIFICACIÓN] Mineral: {terrana.recursos['mineral']:.1f} (Debe ser 100.0)")

        # Bucle de Simulación para completar la misión
        tiempo_total = 5.0 
        delta_tiempo = 0.1 
        num_ticks = 0
        max_duracion = 100.0 
        
        # --- VARIABLES DE CONTROL DE BUCLE INTERACTIVO ---
        ticks_por_comando = 10 # Pausa para comando cada 10 ticks (1.0s de simulación)
        simulacion_activa = True
        
        print("\n--- Continuación de la Simulación (Modo Interactivo) ---")
        
        while tiempo_total < max_duracion and not juego_cargado.mision_completada and simulacion_activa:
            
            juego_cargado.tick_simulacion(delta_tiempo)
            tiempo_total += delta_tiempo
            num_ticks += 1
            
            # DIBUJAR ESTADO EN CONSOLA
            imprimir_estado_juego(juego_cargado)
            
            # --- INTERACCIÓN CON EL JUGADOR ---
            if num_ticks % ticks_por_comando == 0:
                
                # Pausa controlada para entrada de comando
                print("\n[COMANDO] Escriba un comando ('ayuda' para lista, ENTER para continuar): ")
                try:
                    comando_usuario = input(">>> ") 
                    
                    if comando_usuario.strip():
                        resultado = procesar_comando(juego_cargado, comando_usuario)
                        if resultado == 'salir':
                            simulacion_activa = False
                            break
                        # Pausa adicional para leer el resultado del comando
                        time.sleep(2.0) 
                        
                except EOFError:
                    # Permite al usuario continuar si presiona Ctrl+D
                    pass 
                except KeyboardInterrupt:
                    # Permite al usuario salir con Ctrl+C
                    simulacion_activa = False
                    break
            
            # Retraso visual mínimo para que la simulación no parpadee demasiado rápido
            time.sleep(0.05) 
        
        print(f"\n--- Resultado Final (Cargado) ---")
        print(f"Tiempo simulado total: {tiempo_total:.2f} segundos.")
        print(f"Misión completada: {'Sí' if juego_cargado.mision_completada else 'No'}")
        
        if juego_cargado.mision_completada:
            print(f"Mineral final: {terrana.recursos['mineral']:.1f}")
            
    # El resumen de rendimiento debe imprimirse después de que la simulación termine
    juego_cargado.monitor.imprimir_resumen()