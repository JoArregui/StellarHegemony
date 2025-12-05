import time

class MonitorRendimiento:
    def __init__(self):
        self.registros = []
        self.tiempo_inicio_tick = 0.0
        
    def iniciar_tick(self):
        """Marca el inicio de un ciclo de simulación para medir su duración."""
        self.tiempo_inicio_tick = time.time()
        
    def finalizar_tick(self, motor_juego, delta_tiempo):
        """Calcula el tiempo de ejecución y registra las métricas clave del estado del juego."""
        
        tiempo_fin_tick = time.time()
        duracion_tick = tiempo_fin_tick - self.tiempo_inicio_tick
        
        # 1. Métrica de Economía (Terran)
        terrana = motor_juego.facciones.get('Terran')
        
        datos_economia = {
            'mineral': terrana.recursos['mineral'],
            'energia': terrana.recursos['energia'],
            'poblacion_actual': terrana.poblacion_actual,
            'poblacion_maxima': terrana.poblacion_maxima
        }
        
        # 2. Métrica de Objetos (Número de unidades por tipo)
        conteo_objetos = {}
        for obj in motor_juego.objetos.values():
            nombre_clase = obj.__class__.__name__
            conteo_objetos[nombre_clase] = conteo_objetos.get(nombre_clase, 0) + 1
            
        # 3. Registrar el estado
        registro = {
            'tiempo_simulacion': motor_juego.tiempo_total_simulacion, # Lo añadiremos en MotorJuego
            'duracion_cpu': duracion_tick,
            'delta_tiempo': delta_tiempo,
            'economia': datos_economia,
            'objetos': conteo_objetos
        }
        
        self.registros.append(registro)
        return registro
    
    def imprimir_resumen(self):
        """Imprime un resumen de los registros de rendimiento."""
        
        if not self.registros:
            print("[MonitorRendimiento] No hay datos registrados.")
            return

        print("\n--- RESUMEN DE RENDIMIENTO (Trazado) ---")
        
        duraciones = [r['duracion_cpu'] for r in self.registros]
        
        tiempo_total_cpu = sum(duraciones)
        media_cpu = sum(duraciones) / len(duraciones)
        
        print(f"Total Ticks Registrados: {len(self.registros)}")
        print(f"Tiempo Total de CPU: {tiempo_total_cpu:.4f}s")
        print(f"Media de CPU por Tick: {media_cpu * 1000:.4f} ms")
        print(f"Máximo de CPU en un Tick: {max(duraciones) * 1000:.4f} ms")
        print("---------------------------------------")