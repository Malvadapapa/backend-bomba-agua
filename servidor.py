from flask import Flask, jsonify

class ServidorAPI:
    def __init__(self, crear_conexion_bd):
        self.crear_conexion_bd = crear_conexion_bd
        self.app = Flask(__name__)
        self.configurar_rutas()

    def configurar_rutas(self):
        @self.app.route('/litros_consumidos', methods=['GET'])
        def litros_consumidos():
            bd = self.crear_conexion_bd()
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

        @self.app.route('/litros_totales', methods=['GET'])
        def litros_totales():
            bd = self.crear_conexion_bd()
            consulta = "SELECT COALESCE(SUM(litros), 0) AS total_litros FROM bomba"
            resultado = bd.obtener(consulta)
            bd.cerrar()
            total_litros = resultado[0]['total_litros'] if resultado else 0
            return jsonify({'litros_totales': total_litros})

        @self.app.route('/activaciones', methods=['GET'])
        def obtener_activaciones():
            bd = self.crear_conexion_bd()
            consulta = "SELECT * FROM bomba ORDER BY fecha_hora DESC LIMIT 10"
            datos = bd.obtener(consulta)
            bd.cerrar()
            return jsonify(datos)

    def iniciar(self, host="0.0.0.0", puerto=5000, debug=True):
        self.app.run(host=host, port=puerto, debug=debug)
