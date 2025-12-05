from clases.base import ObjetoEspacial
from clases.economia import EconomiaFaccion
# Importar todas las clases necesarias para el mapeo
from clases.estructuras import EstacionMinera, GeneradorFusionBasico, EstacionComandoOrbital
from clases.unidades import CazaLigero, CorbetaDefensiva, DroneRecoleccion, Destructor 
from clases.serializador import guardar_juego, cargar_juego 

class MotorJuego:
    def __init__(self):
        self.objetos = {} 
        self.facciones = {}
        self.contador_id = 0
        
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
                            
        return 


    def iniciar_juego(self, cargar=False): 
        
        if cargar:
            juego_cargado = cargar_juego()
            if juego_cargado:
                # Si se carga, reemplazamos el 'self' actual con el estado cargado
                self.__dict__.update(juego_cargado.__dict__)
                print(f"[REANUDANDO] Mineral actual: {self.facciones['Terran'].recursos['mineral']:.1f}")
                return

        # --- LÓGICA DE INICIO DE JUEGO NUEVO (SOLO SI NO SE CARGÓ) ---
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
        
        # Aquí termina la lógica de inicio de juego nuevo


if __name__ == "__main__":
    
    # --- Ejecutar Prueba 1: GUARDADO INICIAL ---
    print("\n\n=============== PRUEBA 1: GUARDADO INICIAL ===============")
    juego_guardado = MotorJuego()
    
    # Simular solo 5.0s (a medio camino del primer viaje de recolección)
    tiempo_simular_guardado = 5.0
    
    juego_guardado.iniciar_juego(cargar=False) 
    
    # Ejecutar simulación a medio camino
    tiempo_total = 0.0
    delta_tiempo = 0.1
    print("\n--- Simulación a medio camino ---")
    while tiempo_total < tiempo_simular_guardado:
        juego_guardado.tick_simulacion(delta_tiempo)
        tiempo_total += delta_tiempo
        
    print(f"T: {tiempo_total:.1f}s | Mineral al guardar: {juego_guardado.facciones['Terran'].recursos['mineral']:.1f}")
    guardar_juego(juego_guardado)

    # --- Ejecutar Prueba 2: CARGADO Y VICTORIA ---
    print("\n\n=============== PRUEBA 2: CARGADO Y VICTORIA ===============")
    juego_cargado = MotorJuego()
    juego_cargado.iniciar_juego(cargar=True) # Intentar cargar el estado de la Prueba 1

    if not juego_cargado.mision_completada:
        
        terrana = juego_cargado.facciones['Terran']
        
        # El mineral debe seguir en 100.0, ya que no ha habido entregas
        print(f"[VERIFICACIÓN] Mineral: {terrana.recursos['mineral']:.1f} (Debe ser 100.0)")

        # Bucle de Simulación para completar la misión
        tiempo_total = 5.0 # Continuar la simulación desde T=5.0s
        delta_tiempo = 0.1 
        num_ticks = 0
        max_duracion = 100.0 
        
        print("\n--- Continuación de la Simulación ---")
        
        while tiempo_total < max_duracion and not juego_cargado.mision_completada:
            juego_cargado.tick_simulacion(delta_tiempo)
            tiempo_total += delta_tiempo
            num_ticks += 1
            
            if num_ticks % 50 == 0: 
                print(f"T: {tiempo_total:.1f}s | Mineral Actual: {terrana.recursos['mineral']:.1f} | Progreso: {terrana.recursos['mineral']/juego_cargado.objetivo_mision['cantidad_requerida'] * 100:.1f}%")

        print(f"\n--- Resultado Final (Cargado) ---")
        print(f"Tiempo simulado total: {tiempo_total:.2f} segundos.")
        print(f"Misión completada: {'Sí' if juego_cargado.mision_completada else 'No'}")
        
        if juego_cargado.mision_completada:
            print(f"Mineral final: {terrana.recursos['mineral']:.1f}")