class EconomiaFaccion:
    def __init__(self, nombre):
        self.nombre = nombre
        self.recursos = {'mineral': 0, 'energia': 0, 'materia_rara': 0}
        self.poblacion_actual = 0
        self.poblacion_maxima = 0

    def aplicar_mantenimiento(self, objetos_faccion, delta_tiempo):
        """Calcula y aplica el costo de mantenimiento (upkeep) de todas las unidades y estructuras."""
        
        costo_total = {'mineral': 0, 'energia': 0, 'materia_rara': 0}
        
        # 1. Sumar el costo de mantenimiento de todos los objetos
        for objeto in objetos_faccion:
            if hasattr(objeto, 'mantenimiento_coste'):
                for recurso, cantidad_por_segundo in objeto.mantenimiento_coste.items():
                    costo_total[recurso] += cantidad_por_segundo

        # 2. Deducir el costo de los recursos de la facción
        for recurso, costo_por_segundo in costo_total.items():
            costo_a_aplicar = costo_por_segundo * delta_tiempo
            
            # Restamos el costo de la energía. Si el recurso cae en negativo, se aplicará penalización.
            if recurso in self.recursos:
                self.recursos[recurso] -= costo_a_aplicar
    
    # --- MÉTODOS AÑADIDOS PARA COLAS DE PRODUCCIÓN ---

    def puede_pagar(self, coste):
        """Verifica si la facción tiene suficientes recursos para cubrir el coste dado."""
        for recurso, cantidad_necesaria in coste.items():
            # Si el recurso no está en self.recursos, asumimos que la cantidad es 0, lo cual es menor a la necesaria.
            if self.recursos.get(recurso, 0) < cantidad_necesaria:
                return False
        return True

    def pagar(self, coste):
        """Deduce los recursos del coste dado. Asume que puede pagar."""
        for recurso, cantidad_necesaria in coste.items():
            if recurso in self.recursos:
                self.recursos[recurso] -= cantidad_necesaria