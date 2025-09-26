#!/usr/bin/env python3
"""
Empresa Limpieza - Aplicación Móvil KivyMD v8.0
SISTEMA DE AUTENTICACIÓN Y NIVELES DE ACCESO
Punto de entrada principal con control de sesiones
"""

__version__ = "8.0"

from kivymd.app import MDApp
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.tab import MDTabs, MDTabsBase
from kivymd.uix.floatlayout import MDFloatLayout
from kivymd.uix.button import MDIconButton, MDRaisedButton
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.label import MDLabel
from kivy.core.window import Window
from kivy.metrics import dp
from kivy.properties import StringProperty, DictProperty
from kivy.clock import Clock

# Importar pantallas existentes
from screens.chat_screen import ChatScreen
from screens.personal_screen import PersonalScreen
from screens.reportes_screen import ReportesScreen
from screens.info_personal_screen import InfoPersonalScreen

# Importar nuevas pantallas de autenticación
from screens.role_selection_screen import RoleSelectionScreen
from screens.login_screen import LoginScreen
from screens.login_obrero_screen import LoginObreroScreen


class TabContent(MDFloatLayout, MDTabsBase):
    """Clase base para el contenido de las pestañas"""
    pass


class CustomBottomNav(MDBoxLayout):
    """Navegación inferior personalizada con control de niveles v8.0"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(60)
        self.md_bg_color = [0.2, 0.6, 1, 1]  # Color azul
        self.spacing = 0
        self.current_screen = None
        self.screens = {}
        self.buttons = {}
        self.tab_containers = {}  # Para ocultar/mostrar pestañas

    def add_tab(self, name, text, icon, screen_widget, required_levels=None):
        """
        Agregar una pestaña con su pantalla asociada y niveles requeridos

        Args:
            name (str): Nombre de la pestaña
            text (str): Texto a mostrar
            icon (str): Icono de la pestaña
            screen_widget: Widget de la pantalla
            required_levels (list): Niveles que pueden ver esta pestaña ['admin', 'moderador', 'obrero']
        """
        self.screens[name] = screen_widget

        # Crear contenedor para el botón
        button_container = MDBoxLayout(
            orientation="vertical",
            size_hint_x=1,
            spacing=dp(2),
            adaptive_height=True
        )

        # Botón con icono
        button = MDIconButton(
            icon=icon,
            theme_icon_color="Custom",
            icon_color=[1, 1, 1, 1],  # Blanco
            size_hint=(1, None),
            height=dp(32),
            on_release=lambda x, tab_name=name: self.switch_tab(tab_name)
        )

        # Etiqueta de texto
        label = MDLabel(
            text=text,
            font_size=dp(10),
            theme_text_color="Custom",
            text_color=[1, 1, 1, 1],  # Blanco
            halign="center",
            size_hint_y=None,
            height=dp(16)
        )

        button_container.add_widget(button)
        button_container.add_widget(label)
        self.add_widget(button_container)

        self.buttons[name] = (button, label)
        self.tab_containers[name] = {
            'container': button_container,
            'required_levels': required_levels or ['admin', 'moderador', 'obrero']
        }

        # Si es la primera pestaña, activarla
        if len(self.screens) == 1:
            self.switch_tab(name)

    def update_tabs_for_level(self, user_level):
        """
        Actualiza las pestañas visibles según el nivel del usuario

        Args:
            user_level (str): Nivel del usuario ('admin', 'moderador', 'obrero')
        """
        # Limpiar navegación
        self.clear_widgets()
        visible_tabs = []

        # Agregar solo las pestañas permitidas para este nivel
        for tab_name, tab_info in self.tab_containers.items():
            required_levels = tab_info['required_levels']

            if user_level in required_levels:
                self.add_widget(tab_info['container'])
                visible_tabs.append(tab_name)

        # Si hay pestañas visibles, preservar la pestaña actual o activar la primera
        if visible_tabs:
            # Obtener pestaña actual del parent MainLayout
            current_tab = getattr(self.parent, 'current_tab', None) if self.parent else None

            # Si la pestaña actual sigue siendo visible, mantenerla
            if current_tab and current_tab in visible_tabs:
                # Solo actualizar colores de botones, NO cambiar pantalla (evita bucles)
                if self.parent and hasattr(self.parent, 'update_navigation_buttons_only'):
                    self.parent.update_navigation_buttons_only(current_tab)
            else:
                # Si no, activar la primera disponible
                self.switch_tab(visible_tabs[0])

        return visible_tabs
    
    def switch_tab(self, tab_name):
        """Cambiar a una pestaña específica"""
        if tab_name not in self.screens:
            return

        # Actualizar colores de botones
        for name, (button, label) in self.buttons.items():
            if name == tab_name:
                # Pestaña activa - naranja
                button.icon_color = [1, 0.6, 0, 1]
                label.text_color = [1, 0.6, 0, 1]
            else:
                # Pestaña inactiva - blanco
                button.icon_color = [1, 1, 1, 0.7]
                label.text_color = [1, 1, 1, 0.7]

        # Lógica específica para pestaña Personal: reconfigurar dinámicamente
        if tab_name == 'personal' and hasattr(self, 'screens') and 'personal' in self.screens:
            personal_screen = self.screens['personal']
            if hasattr(personal_screen, 'reconfigure_cards_for_current_user'):
                personal_screen.reconfigure_cards_for_current_user()

        # Notificar cambio de pantalla al padre
        if hasattr(self.parent, 'switch_screen'):
            self.parent.switch_screen(tab_name)


class MainLayout(MDBoxLayout):
    """Layout principal con navegación de pestañas y control de autenticación v8.0"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.current_tab = "chat"
        self.setup_ui()

    def setup_ui(self):

        # Contenedor para las pantallas
        self.content_container = MDBoxLayout()

        # Navegación inferior personalizada
        self.bottom_nav = CustomBottomNav()

        # Agregar pestañas CON CONTROL DE NIVELES
        self.chat_screen = ChatScreen()
        self.personal_screen = PersonalScreen()
        self.reportes_screen = ReportesScreen()
        self.info_personal_screen = InfoPersonalScreen()

        # Configurar referencia al layout principal en cada pantalla
        self.chat_screen.main_layout = self
        self.personal_screen.main_layout = self
        self.reportes_screen.main_layout = self
        self.info_personal_screen.main_layout = self

        # Agregar pestañas con niveles requeridos
        self.bottom_nav.add_tab(
            "chat", "Chat", "chat-processing", self.chat_screen,
            required_levels=['admin', 'moderador', 'obrero']  # Todos pueden ver chat
        )
        self.bottom_nav.add_tab(
            "personal", "Personal", "account-group", self.personal_screen,
            required_levels=['admin', 'moderador']  # Solo admin y moderador
        )
        self.bottom_nav.add_tab(
            "reportes", "Reportes", "file-document-multiple", self.reportes_screen,
            required_levels=['admin', 'moderador']  # Solo admin y moderador
        )

        # Ensamblar layout
        self.add_widget(self.content_container)
        self.add_widget(self.bottom_nav)

        # Configurar pestañas según el nivel del usuario
        self.configurar_para_nivel_usuario()

    def configurar_para_nivel_usuario(self):
        """
        Configura las pestañas visibles según el nivel del usuario
        """
        try:
            app = MDApp.get_running_app()
            user_level = getattr(app, 'nivel_usuario', 'obrero')

            # Actualizar pestañas visibles
            visible_tabs = self.bottom_nav.update_tabs_for_level(user_level)

            # Si hay pestañas visibles, gestionar la pantalla inicial
            if visible_tabs:
                # Verificar si necesitamos mostrar una pantalla inicial
                needs_initial_screen = (
                    not self.content_container.children or  # No hay contenido
                    not self.current_tab or  # No hay pestaña actual
                    self.current_tab not in visible_tabs  # Pestaña actual no válida
                )

                if needs_initial_screen:
                    self.switch_screen(visible_tabs[0])
                else:
                    # Mantener pestaña actual pero asegurar que esté visible
                    if self.current_tab in self.bottom_nav.screens and self.current_tab not in [w.name for w in self.content_container.children if hasattr(w, 'name')]:
                        self.switch_screen(self.current_tab)

            # Actualizar UI de todas las pantallas según el nivel de usuario
            self.update_all_screens_for_user_level()

        except Exception as e:
            print(f"❌ Error configurando nivel de usuario: {e}")

    def update_all_screens_for_user_level(self):
        """
        Actualiza la UI de todas las pantallas según el nivel del usuario
        Se ejecuta después del login para aplicar permisos y visibilidad
        """
        try:
            # Actualizar ChatScreen
            if hasattr(self, 'chat_screen') and hasattr(self.chat_screen, 'update_ui_for_user_level'):
                self.chat_screen.update_ui_for_user_level()

            # Aquí se pueden agregar más pantallas en el futuro
            # if hasattr(self, 'personal_screen') and hasattr(self.personal_screen, 'update_ui_for_user_level'):
            #     self.personal_screen.update_ui_for_user_level()

        except Exception as e:
            print(f"❌ Error actualizando UI de pantallas: {e}")

    def switch_screen(self, screen_name):
        """Cambiar la pantalla visible"""
        self.content_container.clear_widgets()
        if screen_name in self.bottom_nav.screens:
            self.current_tab = screen_name

            # Siempre resetear a pantalla principal al cambiar de pestaña
            screen_widget = self.bottom_nav.screens[screen_name]
            if hasattr(screen_widget, 'show_main_screen'):
                screen_widget.show_main_screen()
            elif hasattr(screen_widget, 'mostrar_menu_reportes'):
                screen_widget.mostrar_menu_reportes()
            elif hasattr(screen_widget, 'reset_to_main'):
                screen_widget.reset_to_main()

            self.content_container.add_widget(screen_widget)

            # Actualizar también los colores de los botones sin crear bucle recursivo
            if hasattr(self, 'bottom_nav'):
                self.update_navigation_buttons_only(screen_name)

    def update_navigation_buttons_only(self, active_tab):
        """Actualiza solo los colores de los botones de navegación sin cambiar pantallas"""
        # Actualizar colores de botones directamente sin recursión
        for name, (button, label) in self.bottom_nav.buttons.items():
            if name == active_tab:
                # Pestaña activa - naranja
                button.icon_color = [1, 0.6, 0, 1]
                label.text_color = [1, 0.6, 0, 1]
            else:
                # Pestaña inactiva - blanco
                button.icon_color = [1, 1, 1, 0.7]
                label.text_color = [1, 1, 1, 0.7]
            
    def go_back_to_main(self, tab_name):
        """Volver a la pantalla principal de una pestaña"""
        if hasattr(self.bottom_nav.screens[tab_name], 'show_main_screen'):
            self.bottom_nav.screens[tab_name].show_main_screen()
            
    def show_channel_list(self):
        """Método de compatibilidad para chat screen"""
        if hasattr(self.chat_screen, 'show_main_screen'):
            self.chat_screen.show_main_screen()
            
    def load_channels(self):
        """Método de compatibilidad para recargar canales"""
        if hasattr(self.chat_screen, 'load_channels'):
            self.chat_screen.load_channels()


