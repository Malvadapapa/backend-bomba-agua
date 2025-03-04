class ServicioBomba:
    def __init__(self, crear_conexion_bd):
        """
        :param crear_conexion_bd: Función que devuelve una nueva instancia de BaseDatos.
        """
        self.crear_conexion_bd = crear_conexion_bd

    def registrar_activacion(self, tiempo_total):
        # Calcula los litros (15 litros por segundo)
        litros = tiempo_total * 15

        bd = self.crear_conexion_bd()
        consulta = """
            INSERT INTO bomba (fecha_hora, tiempo_total, litros)
            VALUES (NOW(), %s, %s)
        """
        bd.ejecutar(consulta, (tiempo_total, litros))
        bd.cerrar()
