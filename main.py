# main.py

from clases.base import ObjetoEspacial
from clases.economia import EconomiaFaccion
# Importar todas las clases necesarias para el mapeo
from clases.estructuras import EstacionMinera, GeneradorFusionBasico, EstacionComandoOrbital
from clases.unidades import CazaLigero, CorbetaDefensiva, DroneRecoleccion, Destructor 
from clases.serializador import guardar_juego, cargar_juego 
from clases.monitor import MonitorRendimiento 
from clases.mapeador import MapeadorEspacial 

# =================================================================
#               FUNCIONES DE COMANDO (G)
# =================================================================

def comando_recursos(motor, tiempo_total):
    """Muestra el estado actual de los recursos."""
    if not motor.facciones:
        print("Error: No se ha iniciado ninguna facción.")
        return
        
    faccion = motor.facciones['Terran']
    print(f"\n[ESTADO T={tiempo_total:.1f}s]")
    print(f"  Mineral: {faccion.recursos['mineral']:.1f}")
    print(f"  Energía: {faccion.recursos['energia']:.1f}")
    print(f"  Materia Rara: {faccion.recursos['materia_rara']:.1f}")
    print(f"  Población: {faccion.poblacion_actual}/{faccion.poblacion_maxima}")

def comando_mapa(motor, tiempo_total):
    """Muestra la posición de todos los objetos activos."""
    print(f"\n[MAPA T={tiempo_total:.1f}s]")
    objetos_activos = motor.mapeador.listar_objetos_activos()
    
    if not objetos_activos:
        print("  No hay objetos activos.")
        return
        
    for obj in objetos_activos:
        # Redondear las posiciones para una salida más limpia
        posicion_redondeada = tuple(map(lambda x: round(x, 2), obj['posicion']))
        print(f"  ID {obj['id']}: {obj['clase']} ({obj['faccion']}) | Posición: {posicion_redondeada} | Vida: {obj['vida']}")
        
# =================================================================
#               BUCLE PRINCIPAL DE LA CLI (G)
# =================================================================

def jugar_cli(motor):
    
    delta_tiempo = 0.5 # Avance de tiempo por tick de simulación
    
    # Inicia o Carga el juego
    motor.iniciar_juego(cargar=True)
    
    # Determinar el tiempo inicial (para la partida cargada)
    tiempo_total = 0.0
    if motor.facciones and motor.monitor.historial_ticks:
        # Si se cargó, reanudamos el tiempo desde el último registro
        tiempo_total = motor.monitor.historial_ticks[-1]['tiempo']
        
    print("\n--- INTERFAZ DE COMANDOS (CLI) INICIADA ---")
    print("Comandos: 'tick', 'mapa', 'recursos', 'guardar', 'salir'")
    print(f"  Misión: Recolectar {motor.objetivo_mision['cantidad_requerida']} de {motor.objetivo_mision['recurso'].upper()}.")
    
    while not motor.mision_completada:
        
        try:
            comando = input(f"\nStellarHegemony (T={tiempo_total:.1f}s) > ").strip().lower()
        except EOFError:
            print("\nSaliendo de la simulación. ¡Adiós!")
            break

        if comando == 'salir':
            print("Saliendo de la simulación. ¡Adiós!")
            break
            
        elif comando == 'guardar':
            guardar_juego(motor)
            
        elif comando == 'recursos':
            comando_recursos(motor, tiempo_total)
            
        elif comando == 'mapa':
            comando_mapa(motor, tiempo_total)
            
        elif comando == 'tick':
            # Ejecutar varios ticks para simular un paso de tiempo notable
            ticks_por_comando = 10 # Simular 10 ticks = 5.0 segundos
            
            print(f"Simulando {ticks_por_comando} ticks ({ticks_por_comando * delta_tiempo:.1f}s)...")
            
            for _ in range(ticks_por_comando):
                motor.tick_simulacion(delta_tiempo, tiempo_total)
                tiempo_total += delta_tiempo
                
                if motor.mision_completada:
                    break
                    
            if not motor.mision_completada:
                comando_recursos(motor, tiempo_total)
            
        else:
            print(f"Comando desconocido: '{comando}'.")

    if motor.mision_completada:
        print(f"\n\n¡MISIÓN CUMPLIDA! El juego terminó en T={tiempo_total:.2f}s.")
        print(motor.monitor.generar_informe_final())


