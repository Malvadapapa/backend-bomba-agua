class ServicioSensor:
    def __init__(self, crear_conexion_bd):
        """
        :param crear_conexion_bd: Función que devuelve una nueva instancia de BaseDatos.
        """
        self.crear_conexion_bd = crear_conexion_bd

    def registrar_lectura(self, temperatura, humedad):
        bd = self.crear_conexion_bd()
        consulta = "INSERT INTO sensor (temperatura, humedad) VALUES (%s, %s)"
        bd.ejecutar(consulta, (temperatura, humedad))
        bd.cerrar()
