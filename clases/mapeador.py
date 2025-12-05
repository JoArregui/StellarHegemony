class MapeadorEspacial:
    """Clase para mapear y localizar objetos por facción y posición."""

    def __init__(self):
        # Almacena todos los objetos en el juego, indexados por su ID.
        self.objetos_por_id = {}
        # Lista simplificada de objetos activos para reportes.
        self.lista_activos = [] 

    def actualizar_mapa(self, objetos_del_juego):
        """
        Recopila los datos esenciales de todos los objetos activos en el MotorJuego.
        Debe ser llamado en cada tick.
        """
        self.objetos_por_id = objetos_del_juego # Referencia directa a la fuente de verdad.
        self.lista_activos = []
        
        for obj_id, obj in objetos_del_juego.items():
            if obj.vida_actual > 0:
                self.lista_activos.append({
                    'id': obj_id,
                    'clase': obj.__class__.__name__,
                    'faccion': obj.faccion,
                    'posicion': obj.posicion,
                    'vida': round(obj.vida_actual, 1),
                })
    
    def listar_objetos_activos(self):
        """Devuelve la lista simplificada de objetos activos."""
        return self.lista_activos
    
    def get_objeto_en_posicion(self, posicion):
        """Busca un objeto activo en una posición dada (exacta)."""
        for obj_data in self.lista_activos:
            if obj_data['posicion'] == posicion:
                return obj_data
        return None