# =================================================================
#               CLASE MOTORJUEGO (NO MODIFICADA, SOLO AÑADIDA)
# =================================================================

class MotorJuego:
    def __init__(self):
        self.objetos = {} 
        self.facciones = {}
        self.contador_id = 0
        
        self.monitor = MonitorRendimiento() 
        self.mapeador = MapeadorEspacial()

        self.objetivo_mision = {
            'recurso': 'mineral', 
            'cantidad_requerida': 120 
        }
        self.mision_completada = False

        self.UNIDAD_CLASES = {
            'DroneRecoleccion': DroneRecoleccion,
            'CazaLigero': CazaLigero,
            'CorbetaDefensiva': CorbetaDefensiva,
            'Destructor': Destructor,
            'EstacionMinera': EstacionMinera,
            'GeneradorFusionBasico': GeneradorFusionBasico,
        }

    def crear_objeto(self, clase_objeto, faccion_nombre, posicion):
        self.contador_id += 1
        nuevo_objeto = clase_objeto(self.contador_id, faccion_nombre, posicion)
        self.objetos[self.contador_id] = nuevo_objeto
        
        if isinstance(nuevo_objeto, EstacionComandoOrbital):
            if faccion_nombre in self.facciones:
                self.facciones[faccion_nombre].poblacion_maxima += nuevo_objeto.poblacion_maxima_incremento 

        return nuevo_objeto

    def tick_simulacion(self, delta_tiempo, tiempo_total_acumulado):
        
        recursos_entregados_drones = {}

        # 1. Proceso de Estructuras (Producción y Entrenamiento)
        for id_objeto, objeto in list(self.objetos.items()):
            if isinstance(objeto, EstacionMinera) or isinstance(objeto, GeneradorFusionBasico):
                objeto.tick_simulacion_produccion() 
            if isinstance(objeto, EstacionComandoOrbital):
                 objeto.tick_simulacion_produccion(self, delta_tiempo) 
        
        # 2. Actualización de Unidades (Movimiento, Combate, Recolección)
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

        # 3. Aplicación de Recursos Entregados por Drones (Puntuales)
        for faccion_nombre, recursos in recursos_entregados_drones.items():
            if faccion_nombre in self.facciones:
                economia = self.facciones[faccion_nombre]
                for recurso, cantidad in recursos.items():
                    economia.recursos[recurso] += cantidad
        
        # 4. Aplicación del Costo de Mantenimiento
        for faccion_nombre, faccion in self.facciones.items():
            objetos_faccion = [obj for obj in self.objetos.values() if obj.faccion == faccion_nombre]
            faccion.aplicar_mantenimiento(objetos_faccion, delta_tiempo)
            
        # 5. Chequeo de Misión
        if not self.mision_completada:
            for faccion_nombre, faccion in self.facciones.items():
                recurso_mision = self.objetivo_mision['recurso']
                cantidad_requerida = self.objetivo_mision['cantidad_requerida']
                
                if faccion.recursos.get(recurso_mision, 0) >= cantidad_requerida:
                    self.mision_completada = True
                    print(f"\n[CONDICIÓN DE VICTORIA] ¡Misión completada por {faccion_nombre}!")
                    print(f"Objetivo: Alcanzar {cantidad_requerida} de {recurso_mision.upper()}.")
                    
        # 6. Penalización por Déficit de Recursos
        DANO_DEFICIT_ENERGIA = 2.0 

        for faccion_nombre, faccion in self.facciones.items():
            if faccion.recursos['energia'] < 0:
                dano_aplicar = DANO_DEFICIT_ENERGIA * delta_tiempo
                for id_objeto in list(self.objetos.keys()): 
                    objeto = self.objetos.get(id_objeto)
                    if objeto and objeto.faccion == faccion_nombre and objeto.vida_actual > 0:
                        if hasattr(objeto, 'mantenimiento_coste') and objeto.mantenimiento_coste.get('energia', 0) > 0:
                            objeto.recibir_danio(dano_aplicar)
                            
        # 7. Trazado de Rendimiento
        for faccion in self.facciones.values():
            self.monitor.registrar_estado_faccion(faccion, tiempo_total_acumulado)
            
        # 8. Actualización del Mapeador
        self.mapeador.actualizar_mapa(self.objetos)

        return 


    def iniciar_juego(self, cargar=False): 
        
        if cargar:
            juego_cargado = cargar_juego()
            if juego_cargado:
                self.__dict__.update(juego_cargado.__dict__)
                print(f"[REANUDANDO] Mineral actual: {self.facciones['Terran'].recursos['mineral']:.1f}")
                return

        # --- LÓGICA DE INICIO DE JUEGO NUEVO ---
        print("--- Iniciando Stellar Hegemony: Juego Nuevo ---")
        
        # --- FACCIÓN TERRAN ---
        terrana_nombre = 'Terran'
        self.facciones[terrana_nombre] = EconomiaFaccion(terrana_nombre)
        terrana = self.facciones[terrana_nombre]
        
        terrana.recursos = {'mineral': 100, 'energia': 500, 'materia_rara': 500} 
        
        # 1. Comando (ID 1)
        comando_t = self.crear_objeto(EstacionComandoOrbital, terrana_nombre, (0, 0, 0)) 
        
        # 2. Estación Minera (ID 2)
        minera_t = self.crear_objeto(EstacionMinera, terrana_nombre, (200, 0, 0))
        
        # 3. Drone inicial (ID 3)
        drone_t = self.crear_objeto(DroneRecoleccion, terrana_nombre, (10, 10, 10))
        terrana.poblacion_actual += drone_t.poblacion_coste
        
        drone_t.orden_recolectar(minera_t, comando_t)
        
        print(f"\n[MISIÓN] Recolectar {self.objetivo_mision['cantidad_requerida']} de {self.objetivo_mision['recurso'].upper()}.")
        print(f"[ECONOMÍA INICIAL] Mineral: {terrana.recursos['mineral']:.1f}")
        


