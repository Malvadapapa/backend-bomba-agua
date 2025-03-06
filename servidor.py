from flask import Flask, jsonify
from flask_cors import CORS  

class ServidorAPI:
    def __init__(self):
        """Servidor API simplificado que delega el manejo de rutas"""
        self.app = Flask(__name__)
        CORS(self.app)  
        self.rutas = {}
        
    def registrar_ruta(self, ruta, metodo, funcion, nombre=None):
        """
        Registra una nueva ruta en la API
        
        :param ruta: Path de la ruta (ej: '/temperatura')
        :param metodo: Método HTTP ('GET', 'POST', etc.)
        :param funcion: Función a ejecutar
        :param nombre: Nombre opcional para la ruta
        """
        endpoint = nombre or f"{metodo.lower()}_{ruta.replace('/', '_')}"
        self.app.add_url_rule(
            ruta, 
            endpoint=endpoint, 
            view_func=funcion, 
            methods=[metodo]
        )
        
    def iniciar(self, host="0.0.0.0", puerto=5000, debug=False):
        """Inicia el servidor API"""
        self.app.run(host=host, port=puerto, debug=debug)