import paho.mqtt.client as mqtt
import logging
import uuid

# Configuración de logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger('mqtt_client')

class ManejadorMQTT:
    def __init__(self, broker, puerto, manejadores=None):
        """
        Cliente MQTT simplificado que delega el manejo de mensajes
        
        :param broker: Dirección del broker MQTT
        :param puerto: Puerto del broker MQTT
        :param manejadores: Diccionario de manejadores de mensajes {topico: funcion_handler}
        """
        self.broker = broker
        self.puerto = puerto
        self.conectado = False
        self.manejadores = manejadores or {}
        
        # Generar ID único
        id_cliente = f"bomba_agua_backend_{uuid.uuid4().hex[:8]}"
        
        # Configurar cliente
        self.cliente = mqtt.Client(client_id=id_cliente, clean_session=True)
        self.cliente.on_connect = self.al_conectar
        self.cliente.on_message = self.al_recibir_mensaje
        self.cliente.on_disconnect = self.al_desconectar
        self.cliente.keepalive = 60
        
    def al_conectar(self, cliente, userdata, flags, rc):
        """Callback de conexión al broker"""
        codigos = {
            0: "Conexión exitosa",
            1: "Versión de protocolo incorrecta",
            2: "ID de cliente rechazado",
            3: "Servidor no disponible",
            4: "Usuario/contraseña incorrectos",
            5: "No autorizado"
        }
        
        if rc == 0:
            self.conectado = True
            print(f"✅ Conectado al broker MQTT: {codigos.get(rc, 'Código desconocido')} ({rc})")
            
            # Suscribirse a los tópicos registrados
            topicos = [(topico, 0) for topico in self.manejadores.keys()]
            if topicos:
                cliente.subscribe(topicos)
                print(f"✅ Suscrito a {len(topicos)} tópicos")
        else:
            print(f"❌ Error de conexión MQTT: {codigos.get(rc, 'Error desconocido')} ({rc})")

    def al_desconectar(self, cliente, userdata, rc):
        """Callback de desconexión"""
        self.conectado = False
        if rc != 0:
            print(f"❌ Desconexión inesperada del broker MQTT (código {rc})")
        else:
            print("Desconectado del broker MQTT")

    def al_recibir_mensaje(self, cliente, userdata, mensaje):
        """Delegación del mensaje al manejador correspondiente"""
        topico = mensaje.topic
        try:
            if topico in self.manejadores:
                print(f"📨 Mensaje recibido en tópico: {topico}")
                self.manejadores[topico](cliente, mensaje)
            else:
                print(f"⚠️ Mensaje recibido en tópico sin manejador: {topico}")
        except Exception as e:
            print(f"❌ Error procesando mensaje ({topico}): {e}")

    def registrar_handler(self, topico, funcion):
        """Registra un manejador para un tópico específico"""
        self.manejadores[topico] = funcion
        if self.conectado:
            self.cliente.subscribe(topico)
            print(f"Suscripción añadida a tópico: {topico}")
        
    def conectar(self):
        """Conecta al broker MQTT"""
        print(f"Conectando a broker MQTT: {self.broker}:{self.puerto}")
        try:
            self.cliente.connect(self.broker, self.puerto)
        except Exception as e:
            print(f"❌ Error al conectar con broker MQTT: {e}")
            raise

    def publicar(self, topico, mensaje):
        """Publica un mensaje en un tópico"""
        try:
            self.cliente.publish(topico, mensaje)
            print(f"📤 Mensaje publicado en {topico}")
            return True
        except Exception as e:
            print(f"❌ Error al publicar en {topico}: {e}")
            return False
            
    def iniciar_bucle(self):
        """Inicia el bucle de procesamiento MQTT"""
        print("Iniciando bucle MQTT...")
        try:
            self.cliente.loop_forever()
        except KeyboardInterrupt:
            print("Bucle MQTT detenido por usuario")
        except Exception as e:
            print(f"❌ Error en bucle MQTT: {e}")
        finally:
            if self.conectado:
                self.cliente.disconnect()