# =================================================================
#               EJECUCIÓN PRINCIPAL
# =================================================================

if __name__ == "__main__":
    
    # --- FASE 1: Asegurar un archivo de guardado inicial ---
    # Esto garantiza que el juego tenga un archivo para cargar/continuar.
    print("\n\n=============== FASE 1: CREANDO ARCHIVO DE GUARDADO INICIAL ===============")
    juego_guardado = MotorJuego()
    
    tiempo_simular_guardado = 5.0 # Guardar a los 5.0s de simulación
    
    juego_guardado.iniciar_juego(cargar=False) 
    
    tiempo_total = 0.0
    delta_tiempo = 0.1
    print("\n--- Simulación a medio camino ---")
    while tiempo_total < tiempo_simular_guardado:
        juego_guardado.tick_simulacion(delta_tiempo, tiempo_total) 
        tiempo_total += delta_tiempo
        
    print(f"T: {tiempo_total:.1f}s | Mineral al guardar: {juego_guardado.facciones['Terran'].recursos['mineral']:.1f}")
    guardar_juego(juego_guardado)
    
    # --- FASE 2: INICIO DE LA CLI INTERACTIVA ---
    print("\n\n=============== FASE 2: INICIO DE JUEGO INTERACTIVO ===============")
    juego_interactivo = MotorJuego()
    jugar_cli(juego_interactivo)