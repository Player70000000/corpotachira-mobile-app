# -*- coding: utf-8 -*-
"""
PANTALLA DE SELECCIÓN DE ROL v8.0
CORPOTACHIRA - Sistema de Autenticación

Esta es la pantalla inicial que permite al usuario seleccionar su rol:
- ADMIN: Acceso total al sistema
- MODERADOR: Gestión limitada (no puede gestionar otros moderadores)
- OBRERO: Solo chat en modo lectura

Especificaciones de diseño:
- Material Design con colores corporativos
- Tres botones grandes y diferenciados
- Navegación directa a pantallas de login específicas
"""

from kivymd.app import MDApp
from kivymd.uix.screen import MDScreen
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.button import MDRaisedButton
from kivy.uix.widget import Widget
from kivy.metrics import dp


class RoleSelectionScreen(MDScreen):
    """
    Pantalla de selección de rol de usuario
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'role_selection'
        self.build_ui()

    def build_ui(self):
        """
        Construye la interfaz de usuario de la pantalla con espaciado preciso
        """
        # Layout principal con fondo
        main_layout = MDBoxLayout(
            orientation='vertical',
            md_bg_color=(0.95, 0.95, 0.95, 1)  # Fondo gris 95%
        )

        # Espaciador superior de 10dp desde el tope
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(10)))

        # Título principal CORPOTACHIRA app
        title_label = MDLabel(
            text="CORPOTACHIRA app",
            font_style="H4",
            size_hint_y=None,
            height=dp(80),  # Aumentado a 80dp
            halign="center",
            theme_text_color="Primary",
            bold=True,
            padding=[dp(40), 0, dp(40), 0]  # 40dp izquierda y derecha
        )
        main_layout.add_widget(title_label)

        # Espaciador de 100dp entre título y subtítulo
        main_layout.add_widget(Widget(size_hint_y=None, height=dp(100)))

        # Subtítulo ¿Quién está ingresando?
        subtitle_label = MDLabel(
            text="¿Quién está ingresando?",
            font_style="H6",
            size_hint_y=None,
            height=dp(25),  # Reducido de 35dp a 25dp
            halign="center",
            theme_text_color="Secondary"
        )
        main_layout.add_widget(subtitle_label)


        # Contenedor centrado para los botones
        buttons_container = MDBoxLayout(
            orientation='vertical',
            size_hint=(None, None),
            width=dp(280),  # Ancho fijo para los botones
            height=dp(240),  # Altura total del contenedor
            pos_hint={'center_x': 0.5}  # Centrar horizontalmente
        )

        # Botón ADMINISTRADOR
        admin_button = MDRaisedButton(
            text="ADMIN",
            md_bg_color=(0.25, 0.46, 0.65, 1),  # Azul medio (igual al moderador)
            size_hint=(1, None),  # Ancho completo del contenedor
            height=dp(70),
            font_size="20sp",
            elevation=0,  # Sin sombra
            on_release=self.ir_a_login_admin
        )
        buttons_container.add_widget(admin_button)

        # Espaciador de 20dp entre botones
        buttons_container.add_widget(Widget(size_hint_y=None, height=dp(20)))

        # Botón MODERADOR
        moderador_button = MDRaisedButton(
            text="MODERADOR",
            md_bg_color=(0.25, 0.46, 0.65, 1),  # Azul medio
            size_hint=(1, None),
            height=dp(70),
            font_size="20sp",
            elevation=0,  # Sin sombra
            on_release=self.ir_a_login_moderador
        )
        buttons_container.add_widget(moderador_button)

        # Espaciador de 20dp entre botones
        buttons_container.add_widget(Widget(size_hint_y=None, height=dp(20)))

        # Botón OBRERO
        obrero_button = MDRaisedButton(
            text="OBRERO",
            md_bg_color=(0.25, 0.46, 0.65, 1),  # Azul medio (igual al moderador)
            size_hint=(1, None),
            height=dp(70),
            font_size="20sp",
            elevation=0,  # Sin sombra
            on_release=self.ir_a_login_obrero
        )
        buttons_container.add_widget(obrero_button)

        # Agregar contenedor de botones al layout principal
        main_layout.add_widget(buttons_container)

        # Espaciador flexible para empujar todo hacia arriba
        main_layout.add_widget(Widget())  # Este toma el espacio restante

        # Agregar el layout principal a la pantalla
        self.add_widget(main_layout)

    def ir_a_login_admin(self, instance):
        """
        Navega a la pantalla de login para admin
        """
        try:
            app = MDApp.get_running_app()
            
            # Verificar que la pantalla de login existe
            if 'login' not in app.root.screen_manager.screen_names:
                self.mostrar_error("Pantalla de login no disponible")
                return
            
            # Cambiar a pantalla de login con tipo 'admin'
            login_screen = app.root.screen_manager.get_screen('login')
            login_screen.configurar_para_tipo('admin')
            app.root.screen_manager.current = 'login'
            
        except Exception as e:
            print(f"❌ Error navegando a login admin: {e}")
            self.mostrar_error("Error navegando a login de administrador")

    def ir_a_login_moderador(self, instance):
        """
        Navega a la pantalla de login para moderador
        """
        try:
            app = MDApp.get_running_app()
            
            # Verificar que la pantalla de login existe
            if 'login' not in app.root.screen_manager.screen_names:
                self.mostrar_error("Pantalla de login no disponible")
                return
            
            # Cambiar a pantalla de login con tipo 'moderador'
            login_screen = app.root.screen_manager.get_screen('login')
            login_screen.configurar_para_tipo('moderador')
            app.root.screen_manager.current = 'login'
            
        except Exception as e:
            print(f"❌ Error navegando a login moderador: {e}")
            self.mostrar_error("Error navegando a login de moderador")

    def ir_a_login_obrero(self, instance):
        """
        Navega a la pantalla de login específica para obreros
        """
        try:
            app = MDApp.get_running_app()
            
            # Verificar que la pantalla de login obrero existe
            if 'login_obrero' not in app.root.screen_manager.screen_names:
                self.mostrar_error("Pantalla de login obrero no disponible")
                return
            
            # Cambiar a pantalla de login obrero
            app.root.screen_manager.current = 'login_obrero'
            
        except Exception as e:
            print(f"❌ Error navegando a login obrero: {e}")
            self.mostrar_error("Error navegando a login de obrero")

    def mostrar_error(self, mensaje):
        """
        Muestra un mensaje de error al usuario
        
        Args:
            mensaje (str): Mensaje de error a mostrar
        """
        try:
            from kivymd.uix.snackbar import MDSnackbar
            
            snackbar = MDSnackbar(
                MDLabel(
                    text=mensaje,
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1)
                ),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
                md_bg_color=(0.8, 0.2, 0.2, 1),  # Rojo para errores
                duration=3
            )
            snackbar.open()
            
        except Exception as e:
            print(f"❌ Error mostrando snackbar: {e}")

    def on_enter(self):
        """
        Se ejecuta cuando se entra a la pantalla
        """
        # Limpiar cualquier estado de autenticación previo
        try:
            app = MDApp.get_running_app()
            
            # Limpiar variables de sesión si existen
            if hasattr(app, 'nivel_usuario'):
                app.nivel_usuario = ''
            if hasattr(app, 'token_sesion'):
                app.token_sesion = ''
            if hasattr(app, 'user_data'):
                app.user_data = {}
            if hasattr(app, 'nombre_usuario'):
                app.nombre_usuario = ''
            
            print("🔓 Sesión limpiada - Pantalla de selección de rol")
            
        except Exception as e:
            print(f"⚠️ Error limpiando sesión: {e}")

    def on_leave(self):
        """
        Se ejecuta cuando se sale de la pantalla
        """
        pass