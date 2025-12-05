class ObjetoEspacial:
    def __init__(self, id, faccion, posicion):
        self.id = id
        self.faccion = faccion
        self.posicion = posicion 
        self.vida_actual = 100
        self.vida_maxima = 100
        self.armadura = 0
        self.es_seleccionable = True
        # ... (otros atributos)

    def recibir_danio(self, danio):
        danio_mitigado = max(0, danio - self.armadura)
        self.vida_actual -= danio_mitigado
        if self.vida_actual <= 0:
            self.destruir()

    def destruir(self):
        # Lógica de limpieza y eliminación
        print(f"Objeto {self.id} destruido.")