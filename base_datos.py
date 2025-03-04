import mysql.connector
from mysql.connector import Error

class BaseDatos:
    def __init__(self, host, usuario, contrasena, nombre_bd):
        self.host = host
        self.usuario = usuario
        self.contrasena = contrasena
        self.nombre_bd = nombre_bd
        try:
            self.conexion = mysql.connector.connect(
                host=self.host,
                user=self.usuario,
                password=self.contrasena,
                database=self.nombre_bd
            )
            self.cursor = self.conexion.cursor(dictionary=True)
        except Error as e:
            print(f"Error al conectar a MySQL: {e}")
            raise

    def ejecutar(self, consulta, valores=None):
        try:
            self.cursor.execute(consulta, valores)
            self.conexion.commit()
        except Error as e:
            print(f"Error al ejecutar la consulta: {e}")
            self.conexion.rollback()
            raise

    def obtener(self, consulta, valores=None):
        try:
            self.cursor.execute(consulta, valores)
            return self.cursor.fetchall()
        except Error as e:
            print(f"Error al obtener datos: {e}")
            raise

    def cerrar(self):
        if hasattr(self, 'cursor') and self.cursor:
            self.cursor.close()
        if hasattr(self, 'conexion') and self.conexion:
            self.conexion.close()
