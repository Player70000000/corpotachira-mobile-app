from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.screen import MDScreen
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDRaisedButton

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import API_BASE_URL

# Importar módulos especializados
from .reportes_modules import (
    ReportesObrerosManager,
    ReportesModeradoresManager,
    ReportesGeneralesManager,
    ReportCard
)




class ReportesScreen(MDBoxLayout):
    """Coordinador principal del módulo de reportes modular"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.main_layout = None

        # Inicializar gestores especializados
        self.reportes_obreros = ReportesObrerosManager(self)
        self.reportes_moderadores = ReportesModeradoresManager(self)
        self.reportes_generales = ReportesGeneralesManager(self)

        self.setup_ui()

    def setup_ui(self):
        """Configurar interfaz del menú principal de reportes"""
        # Screen manager para navegación
        self.screen_manager = MDScreenManager()

        # Pantalla del menú principal
        self.main_screen = MDScreen(name="menu_principal")
        self.setup_menu_principal()

        self.screen_manager.add_widget(self.main_screen)
        self.add_widget(self.screen_manager)

    def setup_menu_principal(self):
        """Configurar menú principal con las 3 opciones de reportes"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")

        # Top bar
        top_bar = MDTopAppBar(
            title="Reportes CORPOTACHIRA",
            right_action_items=[["dots-vertical", lambda x: self.show_options_menu(x)]]
        )

        # Contenido del menú
        content_scroll = MDScrollView()
        content_layout = MDBoxLayout(orientation="vertical", spacing="15dp", adaptive_height=True)

        # Las 3 opciones principales de reportes (nuevo orden)
        reportes_opciones = [
            {
                "titulo": "📈 Reportes Generales",
                "descripcion": "Reportes de actividades de cuadrillas con gestión de herramientas",
                "color": (1, 0.95, 1, 1),
                "accion": self.mostrar_reportes_generales
            },
            {
                "titulo": "👤 Reportes de Moderadores",
                "descripcion": "Análisis específico de moderadores y comparaciones",
                "color": (0.95, 0.95, 1, 1),
                "accion": self.mostrar_reportes_moderadores
            },
            {
                "titulo": "👷‍♂️ Reportes de Obreros",
                "descripcion": "Estadísticas detalladas, distribución de tallas y análisis de obreros",
                "color": (0.95, 1, 0.95, 1),
                "accion": self.mostrar_reportes_obreros
            }
        ]

        for opcion in reportes_opciones:
            reporte_card = ReportCard(
                titulo=opcion["titulo"],
                descripcion=opcion["descripcion"],
                color=opcion["color"],
                on_click=opcion["accion"]
            )
            content_layout.add_widget(reporte_card)

        content_scroll.add_widget(content_layout)

        layout.add_widget(top_bar)
        layout.add_widget(content_scroll)

        self.main_screen.add_widget(layout)

    def mostrar_reportes_obreros(self):
        """Mostrar módulo de reportes de obreros"""
        self.reportes_obreros.mostrar_reportes_obreros()

    def mostrar_reportes_moderadores(self):
        """Mostrar módulo de reportes de moderadores"""
        self.reportes_moderadores.mostrar_reportes_moderadores()

    def mostrar_reportes_generales(self):
        """Mostrar módulo de reportes generales"""
        self.reportes_generales.mostrar_reportes_generales()

    def mostrar_menu_reportes(self):
        """Volver al menú principal de reportes"""
        self.clear_widgets()
        self.setup_ui()

    def show_main_screen(self):
        """Mostrar la pantalla principal de reportes (compatibilidad)"""
        self.mostrar_menu_reportes()

    def show_options_menu(self, button):
        """Mostrar menú desplegable con opciones"""
        # Limpiar menú anterior para optimizar memoria
        if hasattr(self, 'menu') and self.menu:
            self.menu.dismiss()
            self.menu = None

        # Crear elementos del menú
        menu_items = [
            {
                "text": "Cerrar Sesión",
                "icon": "logout",
                "on_release": lambda x="cerrar_sesion": self.handle_menu_option(x),
            },
            {
                "text": "Información Personal",
                "icon": "account-circle",
                "on_release": lambda x="info_personal": self.handle_menu_option(x),
            },
        ]

        # Crear y mostrar el menú
        self.menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()

    def handle_menu_option(self, option):
        """Manejar las opciones del menú desplegable"""
        self.menu.dismiss()

        if option == "cerrar_sesion":
            # Mostrar diálogo de confirmación antes de cerrar sesión v8.1
            self.show_logout_confirmation_dialog()
        elif option == "info_personal":
            self.navegar_a_info_personal()

    def show_dialog(self, title, text):
        """Mostrar dialog informativo"""
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: dialog.dismiss()
                )
            ]
        )
        dialog.open()

    def navegar_a_info_personal(self):
        """Navegar a la pantalla de información personal"""
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()

            # Navegar a través del screen manager
            if hasattr(app.root, 'screen_manager'):
                # Primero agregar la pantalla si no existe
                try:
                    info_screen = app.root.screen_manager.get_screen('info_personal')
                except:
                    # Si no existe, la creamos
                    from screens.info_personal_screen import InfoPersonalScreen
                    info_screen = InfoPersonalScreen()
                    app.root.screen_manager.add_widget(info_screen)

                # La pestaña de origen se detectará automáticamente en on_enter()

                # Navegar a la pantalla
                app.root.screen_manager.current = 'info_personal'
            else:
                print("❌ No se pudo acceder al screen manager")

        except Exception as e:
            print(f"❌ Error navegando a información personal: {e}")
            self.show_dialog("Error", "No se pudo abrir la información personal")

    def show_logout_confirmation_dialog(self):
        """
        Mostrar diálogo de confirmación para cerrar sesión v8.1
        Con opciones: Cancelar y Salir
        """
        from kivymd.uix.button import MDFlatButton

        # Crear botones del diálogo
        cancel_button = MDFlatButton(
            text="Cancelar",
            on_release=lambda x: self.logout_dialog.dismiss()
        )

        logout_button = MDRaisedButton(
            text="Salir",
            md_bg_color=[1, 0.3, 0.3, 1],  # Rojo para acción de salida
            on_release=lambda x: self.confirm_logout()
        )

        # Crear diálogo de confirmación
        self.logout_dialog = MDDialog(
            title="Confirmar Cierre de Sesión",
            text="¿Estás seguro de que deseas cerrar tu sesión?\n\nTendrás que volver a iniciar sesión para acceder nuevamente.",
            buttons=[cancel_button, logout_button],
            size_hint=(0.8, None)
        )

        self.logout_dialog.open()

    def confirm_logout(self):
        """
        Ejecutar cierre de sesión después de confirmación v8.1
        """
        # Cerrar diálogo de confirmación
        self.logout_dialog.dismiss()

        try:
            from kivymd.app import MDApp
            from kivymd.uix.snackbar import MDSnackbar
            from kivymd.uix.label import MDLabel
            from kivy.metrics import dp

            app = MDApp.get_running_app()

            # Limpiar variables de sesión
            app.nivel_usuario = ''
            app.token_sesion = ''
            app.user_data = {}
            app.nombre_usuario = ''

            # Navegar a pantalla de selección de rol
            if hasattr(app.root, 'screen_manager'):
                app.root.screen_manager.current = 'role_selection'

            # Mostrar feedback visual (snackbar verde)
            snackbar = MDSnackbar(
                MDLabel(
                    text="Sesión cerrada exitosamente",
                    theme_text_color="Custom",
                    text_color=(1, 1, 1, 1)
                ),
                y=dp(24),
                pos_hint={"center_x": 0.5},
                size_hint_x=0.8,
                md_bg_color=(0.2, 0.7, 0.2, 1),  # Verde
                duration=2
            )
            snackbar.open()

        except Exception as e:
            print(f"❌ Error cerrando sesión: {e}")
            self.show_dialog(
                "Error",
                "Ocurrió un error al intentar cerrar sesión."
            )