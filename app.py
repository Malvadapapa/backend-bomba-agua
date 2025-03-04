import os
import _thread
from dotenv import load_dotenv
from base_datos import BaseDatos
from servicio_sensor import ServicioSensor
from servicio_bomba import ServicioBomba
from mqtt import ManejadorMQTT
from servidor import ServidorAPI


load_dotenv()


DB_HOST = os.getenv("DB_HOST")
DB_USUARIO = os.getenv("DB_USUARIO")
DB_CONTRASENA = os.getenv("DB_CONTRASENA")
DB_NOMBRE = os.getenv("DB_NOMBRE")

if not all([DB_HOST, DB_USUARIO, DB_CONTRASENA, DB_NOMBRE]):
    raise ValueError("Error: Variables de entorno de base de datos no configuradas")

MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PUERTO = int(os.getenv("MQTT_PUERTO", "1883"))

def crear_conexion_bd():
    return BaseDatos(DB_HOST, DB_USUARIO, DB_CONTRASENA, DB_NOMBRE)

if __name__ == '__main__':
    servicio_sensor = ServicioSensor(crear_conexion_bd)
    servicio_bomba = ServicioBomba(crear_conexion_bd)

    manejador_mqtt = ManejadorMQTT(servicio_sensor, servicio_bomba, MQTT_BROKER, MQTT_PUERTO)
    manejador_mqtt.conectar()

    servidor_api = ServidorAPI(crear_conexion_bd)

    # Iniciar MQTT en un hilo separado
    _thread.start_new_thread(manejador_mqtt.iniciar_bucle, ())

    # Iniciar servidor Flask sin reloader
    servidor_api.iniciar(debug=True)
