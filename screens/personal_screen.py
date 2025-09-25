"""
Personal Screen - Coordinador principal para gestión de personal
Versión modularizada que utiliza managers especializados
"""

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.menu import MDDropdownMenu
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivy.metrics import dp

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import API_BASE_URL

# Importar managers modulares
from screens.personal_modules import (
    ObrerosManager,
    ModeradoresManager,
    CuadrillasManager,
    ui_components,
    utils
)


class PersonalScreen(MDBoxLayout):
    """
    Pantalla principal de gestión de personal
    Coordinador que orquesta los managers especializados
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.main_layout = None  # Referencia al layout principal

        # Inicializar managers especializados
        self.cuadrillas_manager = CuadrillasManager(main_screen=self)
        self.moderadores_manager = ModeradoresManager(main_screen=self)
        self.obreros_manager = ObrerosManager(main_screen=self)

        # Estado actual
        self.current_manager = None

        self.setup_ui()

    def setup_ui(self):
        """Configurar interfaz principal"""
        # Screen manager para diferentes vistas
        self.screen_manager = MDScreenManager()

        # Pantalla del menú principal
        self.main_screen = MDScreen(name="main_menu")
        self.setup_main_menu()

        # Agregar pantalla principal al manager
        self.screen_manager.add_widget(self.main_screen)
        self.screen_manager.current = "main_menu"

        # Agregar screen manager al layout principal
        self.add_widget(self.screen_manager)

    def setup_main_menu(self):
        """Configurar menú principal de gestión de personal CON CONTROL DE PERMISOS v8.0"""
        layout = MDBoxLayout(orientation="vertical", padding="10dp", spacing="10dp")

        # Top bar
        top_bar = MDTopAppBar(
            title="Gestión de Personal",
            right_action_items=[["dots-vertical", lambda x: self.show_options_menu(x)]]
        )
        layout.add_widget(top_bar)

        # Contenedor de cards (guardar referencia para reconfiguración dinámica)
        self.cards_container = MDBoxLayout(
            orientation="vertical",
            spacing="15dp",
            adaptive_height=True
        )

        # Configurar cards inicialmente
        self.reconfigure_cards_for_current_user()


        # Scroll container para las cards
        self.scroll = MDScrollView()
        self.scroll.add_widget(self.cards_container)
        layout.add_widget(self.scroll)

        self.main_screen.add_widget(layout)

    def reconfigure_cards_for_current_user(self):
        """
        Reconfigurar las cards según el nivel actual del usuario
        Este método se llama dinámicamente cada vez que se accede a Personal
        """
        # Limpiar contenedor de cards
        self.cards_container.clear_widgets()

        # Obtener nivel del usuario ACTUAL
        user_level = self.get_user_level()

        # Card de Cuadrillas (Admin + Moderador)
        if user_level in ['admin', 'moderador']:
            cuadrillas_card = self.create_module_card(
                title="👷‍♂️ Gestión de Cuadrillas",
                description="Crear, editar y administrar cuadrillas de trabajo.\nOrganiza los equipos por actividades.",
                color=[0.95, 0.95, 1, 1],  # Ligero tinte azul
                callback=self.switch_to_cuadrillas
            )
            self.cards_container.add_widget(cuadrillas_card)

        # Card de Moderadores (SOLO ADMIN)
        if user_level == 'admin':
            moderadores_card = self.create_module_card(
                title="👤 Gestión de Moderadores",
                description="Registrar y administrar moderadores de cuadrilla.\nSupervisa y coordina los equipos.",
                color=[0.95, 1, 0.95, 1],  # Ligero tinte verde
                callback=self.switch_to_moderadores
            )
            self.cards_container.add_widget(moderadores_card)

        # Card de Obreros (Admin + Moderador)
        if user_level in ['admin', 'moderador']:
            obreros_card = self.create_module_card(
                title="👷 Gestión de Obreros",
                description="Registrar y administrar obreros de la empresa.\nMantén el directorio de personal actualizado.",
                color=[1, 1, 0.95, 1],  # Ligero tinte amarillo
                callback=self.switch_to_obreros
            )
            self.cards_container.add_widget(obreros_card)

        # Si no hay cards (usuario sin permisos), mostrar mensaje
        if self.cards_container.children == []:
            no_access_card = self.create_info_card(
                title="⚠️ Sin Permisos",
                description="No tienes permisos para acceder a la gestión de personal.\nContacta al administrador.",
                color=[1, 0.95, 0.95, 1]  # Tinte rojo claro
            )
            self.cards_container.add_widget(no_access_card)

    def get_user_level(self):
        """
        Obtiene el nivel del usuario actual

        Returns:
            str: Nivel del usuario ('admin', 'moderador', 'obrero')
        """
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            nivel = getattr(app, 'nivel_usuario', 'obrero')
            return nivel
        except Exception as e:
            print(f"❌ Error obteniendo nivel de usuario: {e}")
            return 'obrero'

    def create_info_card(self, title, description, color):
        """
        Crear card informativa (no clickeable)

        Args:
            title (str): Título de la card
            description (str): Descripción
            color (list): Color de fondo

        Returns:
            MDCard: Card informativa
        """
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height="140dp",
            padding="20dp",
            spacing="10dp",
            elevation=3,
            md_bg_color=color
        )

        # Título
        title_label = MDLabel(
            text=title,
            font_style="H6",
            theme_text_color="Primary",
            size_hint_y=None,
            height="40dp"
        )
        card.add_widget(title_label)

        # Descripción
        desc_label = MDLabel(
            text=description,
            font_style="Body2",
            theme_text_color="Secondary",
            text_size=(None, None),
            adaptive_height=True
        )
        card.add_widget(desc_label)

        return card

    def create_module_card(self, title, description, color, callback):
        """Crear card para un módulo del sistema - TARJETA CLICKEABLE COMPLETA"""
        card = MDCard(
            orientation="vertical",
            size_hint_y=None,
            height="140dp",
            padding="20dp",
            spacing="10dp",
            elevation=3,
            md_bg_color=color,  # Color de fondo según módulo
            on_release=lambda x: callback()  # ← TODA LA TARJETA ES CLICKEABLE
        )

        # Título
        title_label = MDLabel(
            text=title,
            font_style="H6",
            theme_text_color="Primary",
            size_hint_y=None,
            height="40dp"
        )
        card.add_widget(title_label)

        # Descripción
        desc_label = MDLabel(
            text=description,
            font_style="Body2",
            theme_text_color="Secondary",
            text_size=(None, None)
        )
        card.add_widget(desc_label)

        # Tip visual (sin botón)
        tip_label = MDLabel(
            text="💡 Toca la tarjeta para acceder",
            font_size="12sp",
            theme_text_color="Hint",
            size_hint_y=None,
            height="20dp",
            halign="center"
        )
        card.add_widget(tip_label)

        return card

    def switch_to_cuadrillas(self):
        """Cambiar a gestión de cuadrillas"""
        print("🚧 Cambiando a gestión de cuadrillas...")
        self.current_manager = 'cuadrillas'
        self._switch_to_manager_screen(self.cuadrillas_manager)

    def switch_to_moderadores(self):
        """Cambiar a gestión de moderadores"""
        print("👤 Cambiando a gestión de moderadores...")
        self.current_manager = 'moderadores'
        self._switch_to_manager_screen(self.moderadores_manager)

    def switch_to_obreros(self):
        """Cambiar a gestión de obreros"""
        print("👷 Cambiando a gestión de obreros...")
        self.current_manager = 'obreros'
        self._switch_to_manager_screen(self.obreros_manager)

    def _switch_to_manager_screen(self, manager):
        """Cambiar a pantalla de manager específico"""
        try:
            # Remover pantalla del manager si ya existe
            manager_screen_name = f"{self.current_manager}_screen"

            if self.screen_manager.has_screen(manager_screen_name):
                self.screen_manager.remove_widget(
                    self.screen_manager.get_screen(manager_screen_name)
                )

            # Crear nueva pantalla del manager
            manager_screen = MDScreen(name=manager_screen_name)
            manager_layout = manager.create_main_layout()
            manager_screen.add_widget(manager_layout)

            # Agregar y cambiar a la pantalla
            self.screen_manager.add_widget(manager_screen)
            self.screen_manager.current = manager_screen_name

            print(f"✅ Cambiado exitosamente a {self.current_manager}")

        except Exception as e:
            print(f"❌ Error al cambiar a {self.current_manager}: {e}")
            self.show_error_dialog(f"Error al abrir módulo: {str(e)}")

    def go_back_to_main(self, from_tab=None):
        """Volver al menú principal desde cualquier manager"""
        print("🔙 Volviendo al menú principal...")

        try:
            # Cambiar a pantalla principal
            self.screen_manager.current = "main_menu"

            # Limpiar manager actual
            self.current_manager = None

            print("✅ Regresado al menú principal exitosamente")

        except Exception as e:
            print(f"❌ Error al regresar al menú principal: {e}")

    def show_main_screen(self):
        """Mostrar pantalla principal - método de compatibilidad"""
        self.go_back_to_main()

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

    def show_error_dialog(self, message):
        """Mostrar dialog de error"""
        dialog = ui_components.create_error_dialog(message)
        dialog.open()

    def show_success_dialog(self, message, callback=None):
        """Mostrar dialog de éxito"""
        dialog = ui_components.create_success_dialog(message, callback)
        dialog.open()

    # ===========================================
    # MÉTODOS DE COMPATIBILIDAD CON MAIN.PY
    # ===========================================

    def switch_screen(self, screen_name):
        """Método de compatibilidad para navegación externa"""
        if screen_name == "main_menu":
            self.go_back_to_main()
        elif screen_name == "cuadrillas":
            self.switch_to_cuadrillas()
        elif screen_name == "moderadores":
            self.switch_to_moderadores()
        elif screen_name == "obreros":
            self.switch_to_obreros()

    def get_current_screen_name(self):
        """Obtener nombre de pantalla actual"""
        if self.current_manager:
            return f"{self.current_manager}_screen"
        return "main_menu"

    # ===========================================
    # MÉTODOS PARA ACCESO A MANAGERS EXTERNOS
    # ===========================================

    def get_cuadrillas_manager(self):
        """Obtener manager de cuadrillas"""
        return self.cuadrillas_manager

    def get_moderadores_manager(self):
        """Obtener manager de moderadores"""
        return self.moderadores_manager

    def get_obreros_manager(self):
        """Obtener manager de obreros"""
        return self.obreros_manager

    def reload_all_data(self):
        """Recargar datos de todos los managers"""
        try:
            if hasattr(self.cuadrillas_manager, 'load_cuadrillas_data'):
                self.cuadrillas_manager.load_cuadrillas_data()
            if hasattr(self.moderadores_manager, 'load_moderadores_data'):
                self.moderadores_manager.load_moderadores_data()
            if hasattr(self.obreros_manager, 'load_obreros_data'):
                self.obreros_manager.load_obreros_data()

            print("✅ Datos de todos los managers recargados")

        except Exception as e:
            print(f"❌ Error al recargar datos: {e}")
            self.show_error_dialog(f"Error al recargar datos: {str(e)}")


# ===========================================
# CLASES DE COMPATIBILIDAD (DEPRECATED)
# ===========================================

class CuadrillaListItem:
    """Clase de compatibilidad - DEPRECATED - Usar CuadrillasManager"""
    def __init__(self, *args, **kwargs):
        print("⚠️ DEPRECATED: CuadrillaListItem - Usar CuadrillasManager")
        pass

class EmpleadoListItem:
    """Clase de compatibilidad - DEPRECATED - Usar ObrerosManager/ModeradoresManager"""
    def __init__(self, *args, **kwargs):
        print("⚠️ DEPRECATED: EmpleadoListItem - Usar managers especializados")
        pass

class CuadrillasManagementScreen:
    """Clase de compatibilidad - DEPRECATED - Usar CuadrillasManager"""
    def __init__(self, *args, **kwargs):
        print("⚠️ DEPRECATED: CuadrillasManagementScreen - Usar CuadrillasManager")
        pass

class EmpleadosManagementScreen:
    """Clase de compatibilidad - DEPRECATED - Usar managers especializados"""
    def __init__(self, *args, **kwargs):
        print("⚠️ DEPRECATED: EmpleadosManagementScreen - Usar managers especializados")
        pass