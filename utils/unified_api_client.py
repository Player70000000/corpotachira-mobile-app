# -*- coding: utf-8 -*-
"""
CLIENTE API UNIFICADO v8.0
CORPOTACHIRA - Sistema de Gestión Integral

Cliente HTTP centralizado que consolida toda la funcionalidad de:
- utils/auth_client.py (autenticación base)
- personal_modules/api_client.py (gestión de personal)
- reportes_modules/api_client.py (sistema de reportes)

Características:
- Autenticación JWT automática
- Manejo centralizado de errores
- Métodos para Personal, Reportes y Chat
- Validaciones de integridad
- Redirección automática de login
"""

import requests
import json
from typing import Dict, List, Optional, Any
from kivymd.app import MDApp
from config import API_BASE_URL


class IntegrityError(Exception):
    """Excepción especial para errores de integridad referencial"""

    def __init__(self, message, cuadrillas_afectadas=None, puede_eliminar=False):
        super().__init__(message)
        self.message = message
        self.cuadrillas_afectadas = cuadrillas_afectadas or []
        self.puede_eliminar = puede_eliminar


class UnifiedAPIClient:
    """
    Cliente API unificado para toda la aplicación CORPOTACHIRA
    Consolida autenticación, personal, reportes y validaciones
    """

    def __init__(self):
        self.base_url = API_BASE_URL
        self.timeout = 10

    # =======================================
    # AUTENTICACIÓN Y HEADERS (BASE)
    # =======================================

    def _get_auth_headers(self):
        """
        Obtiene los headers de autenticación con el token actual

        Returns:
            dict: Headers con Authorization Bearer token
        """
        app = MDApp.get_running_app()
        token = getattr(app, 'token_sesion', None)

        # DEBUG: Agregar logs para diagnosticar problemas de token
        if token:
            print(f"🔐 DEBUG: Token encontrado - {token[:50]}...")
        else:
            print("❌ DEBUG: No se encontró token de sesión")
            # Verificar otros atributos de app para debug
            print(f"🔍 DEBUG: Atributos app disponibles: {[attr for attr in dir(app) if not attr.startswith('_')]}")

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
            response: Objeto response de requests

        Returns:
            dict: Resultado con información del error
        """
        if response.status_code == 401:
            # Token expirado o inválido
            print("🔒 Token expirado, redirigiendo al login...")
            self._redirect_to_login()
            return {
                'success': False,
                'error': 'Sesión expirada. Por favor, inicia sesión nuevamente.',
                'status_code': 401,
                'redirect_to_login': True
            }
        elif response.status_code == 403:
            # Sin permisos suficientes
            return {
                'success': False,
                'error': 'No tienes permisos para realizar esta acción.',
                'status_code': 403,
                'insufficient_permissions': True
            }
        else:
            # Otro error de autenticación
            return {
                'success': False,
                'error': f'Error de autenticación: {response.status_code}',
                'status_code': response.status_code
            }

    def _redirect_to_login(self):
        """
        Redirige a la pantalla de login cuando hay problemas de autenticación
        """
        try:
            app = MDApp.get_running_app()

            # Limpiar datos de sesión
            app.nivel_usuario = None
            app.token_sesion = ''
            app.user_data = {}
            app.nombre_usuario = ''

            # Redirigir a selección de rol
            if hasattr(app, 'root') and hasattr(app.root, 'screen_manager'):
                app.root.screen_manager.current = 'role_selection'
                print("🔄 Redirigido a selección de rol por problemas de autenticación")

        except Exception as e:
            print(f"❌ Error en redirección a login: {e}")

    # =======================================
    # MÉTODOS HTTP BASE (GET, POST, PUT, DELETE)
    # =======================================

    def get(self, endpoint, params=None, **kwargs):
        """
        Realizar petición GET autenticada

        Args:
            endpoint (str): Endpoint de la API (ej: '/api/personnel/obreros/')
            params (dict): Parámetros de consulta URL
            **kwargs: Argumentos adicionales para requests

        Returns:
            dict: Resultado de la petición con keys: success, data/error, status_code
        """
        try:
            # Preparar URL y headers
            url = f"{self.base_url}{endpoint}"
            headers = self._get_auth_headers()

            # DEBUG: Log detalles de la petición
            print(f"🌐 DEBUG GET: URL = {url}")
            print(f"🔑 DEBUG GET: Headers = {headers}")
            print(f"📝 DEBUG GET: Params = {params}")

            # Configurar timeout
            kwargs.setdefault('timeout', self.timeout)

            # Realizar petición
            response = requests.get(url, headers=headers, params=params, **kwargs)

            # DEBUG: Log respuesta
            print(f"📡 DEBUG GET: Status = {response.status_code}")
            print(f"📄 DEBUG GET: Response = {response.text[:200]}...")

            # Manejar errores de autenticación
            if response.status_code in [401, 403]:
                return self._handle_auth_error(response)

            # Procesar respuesta exitosa
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'success': True,
                        'data': data,
                        'status_code': 200
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'data': response.text,
                        'status_code': 200
                    }
            else:
                # Error HTTP - Procesar errores especiales
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', f'Error {response.status_code}')

                    # Verificar si es un error de integridad referencial
                    if error_data.get('tipo_error') == 'integridad_referencial':
                        cuadrillas_afectadas = error_data.get('cuadrillas_afectadas', [])
                        puede_eliminar = error_data.get('puede_eliminar', False)

                        # Lanzar IntegrityError para que los managers lo capturen
                        raise IntegrityError(
                            message=error_message,
                            cuadrillas_afectadas=cuadrillas_afectadas,
                            puede_eliminar=puede_eliminar
                        )

                    # Error general sin integridad referencial
                    error_message = error_data.get('message', error_message)
                except json.JSONDecodeError:
                    error_message = f'Error HTTP {response.status_code}'

                return {
                    'success': False,
                    'error': error_message,
                    'status_code': response.status_code
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Tiempo de espera agotado. Verifica tu conexión.',
                'status_code': 0
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'No se pudo conectar al servidor.',
                'status_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error inesperado: {str(e)}',
                'status_code': 0
            }

    def post(self, endpoint, data=None, json_data=None, **kwargs):
        """
        Realizar petición POST autenticada

        Args:
            endpoint (str): Endpoint de la API
            data (dict): Datos para enviar como form-data
            json_data (dict): Datos para enviar como JSON
            **kwargs: Argumentos adicionales para requests

        Returns:
            dict: Resultado de la petición
        """
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self._get_auth_headers()
            kwargs.setdefault('timeout', self.timeout)

            # Determinar tipo de datos
            if json_data:
                response = requests.post(url, headers=headers, json=json_data, **kwargs)
            else:
                response = requests.post(url, headers=headers, data=data, **kwargs)

            # Manejar errores de autenticación
            if response.status_code in [401, 403]:
                return self._handle_auth_error(response)

            # Procesar respuesta
            if response.status_code in [200, 201]:
                try:
                    data = response.json()
                    return {
                        'success': True,
                        'data': data,
                        'status_code': response.status_code
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'data': response.text,
                        'status_code': response.status_code
                    }
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', f'Error {response.status_code}')
                except:
                    error_message = f'Error HTTP {response.status_code}'

                return {
                    'success': False,
                    'error': error_message,
                    'status_code': response.status_code
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Tiempo de espera agotado.',
                'status_code': 0
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'No se pudo conectar al servidor.',
                'status_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error inesperado: {str(e)}',
                'status_code': 0
            }

    def put(self, endpoint, data=None, json_data=None, **kwargs):
        """
        Realizar petición PUT autenticada

        Args:
            endpoint (str): Endpoint de la API
            data (dict): Datos para enviar como form-data
            json_data (dict): Datos para enviar como JSON
            **kwargs: Argumentos adicionales para requests

        Returns:
            dict: Resultado de la petición
        """
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self._get_auth_headers()
            kwargs.setdefault('timeout', self.timeout)

            # Determinar tipo de datos
            if json_data:
                response = requests.put(url, headers=headers, json=json_data, **kwargs)
            else:
                response = requests.put(url, headers=headers, data=data, **kwargs)

            # Manejar errores de autenticación
            if response.status_code in [401, 403]:
                return self._handle_auth_error(response)

            # Procesar respuesta
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'success': True,
                        'data': data,
                        'status_code': 200
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'data': response.text,
                        'status_code': 200
                    }
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get('message', f'Error {response.status_code}')
                except:
                    error_message = f'Error HTTP {response.status_code}'

                return {
                    'success': False,
                    'error': error_message,
                    'status_code': response.status_code
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Tiempo de espera agotado.',
                'status_code': 0
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'No se pudo conectar al servidor.',
                'status_code': 0
            }
        except Exception as e:
            return {
                'success': False,
                'error': f'Error inesperado: {str(e)}',
                'status_code': 0
            }

    def delete(self, endpoint, data=None, json_data=None, **kwargs):
        """
        Realizar petición DELETE autenticada

        Args:
            endpoint (str): Endpoint de la API
            data (dict): Datos para enviar como form-data
            json_data (dict): Datos para enviar como JSON
            **kwargs: Argumentos adicionales para requests

        Returns:
            dict: Resultado de la petición
        """
        try:
            url = f"{self.base_url}{endpoint}"
            headers = self._get_auth_headers()
            kwargs.setdefault('timeout', self.timeout)

            # DEBUG: Log detalles de la petición DELETE
            print(f"🌐 DEBUG DELETE: URL = {url}")
            print(f"🔑 DEBUG DELETE: Headers = {headers}")
            print(f"📝 DEBUG DELETE: JSON Data = {json_data}")

            # Determinar tipo de datos
            if json_data:
                response = requests.delete(url, headers=headers, json=json_data, **kwargs)
            else:
                response = requests.delete(url, headers=headers, data=data, **kwargs)

            # DEBUG: Log respuesta
            print(f"📡 DEBUG DELETE: Status = {response.status_code}")
            print(f"📄 DEBUG DELETE: Response = {response.text[:200]}...")

            # Manejar errores de autenticación
            if response.status_code in [401, 403]:
                return self._handle_auth_error(response)

            # Procesar respuesta
            if response.status_code == 200:
                try:
                    data = response.json()
                    return {
                        'success': True,
                        'data': data,
                        'status_code': 200
                    }
                except json.JSONDecodeError:
                    return {
                        'success': True,
                        'data': response.text,
                        'status_code': 200
                    }
            else:
                try:
                    error_data = response.json()
                    error_message = error_data.get('error', error_data.get('message', f'Error {response.status_code}'))

                    # Verificar si es un error de integridad referencial
                    if error_data.get('tipo_error') == 'integridad_referencial':
                        cuadrillas_afectadas = error_data.get('cuadrillas_afectadas', [])
                        puede_eliminar = error_data.get('puede_eliminar', False)
                        raise IntegrityError(
                            message=error_message,
                            cuadrillas_afectadas=cuadrillas_afectadas,
                            puede_eliminar=puede_eliminar
                        )

                except json.JSONDecodeError:
                    error_message = f'Error HTTP {response.status_code}'
                except IntegrityError:
                    # Re-raise IntegrityError
                    raise

                return {
                    'success': False,
                    'error': error_message,
                    'status_code': response.status_code
                }

        except requests.exceptions.Timeout:
            return {
                'success': False,
                'error': 'Tiempo de espera agotado.',
                'status_code': 0
            }
        except requests.exceptions.ConnectionError:
            return {
                'success': False,
                'error': 'No se pudo conectar al servidor.',
                'status_code': 0
            }
        except IntegrityError:
            # Re-raise IntegrityError para que llegue al manager
            raise
        except Exception as e:
            return {
                'success': False,
                'error': f'Error inesperado: {str(e)}',
                'status_code': 0
            }


    # =======================================
    # MÉTODOS PARA GESTIÓN DE CUADRILLAS
    # =======================================

    def get_cuadrillas(self):
        """Obtener lista de todas las cuadrillas"""
        return self.get('/api/personnel/cuadrillas/')

    def create_cuadrilla(self, cuadrilla_data):
        """Crear nueva cuadrilla"""
        return self.post('/api/personnel/cuadrillas/', json_data=cuadrilla_data)

    def update_cuadrilla(self, cuadrilla_id, cuadrilla_data):
        """Actualizar cuadrilla existente"""
        # Incluir ID en los datos para el backend
        cuadrilla_data['_id'] = cuadrilla_id
        return self.put(f'/api/personnel/cuadrillas/{cuadrilla_id}', json_data=cuadrilla_data)

    def delete_cuadrilla(self, cuadrilla_id):
        """Eliminar cuadrilla"""
        return self.delete(f'/api/personnel/cuadrillas/{cuadrilla_id}')

    def get_next_cuadrilla_number(self):
        """Obtener el siguiente número de cuadrilla disponible"""
        return self.get('/api/personnel/cuadrillas/next-number/')

    # =======================================
    # MÉTODOS PARA GESTIÓN DE MODERADORES
    # =======================================

    def get_moderadores(self):
        """Obtener lista de todos los moderadores"""
        return self.get('/api/personnel/moderadores/')

    def create_moderador(self, moderador_data):
        """Crear nuevo moderador"""
        return self.post('/api/personnel/moderadores/', json_data=moderador_data)

    def update_moderador(self, moderador_data):
        """Actualizar moderador existente"""
        return self.put('/api/personnel/moderadores/', json_data=moderador_data)

    def delete_moderador(self, moderador_data):
        """Eliminar moderador"""
        return self.delete('/api/personnel/moderadores/', json_data=moderador_data)

    # =======================================
    # MÉTODOS PARA GESTIÓN DE OBREROS
    # =======================================

    def get_obreros(self):
        """Obtener lista de todos los obreros"""
        return self.get('/api/personnel/obreros/')

    def create_obrero(self, obrero_data):
        """Crear nuevo obrero"""
        return self.post('/api/personnel/obreros/', json_data=obrero_data)

    def update_obrero(self, obrero_data):
        """Actualizar obrero existente"""
        return self.put('/api/personnel/obreros/', json_data=obrero_data)

    def delete_obrero(self, obrero_data):
        """Eliminar obrero"""
        return self.delete('/api/personnel/obreros/', json_data=obrero_data)

    def get_obreros_disponibles(self):
        """Obtener obreros disponibles (sin cuadrilla asignada)"""
        return self.get('/api/personnel/obreros/disponibles/')

    def search_obreros_by_cedula(self, cedula_partial):
        """Buscar obreros por cédula parcial"""
        return self.get('/api/personnel/obreros/', params={'cedula': cedula_partial})

    def find_obrero_cuadrilla(self, obrero_id):
        """
        Buscar en qué cuadrilla está asignado un obrero

        Args:
            obrero_id (str): ID del obrero a buscar

        Returns:
            dict: Resultado con información de la cuadrilla o None si no está asignado
        """
        try:
            cuadrillas_result = self.get_cuadrillas()
            if not cuadrillas_result.get('success'):
                return cuadrillas_result

            cuadrillas = cuadrillas_result.get('data', [])
            for cuadrilla in cuadrillas:
                for obrero in cuadrilla.get('obreros', []):
                    if obrero.get('id') == obrero_id:
                        return {
                            'success': True,
                            'cuadrilla': cuadrilla,
                            'found': True
                        }

            return {
                'success': True,
                'cuadrilla': None,
                'found': False
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error buscando cuadrilla del obrero: {str(e)}'
            }

    def find_moderador_cuadrilla(self, moderador_id):
        """
        Buscar en qué cuadrilla está asignado un moderador

        Args:
            moderador_id (str): ID del moderador a buscar

        Returns:
            dict: Resultado con información de la cuadrilla o None si no está asignado
        """
        try:
            cuadrillas_result = self.get_cuadrillas()
            if not cuadrillas_result.get('success'):
                return cuadrillas_result

            cuadrillas = cuadrillas_result.get('data', [])
            for cuadrilla in cuadrillas:
                moderador = cuadrilla.get('moderador', {})
                if moderador.get('id') == moderador_id:
                    return {
                        'success': True,
                        'cuadrilla': cuadrilla,
                        'found': True
                    }

            return {
                'success': True,
                'cuadrilla': None,
                'found': False
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Error buscando cuadrilla del moderador: {str(e)}'
            }

    # =======================================
    # MÉTODOS DE VALIDACIÓN DE DUPLICADOS
    # =======================================

    def check_all_duplicates_optimized(self, cedula, email, telefono, exclude_id=None):
        """
        Verificar todos los duplicados en una sola consulta optimizada

        Args:
            cedula (str): Cédula a verificar
            email (str): Email a verificar
            telefono (str): Teléfono a verificar
            exclude_id (str): ID a excluir de la verificación (para edición)

        Returns:
            tuple: (cedula_exists, cedula_where, email_exists, email_where, telefono_exists, telefono_where)
        """
        try:
            # Preparar parámetros de consulta
            params = {
                'cedula': cedula,
                'email': email,
                'telefono': telefono
            }

            if exclude_id:
                params['exclude_id'] = exclude_id

            # Realizar consulta de duplicados
            response = self.get('/api/personnel/check-duplicates/', params=params)

            # CORREGIDO: Procesar respuesta y devolver tupla como espera el manager
            if response.get('success'):
                data = response.get('data', {})
                duplicados = data.get('duplicados', {})
                detalles = duplicados.get('detalles', {})

                # Extraer información de duplicados
                cedula_exists = duplicados.get('cedula', False)
                cedula_where = f"{detalles.get('cedula', {}).get('tipo', 'desconocido')}: {detalles.get('cedula', {}).get('nombre', 'N/A')}" if cedula_exists else ""

                email_exists = duplicados.get('email', False)
                email_where = f"{detalles.get('email', {}).get('tipo', 'desconocido')}: {detalles.get('email', {}).get('nombre', 'N/A')}" if email_exists else ""

                telefono_exists = duplicados.get('telefono', False)
                telefono_where = f"{detalles.get('telefono', {}).get('tipo', 'desconocido')}: {detalles.get('telefono', {}).get('nombre', 'N/A')}" if telefono_exists else ""

                return cedula_exists, cedula_where, email_exists, email_where, telefono_exists, telefono_where
            else:
                # Error en la consulta
                error_msg = response.get('error', 'Error verificando duplicados')
                print(f"❌ DEBUG check_duplicates: error = {error_msg}")
                # Devolver tupla con error
                return False, error_msg, False, error_msg, False, error_msg

        except Exception as e:
            error_msg = f'Error verificando duplicados: {str(e)}'
            print(f"💥 DEBUG check_duplicates: exception = {error_msg}")
            return False, error_msg, False, error_msg, False, error_msg

    def check_cedula_exists(self, cedula, exclude_id=None):
        """
        Verificar si una cédula ya existe en el sistema

        Args:
            cedula (str): Cédula a verificar
            exclude_id (str): ID a excluir de la verificación

        Returns:
            dict: Resultado de la verificación
        """
        try:
            params = {'cedula': cedula}
            if exclude_id:
                params['exclude_id'] = exclude_id

            return self.get('/api/personnel/check-cedula/', params=params)

        except Exception as e:
            return {
                'success': False,
                'error': f'Error verificando cédula: {str(e)}'
            }

    def check_email_exists(self, email, exclude_id=None):
        """
        Verificar si un email ya existe en el sistema

        Args:
            email (str): Email a verificar
            exclude_id (str): ID a excluir de la verificación

        Returns:
            dict: Resultado de la verificación
        """
        try:
            params = {'email': email}
            if exclude_id:
                params['exclude_id'] = exclude_id

            return self.get('/api/personnel/check-email/', params=params)

        except Exception as e:
            return {
                'success': False,
                'error': f'Error verificando email: {str(e)}'
            }

    def check_telefono_exists(self, telefono, exclude_id=None):
        """
        Verificar si un teléfono ya existe en el sistema

        Args:
            telefono (str): Teléfono a verificar
            exclude_id (str): ID a excluir de la verificación

        Returns:
            dict: Resultado de la verificación
        """
        try:
            params = {'telefono': telefono}
            if exclude_id:
                params['exclude_id'] = exclude_id

            return self.get('/api/personnel/check-telefono/', params=params)

        except Exception as e:
            return {
                'success': False,
                'error': f'Error verificando teléfono: {str(e)}'
            }

    # =======================================
    # MÉTODOS PARA REPORTES DE OBREROS
    # =======================================

    def get_resumen_obreros(self) -> Dict[str, Any]:
        """Obtener resumen estadístico de obreros"""
        return self.get('/api/reports/obreros/resumen')

    def get_obreros_por_talla_ropa(self) -> Dict[str, Any]:
        """Obtener distribución de obreros por talla de ropa"""
        return self.get('/api/reports/obreros/tallas-ropa')

    def get_obreros_por_talla_zapatos(self) -> Dict[str, Any]:
        """Obtener distribución de obreros por talla de zapatos"""
        return self.get('/api/reports/obreros/tallas-zapatos')

    def get_obreros_activos_inactivos(self) -> Dict[str, Any]:
        """Obtener estadísticas de obreros activos vs inactivos"""
        return self.get('/api/reports/obreros/activos-inactivos')

    def get_obreros_recientes(self, dias: int = 30) -> Dict[str, Any]:
        """Obtener obreros registrados recientemente"""
        return self.get('/api/reports/obreros/recientes', params={'dias': dias})

    def exportar_obreros(self) -> Dict[str, Any]:
        """Generar y obtener reporte de todos los obreros en PDF"""
        return self.post('/api/reports/obreros/generar')

    # =======================================
    # MÉTODOS PARA REPORTES DE MODERADORES
    # =======================================

    def get_resumen_moderadores(self) -> Dict[str, Any]:
        """Obtener resumen estadístico de moderadores"""
        return self.get('/api/reports/moderadores/resumen')

    def get_moderadores_por_talla_ropa(self) -> Dict[str, Any]:
        """Obtener distribución de moderadores por talla de ropa"""
        return self.get('/api/reports/moderadores/tallas-ropa')

    def get_moderadores_por_talla_zapatos(self) -> Dict[str, Any]:
        """Obtener distribución de moderadores por talla de zapatos"""
        return self.get('/api/reports/moderadores/tallas-zapatos')

    def get_moderadores_activos_inactivos(self) -> Dict[str, Any]:
        """Obtener estadísticas de moderadores activos vs inactivos"""
        return self.get('/api/reports/moderadores/activos-inactivos')

    def get_moderadores_recientes(self, dias: int = 30) -> Dict[str, Any]:
        """Obtener moderadores registrados recientemente"""
        return self.get('/api/reports/moderadores/recientes', params={'dias': dias})

    def exportar_moderadores(self) -> Dict[str, Any]:
        """Generar y obtener reporte de todos los moderadores en PDF"""
        return self.post('/api/reports/moderadores/generar')

    # =======================================
    # MÉTODOS PARA REPORTES GENERALES
    # =======================================

    def get_resumen_general(self) -> Dict[str, Any]:
        """Obtener resumen general del sistema"""
        return self.get('/api/reports/generales/resumen')

    def get_resumen_personal(self) -> Dict[str, Any]:
        """Obtener resumen del personal (moderadores + obreros)"""
        return self.get('/api/reports/generales/personal')

    def get_actividad_chat(self) -> Dict[str, Any]:
        """Obtener estadísticas de actividad del chat"""
        return self.get('/api/reports/generales/chat')

    def get_cuadrillas_por_actividad(self) -> Dict[str, Any]:
        """Obtener distribución de cuadrillas por actividad"""
        return self.get('/api/reports/generales/cuadrillas-actividad')

    def get_estadisticas_globales(self) -> Dict[str, Any]:
        """Obtener estadísticas globales del sistema"""
        return self.get('/api/reports/generales/estadisticas')

    def exportar_cuadrillas(self) -> Dict[str, Any]:
        """Generar y obtener reporte de cuadrillas en PDF"""
        return self.post('/api/reports/generales/generar')

    def exportar_canales(self) -> Dict[str, Any]:
        """Generar y obtener reporte de canales de chat en PDF"""
        return self.get('/api/reports/generales/canales')

    # =======================================
    # MÉTODOS DE UTILIDADES Y SISTEMA
    # =======================================

    def verificar_conexion(self) -> Dict[str, Any]:
        """Verificar conectividad con el servidor"""
        return self.get('/verificar')

    def get_status_sistema(self) -> Dict[str, Any]:
        """Obtener estado general del sistema"""
        return self.get('/api/auth/status')

    # =======================================
    # MÉTODOS PARA MANEJO DE REPORTES EXISTENTES
    # =======================================

    def get_reportes_generales_list(self) -> Dict[str, Any]:
        """Obtener lista de reportes generales generados"""
        return self.get('/api/reports/generales/listar')

    def delete_reporte_general(self, reporte_id: str) -> Dict[str, Any]:
        """Eliminar reporte general específico"""
        return self.delete(f'/api/reports/generales/{reporte_id}')

    def get_reportes_obreros_list(self) -> Dict[str, Any]:
        """Obtener lista de reportes de obreros generados"""
        return self.get('/api/reports/obreros/listar')

    def delete_reporte_obrero(self, reporte_id: str) -> Dict[str, Any]:
        """Eliminar reporte de obrero específico"""
        return self.delete(f'/api/reports/obreros/{reporte_id}')

    def get_reportes_moderadores_list(self) -> Dict[str, Any]:
        """Obtener lista de reportes de moderadores generados"""
        return self.get('/api/reports/moderadores/listar')

    def delete_reporte_moderador(self, reporte_id: str) -> Dict[str, Any]:
        """Eliminar reporte de moderador específico"""
        return self.delete(f'/api/reports/moderadores/{reporte_id}')


# =======================================
# INSTANCIA GLOBAL PARA COMPATIBILIDAD
# =======================================

# Crear instancia global para uso directo
unified_client = UnifiedAPIClient()