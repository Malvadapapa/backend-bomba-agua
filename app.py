import os
import _thread
from dotenv import load_dotenv
from flask import jsonify
from base_datos import BaseDatos
from servicio_sensor import ServicioSensor
from servicio_bomba import ServicioBomba
from mqtt import ManejadorMQTT
from servidor import ServidorAPI

# Cargar variables de entorno
load_dotenv()

# Configuración de BD
DB_HOST = os.getenv("DB_HOST")
DB_USUARIO = os.getenv("DB_USUARIO")
DB_CONTRASENA = os.getenv("DB_CONTRASENA")
DB_NOMBRE = os.getenv("DB_NOMBRE")

if not all([DB_HOST, DB_USUARIO, DB_CONTRASENA, DB_NOMBRE]):
    raise ValueError("Error: Variables de entorno de base de datos no configuradas")

# Configuración MQTT
MQTT_BROKER = os.getenv("MQTT_BROKER")
MQTT_PUERTO = int(os.getenv("MQTT_PUERTO", "1883"))

# Función para crear conexiones a la BD
def crear_conexion_bd():
    return BaseDatos(DB_HOST, DB_USUARIO, DB_CONTRASENA, DB_NOMBRE)

# Variable global para almacenar lecturas temporales
lecturas_sensor = {}

# Variable para controlar si ya se inició el hilo MQTT
hilo_mqtt_iniciado = False

# Handlers para mensajes MQTT
def manejar_temperatura(cliente, mensaje):
    try:
        valor = float(mensaje.payload.decode())
        print(f"🌡️ Temperatura recibida: {valor}°C")
        lecturas_sensor["temperatura"] = valor
        intentar_registrar_lectura()
    except Exception as e:
        print(f"Error procesando temperatura: {e}")

def manejar_humedad(cliente, mensaje):
    try:
        valor = float(mensaje.payload.decode())
        print(f"💧 Humedad recibida: {valor}%")
        lecturas_sensor["humedad"] = valor
        intentar_registrar_lectura()
    except Exception as e:
        print(f"Error procesando humedad: {e}")

def manejar_tiempo_motor(cliente, mensaje):
    try:
        valor = float(mensaje.payload.decode())
        print(f"⚙️ Tiempo motor recibido: {valor} segundos")
        servicio_bomba.registrar_activacion(valor)
        litros = valor * 15
        cliente_mqtt.publicar("bomba_agua_mqtt/litros_consumidos", str(litros))
    except Exception as e:
        print(f"Error procesando tiempo motor: {e}")

def intentar_registrar_lectura():
    """Intenta registrar si tenemos temperatura y humedad disponibles"""
    temp = lecturas_sensor.get("temperatura")
    hum = lecturas_sensor.get("humedad")
    
    if temp is not None and hum is not None:
        try:
            print(f"💾 Registrando: Temperatura={temp}°C, Humedad={hum}%")
            servicio_sensor.registrar_lectura(temp, hum)
            # Limpiar lecturas después de registrar
            lecturas_sensor.clear()
        except Exception as e:
            print(f"❌ Error al guardar en BD: {e}")

# Endpoints 
def obtener_humedad():
    bd = crear_conexion_bd()
    consulta = "SELECT humedad, fecha_hora FROM sensor ORDER BY fecha_hora DESC LIMIT 20"
    datos = bd.obtener(consulta)
    bd.cerrar()
    return jsonify(datos)

def obtener_temperatura():
    bd = crear_conexion_bd()
    consulta = "SELECT temperatura, fecha_hora FROM sensor ORDER BY fecha_hora DESC LIMIT 20"
    datos = bd.obtener(consulta)
    bd.cerrar()
    return jsonify(datos)

def litros_consumidos():
    bd = crear_conexion_bd()
    consulta = """
        SELECT COALESCE(SUM(tiempo_total), 0) AS total_tiempo 
        FROM bomba 
        WHERE tiempo_total IS NOT NULL
    """
    resultado = bd.obtener(consulta)
    bd.cerrar()
    total_tiempo = resultado[0]['total_tiempo'] if resultado and resultado[0]['total_tiempo'] is not None else 0
    litros_totales = total_tiempo * 15
    return jsonify({'litros_consumidos': litros_totales})

