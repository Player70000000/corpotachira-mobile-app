from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.app import MDApp
import requests
import threading
import json
from kivy.clock import Clock

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import API_BASE_URL


class DivisorLinea(MDBoxLayout):
    """Divisor visual personalizado"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = "1dp"
        with self.canvas:
            from kivy.graphics import Color, Rectangle
            Color(0.8, 0.8, 0.8, 1)  # Gris claro
            self.rect = Rectangle(size=self.size, pos=self.pos)
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos


class InfoPersonalScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "info_personal"
        self.origin_tab = "chat"  # Pestaña de origen por defecto
        self.build_layout()

    def build_layout(self):
        # Layout principal
        main_layout = MDBoxLayout(
            orientation="vertical"
        )

        # Barra superior con botón de volver
        top_bar = MDTopAppBar(
            title="Información Personal",
            left_action_items=[["arrow-left", lambda x: self.volver_atras()]],
        )
        main_layout.add_widget(top_bar)

        # Contenido scrollable
        scroll_content = MDBoxLayout(
            orientation="vertical",
            spacing="20dp",
            padding=["20dp", "20dp", "20dp", "20dp"],
            adaptive_height=True,
            size_hint_y=None
        )
        # Importante: bind height para que funcione el scroll
        scroll_content.bind(minimum_height=scroll_content.setter('height'))

        # Sección: Datos Personales
        seccion_datos = self.crear_seccion_datos_personales()
        scroll_content.add_widget(seccion_datos)

        # Divisor
        scroll_content.add_widget(DivisorLinea())

        # Sección: Nivel/Rol
        seccion_rol = self.crear_seccion_rol()
        scroll_content.add_widget(seccion_rol)

        # Divisor
        scroll_content.add_widget(DivisorLinea())

        # Sección: Canales (placeholder por ahora)
        seccion_canales = self.crear_seccion_canales()
        scroll_content.add_widget(seccion_canales)

        # Divisor
        scroll_content.add_widget(DivisorLinea())

        # Botón cerrar sesión
        boton_cerrar_sesion = MDRaisedButton(
            text="Cerrar Sesión",
            theme_icon_color="Custom",
            md_bg_color=[0.8, 0.2, 0.2, 1],  # Rojo
            size_hint_y=None,
            height="50dp",
            pos_hint={"center_x": 0.5}
        )
        boton_cerrar_sesion.bind(on_release=self.cerrar_sesion)
        scroll_content.add_widget(boton_cerrar_sesion)

        # Crear ScrollView
        scroll_view = MDScrollView(
            do_scroll_x=False,  # Solo scroll vertical
            effect_cls="ScrollEffect"
        )
        scroll_view.add_widget(scroll_content)

        # Agregar scroll al layout principal
        main_layout.add_widget(scroll_view)
        self.add_widget(main_layout)

    def crear_seccion_datos_personales(self):
        seccion = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            size_hint_y=None,
            adaptive_height=True
        )

        # Título de la sección
        titulo_seccion = MDLabel(
            text="Datos Personales",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )
        seccion.add_widget(titulo_seccion)

        # Campos de información
        self.label_nombre = MDLabel(
            text="Nombre: [Pendiente]",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        seccion.add_widget(self.label_nombre)

        self.label_apellido = MDLabel(
            text="Apellido: [Pendiente]",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        seccion.add_widget(self.label_apellido)

        self.label_cedula = MDLabel(
            text="Cédula: [Pendiente]",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        seccion.add_widget(self.label_cedula)

        self.label_correo = MDLabel(
            text="Correo: [Pendiente]",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        seccion.add_widget(self.label_correo)

        return seccion

    def crear_seccion_rol(self):
        seccion = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            size_hint_y=None,
            adaptive_height=True
        )

        # Título de la sección
        titulo_seccion = MDLabel(
            text="Nivel/Rol y Cuadrilla",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )
        seccion.add_widget(titulo_seccion)

        # Campo de rol
        self.label_rol = MDLabel(
            text="Rol: [Pendiente]",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        seccion.add_widget(self.label_rol)

        # Campo de cuadrilla
        self.label_cuadrilla = MDLabel(
            text="Cuadrilla: [Pendiente]",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        seccion.add_widget(self.label_cuadrilla)

        return seccion

    def crear_seccion_canales(self):
        seccion = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            size_hint_y=None,
            adaptive_height=True
        )

        # Título de la sección
        titulo_seccion = MDLabel(
            text="Canales",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )
        seccion.add_widget(titulo_seccion)

        # Placeholder para canales
        self.label_canales = MDLabel(
            text="Canales disponibles: [En desarrollo]",
            theme_text_color="Secondary",
            size_hint_y=None,
            height="30dp"
        )
        seccion.add_widget(self.label_canales)

        return seccion

    def volver_atras(self):
        """Volver a la pantalla principal y a la pestaña de origen"""
        try:
            app = MDApp.get_running_app()

            if hasattr(app.root, 'screen_manager'):
                # Volver a la pantalla principal
                app.root.screen_manager.current = 'main'

                # Cambiar a la pestaña de origen usando el método correcto
                main_screen = app.root.screen_manager.get_screen('main')
                if hasattr(main_screen, 'main_layout'):
                    # Solo usar switch_screen - esto ya llama internamente a switch_tab
                    main_screen.main_layout.switch_screen(self.origin_tab)
        except Exception as e:
            print(f"❌ Error volviendo atrás: {e}")

    def cerrar_sesion(self, *args):
        """Función para cerrar sesión"""
        app = MDApp.get_running_app()
        if hasattr(app, 'logout'):
            app.logout()
        else:
            print("❌ No se pudo cerrar sesión")

    def on_enter(self):
        """Se ejecuta cuando se entra a la pantalla"""
        # Detectar la pestaña de origen desde el MainLayout actual
        self.detectar_origen_actual()

        # Cargar los datos del usuario
        self.cargar_datos_usuario()

    def detectar_origen_actual(self):
        """Detecta automáticamente la pestaña de origen desde MainLayout"""
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()

            if hasattr(app.root, 'screen_manager'):
                main_screen = app.root.screen_manager.get_screen('main')
                if hasattr(main_screen, 'main_layout'):
                    current_tab = getattr(main_screen.main_layout, 'current_tab', 'chat')
                    self.origin_tab = current_tab
        except Exception as e:
            # Fallback al valor por defecto
            self.origin_tab = "chat"

    def cargar_datos_usuario(self):
        """Carga los datos del usuario actual desde el backend"""
        try:
            app = MDApp.get_running_app()

            # Obtener datos básicos del usuario logueado
            user_data = getattr(app, 'user_data', {})
            nivel_usuario = getattr(app, 'nivel_usuario', 'obrero')
            nombre_usuario = getattr(app, 'nombre_usuario', 'Usuario')

            # Mostrar mensajes de carga iniciales
            self.label_nombre.text = "Nombre: [Cargando...]"
            self.label_apellido.text = "Apellidos: [Cargando...]"
            self.label_cedula.text = "Cédula: [Cargando...]"
            self.label_correo.text = "Correo: [Cargando...]"

            # Nivel/Rol (este ya lo tenemos)
            nivel_display = {
                'admin': 'Administrador',
                'moderador': 'Moderador',
                'obrero': 'Obrero'
            }.get(nivel_usuario, 'Usuario')

            self.label_rol.text = f"Rol: {nivel_display}"

            # Para admin, usar datos básicos disponibles
            if nivel_usuario == 'admin':
                self.label_nombre.text = "Nombre: Administrador"
                self.label_apellido.text = "Apellidos: Sistema"
                self.label_cedula.text = "Cédula: N/A"
                self.label_correo.text = "Correo: admin@corpotachira.com"
                self.cargar_cuadrilla_asignada()
                return

            # Para moderadores y obreros, obtener datos reales del backend
            cedula_actual = user_data.get('cedula')
            if not cedula_actual:
                # Intentar obtener de otras fuentes si está disponible
                if hasattr(app, 'cedula_usuario'):
                    cedula_actual = app.cedula_usuario
                else:
                    self.mostrar_datos_error()
                    return

            # Consultar datos en hilo separado para no bloquear la UI
            def consultar_datos_backend():
                datos_usuario = self.obtener_datos_usuario_backend(cedula_actual, nivel_usuario)

                # Actualizar UI en el hilo principal
                def actualizar_ui(dt):
                    if datos_usuario:
                        self.label_nombre.text = f"Nombre: {datos_usuario.get('nombre', 'No disponible')}"
                        self.label_apellido.text = f"Apellidos: {datos_usuario.get('apellidos', 'No disponible')}"
                        self.label_cedula.text = f"Cédula: {datos_usuario.get('cedula', 'No disponible')}"
                        self.label_correo.text = f"Correo: {datos_usuario.get('email', 'No disponible')}"
                    else:
                        self.mostrar_datos_error()

                Clock.schedule_once(actualizar_ui, 0)

            # Iniciar consulta en hilo separado
            thread = threading.Thread(target=consultar_datos_backend)
            thread.daemon = True
            thread.start()

            # Cargar cuadrilla asignada
            self.cargar_cuadrilla_asignada()

        except Exception as e:
            print(f"❌ Error cargando datos de usuario: {e}")
            self.mostrar_datos_error()

    def mostrar_datos_error(self):
        """Muestra mensajes de error en todos los campos"""
        self.label_nombre.text = "Nombre: [Error cargando]"
        self.label_apellido.text = "Apellidos: [Error cargando]"
        self.label_cedula.text = "Cédula: [Error cargando]"
        self.label_correo.text = "Correo: [Error cargando]"
        self.label_rol.text = "Rol: [Error cargando]"
        self.label_cuadrilla.text = "Cuadrilla: [Error cargando]"

    def obtener_datos_usuario_backend(self, cedula, nivel_usuario):
        """Obtiene los datos del usuario desde el backend según su nivel"""
        try:
            app = MDApp.get_running_app()
            headers = app.get_auth_headers()

            # Determinar endpoint según el nivel
            if nivel_usuario == 'admin':
                # Para admin no consultamos datos desde personal
                return None
            elif nivel_usuario == 'moderador':
                endpoint = f"{API_BASE_URL}/api/personnel/moderadores/"

                # Hacer petición GET para obtener lista
                response = requests.get(endpoint, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    # Buscar moderador por cédula
                    if isinstance(data, dict):
                        usuarios_lista = data.get('moderadores', [])
                        for usuario in usuarios_lista:
                            if isinstance(usuario, dict) and usuario.get('cedula') == cedula:
                                return usuario
                    return None
                else:
                    print(f"❌ Error HTTP {response.status_code} consultando datos de moderador")
                    return None
            else:  # obrero
                # NUEVO: Usar endpoint específico para obreros
                endpoint = f"{API_BASE_URL}/api/personnel/mi-informacion/"

                # Hacer petición GET para obtener datos propios
                response = requests.get(endpoint, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    # El nuevo endpoint devuelve {"obrero": {...}, "mensaje": "..."}
                    return data.get('obrero')
                else:
                    print(f"❌ Error HTTP {response.status_code} consultando datos de obrero")
                    return None

        except requests.RequestException as e:
            print(f"❌ Error de conexión consultando usuario: {e}")
            return None
        except Exception as e:
            print(f"❌ Error inesperado consultando usuario: {e}")
            return None

    def obtener_cuadrilla_usuario_backend(self, cedula, nivel_usuario):
        """Obtiene la cuadrilla asignada al usuario desde el backend"""
        try:
            app = MDApp.get_running_app()
            headers = app.get_auth_headers()

            # Usar endpoint específico para obreros
            if nivel_usuario == 'obrero':
                # NUEVO: Usar endpoint específico para obreros
                endpoint = f"{API_BASE_URL}/api/personnel/mi-cuadrilla/"

                response = requests.get(endpoint, headers=headers, timeout=10)

                if response.status_code == 200:
                    data = response.json()
                    cuadrilla = data.get('cuadrilla')

                    if cuadrilla:
                        numero_cuadrilla = cuadrilla.get('numero_cuadrilla', 'Sin número')
                        return numero_cuadrilla
                    else:
                        return data.get('mensaje', 'Sin asignar')
                else:
                    print(f"❌ Error HTTP {response.status_code} consultando cuadrilla de obrero")
                    return "Error consultando"

            else:  # moderador
                endpoint = f"{API_BASE_URL}/api/personnel/cuadrillas/"

                # Hacer petición GET para obtener lista de cuadrillas
                response = requests.get(endpoint, headers=headers, timeout=10)

                if response.status_code == 200:
                    cuadrillas = response.json()

                    # El backend devuelve {"cuadrillas": [...]}
                    if isinstance(cuadrillas, dict):
                        cuadrillas_lista = cuadrillas.get('cuadrillas', [])

                        # Buscar cuadrilla donde el moderador esté asignado
                        for cuadrilla in cuadrillas_lista:
                            if not isinstance(cuadrilla, dict):
                                continue

                            # Verificar si es moderador de la cuadrilla
                            moderador = cuadrilla.get('moderador', {})
                            if isinstance(moderador, dict) and moderador.get('cedula') == cedula:
                                numero_cuadrilla = cuadrilla.get('numero_cuadrilla', 'Sin número')
                                return f"{numero_cuadrilla} (Moderador a cargo)"

                    return "Sin asignar"
                else:
                    print(f"❌ Error HTTP {response.status_code} consultando cuadrillas")
                    return "Error consultando"

        except requests.RequestException as e:
            print(f"❌ Error de conexión consultando cuadrillas: {e}")
            return "Error de conexión"
        except Exception as e:
            print(f"❌ Error inesperado consultando cuadrillas: {e}")
            return "Error consultando"

    def cargar_cuadrilla_asignada(self):
        """Obtiene y muestra la cuadrilla asignada al usuario"""
        try:
            app = MDApp.get_running_app()
            user_data = getattr(app, 'user_data', {})
            nivel_usuario = getattr(app, 'nivel_usuario', 'obrero')

            # Solo buscar cuadrilla para moderadores y obreros
            if nivel_usuario == 'admin':
                self.label_cuadrilla.text = "Cuadrilla: N/A (Administrador)"
                return

            # Obtener cédula del usuario actual
            cedula_actual = user_data.get('cedula')
            if not cedula_actual:
                self.label_cuadrilla.text = "Cuadrilla: Sin asignar"
                return

            # Mostrar mensaje de carga
            self.label_cuadrilla.text = "Cuadrilla: [Consultando...]"

            # Consultar cuadrilla en hilo separado
            def consultar_cuadrilla():
                resultado = self.obtener_cuadrilla_usuario_backend(cedula_actual, nivel_usuario)
                # Actualizar UI en el hilo principal
                Clock.schedule_once(lambda dt: setattr(self.label_cuadrilla, 'text', f"Cuadrilla: {resultado}"), 0)

            thread = threading.Thread(target=consultar_cuadrilla)
            thread.daemon = True
            thread.start()

        except Exception as e:
            print(f"❌ Error cargando cuadrilla: {e}")
            self.label_cuadrilla.text = "Cuadrilla: Error consultando"