class MainScreen(MDScreen):
    """Pantalla principal que contiene el MainLayout"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        self.main_layout = MainLayout()
        self.add_widget(self.main_layout)

    def on_enter(self):
        """Se ejecuta al entrar a la pantalla principal"""
        # Reconfigurar para el nivel actual del usuario
        self.main_layout.configurar_para_nivel_usuario()


class EmpresaLimpiezaApp(MDApp):
    """Aplicación principal con sistema de autenticación v8.0"""

    # Variables de sesión globales
    nivel_usuario = StringProperty('')
    token_sesion = StringProperty('')
    nombre_usuario = StringProperty('')
    user_data = DictProperty({})

    # Configuración del servidor
    base_url = StringProperty('https://chat-cv1i.onrender.com')

    def build(self):
        # Configurar tema
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.accent_palette = "Orange"
        self.title = "CORPOTACHIRA v8.0"

        # Configurar ventana móvil
        Window.size = (360, 640)
        Window.minimum_width = 300
        Window.minimum_height = 500

        # Crear Screen Manager con todas las pantallas
        screen_manager = MDScreenManager()

        # Pantallas de autenticación
        screen_manager.add_widget(RoleSelectionScreen())
        screen_manager.add_widget(LoginScreen())
        screen_manager.add_widget(LoginObreroScreen())

        # Pantalla principal
        screen_manager.add_widget(MainScreen())

        # Crear contenedor root
        root_screen = MDScreen()
        root_screen.screen_manager = screen_manager
        root_screen.add_widget(screen_manager)

        # Iniciar en pantalla de selección de rol
        screen_manager.current = 'role_selection'

        return root_screen

    def verificar_sesion_activa(self):
        """
        Verifica si hay una sesión activa válida
        """
        if self.token_sesion and self.nivel_usuario:
            print(f"✅ Sesión activa: {self.nombre_usuario} ({self.nivel_usuario})")
            return True
        else:
            print("❌ No hay sesión activa")
            return False

    def navegar_a_principal_segun_nivel(self):
        """
        Navega a la pantalla principal y configura según el nivel del usuario
        SIEMPRE inicia en Chat después del login
        """
        try:
            self.root.screen_manager.current = 'main'

            # Configurar el layout para el nivel actual
            main_screen = self.root.screen_manager.get_screen('main')
            if hasattr(main_screen, 'main_layout'):
                # FORZAR a Chat en login inicial (resetear estado)
                main_screen.main_layout.current_tab = "chat"
                main_screen.main_layout.content_container.clear_widgets()

                main_screen.main_layout.configurar_para_nivel_usuario()

        except Exception as e:
            print(f"❌ Error navegando a principal: {e}")

    def logout(self):
        """
        Método público para cerrar sesión
        """
        try:
            # Limpiar variables de sesión
            self.nivel_usuario = ''
            self.token_sesion = ''
            self.user_data = {}
            self.nombre_usuario = ''

            # Resetear MainLayout para próximo login
            if hasattr(self.root, 'screen_manager'):
                try:
                    main_screen = self.root.screen_manager.get_screen('main')
                    if hasattr(main_screen, 'main_layout'):
                        # Resetear a Chat para próximo login
                        main_screen.main_layout.current_tab = "chat"
                        main_screen.main_layout.content_container.clear_widgets()
                except:
                    pass

            # Navegar a selección de rol
            self.root.screen_manager.current = 'role_selection'

        except Exception as e:
            print(f"❌ Error en logout: {e}")

    def get_auth_headers(self):
        """
        Obtiene los headers de autenticación para las peticiones API

        Returns:
            dict: Headers con token de autorización
        """
        if self.token_sesion:
            return {
                'Authorization': f'Bearer {self.token_sesion}',
                'Content-Type': 'application/json'
            }
        else:
            return {'Content-Type': 'application/json'}


if __name__ == "__main__":
    EmpresaLimpiezaApp().run()