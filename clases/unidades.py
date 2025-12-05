from clases.base import ObjetoEspacial
import math

# --- Tabla de Fortalezas y Debilidades (Daño Multiplicador) ---
MULTIPLIERS = {
    # Cazas (Fighter) > Capitales
    ('Caza', 'Capital'): 1.5,
    ('Caza', 'Soporte'): 0.5,
    # Soporte > Cazas
    ('Soporte', 'Caza'): 1.5,
    ('Soporte', 'Capital'): 0.5,
    # Capitales > Soporte
    ('Capital', 'Soporte'): 1.5,
    ('Capital', 'Caza'): 0.5,
}

class Unidad(ObjetoEspacial):
    def __init__(self, id, faccion, posicion, nombre, coste, velocidad_maxima, danio_base, alcance, tipo_unidad):
        super().__init__(id, faccion, posicion)
        
        self.nombre = nombre
        self.coste = coste
        self.velocidad_maxima = velocidad_maxima
        self.danio_base = danio_base
        self.alcance = alcance
        self.tipo_unidad = tipo_unidad 
        self.vida_maxima = 100
        self.vida_actual = 100
        self.armadura = 0
        self.poblacion_coste = 1 
        
        # Costo de mantenimiento por segundo (Upkeep)
        self.mantenimiento_coste = {'energia': 0.5} 
        
        self.objetivo_movimiento = None 
        self.objetivo_combate = None    
        self.cooldown_ataque = 0.5     
        self.tiempo_restante_cooldown = 0.0
        self.distancia_a_objetivo = float('inf') 

    def moverse(self, destino):
        self.objetivo_movimiento = destino
        self.objetivo_combate = None 

    def atacar_unidad(self, objetivo):
        self.objetivo_combate = objetivo
        self.objetivo_movimiento = None 
        
    def calcular_distancia(self, pos1, pos2):
        return math.sqrt(
            (pos1[0] - pos2[0])**2 + 
            (pos1[1] - pos2[1])**2 + 
            (pos1[2] - pos2[2])**2
        )

    def atacar(self, objetivo):
        if not objetivo or not objetivo.vida_actual > 0:
            self.objetivo_combate = None
            return

        tipo_objetivo = getattr(objetivo, 'tipo_unidad', 'Estructura') 
        tipos_combate = (self.tipo_unidad, tipo_objetivo)
        multiplicador = MULTIPLIERS.get(tipos_combate, 1.0) 
        danio_efectivo = self.danio_base * multiplicador
        
        # print(f"[{self.nombre}#{self.id}] ataca a {objetivo.nombre}#{objetivo.id} ({tipo_objetivo}). Daño: {danio_efectivo:.1f} (x{multiplicador:.1f})")
        objetivo.recibir_danio(danio_efectivo)

    def recibir_danio(self, danio):
        """Aplica el daño, priorizando los escudos si existen."""
        
        danio_residual = danio
        
        # 1. Absorber con Escudos (Si los tiene)
        if hasattr(self, 'escudo_actual') and self.escudo_actual > 0:
            danio_absorbido = min(self.escudo_actual, danio_residual)
            self.escudo_actual -= danio_absorbido
            danio_residual -= danio_absorbido
            
            if danio_absorbido > 0:
                print(f"[{self.nombre}#{self.id}] Escudo absorbio {danio_absorbido:.2f} daño. Escudo restante: {self.escudo_actual:.2f}")

        # 2. Absorber con Armadura (Solo el daño residual)
        danio_efectivo = max(0, danio_residual - self.armadura)
        
        if danio_efectivo > 0:
            self.vida_actual -= danio_efectivo
        
        if self.vida_actual <= 0:
            # print(f"Objeto {self.id} destruido.")
            pass
            
    def buscar_objetivo_cercano(self, todos_los_objetos):
        """Busca el enemigo más estratégico para atacar (Cercano y Dañado)."""
        enemigo_mas_estrategico = None
        
        # Usaremos una métrica ponderada para encontrar el mejor objetivo
        # Puntuación baja = Mejor objetivo
        mejor_puntuacion = float('inf') 

        for objeto in todos_los_objetos.values():
            # Debe ser de otra facción y estar vivo
            if objeto.faccion != self.faccion and objeto.vida_actual > 0:
                
                distancia = self.calcular_distancia(self.posicion, objeto.posicion)
                
                # Normalizamos la distancia (Ejemplo: Distancia 100 -> Factor 1.0)
                # Usaremos un factor de escala de 100, asumiendo que la mayoría de los combates son dentro de este rango.
                factor_distancia = max(1.0, distancia / 100.0) 
                
                # Porcentaje de vida restante (0.1 a 1.0)
                porcentaje_vida = objeto.vida_actual / objeto.vida_maxima
                
                # --- CÁLCULO DE LA PUNTUACIÓN DE ESTRATEGIA ---
                # Puntuación = FactorDistancia * PorcentajeVida
                
                puntuacion = factor_distancia * porcentaje_vida
                
                # Si el enemigo tiene escudo, el porcentaje de vida se penaliza (es menos 'dañado')
                if hasattr(objeto, 'escudo_actual') and objeto.escudo_actual > 0:
                    # Penalización: Aumentamos la puntuación (lo hacemos menos atractivo como objetivo)
                    puntuacion *= 1.2 

                if puntuacion < mejor_puntuacion:
                    mejor_puntuacion = puntuacion
                    enemigo_mas_estrategico = objeto
        
        if enemigo_mas_estrategico:
            print(f"[{self.nombre}#{self.id}] IA (Focus Fire): Nuevo objetivo -> {enemigo_mas_estrategico.nombre}#{enemigo_mas_estrategico.id} (Puntuación: {mejor_puntuacion:.2f})")
            self.atacar_unidad(enemigo_mas_estrategico)
        else:
            # print(f"[{self.nombre}#{self.id}] IA: No se encontraron enemigos cercanos. Volviendo a ocio.")
            self.objetivo_combate = None

    def tick_simulacion(self, motor_juego, delta_tiempo): 
        
        recursos_entregados = {}
        
        # --- Lógica de Habilidades Activas y Cooldowns ---
        # Si la unidad tiene impulso de velocidad (es decir, si es un CazaLigero)
        velocidad_efectiva = self.velocidad_maxima
        
        if hasattr(self, 'impulso_activo'):
            # 1. Gestionar el Cooldown
            if self.impulso_cooldown_restante > 0:
                self.impulso_cooldown_restante -= delta_tiempo
            
            # 2. Gestionar el Efecto Activo
            if self.impulso_activo:
                self.impulso_tiempo_restante -= delta_tiempo
                velocidad_efectiva = self.velocidad_maxima * self.impulso_multiplicador
                
                if self.impulso_tiempo_restante <= 0:
                    self.impulso_activo = False
                    # print(f"[{self.nombre}#{self.id}] El impulso de velocidad ha terminado.")
            
        # Utilizamos la velocidad_efectiva calculada
        velocidad_base_usar = velocidad_efectiva 

        # --- Lógica de Combate (Activación de IA) ---
        if self.tipo_unidad != 'Civil' and (self.objetivo_combate is None or self.objetivo_combate.vida_actual <= 0):
            self.buscar_objetivo_cercano(motor_juego.objetos) 
            
        
        self.distancia_a_objetivo = float('inf')

        if self.objetivo_combate and self.objetivo_combate.vida_actual > 0:
            
            self.distancia_a_objetivo = self.calcular_distancia(self.posicion, self.objetivo_combate.posicion)
            
            if self.distancia_a_objetivo <= self.alcance:
                self.objetivo_movimiento = None 
                
                if self.tiempo_restante_cooldown <= 0:
                    self.atacar(self.objetivo_combate)
                    self.tiempo_restante_cooldown = self.cooldown_ataque
                else:
                    self.tiempo_restante_cooldown -= delta_tiempo 
            else:
                self.objetivo_movimiento = self.objetivo_combate.posicion 
                
        
        # --- Lógica de Movimiento ---
        if self.objetivo_movimiento:
            distancia = self.calcular_distancia(self.posicion, self.objetivo_movimiento)
            
            if distancia > 0.1: 
                dx = self.objetivo_movimiento[0] - self.posicion[0]
                dy = self.objetivo_movimiento[1] - self.posicion[1]
                dz = self.objetivo_movimiento[2] - self.posicion[2]
                
                # USAMOS velocidad_base_usar
                movimiento_max = velocidad_base_usar * delta_tiempo 
                
                if distancia < movimiento_max:
                    self.posicion = self.objetivo_movimiento
                    self.objetivo_movimiento = None
                else:
                    factor = movimiento_max / distancia
                    self.posicion = (
                        self.posicion[0] + dx * factor,
                        self.posicion[1] + dy * factor,
                        self.posicion[2] + dz * factor
                    )
            else:
                self.objetivo_movimiento = None
        
        # Asegura que el cooldown progrese cuando no hay ataque
        if self.objetivo_combate is None or self.distancia_a_objetivo > self.alcance:
             self.tiempo_restante_cooldown = max(0, self.tiempo_restante_cooldown - delta_tiempo)
             
        return recursos_entregados # Retorna un dict vacío por defecto

