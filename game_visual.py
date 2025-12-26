import pygame
import sys
import random
import math

# Intentamos importar las clases del motor, si no, usamos stubs para que el código sea ejecutable
try:
    from main import MotorJuego, Enemigo, CazaLigero, CruceroBatalla, procesar_comando
except ImportError:
    # Stubs de emergencia para pruebas
    class MotorJuego:
        def __init__(self): 
            self.objetos = {}
            self.facciones = {'Terran': type('F', (), {'recursos': {'mineral': 500, 'energia': 200}})}
        def tick_simulacion(self, dt): pass
        def iniciar_juego(self): pass
    def procesar_comando(m, t): pass
    class CruceroBatalla: pass

# --- CONFIGURACIÓN ESTÉTICA ---
COLOR_FONDO = (5, 5, 10)
COLOR_TERRAN = (0, 255, 180)  # Un cian más neón
COLOR_PIRATA = (255, 40, 60)
COLOR_HUD_BG = (15, 15, 25)
ANCHO, ALTO = 1100, 700

class InterfazGrafica:
    def __init__(self, motor):
        pygame.init()
        # Usamos doble buffering para suavidad
        self.screen = pygame.display.set_mode((ANCHO, ALTO), pygame.DOUBLEBUF)
        pygame.display.set_caption("STELLAR HEGEMONY - ADVANCED TACTICAL HUD")
        self.clock = pygame.time.Clock()
        self.motor = motor
        self.fuente = pygame.font.SysFont("Consolas", 13)
        self.fuente_tit = pygame.font.SysFont("Consolas", 18, bold=True)
        self.input_text = ""
        self.logs = ["SISTEMAS INICIALIZADOS...", "CONEXIÓN SATELITAL ESTABLECIDA."]
        
        # Elementos visuales dinámicos
        self.estrellas = [[random.randint(0, 900), random.randint(0, ALTO), random.random()] for _ in range(100)]
        self.escaneo_y = 0 # Para el efecto de línea de escaneo móvil

    def world_to_screen(self, pos):
        return (int(pos[0] + 450), int(pos[1] + 350))

    def dibujar_entorno(self):
        self.screen.fill(COLOR_FONDO)
        
        # 1. Estrellas con parpadeo
        for s in self.estrellas:
            brillo = int(150 + 105 * math.sin(pygame.time.get_ticks() * 0.005 * s[2]))
            pygame.draw.circle(self.screen, (brillo, brillo, brillo), (int(s[0]), int(s[1])), 1)

        # 2. Rejilla con degradado (Efecto profundidad)
        for x in range(0, 900, 50):
            color = (20, 40, 60) if x % 100 == 0 else (15, 25, 35)
            pygame.draw.line(self.screen, color, (x, 0), (x, ALTO))
        for y in range(0, ALTO, 50):
            color = (20, 40, 60) if y % 100 == 0 else (15, 25, 35)
            pygame.draw.line(self.screen, color, (0, y), (900, y))

    def dibujar_objetos(self):
        for obj in list(self.motor.objetos.values()):
            pos = self.world_to_screen(obj.posicion)
            color = COLOR_TERRAN if obj.faccion == "Terran" else COLOR_PIRATA
            
            # 3. Efecto de "Glow" (Brillo radial)
            # Dibujamos un círculo semitransparente más grande detrás
            glow_surf = pygame.Surface((60, 60), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, 40), (30, 30), 15)
            self.screen.blit(glow_surf, (pos[0]-30, pos[1]-30))

            # Icono de la unidad
            radio = 10
            if "Crucero" in obj.__class__.__name__:
                radio = 18
                pygame.draw.polygon(self.screen, color, [
                    (pos[0], pos[1]-radio), (pos[0]+radio, pos[1]+radio), (pos[0]-radio, pos[1]+radio)
                ], 2)
            else:
                pygame.draw.circle(self.screen, color, pos, radio, 2)
            
            # Láseres con efecto de pulso
            target = getattr(obj, 'objetivo_combate', None)
            if target and hasattr(target, 'posicion'):
                t_pos = self.world_to_screen(target.posicion)
                ancho_laser = random.randint(1, 3) # Parpadeo del láser
                pygame.draw.line(self.screen, color, pos, t_pos, ancho_laser)

            # Barra de vida estilizada
            vida_p = max(0, obj.vida_actual / obj.vida_maxima)
            pygame.draw.rect(self.screen, (40, 20, 20), (pos[0]-15, pos[1]+radio+8, 30, 3))
            pygame.draw.rect(self.screen, color, (pos[0]-15, pos[1]+radio+8, int(30 * vida_p), 3))

    def dibujar_hud(self):
        # Fondo del HUD con transparencia simulada
        hud_rect = pygame.Rect(900, 0, 200, ALTO)
        pygame.draw.rect(self.screen, COLOR_HUD_BG, hud_rect)
        pygame.draw.line(self.screen, COLOR_TERRAN, (900, 0), (900, ALTO), 1)

        # 4. Efecto de cabecera de datos
        res = self.motor.facciones['Terran'].recursos
        self.screen.blit(self.fuente_tit.render("STATUS: OPERATIONAL", True, COLOR_TERRAN), (915, 20))
        
        # Barras de recursos visuales
        for i, (label, val, max_v, col) in enumerate([
            ("MIN", res['mineral'], 2000, (255, 200, 0)),
            ("ENE", res['energia'], 500, (0, 180, 255))
        ]):
            y_off = 60 + i*45
            self.screen.blit(self.fuente.render(label, True, (200, 200, 200)), (915, y_off))
            pygame.draw.rect(self.screen, (30, 30, 40), (915, y_off + 18, 170, 6))
            pygame.draw.rect(self.screen, col, (915, y_off + 18, int(170 * (val/max_v)), 6))

        # Registro de Logs con "Scroll"
        self.screen.blit(self.fuente_tit.render("COMMS LOG", True, COLOR_TERRAN), (915, 170))
        for i, m in enumerate(self.logs[-15:]):
            alpha = int(255 * (i / 15)) # Los logs viejos se desvanecen
            txt = self.fuente.render(f"> {m}", True, (alpha, alpha, alpha))
            self.screen.blit(txt, (910, 200 + i*22))

    def post_procesado(self):
        # 5. Efecto de Scanlines (Líneas de TV antigua)
        for y in range(0, ALTO, 4):
            linea = pygame.Surface((900, 1), pygame.SRCALPHA)
            linea.fill((0, 0, 0, 40))
            self.screen.blit(linea, (0, y))
        
        # 6. Línea de barrido de radar móvil
        self.escaneo_y = (self.escaneo_y + 2) % ALTO
        barrido = pygame.Surface((900, 2), pygame.SRCALPHA)
        barrido.fill((0, 255, 180, 20))
        self.screen.blit(barrido, (0, self.escaneo_y))

    def ejecutar(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        procesar_comando(self.motor, self.input_text)
                        self.logs.append(self.input_text.upper())
                        self.input_text = ""
                    elif event.key == pygame.K_BACKSPACE:
                        self.input_text = self.input_text[:-1]
                    else:
                        if len(self.input_text) < 18:
                            self.input_text += event.unicode

            self.motor.tick_simulacion(dt)
            self.dibujar_entorno()
            self.dibujar_objetos()
            self.dibujar_hud()
            self.post_procesado() # Aplicar efectos finales
            
            # Input de comando centrado en su caja
            pygame.draw.rect(self.screen, (5, 5, 10), (905, ALTO-45, 190, 30))
            pygame.draw.rect(self.screen, COLOR_TERRAN, (905, ALTO-45, 190, 30), 1)
            surf = self.fuente.render(self.input_text + "_", True, COLOR_TERRAN)
            self.screen.blit(surf, (912, ALTO-36))
            
            pygame.display.flip()

if __name__ == "__main__":
    motor = MotorJuego()
    motor.iniciar_juego()
    app = InterfazGrafica(motor)
    app.ejecutar()