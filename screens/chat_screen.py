import requests
from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.label import MDLabel
from kivymd.uix.card import MDCard
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.textfield import MDTextField
from kivymd.uix.dialog import MDDialog
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.screen import MDScreen
from kivymd.uix.screenmanager import MDScreenManager
from kivymd.uix.menu import MDDropdownMenu
from kivy.clock import Clock
from kivy.metrics import dp

import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(__file__)))
from config import API_BASE_URL, DEFAULT_USERNAME
# NUEVO v8.0: Cliente HTTP autenticado
from utils.auth_client import auth_client


class ChannelListItem(OneLineListItem):
    def __init__(self, channel_name, on_select_callback, **kwargs):
        super().__init__(**kwargs)
        self.text = f"{channel_name}"
        self.channel_name = channel_name
        self.on_select_callback = on_select_callback
        self.on_release = self.select_channel
        
    def select_channel(self):
        self.on_select_callback(self.channel_name)


class ChatChannelScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "chat_channel"
        self.channel_name = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # Top bar con back button
        self.top_bar = MDTopAppBar(
            title="Selecciona un canal",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["dots-vertical", lambda x: self.show_channel_options_menu(x)]]
        )
        
        # Área de mensajes sin tarjeta contenedora
        self.messages_container = MDBoxLayout(
            orientation="vertical",
            size_hint_y=0.85,
            padding="10dp"
        )

        self.messages_layout = MDBoxLayout(
            orientation="vertical",
            adaptive_height=True,
            size_hint_y=None,  # CRÍTICO para adaptive_height
            spacing="5dp"
        )

        self.messages_scroll = MDScrollView(
            do_scroll_x=False,  # Sin scroll horizontal
            effect_cls="ScrollEffect"  # Efecto de scroll estándar
        )
        self.messages_scroll.add_widget(self.messages_layout)
        self.messages_container.add_widget(self.messages_scroll)
        
        # Línea divisoria pronunciada antes del área de entrada
        class ProminentSeparatorLine(MDBoxLayout):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint_y = None
                self.height = "3dp"  # Más gruesa para ser pronunciada
                with self.canvas:
                    from kivy.graphics import Color, Rectangle
                    Color(0.7, 0.7, 0.7, 1)  # Gris más oscuro y visible
                    self.rect = Rectangle(size=self.size, pos=self.pos)
                self.bind(size=self._update_rect, pos=self._update_rect)

            def _update_rect(self, instance, value):
                self.rect.size = instance.size
                self.rect.pos = instance.pos

        separator = ProminentSeparatorLine()

        # Área de entrada de mensajes CON CONTROL DE NIVEL v8.0
        self.input_layout = MDBoxLayout(
            size_hint_y=None,
            height="60dp",
            spacing="10dp",
            padding=["10dp", "5dp"]
        )

        self.message_input = MDTextField(
            hint_text="Escribe un mensaje...",
            size_hint_x=0.8,
            multiline=False,
            on_text_validate=self.send_message
        )

        self.send_button = MDIconButton(
            icon="send",
            theme_icon_color="Primary",
            on_release=self.send_message
        )

        self.input_layout.add_widget(self.message_input)
        self.input_layout.add_widget(self.send_button)

        # Mensaje de modo lectura para obreros
        self.read_only_message = MDBoxLayout(
            size_hint_y=None,
            height="50dp",
            padding=["15dp", "10dp"]
        )

        read_only_label = MDLabel(
            text="📖 Modo lectura - Solo puedes ver mensajes",
            font_style="Caption",
            theme_text_color="Secondary",
            halign="center"
        )
        self.read_only_message.add_widget(read_only_label)

        layout.add_widget(self.top_bar)
        layout.add_widget(self.messages_container)
        layout.add_widget(separator)  # Línea divisoria pronunciada

        # Configurar área de entrada según el nivel del usuario
        self.configure_input_area_for_user_level()

        # Siempre agregar el layout de input, pero configurar su visibilidad
        layout.add_widget(self.input_layout)
        
        self.add_widget(layout)
        
    def set_channel(self, channel_name):
        self.channel_name = channel_name
        self.top_bar.title = f"{channel_name}"
        self._scroll_was_enabled = False  # Inicializar estado de scroll
        self.load_messages()
        # Auto-actualizar cada 10 segundos para mejor rendimiento
        self.auto_update_event = Clock.schedule_interval(self.auto_load_messages, 10)
        
    def update_channel_name(self, old_name, new_name):
        """Actualizar solo el nombre del canal si coincide"""
        if self.channel_name == old_name:
            self.channel_name = new_name
            self.top_bar.title = f"{new_name}"
    
    def stop_auto_update(self):
        """Detener actualización automática para mejorar rendimiento"""
        if hasattr(self, 'auto_update_event') and self.auto_update_event:
            Clock.unschedule(self.auto_update_event)
            self.auto_update_event = None
    
    def cleanup(self):
        """Limpiar recursos y referencias para liberar memoria"""
        self.stop_auto_update()
        if hasattr(self, 'messages_layout'):
            self.messages_layout.clear_widgets()
        self.channel_name = None
        self._last_message_count = 0
        
    def auto_load_messages(self, dt):
        # Solo auto-scroll si el usuario está en el pie (no navegando arriba)
        is_at_bottom = self.messages_scroll.scroll_y <= 0.1  # Tolerancia de 10%
        self.load_messages(auto_scroll=is_at_bottom)
        
    def load_messages(self, auto_scroll=True):
        if not self.channel_name:
            return

        try:
            # NUEVO v8.0: Usar cliente autenticado
            result = auth_client.get(f"/mensajes/{self.channel_name}", timeout=3)
            if result['success']:
                data = result['data']
                messages = data.get('mensajes', [])

                # Solo actualizar si hay cambios reales para mejorar rendimiento
                if not hasattr(self, '_last_message_count') or len(messages) != self._last_message_count:
                    self._last_message_count = len(messages)
                    self.messages_layout.clear_widgets()

                    if not messages:
                        no_messages_label = MDLabel(
                            text="No hay mensajes en este canal",
                            theme_text_color="Secondary",
                            halign="center",
                            size_hint_y=None,
                            height="40dp"
                        )
                        self.messages_layout.add_widget(no_messages_label)
                    else:
                        for msg in messages:
                            message_text = msg.get('mensaje', '')
                            sender = msg.get('usuario', '')

                            # Crear contenedor para el mensaje con altura adaptativa
                            message_container = MDBoxLayout(
                                orientation="horizontal",
                                adaptive_height=True,
                                size_hint_y=None,
                                spacing="10dp",
                                padding=["10dp", "5dp"]
                            )

                            # Determinar si es mensaje propio
                            is_own_message = sender == DEFAULT_USERNAME

                            if is_own_message:
                                # Mensaje propio - burbuja azul a la derecha
                                spacer_left = MDBoxLayout(size_hint_x=0.3)  # Espacio izquierdo
                                message_card = MDCard(
                                    md_bg_color=[0.2, 0.6, 1, 1],  # Azul para mensajes propios
                                    elevation=0,  # Sin sombra
                                    padding="12dp",
                                    size_hint_x=0.7,
                                    size_hint_y=None,
                                    adaptive_height=True
                                )
                                message_label = MDLabel(
                                    text=message_text,
                                    theme_text_color="Custom",
                                    text_color=[1, 1, 1, 1],  # Texto blanco
                                    size_hint_y=None,
                                    halign="left",
                                    valign="top"
                                )
                                # Configurar text wrapping
                                def set_text_size_own(instance, value):
                                    instance.text_size = (instance.width, None)
                                message_label.bind(width=set_text_size_own)
                                message_label.bind(texture_size=message_label.setter('size'))

                                message_card.add_widget(message_label)
                                message_container.add_widget(spacer_left)
                                message_container.add_widget(message_card)
                            else:
                                # Mensaje de otros - burbuja gris a la izquierda
                                message_card = MDCard(
                                    md_bg_color=[0.9, 0.9, 0.9, 1],  # Gris claro para otros
                                    elevation=0,  # Sin sombra
                                    padding="12dp",
                                    size_hint_x=0.7,
                                    size_hint_y=None,
                                    adaptive_height=True
                                )
                                message_label = MDLabel(
                                    text=message_text,
                                    theme_text_color="Primary",
                                    size_hint_y=None,
                                    halign="left",
                                    valign="top"
                                )
                                # Configurar text wrapping
                                def set_text_size_other(instance, value):
                                    instance.text_size = (instance.width, None)
                                message_label.bind(width=set_text_size_other)
                                message_label.bind(texture_size=message_label.setter('size'))

                                message_card.add_widget(message_label)
                                spacer_right = MDBoxLayout(size_hint_x=0.3)  # Espacio derecho
                                message_container.add_widget(message_card)
                                message_container.add_widget(spacer_right)

                            self.messages_layout.add_widget(message_container)

                    # Verificar si necesita scroll y configurarlo dinámicamente
                    self.update_scroll_behavior()

                    # Solo hacer scroll automático si se solicita
                    if auto_scroll:
                        self.scroll_to_bottom()
            else:
                # Error de autenticación o permisos - el cliente ya maneja redirección
                print(f"Error autenticado al cargar mensajes: {result.get('message', 'Error desconocido')}")
        except Exception as e:
            print(f"Error loading messages: {e}")

    def update_scroll_behavior(self):
        """Habilitar/deshabilitar scroll según si hay suficiente contenido"""
        def check_scroll(*args):
            # Obtener el número de mensajes
            message_count = len(self.messages_layout.children)

            # Enfoque conservador: una vez habilitado, mantener habilitado
            if hasattr(self, '_scroll_was_enabled') and self._scroll_was_enabled:
                # Si ya estaba habilitado antes, mantenerlo habilitado
                self.messages_scroll.do_scroll_y = True
                return

            # Solo evaluar si deshabilitar scroll al principio o con muy pocos mensajes
            if message_count <= 2:
                # Con 2 mensajes o menos, verificar si realmente necesita scroll
                if self.messages_layout.height <= self.messages_scroll.height * 0.8:
                    # Definitivamente poco contenido - deshabilitar scroll
                    self.messages_scroll.do_scroll_y = False
                    self.messages_scroll.scroll_y = 0
                    self._scroll_was_enabled = False
                else:
                    # Suficiente contenido - habilitar y recordar
                    self.messages_scroll.do_scroll_y = True
                    self._scroll_was_enabled = True
            else:
                # Con 3+ mensajes, siempre habilitar y recordar
                self.messages_scroll.do_scroll_y = True
                self._scroll_was_enabled = True

        # Verificar después de que se actualicen los tamaños
        Clock.schedule_once(check_scroll, 0.1)
            
    def scroll_to_bottom(self):
        if self.messages_layout.children:
            def do_scroll(*args):
                # Scroll al final - probemos ambas direcciones para asegurar
                self.messages_scroll.scroll_y = 0
                # También intentar forzar scroll al final del contenido
                if hasattr(self.messages_scroll, 'scroll_to'):
                    self.messages_scroll.scroll_to(self.messages_layout.children[0])

            # Múltiples intentos para garantizar el scroll correcto
            Clock.schedule_once(do_scroll, 0.1)
            Clock.schedule_once(do_scroll, 0.2)
            Clock.schedule_once(do_scroll, 0.3)
            
    def send_message(self, instance=None):
        # Verificar si el usuario puede enviar mensajes v8.0
        if not hasattr(self, 'can_send_messages') or not self.can_send_messages:
            self.show_dialog("Acceso Restringido", "No tienes permisos para enviar mensajes.\nEstás en modo solo lectura.")
            return

        if not self.channel_name:
            self.show_dialog("Error", "No hay canal seleccionado")
            return

        text = self.message_input.text.strip()
        if not text:
            return
            
        data = {
            "usuario": DEFAULT_USERNAME,
            "mensaje": text,
            "canal": self.channel_name
        }
        
        try:
            # NUEVO v8.0: Usar cliente autenticado
            result = auth_client.post("/enviar", json_data=data, timeout=5)
            if result['success']:
                self.message_input.text = ""
                self.load_messages()
                # Scroll adicional después de que el servidor responda
                Clock.schedule_once(lambda dt: self.scroll_to_bottom(), 0.5)
            else:
                error_msg = result.get('message', 'No se pudo enviar el mensaje')
                self.show_dialog("Error", error_msg)
        except Exception:
            self.show_dialog("Error", "Error de conexión al enviar mensaje")
            
    def go_back(self):
        # Buscar el layout principal navegando hacia arriba
        current = self.parent
        while current:
            if hasattr(current, 'show_channel_list'):
                current.show_channel_list()
                return
            elif hasattr(current, 'main_layout') and current.main_layout:
                current.main_layout.show_channel_list()
                return
            current = current.parent
        
    def show_dialog(self, title, text):
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

    def configure_input_area_for_user_level(self):
        """
        Configura el área de entrada de mensajes según el nivel del usuario v8.0
        Oculta completamente el input para obreros usando opacity y height
        """
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()

            # Verificar si el nivel de usuario está disponible
            if not hasattr(app, 'nivel_usuario') or app.nivel_usuario in [None, '']:
                # Por defecto, ocultar campo hasta saber el nivel real
                self.can_send_messages = False
                self.input_layout.opacity = 0
                self.input_layout.size_hint_y = None
                self.input_layout.height = "0dp"
                return

            user_level = app.nivel_usuario

            if user_level == 'obrero':
                # Obreros: OCULTAR completamente el área de entrada
                self.can_send_messages = False
                self.input_layout.opacity = 0
                self.input_layout.size_hint_y = None
                self.input_layout.height = "0dp"
            else:
                # Admin y moderadores: MOSTRAR área de entrada normalmente
                self.can_send_messages = True
                self.input_layout.opacity = 1
                self.input_layout.size_hint_y = None
                self.input_layout.height = "60dp"  # Altura un poco más grande para mejor UX

        except Exception as e:
            print(f"❌ Error configurando nivel de usuario en chat: {e}")
            # Por defecto, mostrar campo (modo fallback)
            self.can_send_messages = True
            self.input_layout.opacity = 1
            self.input_layout.size_hint_y = None
            self.input_layout.height = "60dp"

    # ELIMINADO: get_current_input_widget() ya no es necesario
    # La visibilidad se controla directamente en configure_input_area_for_user_level()

    def show_channel_options_menu(self, button):
        """Mostrar menú de opciones del canal actual CON CONTROL DE PERMISOS v8.0"""
        if not self.channel_name:
            self.show_dialog("Error", "No hay canal seleccionado")
            return

        # Verificar nivel del usuario
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            user_level = getattr(app, 'nivel_usuario', 'obrero')
        except Exception:
            user_level = 'obrero'

        # Limpiar menú anterior si existe
        if hasattr(self, 'channel_menu') and self.channel_menu:
            self.channel_menu.dismiss()
            self.channel_menu = None

        menu_items = []

        # Solo admin y moderadores pueden ver ajustes del canal
        if user_level in ['admin', 'moderador']:
            menu_items.append({
                "text": "Ajustes del canal",
                "icon": "cog",
                "on_release": self.open_channel_settings,
            })

        # Si no hay opciones disponibles para este nivel, mostrar mensaje
        if not menu_items:
            self.show_dialog("Sin Opciones", "No hay opciones disponibles para tu nivel de usuario.")
            return
        
        self.channel_menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4,
        )
        self.channel_menu.open()
        
    def open_channel_settings(self, *args):
        """Abrir los ajustes del canal"""
        self.channel_menu.dismiss()
        
        # Buscar el ChatScreen padre para acceder a settings_screen
        current = self.parent
        while current:
            if hasattr(current, 'settings_screen') and hasattr(current, 'show_channel_settings'):
                current.settings_screen.set_channel_data(self.channel_name)
                current.show_channel_settings()
                return
            current = current.parent
        self.show_dialog("Error", "No se pudo acceder a los ajustes del canal")
            


class CreateChannelScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "create_channel"
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical", padding="20dp", spacing="20dp")
        
        # Top bar
        top_bar = MDTopAppBar(
            title="Crear Canal",
            left_action_items=[["arrow-left", lambda x: self.go_back()]]
        )
        
        # Content card
        content_card = MDCard(
            elevation=2,
            padding="20dp",
            size_hint_y=None,
            height="300dp"
        )
        
        content_layout = MDBoxLayout(orientation="vertical", spacing="15dp")
        
        # Título
        title_label = MDLabel(
            text="Nuevo Canal de Chat",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )
        
        # Channel name input
        self.name_input = MDTextField(
            hint_text="Nombre del canal",
            required=True,
            helper_text="Ej: general, soporte, anuncios",
            helper_text_mode="on_focus"
        )
        
        # Channel description input
        self.description_input = MDTextField(
            hint_text="Descripción (opcional)",
            multiline=True,
            max_text_length=200
        )
        
        # Create button
        self.create_button = MDRaisedButton(
            text="CREAR CANAL",
            size_hint_y=None,
            height="40dp",
            on_release=self.create_channel
        )
        
        content_layout.add_widget(title_label)
        content_layout.add_widget(self.name_input)
        content_layout.add_widget(self.description_input)
        content_layout.add_widget(self.create_button)
        
        content_card.add_widget(content_layout)
        
        layout.add_widget(top_bar)
        layout.add_widget(content_card)
        
        self.add_widget(layout)
        
    def create_channel(self, instance):
        name = self.name_input.text.strip()
        description = self.description_input.text.strip()
        
        if not name:
            self.show_dialog("Error", "El nombre del canal no puede estar vacío")
            return
            
        self.create_button.disabled = True
        self.create_button.text = "CREANDO..."
        
        try:
            data = {"nombre": name}
            if description:
                data["descripcion"] = description

            # NUEVO v8.0: Usar cliente autenticado
            result = auth_client.post("/crear_canal", json_data=data, timeout=10)

            if result['success']:
                self.name_input.text = ""
                self.description_input.text = ""
                self.show_success_dialog("¡Éxito!", f"Canal '{name}' creado exitosamente")
            elif result.get('status_code') == 409:
                self.show_dialog("Error", "El canal ya existe")
            else:
                error_msg = result.get('message', 'Error del servidor')
                self.show_dialog("Error", error_msg)

        except Exception as e:
            self.show_dialog("Error", "Error inesperado al crear el canal")
        finally:
            self.create_button.disabled = False
            self.create_button.text = "CREAR CANAL"
            
    def show_success_dialog(self, title, text):
        dialog = MDDialog(
            title=title,
            text=text,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: self.close_and_return(dialog)
                )
            ]
        )
        dialog.open()
        
    def close_and_return(self, dialog):
        dialog.dismiss()
        self.go_back_with_refresh()
        
    def go_back_with_refresh(self):
        # Buscar el layout principal navegando hacia arriba
        current = self.parent
        while current:
            if hasattr(current, 'show_channel_list'):
                current.show_channel_list()
                if hasattr(current, 'load_channels'):
                    current.load_channels()
                return
            elif hasattr(current, 'main_layout') and current.main_layout:
                current.main_layout.show_channel_list()
                current.main_layout.load_channels()
                return
            current = current.parent
        
    def go_back(self):
        # Buscar el layout principal navegando hacia arriba 
        current = self.parent
        while current:
            if hasattr(current, 'show_channel_list'):
                current.show_channel_list()
                return
            elif hasattr(current, 'main_layout') and current.main_layout:
                current.main_layout.show_channel_list()
                return
            current = current.parent
        
    def show_dialog(self, title, text):
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



class ChannelEditScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "channel_edit"
        self.channel_name = None
        self.channel_data = {}
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical", padding="20dp", spacing="20dp")
        
        # Top bar
        top_bar = MDTopAppBar(
            title="Editar Canal",
            left_action_items=[["arrow-left", lambda x: self.go_back()]]
        )
        
        # Content card
        content_card = MDCard(
            elevation=2,
            padding="20dp",
            size_hint_y=None,
            height="400dp"
        )
        
        content_layout = MDBoxLayout(orientation="vertical", spacing="20dp")
        
        # Campo para nombre del canal
        self.name_field = MDTextField(
            hint_text="Nombre del canal",
            required=True,
            helper_text="El nombre del canal es obligatorio",
            helper_text_mode="on_error",
            size_hint_y=None,
            height="60dp"
        )
        
        # Campo para descripción del canal
        self.description_field = MDTextField(
            hint_text="Descripción del canal",
            multiline=True,
            max_text_length=500,
            size_hint_y=None,
            height="120dp"
        )
        
        # Botón de guardar
        self.save_button = MDRaisedButton(
            text="GUARDAR CAMBIOS",
            md_bg_color=[0.2, 0.6, 1, 1],
            size_hint_y=None,
            height="50dp",
            on_release=self.save_changes
        )
        
        content_layout.add_widget(self.name_field)
        content_layout.add_widget(self.description_field)
        content_layout.add_widget(MDLabel(size_hint_y=None, height="20dp"))  # Spacer
        content_layout.add_widget(self.save_button)
        
        content_card.add_widget(content_layout)
        layout.add_widget(top_bar)
        layout.add_widget(content_card)
        
        self.add_widget(layout)
    
    def set_channel_data(self, channel_name):
        """Configurar datos del canal para edición"""
        self.channel_name = channel_name
        self._original_channel_name = channel_name  # Guardar nombre original para comparación
        self.name_field.text = channel_name
        
        # Cargar datos del canal desde el API
        self.load_channel_data()
    
    def load_channel_data(self):
        """Cargar datos actuales del canal"""
        try:
            # FIX: Usar endpoint sin autenticación para carga inicial
            result = auth_client.get("/api/channels/", timeout=5)
            if result['success']:
                data = result['data']
                channels = data.get('channels', []) if isinstance(data, dict) else data
                
                # Buscar el canal específico
                for channel in channels:
                    if channel.get('nombre') == self.channel_name:
                        self.channel_data = channel
                        self.description_field.text = channel.get('descripcion', '')
                        break
        except Exception as e:
            print(f"Error cargando datos del canal: {e}")
    
    def save_changes(self, *args):
        """Guardar cambios del canal"""
        # Validar nombre no vacío
        if not self.name_field.text.strip():
            self.name_field.error = True
            return
        
        self.save_button.disabled = True
        self.save_button.text = "GUARDANDO..."
        
        try:
            # Preparar datos para actualizar
            update_data = {
                "nombre": self.name_field.text.strip(),
                "descripcion": self.description_field.text.strip()
            }
            
            # NUEVO v8.0: Hacer llamada al API usando cliente autenticado
            result = auth_client.put(f"/canal/{self.channel_name}", json_data=update_data, timeout=10)

            if result['success']:
                # Éxito - mostrar mensaje y regresar
                from kivymd.toast import toast
                toast("Canal editado exitosamente")

                # Actualizar el nombre local si cambió
                self.channel_name = self.name_field.text.strip()

                # Regresar a ajustes del canal después de un breve delay
                Clock.schedule_once(lambda dt: self.return_to_settings(), 1)

            else:
                # Error del servidor
                error_msg = result.get('message', 'Error desconocido')
                self.show_dialog("Error", f"No se pudo actualizar el canal:\n{error_msg}")

        except Exception as e:
            self.show_dialog("Error", f"Error inesperado: {str(e)}")
        finally:
            self.save_button.disabled = False
            self.save_button.text = "GUARDAR CAMBIOS"
    
    def return_to_settings(self):
        """Regresar a la pantalla de ajustes del canal"""
        chat_screen_ref = getattr(self, '_chat_screen_ref', None)
        if chat_screen_ref:
            old_channel_name = getattr(self, '_original_channel_name', self.channel_name)
            new_channel_name = self.channel_name
            
            # Actualizar el nombre en la pantalla de ajustes
            if hasattr(chat_screen_ref, 'settings_screen'):
                chat_screen_ref.settings_screen.channel_name = new_channel_name
                chat_screen_ref.settings_screen.title_label.text = f"{new_channel_name}"
                # Recargar información del canal
                chat_screen_ref.settings_screen.load_channel_info()
            
            # Actualizar el chat individual si existe
            if hasattr(chat_screen_ref, 'chat_screen') and hasattr(chat_screen_ref.chat_screen, 'update_channel_name'):
                chat_screen_ref.chat_screen.update_channel_name(old_channel_name, new_channel_name)
            
            # Recargar la lista de canales para mostrar cambios inmediatamente
            if hasattr(chat_screen_ref, 'load_channels'):
                chat_screen_ref.load_channels()
            
            # Cambiar a la pantalla de ajustes
            chat_screen_ref.screen_manager.current = "channel_settings"
    
    def go_back(self):
        """Volver a la pantalla de ajustes"""
        self.return_to_settings()
    
    def show_dialog(self, title, text):
        """Mostrar diálogo informativo"""
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