def litros_totales():
    bd = crear_conexion_bd()
    consulta = "SELECT COALESCE(SUM(litros), 0) AS total_litros FROM bomba"
    resultado = bd.obtener(consulta)
    bd.cerrar()
    total_litros = resultado[0]['total_litros'] if resultado else 0
    return jsonify({'litros_totales': total_litros})

def litros_ultimo_dia():
    bd = crear_conexion_bd()
    consulta = """
        SELECT COALESCE(SUM(litros), 0) AS litros_dia 
        FROM bomba 
        WHERE fecha_hora >= DATE_SUB(NOW(), INTERVAL 1 DAY)
    """
    resultado = bd.obtener(consulta)
    bd.cerrar()
    litros_dia = resultado[0]['litros_dia'] if resultado else 0
    return jsonify({'litros_ultimo_dia': litros_dia})

def estado_bomba():
    bd = crear_conexion_bd()
    consulta = """
        SELECT COUNT(*) AS activa 
        FROM bomba 
        WHERE fecha_hora >= DATE_SUB(NOW(), INTERVAL 30 SECOND)
          AND fecha_hora <= NOW()
    """
    resultado = bd.obtener(consulta)
    bd.cerrar()
    activa = resultado[0]['activa'] > 0 if resultado else False
    return jsonify({'bomba_encendida': activa})

def litros_ultimos_7_dias():
    bd = crear_conexion_bd()
    consulta = """
        SELECT 
            DATE(fecha_hora) AS fecha,
            COALESCE(SUM(litros), 0) AS litros_dia
        FROM bomba 
        WHERE fecha_hora >= DATE_SUB(CURRENT_DATE(), INTERVAL 7 DAY)
        GROUP BY DATE(fecha_hora)
        ORDER BY fecha
    """
    datos = bd.obtener(consulta)
    bd.cerrar()
    return jsonify(datos)

def obtener_activaciones():
    bd = crear_conexion_bd()
    consulta = "SELECT * FROM bomba ORDER BY fecha_hora DESC LIMIT 10"
    datos = bd.obtener(consulta)
    bd.cerrar()
    return jsonify(datos)

if __name__ == '__main__':
    print("🚀 Iniciando aplicación...")
    
    # Inicializar servicios
    servicio_sensor = ServicioSensor(crear_conexion_bd)
    servicio_bomba = ServicioBomba(crear_conexion_bd)
    
    # Configurar cliente MQTT
    cliente_mqtt = ManejadorMQTT(MQTT_BROKER, MQTT_PUERTO)
    
    # Registrar handlers para tópicos MQTT
    cliente_mqtt.registrar_handler("bomba_agua_mqtt/temperatura", manejar_temperatura)
    cliente_mqtt.registrar_handler("bomba_agua_mqtt/humedad", manejar_humedad)
    cliente_mqtt.registrar_handler("bomba_agua_mqtt/tiempo_motor", manejar_tiempo_motor)
    
    # Conectar al broker MQTT
    cliente_mqtt.conectar()
    
    # Configurar servidor API
    servidor_api = ServidorAPI()
    
    # Registrar rutas
    servidor_api.registrar_ruta('/humedad', 'GET', obtener_humedad)
    servidor_api.registrar_ruta('/temperatura', 'GET', obtener_temperatura)
    servidor_api.registrar_ruta('/litros_consumidos', 'GET', litros_consumidos)
    servidor_api.registrar_ruta('/litros_totales', 'GET', litros_totales)
    servidor_api.registrar_ruta('/litros_ultimo_dia', 'GET', litros_ultimo_dia)
    servidor_api.registrar_ruta('/estado_bomba', 'GET', estado_bomba)
    servidor_api.registrar_ruta('/litros_ultimos_7_dias', 'GET', litros_ultimos_7_dias)
    servidor_api.registrar_ruta('/activaciones', 'GET', obtener_activaciones)
    
    # Iniciar cliente MQTT en un hilo separado (solo una vez)
    if not hilo_mqtt_iniciado:
        hilo_mqtt_iniciado = True
        _thread.start_new_thread(cliente_mqtt.iniciar_bucle, ())
        print("🧵 Hilo MQTT iniciado")
    
    # Iniciar servidor API (bloquea hasta que se cierre)
    print("🌐 Iniciando servidor API...")
    servidor_api.iniciar(debug=False)
