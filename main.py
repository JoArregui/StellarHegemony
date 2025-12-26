import pygame
import sys
import random
import math

try:
    from main import MotorJuego, Enemigo, CazaLigero, CruceroBatalla, procesar_comando
except ImportError:
    print("Error: El archivo debe estar en la raíz del proyecto junto a main.py")
    sys.exit()

# Configuración Visual
NEGRO = (10, 10, 15)
BLANCO = (230, 230, 230)
VERDE = (0, 255, 120)
ROJO = (255, 60, 60)
AZUL = (0, 180, 255)
AMARILLO = (255, 255, 0)
GRIS_PANEL = (25, 25, 35)

ANCHO, ALTO = 1100, 700

class InterfazGrafica:
    def __init__(self, motor):
        pygame.init()
        self.screen = pygame.display.set_mode((ANCHO, ALTO))
        pygame.display.set_caption("STELLAR HEGEMONY - Tactical Control")
        self.clock = pygame.time.Clock()
        self.motor = motor
        self.fuente = pygame.font.SysFont("Consolas", 14)
        self.fuente_hud = pygame.font.SysFont("Consolas", 18, bold=True)
        
        # Estado de la Interfaz
        self.input_text = ""
        self.log_mensajes = ["Ratón activado...", "Clic Izq: Seleccionar", "Clic Der: Acción"]
        self.seleccionado = None # Objeto actualmente seleccionado

    def world_to_screen(self, pos):
        return (int(pos[0] + 450), int(pos[1] + 350))

    def screen_to_world(self, pos):
        return (pos[0] - 450, pos[1] - 350)

    def dibujar_objetos(self):
        for obj in list(self.motor.objetos.values()):
            pos = self.world_to_screen(obj.posicion)
            color = VERDE if obj.faccion == "Terran" else ROJO
            radio = 25 if isinstance(obj, CruceroBatalla) else 15
            if "Estacion" in obj.__class__.__name__: radio = 20

            # Si está seleccionado, dibujar un círculo de brillo
            if self.seleccionado and self.seleccionado.id_objeto == obj.id_objeto:
                pygame.draw.circle(self.screen, AMARILLO, pos, radio + 5, 1)

            # Dibujar Unidad
            pygame.draw.circle(self.screen, color, pos, radio, 2)
            
            # Dibujar Láseres (si tiene objetivo)
            target = getattr(obj, 'objetivo_combate', None)
            if target and target.id_objeto in self.motor.objetos:
                t_pos = self.world_to_screen(target.posicion)
                pygame.draw.line(self.screen, color, pos, t_pos, 1)

            # Barra de Vida
            vida_p = max(0, obj.vida_actual / obj.vida_maxima)
            pygame.draw.rect(self.screen, (60, 0, 0), (pos[0]-20, pos[1]+radio+5, 40, 4))
            pygame.draw.rect(self.screen, color, (pos[0]-20, pos[1]+radio+5, int(40 * vida_p), 4))

    def manejar_clic(self, pos_raton, boton):
        world_pos = self.screen_to_world(pos_raton)
        
        # 1. Clic Izquierdo: SELECCIONAR
        if boton == 1:
            self.seleccionado = None
            for obj in self.motor.objetos.values():
                dist = math.sqrt((obj.posicion[0] - world_pos[0])**2 + (obj.posicion[1] - world_pos[1])**2)
                if dist < 25:
                    self.seleccionado = obj
                    self.log_mensajes.append(f"Seleccionado: {obj.__class__.__name__} #{obj.id_objeto}")
                    break

        # 2. Clic Derecho: ACCIÓN (Atacar / Mover)
        elif boton == 3 and self.seleccionado:
            for obj in self.motor.objetos.values():
                dist = math.sqrt((obj.posicion[0] - world_pos[0])**2 + (obj.posicion[1] - world_pos[1])**2)
                if dist < 25 and obj.faccion != self.seleccionado.faccion:
                    # Orden de ataque
                    if hasattr(self.seleccionado, 'objetivo_combate'):
                        self.seleccionado.objetivo_combate = obj
                        self.log_mensajes.append(f"Orden: Atacar #{obj.id_objeto}")
                    return

    def dibujar_hud(self):
        pygame.draw.rect(self.screen, GRIS_PANEL, (900, 0, 200, ALTO))
        pygame.draw.line(self.screen, AZUL, (900, 0), (900, ALTO), 2)

        f = self.motor.facciones['Terran']
        self.screen.blit(self.fuente_hud.render("SISTEMA TÁCTICO", True, AZUL), (915, 20))
        self.screen.blit(self.fuente.render(f"MIN: {int(f.recursos['mineral'])}", True, BLANCO), (915, 50))
        self.screen.blit(self.fuente.render(f"ENE: {int(f.recursos['energia'])}", True, BLANCO), (915, 75))

        # Información del seleccionado
        if self.seleccionado:
            self.screen.blit(self.fuente_hud.render("INFO UNIDAD", True, AMARILLO), (915, 120))
            self.screen.blit(self.fuente.render(f"Tipo: {self.seleccionado.__class__.__name__}", True, BLANCO), (915, 145))
            self.screen.blit(self.fuente.render(f"HP: {int(self.seleccionado.vida_actual)}", True, BLANCO), (915, 165))
        
        # Log
        for i, m in enumerate(self.log_mensajes[-10:]):
            txt = self.fuente.render(f"> {m}", True, (150, 150, 150))
            self.screen.blit(txt, (910, 300 + i*20))

    def ejecutar(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    pygame.quit(); sys.exit()
                
                if event.type == pygame.MOUSEBUTTONDOWN:
                    self.manejar_clic(pygame.mouse.get_pos(), event.button)

                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN:
                        procesar_comando(self.motor, self.input_text)
                        self.input_text = ""
                    elif event.key == pygame.K_BACKSPACE: self.input_text = self.input_text[:-1]
                    else: self.input_text += event.unicode

            self.motor.tick_simulacion(dt)
            self.screen.fill(NEGRO)
            self.dibujar_objetos()
            self.dibujar_hud()
            pygame.display.flip()

if __name__ == "__main__":
    motor = MotorJuego()
    motor.iniciar_juego()
    app = InterfazGrafica(motor)
    app.ejecutar()