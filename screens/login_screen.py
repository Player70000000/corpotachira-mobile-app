# -*- coding: utf-8 -*-
"""
PANTALLA DE LOGIN ADMIN/MODERADOR v8.0
CORPOTACHIRA - Sistema de Autenticación

Pantalla de login unificada para Administradores y Moderadores:
- Admin: usuario "admin" + contraseña
- Moderador: usuario generado automáticamente + contraseña

Características:
- Validación en tiempo real
- Control de intentos fallidos
- Spinner de carga durante autenticación
- Mensajes de error específicos
- Navegación de retorno
"""

import json
import requests
from threading import Thread
from kivy.clock import Clock
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.snackbar import MDSnackbar


class LoginScreen(MDScreen):
    """
    Pantalla de login para Admin y Moderadores
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'login'
        self.tipo_usuario = 'admin'  # Por defecto admin
        self.intentos_fallidos = 0
        self.max_intentos = 5
        self.build_ui()

    def build_ui(self):
        """
        Construye la interfaz de usuario sin tarjeta
        """
        # Contenedor principal con fondo
        main_container = MDBoxLayout(
            orientation='vertical',
            md_bg_color=(0.95, 0.95, 0.95, 1),  # Fondo gris claro
            padding=[dp(30), dp(40), dp(30), dp(40)],
            spacing=dp(20)
        )

        # Header con botón de retroceso
        header_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            spacing=dp(10)
        )

        # Botón de retroceso
        back_button = MDIconButton(
            icon="arrow-left",
            theme_icon_color="Primary",
            on_release=self.ir_atras
        )

        # Título del header
        header_title = MDLabel(
            text="Iniciar Sesión",
            font_style="H5",
            theme_text_color="Primary",
            halign="left",
            valign="center"
        )

        header_layout.add_widget(back_button)
        header_layout.add_widget(header_title)

        # Título principal
        title_label = MDLabel(
            text="CORPOTACHIRA",
            font_style="H4",
            size_hint_y=None,
            height=dp(60),
            halign="center",
            theme_text_color="Primary",
            bold=True
        )

        # Subtítulo dinámico
        self.subtitle_label = MDLabel(
            text="Ingresa tu usuario y contraseña",
            font_style="Subtitle1",
            size_hint_y=None,
            height=dp(40),
            halign="center",
            theme_text_color="Secondary"
        )

        # Formulario
        form_layout = MDBoxLayout(
            orientation='vertical',
            spacing=dp(20),
            size_hint_y=None,
            height=dp(160)
        )

        # Campo Usuario
        self.username_field = MDTextField(
            hint_text="Usuario",
            helper_text="",
            helper_text_mode="on_error",
            size_hint_y=None,
            height=dp(60),
            multiline=False,
            on_text_validate=self.focus_password,
            on_text=self.validar_usuario_tiempo_real
        )

        # FORZAR binding adicional para asegurar que funcione
        self.username_field.bind(text=self.validar_usuario_tiempo_real)

        # Campo Contraseña
        password_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(5)
        )

        self.password_field = MDTextField(
            hint_text="Contraseña",
            helper_text="",
            helper_text_mode="on_error",
            password=True,
            size_hint_x=0.9,
            multiline=False,
            on_text_validate=self.intentar_login,
            on_text=self.validar_contraseña_tiempo_real
        )

        # FORZAR binding adicional para asegurar que funcione
        self.password_field.bind(text=self.validar_contraseña_tiempo_real)

        # Botón para mostrar/ocultar contraseña
        self.show_password_button = MDIconButton(
            icon="eye-off",
            theme_icon_color="Primary",
            size_hint_x=0.1,
            on_release=self.toggle_password_visibility
        )

        password_layout.add_widget(self.password_field)
        password_layout.add_widget(self.show_password_button)

        form_layout.add_widget(self.username_field)
        form_layout.add_widget(password_layout)

        # Botón de login
        self.login_button = MDRaisedButton(
            text="INGRESAR",
            size_hint_y=None,
            height=dp(50),
            md_bg_color=(0.12, 0.29, 0.49, 1),  # Azul corporativo
            elevation=8,
            disabled=True,  # Inicialmente deshabilitado
            on_release=self.intentar_login
        )

        # Spinner de carga (inicialmente oculto)
        self.spinner = MDSpinner(
            size_hint=(None, None),
            size=(dp(40), dp(40)),
            pos_hint={'center_x': 0.5},
            active=False
        )

        # Información adicional
        self.info_label = MDLabel(
            text="",
            font_style="Caption",
            size_hint_y=None,
            height=dp(30),
            halign="center",
            theme_text_color="Hint"
        )

        # Agregar widgets directamente al contenedor principal
        main_container.add_widget(header_layout)
        main_container.add_widget(title_label)
        main_container.add_widget(self.subtitle_label)
        main_container.add_widget(MDLabel())  # Spacer
        main_container.add_widget(form_layout)
        main_container.add_widget(self.login_button)
        main_container.add_widget(self.spinner)
        main_container.add_widget(MDLabel())  # Spacer
        main_container.add_widget(self.info_label)

        # Agregar el contenedor principal a la pantalla
        self.add_widget(main_container)

    def configurar_para_tipo(self, tipo):
        """
        Configura la pantalla para un tipo específico de usuario

        Args:
            tipo (str): 'admin' o 'moderador'
        """
        print(f"🔧 Configurando pantalla para tipo: {tipo}")
        self.tipo_usuario = tipo

        if tipo == 'admin':
            self.subtitle_label.text = "Acceso de Administrador"
            self.username_field.hint_text = "Ingresa 'admin'"
            self.info_label.text = "Usa las credenciales de administrador del sistema"
        elif tipo == 'moderador':
            self.subtitle_label.text = "Acceso de Moderador"
            self.username_field.hint_text = "Ej: D31510033"
            self.info_label.text = "Usuario: Primera letra + cédula | Contraseña: proporcionada"

        # Limpiar campos y resetear estado
        self.username_field.text = ""
        self.password_field.text = ""
        self.username_field.error = False
        self.password_field.error = False
        self.username_field.helper_text = ""
        self.password_field.helper_text = ""
        self.intentos_fallidos = 0

        # Resetear botón explícitamente
        self.login_button.disabled = True
        self.login_button.md_bg_color = (0.7, 0.7, 0.7, 1)  # Gris inicial
        self.spinner.active = False

        print(f"🔧 Pantalla configurada. Botón deshabilitado: {self.login_button.disabled}")

    def validar_usuario_tiempo_real(self, instance, texto):
        """
        Valida el campo usuario en tiempo real
        """
        if len(texto) > 0:
            self.username_field.error = False
            self.username_field.helper_text = "✓ Usuario válido"
        else:
            self.username_field.error = False  # No mostrar error, solo guía
            self.username_field.helper_text = "Ingresa tu usuario"

        self.validar_formulario()

    def validar_contraseña_tiempo_real(self, instance, texto):
        """
        Valida el campo contraseña en tiempo real
        """
        if len(texto) > 0:
            self.password_field.error = False
            self.password_field.helper_text = "✓ Contraseña válida"
        else:
            self.password_field.error = False  # No mostrar error, solo guía
            self.password_field.helper_text = "Ingresa tu contraseña"

        self.validar_formulario()

    def validar_formulario(self):
        """
        Valida el formulario completo y habilita/deshabilita el botón
        """
        # VALIDACIÓN ULTRA PERMISIVA - Cualquier texto habilita el botón
        usuario_texto = self.username_field.text
        contraseña_texto = self.password_field.text

        # CAMBIO RADICAL: Solo verificar que NO estén completamente vacíos
        usuario_valido = len(usuario_texto) > 0
        contraseña_valida = len(contraseña_texto) > 0

        formulario_valido = usuario_valido and contraseña_valida

        # Habilitar/deshabilitar botón según validación
        self.login_button.disabled = not formulario_valido

        # Cambiar color visual para mayor claridad
        if formulario_valido:
            self.login_button.md_bg_color = (0.12, 0.29, 0.49, 1)  # Azul corporativo
        else:
            self.login_button.md_bg_color = (0.7, 0.7, 0.7, 1)  # Gris explícito

    def focus_password(self, instance):
        """
        Enfoca el campo de contraseña cuando se presiona Enter en usuario
        """
        self.password_field.focus = True

    def toggle_password_visibility(self, instance):
        """
        Alterna la visibilidad de la contraseña
        """
        if self.password_field.password:
            self.password_field.password = False
            self.show_password_button.icon = "eye"
        else:
            self.password_field.password = True
            self.show_password_button.icon = "eye-off"

    def intentar_login(self, instance=None):
        """
        Intenta realizar el login
        """
        if self.login_button.disabled:
            return

        username = self.username_field.text.strip()
        password = self.password_field.text.strip()

        if not username or not password:
            self.mostrar_error("Usuario y contraseña son requeridos")
            return

        # Verificar límite de intentos
        if self.intentos_fallidos >= self.max_intentos:
            self.mostrar_error(f"Cuenta bloqueada. Máximo {self.max_intentos} intentos alcanzados")
            return

        # Mostrar spinner
        self.mostrar_cargando(True)

        # Realizar login en hilo separado
        thread = Thread(target=self._realizar_login, args=(username, password))
        thread.daemon = True
        thread.start()

    def _realizar_login(self, username, password):
        """
        Realiza el login en hilo separado

        Args:
            username (str): Nombre de usuario
            password (str): Contraseña
        """
        try:
            app = MDApp.get_running_app()
            base_url = getattr(app, 'base_url', 'https://chat-cv1i.onrender.com')

            # Preparar datos
            data = {
                'username': username,
                'password': password
            }

            # Realizar petición
            response = requests.post(
                f"{base_url}/api/auth/login/admin-moderador",
                json=data,
                headers={'Content-Type': 'application/json'},
                timeout=30
            )

            # Procesar respuesta en hilo principal
            Clock.schedule_once(
                lambda dt: self._procesar_respuesta_login(response),
                0
            )

        except requests.exceptions.Timeout:
            Clock.schedule_once(
                lambda dt: self._manejar_error_login("Tiempo de espera agotado. Verifica tu conexión."),
                0
            )
        except requests.exceptions.ConnectionError:
            Clock.schedule_once(
                lambda dt: self._manejar_error_login("No se pudo conectar al servidor."),
                0
            )
        except Exception as e:
            Clock.schedule_once(
                lambda dt: self._manejar_error_login(f"Error inesperado: {str(e)}"),
                0
            )

    def _procesar_respuesta_login(self, response):
        """
        Procesa la respuesta del login

        Args:
            response: Respuesta HTTP
        """
        try:
            self.mostrar_cargando(False)

            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    self._login_exitoso(result)
                else:
                    self._login_fallido(result.get('message', 'Error desconocido'))
            else:
                try:
                    error_data = response.json()
                    mensaje = error_data.get('message', f'Error {response.status_code}')
                except:
                    mensaje = f'Error del servidor: {response.status_code}'

                self._login_fallido(mensaje)

        except Exception as e:
            self._manejar_error_login(f"Error procesando respuesta: {e}")

    def _login_exitoso(self, result):
        """
        Maneja un login exitoso

        Args:
            result (dict): Datos de respuesta del servidor
        """
        try:
            app = MDApp.get_running_app()

            # Guardar datos de sesión
            user_data = result.get('user_data', {})
            token = result.get('token', '')

            app.nivel_usuario = user_data.get('tipo_usuario', '')
            app.token_sesion = token
            app.user_data = user_data
            app.nombre_usuario = user_data.get('nombre_completo', user_data.get('username', ''))

            print(f"✅ Login exitoso: {app.nombre_usuario} ({app.nivel_usuario})")

            # Mostrar mensaje de éxito
            self.mostrar_exito(f"Bienvenido, {app.nombre_usuario}")

            # Navegar a pantalla principal
            Clock.schedule_once(self._navegar_a_principal, 1.5)

        except Exception as e:
            self._manejar_error_login(f"Error guardando sesión: {e}")

    def _login_fallido(self, mensaje):
        """
        Maneja un login fallido

        Args:
            mensaje (str): Mensaje de error
        """
        self.intentos_fallidos += 1
        intentos_restantes = self.max_intentos - self.intentos_fallidos

        if intentos_restantes > 0:
            mensaje_completo = f"{mensaje}\nIntentos restantes: {intentos_restantes}"
        else:
            mensaje_completo = f"{mensaje}\nCuenta bloqueada. Contacta al administrador."
            self.login_button.disabled = True

        self.mostrar_error(mensaje_completo)

        # Limpiar solo contraseña
        self.password_field.text = ""
        self.password_field.focus = True

    def _manejar_error_login(self, mensaje):
        """
        Maneja errores generales del login

        Args:
            mensaje (str): Mensaje de error
        """
        self.mostrar_cargando(False)
        self.mostrar_error(mensaje)

    def _navegar_a_principal(self, dt):
        """
        Navega a la pantalla principal y configura según el nivel de usuario
        """
        try:
            app = MDApp.get_running_app()
            # CAMBIO v8.0: Usar función que configura las pestañas según el nivel
            app.navegar_a_principal_segun_nivel()
        except Exception as e:
            print(f"❌ Error navegando a principal: {e}")
            self.mostrar_error("Error navegando a pantalla principal")

    def mostrar_cargando(self, mostrar):
        """
        Muestra u oculta el spinner de carga

        Args:
            mostrar (bool): True para mostrar, False para ocultar
        """
        self.spinner.active = mostrar
        button_disabled = mostrar or (self.intentos_fallidos >= self.max_intentos)
        self.login_button.disabled = button_disabled

        # Revalidar formulario después de cambiar estado de carga
        if not mostrar:
            self.validar_formulario()

    def mostrar_error(self, mensaje):
        """
        Muestra un mensaje de error

        Args:
            mensaje (str): Mensaje de error
        """
        try:
            snackbar = MDSnackbar(
                MDLabel(
                    text=mensaje,
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1)
                ),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
                md_bg_color=(0.8, 0.2, 0.2, 1),
                duration=4
            )
            snackbar.open()
        except Exception as e:
            print(f"❌ Error mostrando snackbar de error: {e}")

    def mostrar_exito(self, mensaje):
        """
        Muestra un mensaje de éxito

        Args:
            mensaje (str): Mensaje de éxito
        """
        try:
            snackbar = MDSnackbar(
                MDLabel(
                    text=mensaje,
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1)
                ),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
                md_bg_color=(0.2, 0.7, 0.2, 1),
                duration=2
            )
            snackbar.open()
        except Exception as e:
            print(f"❌ Error mostrando snackbar de éxito: {e}")

    def ir_atras(self, instance):
        """
        Regresa a la pantalla de selección de rol
        """
        try:
            app = MDApp.get_running_app()
            app.root.screen_manager.current = 'role_selection'
        except Exception as e:
            print(f"❌ Error navegando atrás: {e}")

    def on_enter(self):
        """
        Se ejecuta al entrar a la pantalla
        """
        print(f"📱 Entrando a pantalla de login. Tipo: {self.tipo_usuario}")

        # Resetear estado del botón explícitamente
        self.validar_formulario()

        # Enfocar campo de usuario
        Clock.schedule_once(lambda dt: setattr(self.username_field, 'focus', True), 0.1)

    def on_leave(self):
        """
        Se ejecuta al salir de la pantalla
        """
        # Limpiar campos sensibles
        self.password_field.text = ""