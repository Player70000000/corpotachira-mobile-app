# -*- coding: utf-8 -*-
"""
CLIENTE HTTP AUTENTICADO v8.0
CORPOTACHIRA - Sistema de Autenticación

Cliente HTTP centralizado que maneja automáticamente:
- Headers de autenticación JWT
- Renovación de tokens expirados
- Redirección de login cuando es necesario
- Manejo de errores de autenticación
"""

import requests
import json
from kivymd.app import MDApp
from config import API_BASE_URL


class AuthHTTPClient:
    """
    Cliente HTTP que maneja automáticamente la autenticación JWT
    """

    def __init__(self):
        self.timeout = 10

    def _get_auth_headers(self):
        """
        Obtiene los headers de autenticación con el token actual

        Returns:
            dict: Headers con Authorization Bearer token
        """
        app = MDApp.get_running_app()
        token = getattr(app, 'token_sesion', None)

        headers = {
            'Content-Type': 'application/json'
        }

        if token:
            headers['Authorization'] = f'Bearer {token}'

        return headers

    def _handle_auth_error(self, response):
        """
        Maneja errores de autenticación (401, 403)

        Args:
            response: Respuesta HTTP

        Returns:
            dict: Información del error
        """
        try:
            error_data = response.json()
            code = error_data.get('code', 'UNKNOWN_ERROR')
            message = error_data.get('message', 'Error de autenticación')

            # Si es error de token, redirigir a login
            if code in ['NO_TOKEN', 'INVALID_TOKEN', 'INVALID_TOKEN_FORMAT']:
                print(f"⚠️ Token inválido, redirigir a login: {message}")
                self._redirect_to_login()

            elif code == 'INSUFFICIENT_PERMISSIONS':
                print(f"⚠️ Permisos insuficientes: {message}")

            return {
                'success': False,
                'error': 'auth_error',
                'message': message,
                'code': code,
                'status_code': response.status_code
            }

        except Exception as e:
            return {
                'success': False,
                'error': 'auth_error',
                'message': 'Error de autenticación',
                'status_code': response.status_code
            }

    def _redirect_to_login(self):
        """
        Redirige a la pantalla de login cuando el token es inválido
        """
        try:
            app = MDApp.get_running_app()

            # Limpiar datos de sesión
            app.token_sesion = None
            app.user_data = None
            app.nivel_usuario = None
            app.nombre_usuario = None

            # Navegar a selección de rol
            if hasattr(app.root, 'switch_to_auth'):
                app.root.switch_to_auth()

        except Exception as e:
            print(f"Error redirigiendo a login: {e}")

    def get(self, endpoint, params=None, **kwargs):
        """
        Petición GET autenticada

        Args:
            endpoint (str): Endpoint de la API (ej: '/canales')
            params (dict): Parámetros de consulta
            **kwargs: Argumentos adicionales para requests

        Returns:
            dict: Respuesta del servidor o información del error
        """
        try:
            url = f"{API_BASE_URL}{endpoint}"
            headers = self._get_auth_headers()

            response = requests.get(
                url,
                headers=headers,
                params=params,
                timeout=kwargs.get('timeout', self.timeout),
                **{k: v for k, v in kwargs.items() if k != 'timeout'}
            )

            # Manejar errores de autenticación
            if response.status_code in [401, 403]:
                return self._handle_auth_error(response)

            # Respuesta exitosa
            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }

            # Otros errores HTTP
            return {
                'success': False,
                'error': 'http_error',
                'message': f'Error HTTP {response.status_code}',
                'status_code': response.status_code
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': 'network_error',
                'message': f'Error de conexión: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'unknown_error',
                'message': f'Error inesperado: {str(e)}'
            }

    def post(self, endpoint, data=None, json_data=None, **kwargs):
        """
        Petición POST autenticada

        Args:
            endpoint (str): Endpoint de la API
            data: Datos para enviar (form data)
            json_data: Datos JSON para enviar
            **kwargs: Argumentos adicionales para requests

        Returns:
            dict: Respuesta del servidor o información del error
        """
        try:
            url = f"{API_BASE_URL}{endpoint}"
            headers = self._get_auth_headers()

            response = requests.post(
                url,
                headers=headers,
                data=data,
                json=json_data,
                timeout=kwargs.get('timeout', self.timeout),
                **{k: v for k, v in kwargs.items() if k != 'timeout'}
            )

            # Manejar errores de autenticación
            if response.status_code in [401, 403]:
                return self._handle_auth_error(response)

            # Respuesta exitosa
            if response.status_code in [200, 201]:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }

            # Otros errores HTTP
            try:
                error_data = response.json()
                message = error_data.get('message', f'Error HTTP {response.status_code}')
            except:
                message = f'Error HTTP {response.status_code}'

            return {
                'success': False,
                'error': 'http_error',
                'message': message,
                'status_code': response.status_code
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': 'network_error',
                'message': f'Error de conexión: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'unknown_error',
                'message': f'Error inesperado: {str(e)}'
            }

    def put(self, endpoint, data=None, json_data=None, **kwargs):
        """
        Petición PUT autenticada
        """
        try:
            url = f"{API_BASE_URL}{endpoint}"
            headers = self._get_auth_headers()

            response = requests.put(
                url,
                headers=headers,
                data=data,
                json=json_data,
                timeout=kwargs.get('timeout', self.timeout),
                **{k: v for k, v in kwargs.items() if k != 'timeout'}
            )

            if response.status_code in [401, 403]:
                return self._handle_auth_error(response)

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }

            try:
                error_data = response.json()
                message = error_data.get('message', f'Error HTTP {response.status_code}')
            except:
                message = f'Error HTTP {response.status_code}'

            return {
                'success': False,
                'error': 'http_error',
                'message': message,
                'status_code': response.status_code
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': 'network_error',
                'message': f'Error de conexión: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'unknown_error',
                'message': f'Error inesperado: {str(e)}'
            }

    def delete(self, endpoint, data=None, json_data=None, **kwargs):
        """
        Petición DELETE autenticada

        Args:
            endpoint (str): Endpoint de la API
            data: Datos para enviar (form data)
            json_data: Datos JSON para enviar
            **kwargs: Argumentos adicionales para requests
        """
        try:
            url = f"{API_BASE_URL}{endpoint}"
            headers = self._get_auth_headers()

            response = requests.delete(
                url,
                headers=headers,
                data=data,
                json=json_data,
                timeout=kwargs.get('timeout', self.timeout),
                **{k: v for k, v in kwargs.items() if k not in ['timeout', 'data', 'json_data']}
            )

            if response.status_code in [401, 403]:
                return self._handle_auth_error(response)

            if response.status_code == 200:
                return {
                    'success': True,
                    'data': response.json(),
                    'status_code': response.status_code
                }

            try:
                error_data = response.json()
                message = error_data.get('message', f'Error HTTP {response.status_code}')
            except:
                message = f'Error HTTP {response.status_code}'

            return {
                'success': False,
                'error': 'http_error',
                'message': message,
                'status_code': response.status_code
            }

        except requests.exceptions.RequestException as e:
            return {
                'success': False,
                'error': 'network_error',
                'message': f'Error de conexión: {str(e)}'
            }
        except Exception as e:
            return {
                'success': False,
                'error': 'unknown_error',
                'message': f'Error inesperado: {str(e)}'
            }


