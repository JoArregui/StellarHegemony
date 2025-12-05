from clases.base import ObjetoEspacial
# Importar unidades para la verificación de costos/creación en EstacionComandoOrbital
from clases.unidades import DroneRecoleccion, CazaLigero, CorbetaDefensiva, Destructor 
import math

class Estructura(ObjetoEspacial):
    def __init__(self, id, faccion, posicion, nombre, coste, tipo_estructura='Base'):
        super().__init__(id, faccion, posicion)
        self.nombre = nombre
        self.coste = coste
        self.tipo_estructura = tipo_estructura
        self.vida_maxima = 500
        self.vida_actual = 500
        self.armadura = 5
        self.poblacion_coste = 0 
        self.mantenimiento_coste = {'energia': 1.0} 

    def recibir_danio(self, danio):
        danio_efectivo = max(0, danio - self.armadura)
        self.vida_actual -= danio_efectivo
        if self.vida_actual <= 0:
            # print(f"Estructura {self.id} destruida.")
            pass

class EstacionComandoOrbital(Estructura):
    def __init__(self, id, faccion, posicion):
        super().__init__(
            id, faccion, posicion,
            nombre="EstacionComandoOrbital",
            coste={'mineral': 400, 'energia': 200},
            tipo_estructura='Capital'
        )
        self.vida_maxima = 1000
        self.vida_actual = 1000
        self.mantenimiento_coste = {'energia': 2.0} 
        self.poblacion_maxima_incremento = 10
        
        # --- Cola de Producción ---
        self.cola_produccion = [] # Lista de diccionarios: {'nombre', 'tiempo', 'coste'}
        self.item_actual = None    
        self.tiempo_restante_produccion = 0.0
        
        # Mapa de tiempos de construcción (simulando complejidad)
        self.tiempos_base_construccion = {
            'DroneRecoleccion': 5.0,
            'CazaLigero': 8.0,
            'CorbetaDefensiva': 12.0,
            'Destructor': 30.0,
            'EstacionMinera': 15.0,
            'GeneradorFusionBasico': 10.0,
        }
        
    def agregar_a_cola(self, item_nombre, motor_juego):
        """Intenta agregar una unidad o estructura a la cola de producción."""
        faccion = motor_juego.facciones.get(self.faccion)
        
        # 1. Verificar si el nombre está en el mapa de clases
        if item_nombre not in motor_juego.UNIDAD_CLASES:
            print(f"[{self.nombre}#{self.id}] ERROR: '{item_nombre}' no está definido para la producción.")
            return False

        # 2. Obtener la clase, costo y tiempo
        item_clase = motor_juego.UNIDAD_CLASES[item_nombre]
        
        # Crear instancia temporal para obtener costos (ID 0, Posición 0,0,0)
        temp_item = item_clase(0, self.faccion, (0,0,0)) 
        coste = temp_item.coste
        tiempo = self.tiempos_base_construccion.get(item_nombre)
        
        if not tiempo:
             print(f"[{self.nombre}#{self.id}] ERROR: Tiempo de construcción no definido para '{item_nombre}'.")
             return False

        # 3. Verificar recursos y población
        poblacion_necesaria = getattr(temp_item, 'poblacion_coste', 0)
        
        if faccion.puede_pagar(coste) and (faccion.poblacion_actual + poblacion_necesaria <= faccion.poblacion_maxima):
            
            faccion.pagar(coste)
            
            self.cola_produccion.append({'nombre': item_nombre, 'tiempo': tiempo, 'coste': coste})
            print(f"[{self.nombre}#{self.id}] '{item_nombre}' añadido a la cola. Coste Deducido: {coste}")
            return True
        else:
            if not faccion.puede_pagar(coste):
                 print(f"[{self.nombre}#{self.id}] Falla al añadir '{item_nombre}'. Recursos insuficientes.")
            else:
                 print(f"[{self.nombre}#{self.id}] Falla al añadir '{item_nombre}'. Límite de población alcanzado.")

            return False

    def tick_simulacion_produccion(self, motor_juego, delta_tiempo):
        """Gestiona la cola de producción y crea objetos."""
        
        # 1. Iniciar el siguiente ítem si la cola no está vacía
        if self.item_actual is None and self.cola_produccion:
            self.item_actual = self.cola_produccion.pop(0)
            self.tiempo_restante_produccion = self.item_actual['tiempo']
            print(f"[{self.nombre}#{self.id}] Comienza la producción de: {self.item_actual['nombre']} ({self.tiempo_restante_produccion:.1f}s restantes)")
        
        # 2. Procesar el ítem actual
        if self.item_actual:
            self.tiempo_restante_produccion -= delta_tiempo
            
            if self.tiempo_restante_produccion <= 0:
                # Producción terminada!
                nombre_clase = self.item_actual['nombre']
                item_clase = motor_juego.UNIDAD_CLASES[nombre_clase]
                
                # Ubicación de spawn (un poco al lado del comando)
                spawn_pos = (self.posicion[0] + 5, self.posicion[1] + 5, self.posicion[2])
                
                # Crear el objeto (usando la función del motor de juego)
                nuevo_objeto = motor_juego.crear_objeto(item_clase, self.faccion, spawn_pos)
                
                # El motor de juego ya gestiona la población máxima en crear_objeto
                
                print(f"[{self.nombre}#{self.id}] ¡Producción finalizada! Creado: {nuevo_objeto.nombre}#{nuevo_objeto.id} en {spawn_pos}")
                
                # Resetear
                self.item_actual = None
                self.tiempo_restante_produccion = 0.0


class EstacionMinera(Estructura):
    def __init__(self, id, faccion, posicion):
        super().__init__(
            id, faccion, posicion,
            nombre="EstacionMinera",
            coste={'mineral': 100, 'energia': 50},
            tipo_estructura='Soporte'
        )
        self.recurso_clave = 'mineral'
        self.almacen_recurso = 0
        self.tasa_produccion = 5.0 

    def tick_simulacion_produccion(self):
        """Llena el almacén interno de la minera."""
        self.almacen_recurso += self.tasa_produccion
        
    def extraer_recursos(self, cantidad):
        """Permite que los drones extraigan recursos de la minera."""
        extraido = min(cantidad, self.almacen_recurso)
        self.almacen_recurso -= extraido
        return {self.recurso_clave: extraido}

class GeneradorFusionBasico(Estructura):
    def __init__(self, id, faccion, posicion):
        super().__init__(
            id, faccion, posicion,
            nombre="GeneradorFusionBasico",
            coste={'mineral': 50, 'energia': 150},
            tipo_estructura='Soporte'
        )
        self.recurso_clave = 'energia'
        self.almacen_recurso = 0
        self.tasa_produccion = 10.0 

    def tick_simulacion_produccion(self):
        """Llena el almacén interno del generador (no usado actualmente)."""
        self.almacen_recurso += self.tasa_produccion