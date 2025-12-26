import pygame
import sys
import random
import math
import os

# --- Clases Core ---

class ObjetoEspacial:
    def __init__(self, id, faccion, posicion):
        self.id = id
        self.faccion = faccion
        self.posicion = list(posicion) 
        self.vida_actual = 150.0
        self.vida_maxima = 150.0
        self.objetivo_combate = None
        self.radio_visual = 20 # Aumentado para colisión de selección con sprites
        self.radar_timer = random.uniform(0, 3)

    def recibir_danio(self, danio, motor):
        self.vida_actual -= danio
        if self.vida_actual <= 0:
            if motor:
                motor.crear_explosion(self.posicion[:2], self.faccion)
                if self.faccion == "Pirata":
                    recompensa = 25 if self.vida_maxima < 200 else 75
                    motor.facciones['Terran'].recursos['mineral'] += recompensa
            print(f"Destruido: {self.id} ({self.faccion})")

    def actualizar(self, motor, dt):
        self.radar_timer += dt
        if self.radar_timer > 3: self.radar_timer = 0

class EconomiaFaccion:
    def __init__(self, nombre):
        self.recursos = {'mineral': 400, 'energia': 100}

# --- Sistema de Efectos ---

class Particula:
    def __init__(self, pos, color):
        self.pos = list(pos)
        angle = random.uniform(0, math.pi * 2)
        speed = random.uniform(40, 150)
        self.vx = math.cos(angle) * speed
        self.vy = math.sin(angle) * speed
        self.vida = 0.8
        self.color = color

    def update(self, dt):
        self.pos[0] += self.vx * dt
        self.pos[1] += self.vy * dt
        self.vida -= dt

# --- Entidades ---

class EstacionComando(ObjetoEspacial):
    def __init__(self, id_obj, pos):
        super().__init__(id_obj, "Terran", pos)
        self.vida_maxima = 1000.0
        self.vida_actual = 1000.0
        self.danio = 35
        self.rango = 260
        self.timer_reparacion_visual = 0

    def reparar(self, motor):
        if motor.facciones['Terran'].recursos['energia'] >= 50:
            motor.facciones['Terran'].recursos['energia'] -= 50
            self.timer_reparacion_visual = 0.4
            for obj in motor.objetos.values():
                if obj.faccion == "Terran" and math.dist(self.posicion[:2], obj.posicion[:2]) < self.rango:
                    obj.vida_actual = min(obj.vida_maxima, obj.vida_actual + 100)

    def actualizar(self, motor, dt):
        super().actualizar(motor, dt)
        if self.timer_reparacion_visual > 0: self.timer_reparacion_visual -= dt
        self.objetivo_combate = None
        for obj in motor.objetos.values():
            if obj.faccion == "Pirata" and math.dist(self.posicion[:2], obj.posicion[:2]) < self.rango:
                self.objetivo_combate = obj
                obj.recibir_danio(self.danio * dt, motor)
                break

class EstacionMinera(ObjetoEspacial):
    def __init__(self, id_obj, pos):
        super().__init__(id_obj, "Terran", pos)
        self.produccion = 12.0
        self.vida_maxima = 300.0
        self.vida_actual = 300.0

class UnidadDefensa(ObjetoEspacial):
    def __init__(self, id_obj, pos):
        super().__init__(id_obj, "Terran", pos)
        self.danio = 65
        self.rango = 220
        self.velocidad = 125
        self.objetivo_movimiento = None

    def actualizar(self, motor, dt):
        super().actualizar(motor, dt)
        if self.objetivo_movimiento:
            dist = math.dist(self.posicion[:2], self.objetivo_movimiento)
            if dist > 5:
                dx = (self.objetivo_movimiento[0] - self.posicion[0]) / dist
                dy = (self.objetivo_movimiento[1] - self.posicion[1]) / dist
                self.posicion[0] += dx * self.velocidad * dt
                self.posicion[1] += dy * self.velocidad * dt
            else: self.objetivo_movimiento = None

        self.objetivo_combate = None
        for obj in motor.objetos.values():
            if obj.faccion == "Pirata" and math.dist(self.posicion[:2], obj.posicion[:2]) < self.rango:
                self.objetivo_combate = obj
                obj.recibir_danio(self.danio * dt, motor)
                break