class ChannelSettingsScreen(MDScreen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "channel_settings"
        self.channel_name = None
        self.setup_ui()
        
    def setup_ui(self):
        layout = MDBoxLayout(orientation="vertical", padding="20dp", spacing="20dp")
        
        # Top bar
        self.top_bar = MDTopAppBar(
            title="Ajustes del canal",
            left_action_items=[["arrow-left", lambda x: self.go_back()]],
            right_action_items=[["dots-vertical", lambda x: self.show_settings_menu()]]
        )
        
        # Content card
        content_card = MDCard(
            elevation=2,
            padding="20dp",
            size_hint_y=None,
            height="400dp"
        )
        
        content_layout = MDBoxLayout(orientation="vertical", spacing="20dp")
        
        # Título con nombre del canal
        self.title_label = MDLabel(
            text="Canal",
            theme_text_color="Primary",
            font_style="H5",
            size_hint_y=None,
            height="40dp",
            halign="center"
        )
        
        # Información del canal
        info_layout = MDBoxLayout(orientation="vertical", spacing="15dp")

        # Información simple con líneas separadoras completas
        info_container = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            size_hint_y=None,
            height="100dp"
        )

        # Línea divisoria superior (como las de las listas)
        class SeparatorLine(MDBoxLayout):
            def __init__(self, **kwargs):
                super().__init__(**kwargs)
                self.size_hint_y = None
                self.height = dp(1)
                with self.canvas:
                    from kivy.graphics import Color, Rectangle
                    Color(0.9, 0.9, 0.9, 0.8)  # Gris más visible
                    self.rect = Rectangle(size=self.size, pos=self.pos)
                self.bind(size=self._update_rect, pos=self._update_rect)

            def _update_rect(self, instance, value):
                self.rect.size = instance.size
                self.rect.pos = instance.pos

        separator_top = SeparatorLine()

        # Contenido con padding lateral
        content_container = MDBoxLayout(
            orientation="vertical",
            spacing="8dp",
            padding=["20dp", "15dp", "20dp", "15dp"]
        )

        # Descripción del canal (alineada a la izquierda)
        self.desc_label = MDLabel(
            text="Cargando...",
            theme_text_color="Primary",
            font_style="Body1",
            size_hint_y=None,
            height="25dp",
            halign="left"
        )
        # Configurar text_size después de creación para alineación
        self.desc_label.bind(size=self._update_desc_text_size)

        # Fecha de creación (alineada a la izquierda)
        self.date_label = MDLabel(
            text="Se creo el Cargando...",
            theme_text_color="Secondary",
            font_style="Body2",
            size_hint_y=None,
            height="20dp",
            halign="left"
        )
        # Configurar text_size después de creación para alineación
        self.date_label.bind(size=self._update_date_text_size)

        content_container.add_widget(self.desc_label)
        content_container.add_widget(self.date_label)

        # Línea divisoria inferior
        separator_bottom = SeparatorLine()

        info_container.add_widget(separator_top)
        info_container.add_widget(content_container)
        info_container.add_widget(separator_bottom)

        info_layout.add_widget(info_container)
        
        # Botón de eliminar canal
        self.delete_button = MDRaisedButton(
            text="ELIMINAR CANAL",
            size_hint_y=None,
            height="45dp",
            md_bg_color=[0.8, 0.2, 0.2, 1],  # Color rojo
            on_release=self.confirm_delete_channel
        )
        
        content_layout.add_widget(self.title_label)
        content_layout.add_widget(info_layout)
        content_layout.add_widget(self.delete_button)
        
        content_card.add_widget(content_layout)
        
        layout.add_widget(self.top_bar)
        layout.add_widget(content_card)
        
        self.add_widget(layout)
        
    def set_channel_data(self, channel_name):
        """Configurar los datos del canal"""
        self.channel_name = channel_name
        self.title_label.text = f"{channel_name}"
        
        # Cargar información real del canal desde el API
        self.load_channel_info()
        
    def load_channel_info(self):
        """Cargar información detallada del canal desde el API"""
        try:
            # NUEVO v8.0: Hacer llamada al API usando cliente autenticado
            result = auth_client.get(f"/canal_info/{self.channel_name}", timeout=5)
            if result['success']:
                data = result['data']
                descripcion = data.get('descripcion', 'Sin descripción')
                # Manejar descripción vacía
                if not descripcion or descripcion.strip() == '':
                    descripcion = 'Sin descripción'
                fecha_creacion = data.get('fecha_creacion', 'Fecha no disponible')

                self.desc_label.text = f"{descripcion}"
                self.date_label.text = f"Se creo el {fecha_creacion}"
            else:
                # Si no hay endpoint específico, intentar obtener de la lista de canales
                self.load_channel_from_list()
        except Exception as e:
            print(f"Error cargando info del canal: {e}")
            self.load_channel_from_list()
            
    def load_channel_from_list(self):
        """Cargar información del canal desde la lista de canales"""
        try:
            # FIX: Usar endpoint sin autenticación para carga inicial
            result = auth_client.get("/api/channels/", timeout=5)
            if result['success']:
                data = result['data']
                channels = data.get('channels', []) if isinstance(data, dict) else data
                
                print(f"DEBUG: Datos recibidos: {data}")  # Debug
                
                # Buscar el canal específico
                channel_info = None
                for channel in channels:
                    if channel.get('nombre') == self.channel_name:
                        channel_info = channel
                        break
                
                if channel_info:
                    print(f"DEBUG: Info del canal encontrada: {channel_info}")  # Debug

                    descripcion = channel_info.get('descripcion', 'Sin descripción')
                    # Manejar descripción vacía
                    if not descripcion or descripcion.strip() == '':
                        descripcion = 'Sin descripción'
                    
                    # Intentar varios campos posibles para la fecha
                    fecha_creacion = (
                        channel_info.get('fecha_creacion') or 
                        channel_info.get('creado_en') or 
                        channel_info.get('created_at') or
                        channel_info.get('fecha') or
                        channel_info.get('_id', {}).get('$date') if isinstance(channel_info.get('_id'), dict) else None
                    )
                    
                    # Si tenemos fecha, formatearla
                    if fecha_creacion and fecha_creacion != 'Fecha no disponible':
                        try:
                            # Si es timestamp de MongoDB ($date)
                            if isinstance(fecha_creacion, (int, float)):
                                from datetime import datetime
                                fecha_formateada = datetime.fromtimestamp(fecha_creacion/1000 if fecha_creacion > 1000000000000 else fecha_creacion).strftime('%d/%m/%Y')
                            # Si ya es string
                            elif isinstance(fecha_creacion, str):
                                if 'T' in fecha_creacion:  # ISO format
                                    from datetime import datetime
                                    fecha_dt = datetime.fromisoformat(fecha_creacion.replace('Z', '+00:00'))
                                    fecha_formateada = fecha_dt.strftime('%d/%m/%Y')
                                else:
                                    fecha_formateada = fecha_creacion
                            else:
                                fecha_formateada = str(fecha_creacion)
                        except Exception as e:
                            print(f"DEBUG: Error formateando fecha {fecha_creacion}: {e}")
                            from datetime import datetime
                            fecha_formateada = datetime.now().strftime('%d/%m/%Y')
                    else:
                        # Sin fecha disponible, usar actual
                        from datetime import datetime
                        fecha_formateada = datetime.now().strftime('%d/%m/%Y')
                    
                    self.desc_label.text = f"{descripcion}"
                    self.date_label.text = f"Se creo el {fecha_formateada}"
                    
                    print(f"DEBUG: Descripción final: {descripcion}")  # Debug
                    print(f"DEBUG: Fecha final: {fecha_formateada}")  # Debug
                else:
                    print(f"DEBUG: Canal '{self.channel_name}' no encontrado en la lista")  # Debug
                    # Datos por defecto si no se encuentra
                    self.desc_label.text = "Sin descripción"
                    from datetime import datetime
                    self.date_label.text = f"Se creo el {datetime.now().strftime('%d/%m/%Y')}"
            else:
                print(f"DEBUG: Error en respuesta: {response.status_code}")  # Debug
                # Datos por defecto en caso de error
                self.desc_label.text = "Sin descripción"
                from datetime import datetime
                self.date_label.text = f"Se creo el {datetime.now().strftime('%d/%m/%Y')}"
        except Exception as e:
            print(f"ERROR cargando canales: {e}")
            # Datos por defecto
            self.desc_label.text = "Sin descripción"
            from datetime import datetime
            self.date_label.text = f"Se creo el {datetime.now().strftime('%d/%m/%Y')}"
        
    def confirm_delete_channel(self, instance):
        """Confirmar eliminación del canal"""
        dialog = MDDialog(
            title="⚠️ Eliminar Canal",
            text=f"¿Estás seguro de que deseas eliminar el canal '{self.channel_name}'?\n\n• Se perderán todos los mensajes\n• Esta acción no se puede deshacer\n• Los miembros perderán acceso al canal",
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    on_release=lambda x: dialog.dismiss()
                ),
                MDRaisedButton(
                    text="ELIMINAR",
                    md_bg_color=[0.8, 0.2, 0.2, 1],
                    on_release=lambda x: self.delete_channel(dialog)
                )
            ]
        )
        dialog.open()
        
    def delete_channel(self, dialog):
        """Eliminar el canal"""
        dialog.dismiss()
        
        self.delete_button.disabled = True
        self.delete_button.text = "ELIMINANDO..."
        
        try:
            print(f"DEBUG: Intentando eliminar canal: {self.channel_name}")

            # NUEVO v8.0: Usar cliente autenticado para eliminar canal
            result = auth_client.delete(f"/canal/{self.channel_name}", timeout=10)
            print(f"DEBUG: Result success: {result.get('success')}")

            if result['success']:
                print("DEBUG: Canal eliminado exitosamente")

                # Mostrar mensaje simple
                from kivymd.toast import toast
                toast(f"Canal eliminado exitosamente")

                # Regresar inmediatamente a la lista de canales y recargar
                self.return_to_channel_list()
            else:
                error_msg = result.get('message', 'Error desconocido')
                status_code = result.get('status_code', 0)

                if status_code == 404:
                    self.show_dialog("Error", f"El canal '{self.channel_name}' no existe en el servidor.")
                elif status_code == 403:
                    self.show_dialog("Error", "No tienes permisos para eliminar este canal.")
                else:
                    self.show_dialog("Error", f"Error del servidor: {error_msg}")

        except Exception as e:
            self.show_dialog("Error", f"Error inesperado al eliminar el canal: {str(e)}")
        finally:
            self.delete_button.disabled = False
            self.delete_button.text = "ELIMINAR CANAL"
            
    def return_to_channel_list(self):
        """Regresar a la lista de canales después de eliminar"""
        # Usar la referencia guardada al ChatScreen
        chat_screen_ref = getattr(self, '_chat_screen_ref', None)
        if chat_screen_ref:
            # Cambiar a la pantalla de canales
            if hasattr(chat_screen_ref, 'show_main_screen'):
                chat_screen_ref.show_main_screen()
            
            # Forzar recarga de la lista de canales
            if hasattr(chat_screen_ref, 'load_channels'):
                # Programar la recarga después de un pequeño delay
                Clock.schedule_once(lambda dt: chat_screen_ref.load_channels(), 0.5)
                
        print("DEBUG: Navegación completada")
        
    def go_back(self):
        """Volver al chat del canal"""
        current = self.parent
        while current:
            if hasattr(current, 'show_chat_channel'):
                current.show_chat_channel()
                return
            elif hasattr(current, 'screen_manager'):
                current.screen_manager.current = "chat_channel"
                return
            current = current.parent
    
    def show_settings_menu(self):
        """Mostrar menú de opciones de ajustes del canal"""
        # Limpiar menú anterior para optimizar memoria
        if hasattr(self, 'settings_menu') and self.settings_menu:
            self.settings_menu.dismiss()
            self.settings_menu = None
            
        menu_items = [
            {
                "text": "Editar canal",
                "on_release": self.open_edit_channel,
            }
        ]
        
        self.settings_menu = MDDropdownMenu(
            items=menu_items,
            width_mult=4,
            caller=self.top_bar,
            position="bottom"
        )
        
        self.settings_menu.open()
    
    def open_edit_channel(self, *args):
        """Abrir pantalla de edición del canal"""
        self.settings_menu.dismiss()
        
        # Buscar el ChatScreen para navegar a edición
        chat_screen_ref = getattr(self, '_chat_screen_ref', None)
        if chat_screen_ref:
            chat_screen_ref.edit_channel(self.channel_name)
        
    def show_dialog(self, title, text):
        """Mostrar diálogo informativo"""
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

    def _update_desc_text_size(self, instance, value):
        """Actualizar text_size para alineación izquierda en descripción"""
        instance.text_size = (instance.width, None)

    def _update_date_text_size(self, instance, value):
        """Actualizar text_size para alineación izquierda en fecha"""
        instance.text_size = (instance.width, None)


