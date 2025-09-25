# -*- coding: utf-8 -*-
"""
PANTALLA DE LOGIN OBRERO v8.0
CORPOTACHIRA - Sistema de Autenticación

Pantalla de login específica para obreros:
- Solo requiere cédula (sin contraseña)
- Validación de formato de cédula
- Navegación directa al chat en modo lectura
- Interfaz simplificada y amigable

Características especiales:
- Sin campo de contraseña
- Validación numérica de cédula
- Mensaje informativo sobre no necesitar contraseña
- Acceso directo al chat después de autenticación
"""

import json
import requests
from threading import Thread
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.widget import Widget
from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.textfield import MDTextField
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.spinner import MDSpinner
from kivymd.uix.snackbar import MDSnackbar


class LoginObreroScreen(MDScreen):
    """
    Pantalla de login específica para obreros
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'login_obrero'
        self.build_ui()

    def build_ui(self):
        """
        Construye la interfaz de usuario simplificada
        """
        # Contenedor principal con fondo
        main_container = MDBoxLayout(
            orientation='vertical',
            md_bg_color=(0.95, 0.95, 0.95, 1),  # Fondo gris claro
            spacing=dp(20)
        )

        # Header con botón de retroceso más pegado a la esquina
        header_layout = MDBoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(50),
            padding=[dp(10), dp(10), dp(10), 0]  # Menos padding para acercar a la esquina
        )

        # Botón de retroceso
        back_button = MDIconButton(
            icon="arrow-left",
            theme_icon_color="Primary",
            on_release=self.ir_atras,
            pos_hint={'center_y': 0.5}
        )

        # Espaciador para centrar el título
        left_spacer = Widget(size_hint_x=0.15)  # Espaciador izquierdo

        # Título del header - "Iniciar Sesión" centrado
        header_title = MDLabel(
            text="Iniciar Sesión",
            font_style="H5",
            theme_text_color="Primary",
            halign="center",  # Centrado
            valign="center",
            size_hint_x=0.7  # Toma el 70% del ancho
        )

        # Espaciador derecho para balance
        right_spacer = Widget(size_hint_x=0.15)

        header_layout.add_widget(back_button)
        header_layout.add_widget(left_spacer)
        header_layout.add_widget(header_title)
        header_layout.add_widget(right_spacer)

        # Contenedor del contenido con padding lateral
        content_container = MDBoxLayout(
            orientation='vertical',
            padding=[dp(30), 0, dp(30), dp(40)],
            spacing=dp(20)
        )

        # Título principal - Solo CORPOTACHIRA
        title_label = MDLabel(
            text="CORPOTACHIRA",
            font_style="H4",
            size_hint_y=None,
            height=dp(60),
            halign="center",
            theme_text_color="Primary",
            bold=True
        )

        # Subtítulo
        subtitle_label = MDLabel(
            text="Ingresa tu cédula",
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
            height=dp(100)
        )

        # Campo de cédula
        self.cedula_field = MDTextField(
            hint_text="Cédula",
            helper_text="",
            helper_text_mode="on_error",
            size_hint_y=None,
            height=dp(60),
            multiline=False,
            input_filter="int",  # Solo números
            max_text_length=10,
            on_text_validate=self.intentar_login,
            on_text=self.validar_cedula_tiempo_real
        )

        # Forzar binding
        self.cedula_field.bind(text=self.validar_cedula_tiempo_real)
        
        form_layout.add_widget(self.cedula_field)

        # Botón de login (tamaño reducido)
        self.login_button = MDRaisedButton(
            text="INGRESAR",
            size_hint_y=None,
            height=dp(50),  # Mismo tamaño que el otro login
            md_bg_color=(0.35, 0.63, 0.8, 1),  # Azul claro para obreros
            elevation=8,
            disabled=True,
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
        info_label_container = MDBoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(60),
            spacing=dp(5)
        )

        info_label = MDLabel(
            text="No necesitas contraseña",
            font_style="Body2",
            size_hint_y=None,
            height=dp(25),
            halign="center",
            theme_text_color="Primary"
        )

        self.status_label = MDLabel(
            text="Solo ingresa tu cédula para acceder",
            font_style="Caption",
            size_hint_y=None,
            height=dp(20),
            halign="center",
            theme_text_color="Hint"
        )

        info_label_container.add_widget(info_label)
        info_label_container.add_widget(self.status_label)

        # Agregar widgets al content_container
        content_container.add_widget(title_label)
        content_container.add_widget(subtitle_label)
        content_container.add_widget(MDLabel())  # Spacer
        content_container.add_widget(form_layout)
        content_container.add_widget(self.login_button)
        content_container.add_widget(self.spinner)
        content_container.add_widget(MDLabel())  # Spacer
        content_container.add_widget(info_label_container)

        # Agregar header y contenido al contenedor principal
        main_container.add_widget(header_layout)
        main_container.add_widget(content_container)

        # Agregar el contenedor principal a la pantalla
        self.add_widget(main_container)

    def validar_cedula_tiempo_real(self, instance, texto):
        """
        Valida el campo cédula en tiempo real
        """
        # Validar que solo contenga números
        cedula_limpia = ''.join(filter(str.isdigit, texto))

        # Si el texto es diferente, actualizar
        if cedula_limpia != texto:
            instance.text = cedula_limpia

        # Validar longitud
        longitud = len(cedula_limpia)

        if longitud == 0:
            self.cedula_field.error = False
            self.cedula_field.helper_text = "Ingresa tu cédula"
            self.login_button.disabled = True
            self.login_button.md_bg_color = (0.7, 0.7, 0.7, 1)

        elif longitud < 6:
            self.cedula_field.error = False
            self.cedula_field.helper_text = f"Mínimo 6 dígitos (tienes {longitud})"
            self.login_button.disabled = True
            self.login_button.md_bg_color = (0.7, 0.7, 0.7, 1)

        elif 6 <= longitud <= 10:
            self.cedula_field.error = False
            self.cedula_field.helper_text = "✓ Cédula válida"
            self.login_button.disabled = False
            self.login_button.md_bg_color = (0.35, 0.63, 0.8, 1)

        else:  # > 10
            self.cedula_field.error = True
            self.cedula_field.helper_text = "Máximo 10 dígitos"
            self.login_button.disabled = True
            self.login_button.md_bg_color = (0.7, 0.7, 0.7, 1)

    def intentar_login(self, instance=None):
        """
        Intenta realizar el login del obrero
        """
        if self.login_button.disabled:
            return

        cedula = self.cedula_field.text.strip()

        if not cedula:
            self.mostrar_error("La cédula es requerida")
            return

        # Validación final
        if not cedula.isdigit() or len(cedula) < 6 or len(cedula) > 10:
            self.mostrar_error("Cédula debe tener entre 6 y 10 dígitos")
            return

        # Mostrar spinner
        self.mostrar_cargando(True)

        # Realizar login en hilo separado
        thread = Thread(target=self._realizar_login, args=(cedula,))
        thread.daemon = True
        thread.start()

    def _realizar_login(self, cedula):
        """
        Realiza el login en hilo separado
        """
        try:
            app = MDApp.get_running_app()
            base_url = getattr(app, 'base_url', 'https://chat-cv1i.onrender.com')

            # Preparar datos
            data = {'cedula': cedula}

            # Realizar petición
            response = requests.post(
                f"{base_url}/api/auth/login/obrero",
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
        """
        try:
            app = MDApp.get_running_app()

            # Guardar datos de sesión específicos para obrero
            user_data = result.get('user_data', {})
            token = result.get('token', '')

            app.nivel_usuario = 'obrero'
            app.token_sesion = token
            app.user_data = user_data
            app.nombre_usuario = user_data.get('nombre_completo', f"Obrero {user_data.get('cedula', '')}")

            print(f"✅ Login obrero exitoso: {app.nombre_usuario}")

            # Mostrar mensaje de éxito
            self.mostrar_exito(f"Bienvenido, {app.nombre_usuario}")

            # Navegar según nivel
            Clock.schedule_once(self._navegar_a_chat, 1.5)

        except Exception as e:
            self._manejar_error_login(f"Error guardando sesión: {e}")

    def _login_fallido(self, mensaje):
        """
        Maneja un login fallido
        """
        self.mostrar_error(mensaje)

        # Limpiar campo y enfocar
        self.cedula_field.text = ""
        self.cedula_field.focus = True

    def _manejar_error_login(self, mensaje):
        """
        Maneja errores generales del login
        """
        self.mostrar_cargando(False)
        self.mostrar_error(mensaje)

    def _navegar_a_chat(self, dt):
        """
        Navega directamente a la pantalla de chat
        """
        try:
            app = MDApp.get_running_app()
            app.navegar_a_principal_segun_nivel()
            print("📄 Obrero navegado al chat con configuración automática")

        except Exception as e:
            print(f"❌ Error navegando a chat: {e}")
            self.mostrar_error("Error navegando al chat")

    def mostrar_cargando(self, mostrar):
        """
        Muestra u oculta el spinner de carga
        """
        self.spinner.active = mostrar
        self.login_button.disabled = mostrar

        # Cambiar color según estado
        if mostrar:
            self.login_button.md_bg_color = (0.7, 0.7, 0.7, 1)
        else:
            # Revalidar después de la carga
            cedula_valida = len(self.cedula_field.text.strip()) >= 6
            if cedula_valida:
                self.login_button.md_bg_color = (0.35, 0.63, 0.8, 1)
                self.login_button.disabled = False

    def mostrar_error(self, mensaje):
        """
        Muestra un mensaje de error
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
        # Limpiar campo
        self.cedula_field.text = ""

        # Enfocar campo de cédula
        Clock.schedule_once(lambda dt: setattr(self.cedula_field, 'focus', True), 0.1)

    def on_leave(self):
        """
        Se ejecuta al salir de la pantalla
        """
        # Limpiar estado
        self.cedula_field.text = ""
        self.mostrar_cargando(False)