class Enemigo(ObjetoEspacial):
    def __init__(self, id_obj, pos, dificultad_base):
        super().__init__(id_obj, "Pirata", pos)
        tipo = random.random()
        if tipo < 0.70:
            self.tipo_nombre = "Caza"
            self.vida_maxima = 80.0 + dificultad_base
            self.danio = 25
            self.velocidad = 80
        elif tipo < 0.90:
            self.tipo_nombre = "Elite"
            self.vida_maxima = 150.0 + dificultad_base
            self.danio = 40
            self.velocidad = 110
        else:
            self.tipo_nombre = "Acorazado"
            self.vida_maxima = 450.0 + (dificultad_base * 2)
            self.danio = 65
            self.velocidad = 40
        self.vida_actual = self.vida_maxima

    def actualizar(self, motor, dt):
        super().actualizar(motor, dt)
        objetivo = None
        dist_min = 3000
        for obj in motor.objetos.values():
            if obj.faccion == "Terran":
                d = math.dist(self.posicion[:2], obj.posicion[:2])
                if d < dist_min:
                    dist_min = d
                    objetivo = obj
        if objetivo:
            if dist_min > 45:
                dx = (objetivo.posicion[0] - self.posicion[0]) / dist_min
                dy = (objetivo.posicion[1] - self.posicion[1]) / dist_min
                self.posicion[0] += dx * self.velocidad * dt
                self.posicion[1] += dy * self.velocidad * dt
            else:
                objetivo.recibir_danio(self.danio * dt, motor)
                self.objetivo_combate = objetivo

# --- Motor de Juego ---

