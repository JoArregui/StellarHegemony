import dill
import os

NOMBRE_ARCHIVO_GUARDADO = "partida_guardada.shg" # Stellar Hegemony Game

def guardar_juego(motor_juego):
    """Serializa y guarda el objeto MotorJuego en un archivo."""
    try:
        # Usamos 'dill.dump' para serializar el objeto MotorJuego y todas sus referencias.
        with open(NOMBRE_ARCHIVO_GUARDADO, 'wb') as archivo:
            dill.dump(motor_juego, archivo)
        print(f"\n[GUARDADO EXITOSO] Estado del juego guardado en '{NOMBRE_ARCHIVO_GUARDADO}'")
        return True
    except Exception as e:
        print(f"[ERROR DE GUARDADO] No se pudo guardar el juego: {e}")
        return False

def cargar_juego():
    """Carga y deserializa el objeto MotorJuego desde un archivo."""
    if not os.path.exists(NOMBRE_ARCHIVO_GUARDADO):
        print(f"[ERROR DE CARGA] Archivo '{NOMBRE_ARCHIVO_GUARDADO}' no encontrado.")
        return None
        
    try:
        # Usamos 'dill.load' para reconstruir el objeto MotorJuego.
        with open(NOMBRE_ARCHIVO_GUARDADO, 'rb') as archivo:
            motor_juego = dill.load(archivo)
        print(f"\n[CARGADO EXITOSO] Estado del juego cargado desde '{NOMBRE_ARCHIVO_GUARDADO}'")
        return motor_juego
    except Exception as e:
        print(f"[ERROR DE CARGA] No se pudo cargar el juego. El archivo podría estar corrupto o ser incompatible: {e}")
        return None