class ChatScreen(MDBoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.spacing = "10dp"
        self.main_layout = None  # Referencia al layout principal
        self.setup_ui()
        # Optimización: reducir delay inicial 
        Clock.schedule_once(lambda dt: self.load_channels(), 0.2)
        
    def setup_ui(self):
        # Screen manager para diferentes vistas
        self.screen_manager = MDScreenManager()
        
        # Pantalla de lista de canales
        self.channel_screen = MDScreen(name="channels")
        self.setup_channel_list()
        
        # Pantalla de chat
        self.chat_screen = ChatChannelScreen()
        
        # Pantalla de crear canal
        self.create_screen = CreateChannelScreen()
        
        
        # Pantalla de ajustes del canal
        self.settings_screen = ChannelSettingsScreen()
        self.settings_screen._chat_screen_ref = self
        
        # Pantalla de edición de canal (nueva)
        self.channel_edit_screen = ChannelEditScreen()
        self.channel_edit_screen._chat_screen_ref = self
        
        self.screen_manager.add_widget(self.channel_screen)
        self.screen_manager.add_widget(self.chat_screen)
        self.screen_manager.add_widget(self.create_screen)
        self.screen_manager.add_widget(self.settings_screen)
        self.screen_manager.add_widget(self.channel_edit_screen)
        
        self.add_widget(self.screen_manager)
        
    def setup_channel_list(self):
        layout = MDBoxLayout(orientation="vertical")
        
        # Top bar
        self.top_bar = MDTopAppBar(
            title="Canales CORPOTACHIRA",
            right_action_items=[["dots-vertical", lambda x: self.show_options_menu(x)]]
        )
        
        # Card principal con botón y lista juntos (igual que Moderadores)
        self.channels_card = MDCard(
            elevation=1,
            padding="15dp"
        )

        card_content = MDBoxLayout(orientation="vertical", spacing="15dp")

        # Botón crear canal CON CONTROL DE PERMISOS v8.0
        self.crear_canal_button = MDRaisedButton(
            text="➕ CREAR CANAL",
            md_bg_color=[0.2, 0.6, 1, 1],  # Azul igual que el chat
            size_hint_y=None,
            height="50dp",
            on_release=lambda x: self.show_create_channel()
        )

        # NOTA: configure_create_button_for_user_level() se llama después del login
        # No se puede llamar aquí porque app.nivel_usuario aún no está disponible

        # Título para la lista
        lista_title = MDLabel(
            text="Lista de Canales",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )

        # Lista de canales
        self.channels_scroll = MDScrollView()
        self.channels_list = MDList()
        self.channels_scroll.add_widget(self.channels_list)

        # Agregar componentes al card
        # Botón siempre se crea, pero se oculta/muestra según nivel
        card_content.add_widget(self.crear_canal_button)
        card_content.add_widget(lista_title)
        card_content.add_widget(self.channels_scroll)
        self.channels_card.add_widget(card_content)
        
        layout.add_widget(self.top_bar)
        layout.add_widget(self.channels_card)

        self.channel_screen.add_widget(layout)

    def configure_create_button_for_user_level(self):
        """
        Configura la visibilidad del botón crear canal según el nivel del usuario v8.0
        Maneja el caso cuando nivel_usuario aún no está disponible
        """
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()

            # Verificar si el nivel de usuario está disponible
            if not hasattr(app, 'nivel_usuario') or app.nivel_usuario in [None, '']:
                print("⏳ Nivel de usuario aún no disponible o vacío, configurando botón como oculto por defecto")
                # Por defecto, ocultar hasta saber el nivel real
                self.crear_canal_button.opacity = 0
                self.crear_canal_button.size_hint_y = None
                self.crear_canal_button.height = "0dp"
                self.crear_canal_button.disabled = True
                return

            user_level = app.nivel_usuario

            if user_level == 'obrero':
                # Obreros: OCULTAR completamente el botón (invisible y sin espacio)
                self.crear_canal_button.opacity = 0
                self.crear_canal_button.size_hint_y = None
                self.crear_canal_button.height = "0dp"
                self.crear_canal_button.disabled = True
            else:
                # Admin y moderadores: MOSTRAR botón normalmente
                self.crear_canal_button.opacity = 1
                self.crear_canal_button.size_hint_y = None
                self.crear_canal_button.height = "50dp"  # Altura original del botón
                self.crear_canal_button.disabled = False
                self.crear_canal_button.text = "➕ CREAR CANAL"
                self.crear_canal_button.md_bg_color = [0.2, 0.6, 1, 1]  # Azul

        except Exception as e:
            print(f"❌ Error configurando visibilidad botón crear canal: {e}")
            # Por defecto, ocultar botón en caso de error (más seguro)
            self.crear_canal_button.opacity = 0
            self.crear_canal_button.size_hint_y = None
            self.crear_canal_button.height = "0dp"
            self.crear_canal_button.disabled = True

    def load_channels(self):
        self.channels_list.clear_widgets()

        # NOTA: No configurar botón aquí porque load_channels se ejecuta antes del login
        # El botón se configurará desde update_ui_for_user_level() después del login

        # Indicador de carga
        loading_item = OneLineListItem(text="🔄 Cargando canales...")
        self.channels_list.add_widget(loading_item)
        
        try:
            # FIX: Usar endpoint sin autenticación para carga inicial
            result = auth_client.get("/api/channels/", timeout=8)
            self.channels_list.clear_widgets()

            if result['success']:
                data = result['data']
                channels = data.get('channels', []) if isinstance(data, dict) else data

                if not channels:
                    no_channels_item = OneLineListItem(
                        text="📝 No hay canales disponibles. Crea uno usando el botón +"
                    )
                    self.channels_list.add_widget(no_channels_item)
                else:
                    for channel in channels:
                        channel_name = str(channel.get('nombre', 'Canal sin nombre'))
                        channel_item = ChannelListItem(
                            channel_name=channel_name,
                            on_select_callback=self.select_channel
                        )
                        self.channels_list.add_widget(channel_item)
            else:
                error_msg = result.get('message', 'Error del servidor')
                error_item = OneLineListItem(text=f"❌ {error_msg}")
                self.channels_list.add_widget(error_item)
                
        except requests.exceptions.Timeout:
            self.show_error("⏱️ Timeout: El servidor tardó demasiado en responder")
        except requests.exceptions.ConnectionError:
            self.show_error("🌐 Error de conexión: Verifica tu conexión a internet")
        except Exception as e:
            self.show_error(f"⚠️ Error inesperado: {str(e)}")
            
    def show_error(self, message):
        self.channels_list.clear_widgets()
        error_item = OneLineListItem(text=message)
        self.channels_list.add_widget(error_item)
        
        retry_item = OneLineListItem(
            text="🔄 Reintentar carga",
            on_release=lambda x: self.load_channels()
        )
        self.channels_list.add_widget(retry_item)
        
    def select_channel(self, channel_name):
        self.chat_screen.set_channel(channel_name)
        self.screen_manager.current = "chat_channel"
        
    def show_create_channel(self):
        """Mostrar pantalla de crear canal CON VERIFICACIÓN DE PERMISOS v8.0"""
        # Verificar nivel del usuario antes de permitir crear canal
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            user_level = getattr(app, 'nivel_usuario', 'obrero')

            if user_level == 'obrero':
                self.show_dialog(
                    "Acceso Restringido",
                    "No tienes permisos para crear canales.\nEsta función está reservada para administradores y moderadores."
                )
                return

            # Solo admin y moderadores pueden crear canales
            self.screen_manager.current = "create_channel"

        except Exception as e:
            print(f"❌ Error verificando permisos para crear canal: {e}")
            # Por seguridad, denegar acceso si hay error
            self.show_dialog(
                "Error",
                "No se pudieron verificar los permisos. Intenta de nuevo."
            )
        
    def show_edit_channel(self):
        self.screen_manager.current = "edit_channel"
        
    def show_channel_settings(self):
        self.screen_manager.current = "channel_settings"
        
    def show_channel_list(self):
        self.screen_manager.current = "channels"
        
        
    def show_main_screen(self):
        """Mostrar la pantalla principal de canales"""
        self.show_channel_list()
        
    def show_dialog(self, title, text):
        """Mostrar diálogo informativo"""
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

    def show_options_menu(self, button):
        """Mostrar menú desplegable con opciones CON CONTROL DE PERMISOS v8.0"""
        # Verificar nivel del usuario
        try:
            from kivymd.app import MDApp
            app = MDApp.get_running_app()
            user_level = getattr(app, 'nivel_usuario', 'obrero')
        except Exception:
            user_level = 'obrero'

        # Limpiar menú anterior para optimizar memoria
        if hasattr(self, 'menu') and self.menu:
            self.menu.dismiss()
            self.menu = None

        # Crear elementos del menú - diferentes según nivel
        menu_items = []

        # Opción de cerrar sesión para todos los niveles
        menu_items.append({
            "text": "Cerrar Sesión",
            "icon": "logout",
            "on_release": lambda x="cerrar_sesion": self.handle_menu_option(x),
        })

        # Información Personal disponible para todos los niveles
        menu_items.append({
            "text": "Información Personal",
            "icon": "account-circle",
            "on_release": lambda x="info_personal": self.handle_menu_option(x),
        })
        
        # Crear y mostrar el menú
        self.menu = MDDropdownMenu(
            caller=button,
            items=menu_items,
            width_mult=4,
        )
        self.menu.open()
        
    def handle_menu_option(self, option):
        """Manejar las opciones del menú desplegable CON NUEVAS OPCIONES v8.0"""
        self.menu.dismiss()

        if option == "cerrar_sesion":
            # Mostrar diálogo de confirmación antes de cerrar sesión v8.1
            self.show_logout_confirmation_dialog()
        elif option == "info_personal":
            self.navegar_a_info_personal()

    def show_logout_confirmation_dialog(self):
        """
        Mostrar diálogo de confirmación para cerrar sesión v8.1
        Con opciones: Cancelar y Salir
        """
        from kivymd.uix.dialog import MDDialog
        from kivymd.uix.button import MDFlatButton, MDRaisedButton

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

    def edit_channel(self, channel_name):
        """Mostrar pantalla de edición del canal"""
        # Configurar la pantalla de edición con los datos del canal
        if hasattr(self, 'channel_edit_screen'):
            self.channel_edit_screen.set_channel_data(channel_name)
            self.screen_manager.current = "channel_edit"
        else:
            print(f"ERROR: channel_edit_screen no encontrada")
    
    def cleanup_menus(self):
        """Limpiar todos los menús dropdown para liberar memoria"""
        if hasattr(self, 'menu') and self.menu:
            self.menu.dismiss()
            self.menu = None
        
        # Limpiar menús de pantallas hijas
        if hasattr(self, 'chat_screen') and hasattr(self.chat_screen, 'channel_menu'):
            if self.chat_screen.channel_menu:
                self.chat_screen.channel_menu.dismiss()
                self.chat_screen.channel_menu = None
        
        if hasattr(self, 'settings_screen') and hasattr(self.settings_screen, 'settings_menu'):
            if self.settings_screen.settings_menu:
                self.settings_screen.settings_menu.dismiss()
                self.settings_screen.settings_menu = None

    def update_ui_for_user_level(self):
        """
        Método público para actualizar la UI según el nivel del usuario
        Se debe llamar DESPUÉS de establecer app.nivel_usuario en el login
        """

        # Configurar visibilidad del botón crear canal
        self.configure_create_button_for_user_level()

        # Configurar área de entrada de mensajes en la pantalla de chat
        if hasattr(self, 'chat_screen') and hasattr(self.chat_screen, 'configure_input_area_for_user_level'):
            self.chat_screen.configure_input_area_for_user_level()