class MotorJuego:
    def __init__(self):
        self.objetos = {}
        self.particulas = []
        self.facciones = {'Terran': EconomiaFaccion('Terran')}
        self.id_counter = 100
        self.tiempo_total = 0
        self.timer_pirata = 35.0 
        self.base_ref = None

    def crear(self, clase, pos, extra=0):
        self.id_counter += 1
        if clase == Enemigo: obj = clase(self.id_counter, pos, extra)
        else: obj = clase(self.id_counter, pos)
        if isinstance(obj, EstacionComando): self.base_ref = obj
        self.objetos[self.id_counter] = obj
        return obj

    def crear_explosion(self, pos, faccion):
        color = (0, 200, 255) if faccion == "Terran" else (255, 120, 0)
        for _ in range(25):
            self.particulas.append(Particula(pos, color))

    def update(self, dt):
        self.tiempo_total += dt
        self.timer_pirata -= dt
        if self.timer_pirata <= 0:
            dificultad = (self.tiempo_total // 40) * 20
            spawn_pos = [random.choice([-650, 650]), random.randint(-450, 450), 0]
            self.crear(Enemigo, spawn_pos, dificultad)
            self.timer_pirata = max(5.0, random.uniform(8.0, 16.0) - (self.tiempo_total / 60.0))

        for id_obj, obj in list(self.objetos.items()):
            if obj.vida_actual <= 0:
                del self.objetos[id_obj]
                continue
            obj.actualizar(self, dt)

        for p in self.particulas[:]:
            p.update(dt)
            if p.vida <= 0: self.particulas.remove(p)

        res = self.facciones['Terran'].recursos
        res['mineral'] += (5.0 + sum(getattr(o, 'produccion', 0) for o in self.objetos.values())) * dt
        res['energia'] = min(250, res['energia'] + 8 * dt)

# --- Interfaz con PNGs ---

class JuegoVisual:
    def __init__(self):
        pygame.init()
        self.screen = pygame.display.set_mode((1100, 700))
        pygame.display.set_caption("STELLAR HEGEMONY - SPRITE EDITION")
        self.clock = pygame.time.Clock()
        self.motor = MotorJuego()
        self.motor.crear(EstacionComando, [0, 0, 0])
        self.fuente = pygame.font.SysFont("Consolas", 14)
        self.seleccionado = None
        
        # --- CARGA DE ASSETS ---
        self.sprites = {}
        self.cargar_assets()

    def cargar_assets(self):
        # Fondo
        ruta_fondo = r"C:\Users\josearregui\Desktop\Josetxo\StellarHegemony\Stellar.jpg"
        if os.path.exists(ruta_fondo):
            img = pygame.image.load(ruta_fondo).convert()
            self.fondo_img = pygame.transform.scale(img, (900, 700))
            filtro = pygame.Surface((900, 700)); filtro.set_alpha(150); filtro.fill((0,0,0))
            self.fondo_img.blit(filtro, (0,0))
        else: self.fondo_img = None

        # Función auxiliar para cargar/crear fallback
        def cargar_sprite(nombre, size, color_fallback):
            try:
                img = pygame.image.load(nombre).convert_alpha()
                return pygame.transform.scale(img, size)
            except:
                # Si no encuentra el PNG, crea un recuadro de color para que no de error
                surf = pygame.Surface(size, pygame.SRCALPHA)
                pygame.draw.rect(surf, color_fallback, (0, 0, size[0], size[1]), 2)
                return surf

        self.sprites['base'] = cargar_sprite("base.png", (80, 80), (0, 255, 180))
        self.sprites['extractor'] = cargar_sprite("extractor.png", (40, 40), (200, 200, 0))
        self.sprites['caza'] = cargar_sprite("caza.png", (30, 30), (0, 200, 255))
        self.sprites['pirata_Caza'] = cargar_sprite("enemigo_caza.png", (25, 25), (255, 50, 50))
        self.sprites['pirata_Elite'] = cargar_sprite("enemigo_elite.png", (35, 35), (255, 50, 50))
        self.sprites['pirata_Acorazado'] = cargar_sprite("enemigo_acorazado.png", (60, 60), (255, 50, 50))

    def ejecutar(self):
        while True:
            dt = self.clock.tick(60) / 1000.0
            mx, my = pygame.mouse.get_pos()
            wx, wy = mx - 450, my - 350
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT: pygame.quit(); sys.exit()
                if event.type == pygame.MOUSEBUTTONDOWN:
                    if event.button == 1:
                        if mx > 900: # HUD
                            res = self.motor.facciones['Terran'].recursos
                            if 110 <= my <= 145 and res['mineral'] >= 100:
                                res['mineral'] -= 100
                                self.motor.crear(UnidadDefensa, [random.randint(-100,100), random.randint(-100,100), 0])
                            elif 155 <= my <= 190 and res['mineral'] >= 150:
                                res['mineral'] -= 150
                                self.motor.crear(EstacionMinera, [random.randint(-200, 200), random.randint(-200, 200), 0])
                            elif 200 <= my <= 235:
                                if self.motor.base_ref: self.motor.base_ref.reparar(self.motor)
                        else: # Selección
                            self.seleccionado = None
                            for obj in self.motor.objetos.values():
                                if math.dist([wx, wy], obj.posicion[:2]) < 30:
                                    self.seleccionado = obj; break
                    if event.button == 3 and self.seleccionado:
                        if mx < 900: self.seleccionado.objetivo_movimiento = [wx, wy]

            self.motor.update(dt)
            
            # --- DIBUJO ---
            if self.fondo_img: self.screen.blit(self.fondo_img, (0,0))
            else: self.screen.fill((5, 5, 15))

            for p in self.motor.particulas:
                pygame.draw.circle(self.screen, p.color, (int(p.pos[0]+450), int(p.pos[1]+350)), 2)

            for obj in self.motor.objetos.values():
                px, py = int(obj.posicion[0] + 450), int(obj.posicion[1] + 350)
                
                # Seleccionar Sprite
                img = None
                if isinstance(obj, EstacionComando): img = self.sprites['base']
                elif isinstance(obj, EstacionMinera): img = self.sprites['extractor']
                elif isinstance(obj, UnidadDefensa): img = self.sprites['caza']
                elif isinstance(obj, Enemigo): img = self.sprites.get(f"pirata_{obj.tipo_nombre}")

                if img:
                    rect = img.get_rect(center=(px, py))
                    self.screen.blit(img, rect)

                # Barras de vida sobre el sprite
                ratio = max(0, obj.vida_actual / obj.vida_maxima)
                color_hp = (0, 255, 100) if obj.faccion == "Terran" else (255, 50, 50)
                pygame.draw.rect(self.screen, (40, 40, 40), (px-20, py-rect.height//2-10, 40, 4))
                pygame.draw.rect(self.screen, color_hp, (px-20, py-rect.height//2-10, int(40 * ratio), 4))

                if self.seleccionado == obj:
                    pygame.draw.circle(self.screen, (255, 255, 255), (px, py), rect.width//2 + 5, 1)

            # HUD
            pygame.draw.rect(self.screen, (10, 10, 20), (900, 0, 200, 700))
            res = self.motor.facciones['Terran'].recursos
            self.screen.blit(self.fuente.render(f"CREDITOS: {int(res['mineral'])}", True, (255, 215, 0)), (915, 30))
            self.screen.blit(self.fuente.render(f"ENERGIA: {int(res['energia'])}", True, (0, 150, 255)), (915, 55))
            
            # Botones
            for txt, y in [("CAZA", 110), ("EXTRACTOR", 155), ("REPARAR", 200)]:
                pygame.draw.rect(self.screen, (50, 50, 70), (910, y, 175, 35), border_radius=5)
                self.screen.blit(self.fuente.render(txt, True, (255,255,255)), (920, y+10))
            
            pygame.display.flip()

if __name__ == "__main__":
    JuegoVisual().ejecutar()