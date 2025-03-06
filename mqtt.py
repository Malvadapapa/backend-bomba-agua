import paho.mqtt.client as mqtt
import uuid

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
        
    def al_conectar(self, cliente_mqtt, datos_usuario, banderas_conexion, codigo_resultado):
        """Callback de conexión al broker"""
        codigos = {
            0: "Conexión exitosa",
            1: "Versión de protocolo incorrecta",
            2: "ID de cliente rechazado",
            3: "Servidor no disponible",
            4: "Usuario/contraseña incorrectos",
            5: "No autorizado"
        }
        
        if codigo_resultado == 0:
            self.conectado = True
            print(f"✅ Conectado al broker MQTT: {codigos.get(codigo_resultado, 'Código desconocido')} ({codigo_resultado})")
            
            # Suscribirse a los tópicos registrados
            topicos = [(topico, 0) for topico in self.manejadores.keys()]
            if topicos:
                cliente_mqtt.subscribe(topicos)
                print(f"✅ Suscrito a {len(topicos)} tópicos")
        else:
            print(f"❌ Error de conexión MQTT: {codigos.get(codigo_resultado, 'Error desconocido')} ({codigo_resultado})")

    def al_desconectar(self, cliente_mqtt, datos_usuario, codigo_resultado):
        """Callback de desconexión"""
        self.conectado = False
        if codigo_resultado != 0:
            print(f"❌ Desconexión inesperada del broker MQTT (código {codigo_resultado})")
        else:
            print("Desconectado del broker MQTT")

    def al_recibir_mensaje(self, cliente_mqtt, datos_usuario, mensaje_mqtt):
        """Delegación del mensaje al manejador correspondiente"""
        topico = mensaje_mqtt.topic
        try:
            if topico in self.manejadores:
                print(f"📨 Mensaje recibido en tópico: {topico}")
                self.manejadores[topico](cliente_mqtt, mensaje_mqtt)
            else:
                print(f"⚠️ Mensaje recibido en tópico sin manejador: {topico}")
        except Exception as error:
            print(f"❌ Error procesando mensaje ({topico}): {error}")

    def registrar_handler(self, topico, funcion_manejadora):
        """Registra un manejador para un tópico específico"""
        self.manejadores[topico] = funcion_manejadora
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