# Instancia global del cliente autenticado
auth_client = AuthHTTPClient()


def make_authenticated_request(method, endpoint, **kwargs):
    """
    Función de conveniencia para hacer peticiones autenticadas

    Args:
        method (str): Método HTTP ('GET', 'POST', 'PUT', 'DELETE')
        endpoint (str): Endpoint de la API
        **kwargs: Argumentos para la petición

    Returns:
        dict: Respuesta del servidor
    """
    method = method.upper()

    if method == 'GET':
        return auth_client.get(endpoint, **kwargs)
    elif method == 'POST':
        return auth_client.post(endpoint, **kwargs)
    elif method == 'PUT':
        return auth_client.put(endpoint, **kwargs)
    elif method == 'DELETE':
        return auth_client.delete(endpoint, **kwargs)
    else:
        return {
            'success': False,
            'error': 'invalid_method',
            'message': f'Método HTTP no soportado: {method}'
        }


# Funciones de conveniencia para uso directo
def get(endpoint, **kwargs):
    """Petición GET autenticada"""
    return auth_client.get(endpoint, **kwargs)


def post(endpoint, **kwargs):
    """Petición POST autenticada"""
    return auth_client.post(endpoint, **kwargs)


def put(endpoint, **kwargs):
    """Petición PUT autenticada"""
    return auth_client.put(endpoint, **kwargs)


def delete(endpoint, **kwargs):
    """Petición DELETE autenticada"""
    return auth_client.delete(endpoint, **kwargs)