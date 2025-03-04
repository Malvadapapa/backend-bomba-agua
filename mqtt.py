import paho.mqtt.client as mqtt

class ManejadorMQTT:
    def __init__(self, servicio_sensor, servicio_bomba, broker, puerto):
        """
        :param servicio_sensor: Instancia de ServicioSensor.
        :param servicio_bomba: Instancia de ServicioBomba.
        :param broker: Dirección del broker MQTT.
        :param puerto: Puerto del broker.
        """
        self.servicio_sensor = servicio_sensor
        self.servicio_bomba = servicio_bomba
        self.broker = broker
        self.puerto = puerto
        self.cliente = mqtt.Client(client_id="bomba_agua_cliente", clean_session=True)
        self.cliente.on_message = self.al_recibir_mensaje
        self.cliente.on_connect = self.al_conectar
        self.cliente.on_subscribe = self.al_suscribir

        # Variables para almacenar temporalmente datos de sensor.
        self.temperatura = None
        self.humedad = None

    def al_conectar(self, cliente, userdata, flags, rc):
        print(f"Conectado al broker con código: {rc}")
        if rc == 0:
            print("Conexión exitosa")
        else:
            print(f"Error de conexión, código: {rc}")

    def al_suscribir(self, cliente, userdata, mid, granted_qos):
        print(f"Suscripción confirmada. MID: {mid}, QoS: {granted_qos}")

    def conectar(self):
        print(f"Intentando conectar a {self.broker}:{self.puerto}")
        self.cliente.connect(self.broker, self.puerto)
        temas = [
            ("bomba_agua_mqtt/temperatura", 1),  # Cambiado a QoS 1
            ("bomba_agua_mqtt/humedad", 1),      # Cambiado a QoS 1
            ("bomba_agua_mqtt/tiempo_motor", 1)  # Cambiado a QoS 1
        ]
        self.cliente.subscribe(temas)

    def al_recibir_mensaje(self, cliente, userdata, mensaje):
        tema = mensaje.topic
        valor = mensaje.payload.decode()
        print(f"Mensaje recibido - Tema: {tema}, Valor: {valor}")  # Debug

        if tema == "bomba_agua_mqtt/temperatura":
            try:
                self.temperatura = float(valor)
                print(f"Temperatura guardada: {self.temperatura}")  # Debug
                if self.humedad is not None:
                    self.servicio_sensor.registrar_lectura(self.temperatura, self.humedad)
                    self.temperatura = None
                    self.humedad = None
            except ValueError as e:
                print(f"Error al procesar temperatura: {e}")
                return

        elif tema == "bomba_agua_mqtt/humedad":
            try:
                self.humedad = float(valor)
                print(f"Humedad guardada: {self.humedad}")  # Debug
                if self.temperatura is not None:
                    self.servicio_sensor.registrar_lectura(self.temperatura, self.humedad)
                    self.temperatura = None
                    self.humedad = None
            except ValueError as e:
                print(f"Error al procesar humedad: {e}")
                return

        elif tema == "bomba_agua_mqtt/tiempo_motor":
            try:
                tiempo_total = float(valor)
                print(f"Tiempo motor recibido: {tiempo_total}")  # Debug
                
                # Registrar la activación en la base de datos
                self.servicio_bomba.registrar_activacion(tiempo_total)

                # Publicar los litros consumidos
                litros = tiempo_total * 15
                cliente.publish("bomba_agua_mqtt/litros_consumidos", str(litros))
            except ValueError as e:
                print(f"Error al procesar tiempo motor: {e}")
                return

    def iniciar_bucle(self):
        self.cliente.loop_forever()