# --- Subclases de Unidades ---

class CazaLigero(Unidad):
    def __init__(self, id, faccion, posicion):
        super().__init__(
            id, faccion, posicion,
            nombre="CazaLigero", 
            coste={'mineral': 50, 'energia': 25},
            velocidad_maxima=50.0,
            danio_base=15, 
            alcance=10.0,
            tipo_unidad='Caza'
        )
        self.vida_maxima = 80
        self.vida_actual = 80
        self.armadura = 0

        # --- Habilidad Activa: Impulso de Velocidad ---
        self.impulso_activo = False
        self.impulso_duracion_max = 3.0       # Dura 3 segundos
        self.impulso_tiempo_restante = 0.0
        self.impulso_multiplicador = 2.0      # Duplica la velocidad (100.0)
        self.impulso_cooldown_max = 10.0      # Se puede usar cada 10 segundos
        self.impulso_cooldown_restante = 0.0

    def activar_impulso_velocidad(self):
        """Activa el impulso de velocidad si el cooldown lo permite."""
        if self.impulso_cooldown_restante <= 0 and not self.impulso_activo:
            self.impulso_activo = True
            self.impulso_tiempo_restante = self.impulso_duracion_max
            self.impulso_cooldown_restante = self.impulso_cooldown_max
            print(f"[{self.nombre}#{self.id}] Habilidad Activada: ¡Impulso de Velocidad! Velocidad duplicada.")
            return True
        return False

