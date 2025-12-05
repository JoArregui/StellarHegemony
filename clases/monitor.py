class MonitorRendimiento:
    """Clase para recolectar y almacenar métricas clave de la simulación por tick."""
    
    def __init__(self):
        # Lista de diccionarios, donde cada diccionario representa el estado al final de un tick.
        # Esto nos permite analizar la simulación paso a paso.
        self.historial_ticks = []
        
    def registrar_estado_faccion(self, faccion, tiempo_total):
        """
        Registra los recursos, población y estado general de la facción.
        
        @param faccion: Objeto EconomiaFaccion a registrar.
        @param tiempo_total: El tiempo acumulado de la simulación.
        """
        
        estado = {
            'tiempo': round(tiempo_total, 2),
            'faccion': faccion.nombre,
            'mineral': round(faccion.recursos['mineral'], 2),
            'energia': round(faccion.recursos['energia'], 2),
            'materia_rara': round(faccion.recursos['materia_rara'], 2),
            'poblacion_actual': faccion.poblacion_actual,
            'poblacion_maxima': faccion.poblacion_maxima,
            # Añadir futuras métricas de rendimiento (ej: unidades activas, DPS total, etc.)
        }
        self.historial_ticks.append(estado)
        
    def generar_informe_final(self):
        """Muestra un resumen de las métricas registradas."""
        if not self.historial_ticks:
            return "No hay datos registrados."

        # Tomar el primer y último estado
        primer_estado = self.historial_ticks[0]
        ultimo_estado = self.historial_ticks[-1]
        
        duracion = ultimo_estado['tiempo'] - primer_estado['tiempo']
        
        informe = f"\n--- INFORME DE RENDIMIENTO FINAL ---\n"
        informe += f"Duración simulada: {duracion:.2f} segundos ({len(self.historial_ticks)} ticks)\n"
        informe += f"Recurso (Mineral) Inicial: {primer_estado['mineral']:.2f}\n"
        informe += f"Recurso (Mineral) Final: {ultimo_estado['mineral']:.2f}\n"
        informe += f"Ganancia Neta (Mineral): {ultimo_estado['mineral'] - primer_estado['mineral']:.2f}\n"
        informe += f"Energía Final: {ultimo_estado['energia']:.2f}\n"
        informe += f"Población Final: {ultimo_estado['poblacion_actual']}/{ultimo_estado['poblacion_maxima']}\n"
        informe += f"-----------------------------------------\n"
        
        return informe