class CorbetaDefensiva(Unidad):
    def __init__(self, id, faccion, posicion):
        super().__init__(
            id, faccion, posicion,
            nombre="CorbetaDefensiva", 
            coste={'mineral': 75, 'energia': 50},
            velocidad_maxima=30.0,
            danio_base=10, 
            alcance=15.0,
            tipo_unidad='Soporte'
        )
        self.vida_maxima = 150
        self.vida_actual = 150
        self.armadura = 2

class Destructor(Unidad):
    def __init__(self, id, faccion, posicion):
        super().__init__(
            id, faccion, posicion,
            nombre="Destructor", 
            coste={'mineral': 200, 'energia': 150, 'materia_rara': 50},
            velocidad_maxima=15.0,
            danio_base=40, 
            alcance=20.0,
            tipo_unidad='Capital'
        )
        self.vida_maxima = 400
        self.vida_actual = 400
        self.armadura = 5
        self.poblacion_coste = 5 
        self.mantenimiento_coste = {'energia': 5.0} 

        # --- Habilidad Especial: ESCUDO DE ENERGÍA ---
        self.escudo_maximo = 100.0
        self.escudo_actual = 100.0 
        self.tasa_regeneracion_escudo = 5.0 

    def tick_simulacion(self, motor_juego, delta_tiempo):
        # 1. Regeneración del Escudo
        if self.escudo_actual < self.escudo_maximo:
            regeneracion = self.tasa_regeneracion_escudo * delta_tiempo
            self.escudo_actual = min(self.escudo_maximo, self.escudo_actual + regeneracion)

        # 2. Ejecutar la lógica base (movimiento, combate, IA)
        return super().tick_simulacion(motor_juego, delta_tiempo)


class DroneRecoleccion(Unidad):
    # Estados de Recolección
    ESTADO_OCIO = 0
    ESTADO_IR_A_RECURSO = 1
    ESTADO_RECOLECTANDO = 2
    ESTADO_IR_A_ENTREGA = 3
    ESTADO_ENTREGANDO = 4
    
    CAPACIDAD_CARGA = 5     
    TIEMPO_RECOLECCION = 3.0
    
    def __init__(self, id, faccion, posicion):
        super().__init__(
            id, faccion, posicion,
            nombre="DroneRecoleccion", 
            coste={'mineral': 50, 'energia': 0},
            velocidad_maxima=20.0,
            danio_base=1, 
            alcance=5.0,
            tipo_unidad='Civil'
        )
        self.vida_maxima = 40
        self.vida_actual = 40
        self.armadura = 0
        self.poblacion_coste = 1 
        self.mantenimiento_coste = {'energia': 0.5} 
        
        # Atributos de Recolección
        self.objetivo_recurso = None      
        self.objetivo_entrega = None      
        self.estado_recoleccion = self.ESTADO_OCIO
        self.recurso_transportado = 0     
        self.tiempo_restante_accion = 0.0

    def orden_recolectar(self, objetivo_recurso, objetivo_entrega):
        """Asigna una estación de recurso y una de entrega."""
        self.objetivo_recurso = objetivo_recurso
        self.objetivo_entrega = objetivo_entrega
        self.objetivo_combate = None
        self.recurso_transportado = 0
        if objetivo_recurso and objetivo_entrega:
            self.estado_recoleccion = self.ESTADO_IR_A_RECURSO
        else:
            self.estado_recoleccion = self.ESTADO_OCIO
    
    def tick_simulacion(self, motor_juego, delta_tiempo): 
        
        recursos_entregados = {}

        # 1. Gestionar el estado de Recolección
        if self.estado_recoleccion != self.ESTADO_OCIO:
            
            if self.estado_recoleccion == self.ESTADO_IR_A_RECURSO:
                self._logica_ir_a_recurso(delta_tiempo)
            
            elif self.estado_recoleccion == self.ESTADO_RECOLECTANDO:
                recursos_entregados = self._logica_recolectando(delta_tiempo)
                
            elif self.estado_recoleccion == self.ESTADO_IR_A_ENTREGA:
                self._logica_ir_a_entrega(delta_tiempo)
            
            elif self.estado_recoleccion == self.ESTADO_ENTREGANDO:
                recursos_entregados = self._logica_entregando(delta_tiempo)
        
        # 2. Ejecutar la lógica de movimiento y combate base (Drone es civil, no busca combate)
        super_recursos = super().tick_simulacion(motor_juego, delta_tiempo)
        
        return recursos_entregados if recursos_entregados else super_recursos


    def _logica_ir_a_recurso(self, delta_tiempo):
        self.objetivo_movimiento = self.objetivo_recurso.posicion
        distancia = self.calcular_distancia(self.posicion, self.objetivo_recurso.posicion)
        
        if distancia <= self.alcance: 
            self.objetivo_movimiento = None
            self.estado_recoleccion = self.ESTADO_RECOLECTANDO
            self.tiempo_restante_accion = self.TIEMPO_RECOLECCION

    def _logica_recolectando(self, delta_tiempo):
        self.tiempo_restante_accion -= delta_tiempo
        
        if self.tiempo_restante_accion <= 0:
            recursos_extraidos = self.objetivo_recurso.extraer_recursos(self.CAPACIDAD_CARGA)
            recurso_clave = self.objetivo_recurso.recurso_clave
            
            if recurso_clave in recursos_extraidos and recursos_extraidos[recurso_clave] > 0:
                self.recurso_transportado = recursos_extraidos[recurso_clave]
                
                self.estado_recoleccion = self.ESTADO_IR_A_ENTREGA
                self.objetivo_movimiento = self.objetivo_entrega.posicion
            else:
                self.tiempo_restante_accion = 1.0 
                self.estado_recoleccion = self.ESTADO_RECOLECTANDO
        return {} 
        
    def _logica_ir_a_entrega(self, delta_tiempo):
        self.objetivo_movimiento = self.objetivo_entrega.posicion
        distancia = self.calcular_distancia(self.posicion, self.objetivo_entrega.posicion)
        
        if distancia <= self.alcance: 
            self.objetivo_movimiento = None
            self.estado_recoleccion = self.ESTADO_ENTREGANDO
            self.tiempo_restante_accion = 0.5 

    def _logica_entregando(self, delta_tiempo):
        self.tiempo_restante_accion -= delta_tiempo
        
        if self.tiempo_restante_accion <= 0:
            recursos_entregados = {}
            if self.recurso_transportado > 0:
                recurso_clave = self.objetivo_recurso.recurso_clave
                recursos_entregados[recurso_clave] = self.recurso_transportado
            
            self.recurso_transportado = 0
            self.estado_recoleccion = self.ESTADO_IR_A_RECURSO
            self.objetivo_movimiento = self.objetivo_recurso.posicion
            return recursos_entregados
        return {}