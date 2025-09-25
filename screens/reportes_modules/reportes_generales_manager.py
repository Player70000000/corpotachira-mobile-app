"""
Módulo de Reportes Generales de Cuadrillas
Gestor modular para reportes de trabajo de cuadrillas con herramientas
"""

from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList, OneLineListItem
from kivymd.uix.textfield import MDTextField
from kivymd.uix.gridlayout import MDGridLayout
from kivymd.uix.menu import MDDropdownMenu
from kivy.uix.widget import Widget
from kivy.clock import Clock
from kivy.metrics import dp
import requests
# NUEVO v8.0: Cliente autenticado
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.auth_client import auth_client

from utils.unified_api_client import unified_client as ReportesAPIClient


class SimpleDivider(Widget):
    """Separador simple para listas"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint_y = None
        self.height = dp(1)

        # Crear canvas con línea
        with self.canvas:
            from kivy.graphics import Color, Rectangle
            Color(0.9, 0.9, 0.9, 0.5)  # Color gris sutil
            self.rect = Rectangle(size=self.size, pos=self.pos)

        # Actualizar rect cuando cambie el tamaño
        self.bind(size=self._update_rect, pos=self._update_rect)

    def _update_rect(self, instance, value):
        self.rect.size = instance.size
        self.rect.pos = instance.pos


class ReporteListItem(MDBoxLayout):
    """Item minimalista para lista de reportes: Cuadrilla + Botón Eliminar"""

    def __init__(self, reporte_data, manager_callback, **kwargs):
        super().__init__(**kwargs)

        # Configuración del layout horizontal
        self.orientation = 'horizontal'
        self.size_hint_y = None
        self.height = dp(48)  # Altura fija de una línea
        self.padding = [dp(16), 0]
        self.spacing = dp(10)

        # Guardar datos del reporte y callback
        self.reporte_data = reporte_data
        self.manager_callback = manager_callback

        # Texto de reporte (lado izquierdo)
        numero_reporte = reporte_data.get('numero_reporte', 'N/A')
        reporte_text = f"Reporte N°{numero_reporte}"
        self.reporte_label = MDLabel(
            text=reporte_text,
            size_hint_x=0.8,
            font_style="Body1",
            theme_text_color="Primary",
            valign="center"
        )

        # Botón eliminar (lado derecho)
        self.eliminar_btn = MDIconButton(
            icon="trash-can-outline",
            theme_text_color="Custom",
            text_color=(1, 0, 0, 0.8),  # Rojo suave
            size_hint_x=0.2,
            pos_hint={'center_y': 0.5},
            on_release=self._on_eliminar_clicked
        )

        # Hacer que todo el layout sea clickeable para abrir PDF (excepto el botón)
        self.bind(on_touch_down=self._on_item_clicked)

        # Agregar widgets al layout
        self.add_widget(self.reporte_label)
        self.add_widget(self.eliminar_btn)

    def _on_item_clicked(self, instance, touch):
        """Manejar click en el item para abrir PDF"""
        if self.collide_point(*touch.pos):
            # Verificar que no sea click en el botón eliminar
            if not self.eliminar_btn.collide_point(*touch.pos):
                # Llamar al callback del manager para abrir PDF
                self.manager_callback('abrir_pdf', self.reporte_data)
                return True
        return False

    def _on_eliminar_clicked(self, instance):
        """Manejar click en botón eliminar"""
        # Llamar al callback del manager para iniciar eliminación
        self.manager_callback('eliminar', self.reporte_data)


class ReportesGeneralesManager:
    """Gestor de reportes generales de cuadrillas y trabajo"""

    def __init__(self, parent_layout):
        self.parent_layout = parent_layout
        self.api_client = ReportesAPIClient
        self.current_layout = None

        # Data para la creación de reportes
        self.cuadrillas_data = []
        self.herramientas_utilizadas = []
        self.screen_stack = []  # Para navegación entre pantallas

        # Variables para cuadrilla seleccionada
        self.selected_cuadrilla_data = None

    def mostrar_reportes_generales(self):
        """Mostrar pantalla principal de reportes generales"""
        self.current_layout = MDBoxLayout(orientation="vertical", spacing="10dp")

        # Top bar
        top_bar = MDTopAppBar(
            title="📋 Reportes Generales",
            left_action_items=[["arrow-left", lambda x: self._volver_menu_principal()]],
            right_action_items=[["refresh", lambda x: self._refrescar_datos()]]
        )

        # Scroll para el contenido
        self.content_scroll = MDScrollView()
        self.content_layout = MDBoxLayout(
            orientation="vertical",
            spacing="15dp",
            adaptive_height=True,
            padding="10dp"
        )

        self.content_scroll.add_widget(self.content_layout)
        self.current_layout.add_widget(top_bar)
        self.current_layout.add_widget(self.content_scroll)

        # Cargar datos iniciales
        self._cargar_pantalla_principal()

        # Mostrar en el layout principal
        self.parent_layout.clear_widgets()
        self.parent_layout.add_widget(self.current_layout)

    def _cargar_pantalla_principal(self):
        """Cargar pantalla principal con botón generar y lista de reportes"""
        self.content_layout.clear_widgets()

        # Botón para generar nuevo reporte
        generar_button = MDRaisedButton(
            text="📊 GENERAR NUEVO REPORTE",
            md_bg_color=[0.2, 0.7, 0.3, 1],
            size_hint_y=None,
            height="50dp",
            on_release=lambda x: self._abrir_pantalla_creacion()
        )

        # Título de lista
        lista_title = MDLabel(
            text="Lista de Reportes Generales",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )

        # Scroll y lista para reportes (patrón exitoso)
        self.reportes_scroll = MDScrollView(
            size_hint_y=None,
            height="300dp"
        )
        self.reportes_list = MDList(adaptive_height=True)
        self.reportes_scroll.add_widget(self.reportes_list)

        # Agregar elementos al layout
        self.content_layout.add_widget(generar_button)
        self.content_layout.add_widget(lista_title)
        self.content_layout.add_widget(self.reportes_scroll)

        # Cargar reportes existentes
        Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)

    def _cargar_lista_reportes(self):
        """Cargar lista de reportes generales existentes"""
        try:
            # NUEVO v8.0: Usar cliente autenticado
            result = auth_client.get("/api/reports/generales/listar", timeout=10)

            if result['success']:
                data = result['data']
                if data.get('success'):
                    reportes = data.get('reportes', [])
                    self._mostrar_lista_reportes(reportes)
                else:
                    self._mostrar_error_lista(f"Error: {data.get('error', 'Error desconocido')}")
            else:
                error_msg = result.get('message', 'Error del servidor')
                self._mostrar_error_lista(f"Error: {error_msg}")
        except Exception as e:
            self._mostrar_error_lista(f"Error de conexión: {str(e)}")

    def _mostrar_lista_reportes(self, reportes):
        """Mostrar lista de reportes usando diseño minimalista con botón eliminar"""
        self.reportes_list.clear_widgets()

        if not reportes:
            no_data_label = MDLabel(
                text="No hay reportes generales disponibles",
                theme_text_color="Hint",
                halign="center",
                size_hint_y=None,
                height="50dp"
            )
            self.reportes_list.add_widget(no_data_label)
            return

        # Ordenar por número de reporte ascendente (más recientes primero)
        reportes_ordenados = list(reversed(reportes))

        for i, reporte in enumerate(reportes_ordenados):
            # Crear item minimalista personalizado
            reporte_item = ReporteListItem(
                reporte_data=reporte,
                manager_callback=self._manejar_callback_item
            )
            self.reportes_list.add_widget(reporte_item)

            # Agregar separador sutil entre items (excepto el último)
            if i < len(reportes_ordenados) - 1:
                divider = SimpleDivider()
                self.reportes_list.add_widget(divider)

    def _mostrar_error_lista(self, mensaje):
        """Mostrar error en la lista de reportes"""
        self.reportes_list.clear_widgets()
        error_label = MDLabel(
            text=f"❌ {mensaje}",
            theme_text_color="Error",
            halign="center",
            size_hint_y=None,
            height="50dp"
        )
        self.reportes_list.add_widget(error_label)

    def _abrir_reporte_desde_lista(self, reporte_data):
        """Abrir reporte desde la lista (abrir PDF)"""
        try:
            pdf_url = reporte_data.get('pdf_url', '')
            if pdf_url:
                # Abrir PDF en navegador
                import webbrowser
                full_url = f"{self.api_client.base_url}{pdf_url}"
                webbrowser.open(full_url)
            else:
                self._mostrar_error_dialog("No se encontró el archivo PDF del reporte")
        except Exception as e:
            self._mostrar_error_dialog(f"Error al abrir reporte: {str(e)}")

    def _abrir_pantalla_creacion(self):
        """Abrir pantalla completa de creación de reporte"""
        # Guardar pantalla actual en stack
        self.screen_stack.append(self.current_layout)

        # Crear nueva pantalla completa
        self._crear_pantalla_creacion()

    def _crear_pantalla_creacion(self):
        """Crear pantalla completa para nuevo reporte"""
        # Layout principal de la pantalla
        self.creation_layout = MDBoxLayout(orientation="vertical", spacing="10dp")

        # Top bar para pantalla de creación
        creation_top_bar = MDTopAppBar(
            title="📝 Crear Reporte General",
            left_action_items=[["arrow-left", lambda x: self._volver_pantalla_principal()]],
            right_action_items=[["check", lambda x: self._validar_y_guardar_reporte()]]
        )

        # Scroll para formulario
        form_scroll = MDScrollView()
        self.form_layout = MDBoxLayout(
            orientation="vertical",
            spacing="20dp",
            adaptive_height=True,
            padding="15dp"
        )

        form_scroll.add_widget(self.form_layout)
        self.creation_layout.add_widget(creation_top_bar)
        self.creation_layout.add_widget(form_scroll)

        # Resetear variables de selección
        self.selected_cuadrilla_data = None

        # Crear campos del formulario
        self._crear_campos_formulario()

        # Cargar datos de cuadrillas
        self._cargar_cuadrillas_data()

        # Mostrar pantalla de creación
        self.parent_layout.clear_widgets()
        self.parent_layout.add_widget(self.creation_layout)

    def _crear_campos_formulario(self):
        """Crear todos los campos del formulario"""
        self.form_layout.clear_widgets()

        # 1. DROPDOWN DE CUADRILLA
        cuadrilla_label = MDLabel(
            text="🏗️ Cuadrilla:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(cuadrilla_label)

        self.cuadrilla_field = MDRaisedButton(
            text="Seleccionar Cuadrilla *",
            md_bg_color=[0.95, 0.95, 0.95, 1],  # Gris claro como campo
            theme_text_color="Primary",
            size_hint_y=None,
            height="50dp",
            on_release=self._mostrar_selector_cuadrilla
        )
        self.form_layout.add_widget(self.cuadrilla_field)

        # 2. CAMPO ACTIVIDAD (Solo lectura)
        actividad_label = MDLabel(
            text="⚡ Actividad:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(actividad_label)

        self.actividad_field = MDTextField(
            hint_text="Actividad se carga automáticamente...",
            readonly=True,
            size_hint_y=None,
            height="50dp"
        )
        self.form_layout.add_widget(self.actividad_field)

        # 3. MUNICIPIO
        municipio_label = MDLabel(
            text="🏘️ Municipio:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(municipio_label)

        self.municipio_field = MDTextField(
            hint_text="Escribir municipio...",
            size_hint_y=None,
            height="50dp",
            on_text=self._validar_municipio
        )
        self.form_layout.add_widget(self.municipio_field)

        # 4. DISTANCIA
        distancia_label = MDLabel(
            text="📏 Distancia (metros):",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(distancia_label)

        self.distancia_field = MDTextField(
            hint_text="Distancia en metros...",
            input_filter="int",
            size_hint_y=None,
            height="50dp",
            on_text=self._validar_distancia
        )
        self.form_layout.add_widget(self.distancia_field)

        # 5. HERRAMIENTAS UTILIZADAS (Solo herramientas con cantidad)
        herramientas_label = MDLabel(
            text="🔨 Herramientas Utilizadas:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(herramientas_label)

        # Container para herramientas utilizadas
        self.herramientas_container = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            adaptive_height=True
        )
        self.form_layout.add_widget(self.herramientas_container)

        # Inicializar listas separadas
        self.herramientas_utilizadas = []
        self.herramientas_dañadas = []
        self.herramientas_perdidas = []

        self._agregar_herramienta_inicial()

        # Sincronizar después de que todo esté inicializado
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._sincronizar_herramientas_dañadas_perdidas(), 0.1)

        # Botón agregar herramienta utilizada
        add_herramienta_btn = MDRaisedButton(
            text="➕ Agregar Herramienta",
            size_hint_y=None,
            height="40dp",
            md_bg_color=(0.3, 0.7, 0.3, 1),
            on_release=self._agregar_nueva_herramienta
        )
        self.form_layout.add_widget(add_herramienta_btn)

        # 6. HERRAMIENTAS DAÑADAS (Sección separada)
        dañadas_label = MDLabel(
            text="⚠️ Herramientas Dañadas:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(dañadas_label)

        # Container para herramientas dañadas
        self.dañadas_container = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            adaptive_height=True
        )
        self.form_layout.add_widget(self.dañadas_container)

        # 7. HERRAMIENTAS PERDIDAS (Sección separada)
        perdidas_label = MDLabel(
            text="❌ Herramientas Perdidas:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(perdidas_label)

        # Container para herramientas perdidas
        self.perdidas_container = MDBoxLayout(
            orientation="vertical",
            spacing="10dp",
            adaptive_height=True
        )
        self.form_layout.add_widget(self.perdidas_container)

        # 8. DETALLES ADICIONALES
        detalles_label = MDLabel(
            text="📝 Detalles Adicionales:",
            theme_text_color="Primary",
            font_style="Subtitle1",
            size_hint_y=None,
            height="30dp"
        )
        self.form_layout.add_widget(detalles_label)

        self.detalles_field = MDTextField(
            hint_text="Información adicional del trabajo...",
            multiline=True,
            size_hint_y=None,
            height="100dp"
        )
        self.form_layout.add_widget(self.detalles_field)

    def _cargar_cuadrillas_data(self):
        """Cargar datos de cuadrillas desde la API"""
        try:
            # NUEVO v8.0: Usar cliente autenticado
            print(f"🔗 Cargando cuadrillas usando cliente autenticado")

            result = auth_client.get("/api/personnel/cuadrillas/", timeout=10)
            print(f"📡 Result success: {result.get('success')}")

            if result['success']:
                data = result['data']
                print(f"📊 Data recibida: {data}")
                if data.get('success'):
                    cuadrillas = data.get('cuadrillas', [])
                    print(f"✅ Cuadrillas encontradas: {len(cuadrillas)}")
                    for i, c in enumerate(cuadrillas):
                        print(f"  {i+1}. {c.get('numero_cuadrilla', 'N/A')}")
                    self.cuadrillas_data = cuadrillas
                else:
                    print(f"❌ API retornó success=False: {data.get('error', 'Sin error')}")
                    self.cuadrillas_data = []
            else:
                error_msg = result.get('message', 'Error del servidor')
                print(f"❌ Error: {error_msg}")
                self.cuadrillas_data = []
        except Exception as e:
            self.cuadrillas_data = []
            print(f"💥 Error cargando cuadrillas: {str(e)}")

    def _mostrar_selector_cuadrilla(self, instance):
        """Mostrar dropdown de cuadrillas cuando se hace clic en el botón"""
        print(f"🎯 Selector cuadrilla clicked - Cuadrillas disponibles: {len(self.cuadrillas_data)}")

        # Si no hay cuadrillas cargadas, cargar antes de mostrar
        if not self.cuadrillas_data:
            print(f"⏳ Cuadrillas no cargadas, cargando ahora...")
            self._cargar_cuadrillas_data()

        if self.cuadrillas_data:
            print(f"📋 Listando cuadrillas disponibles:")
            for i, c in enumerate(self.cuadrillas_data):
                print(f"  {i+1}. {c.get('numero_cuadrilla', 'N/A')} - {c.get('actividad', 'Sin actividad')}")

            # Crear lista de items para el dropdown (FIX: lambda closure bug)
            menu_items = []
            for idx, cuadrilla in enumerate(self.cuadrillas_data):
                numero = cuadrilla.get('numero_cuadrilla', 'N/A')
                menu_items.append({
                    "text": numero,
                    # Usar índice como default parameter para evitar closure bug
                    "on_release": lambda x=None, idx=idx: self._on_cuadrilla_selected_with_close(self.cuadrillas_data[idx], self.cuadrilla_dropdown)
                })

            print(f"📝 Items del dropdown: {len(menu_items)}")

            # Crear y mostrar dropdown
            self.cuadrilla_dropdown = MDDropdownMenu(
                caller=instance,
                items=menu_items,
                width_mult=2,  # Reducir ancho para que no se salga
                max_height="200dp",
                position="auto"  # Posición automática mejor
            )

            # Actualizar referencias del menu en los items (FIX: lambda closure bug)
            for i, item in enumerate(menu_items):
                # Usar default parameter para capturar el valor de i correctamente
                item["on_release"] = lambda x=None, idx=i: self._on_cuadrilla_selected_with_close(self.cuadrillas_data[idx], self.cuadrilla_dropdown)

            self.cuadrilla_dropdown.open()
        else:
            print(f"❌ Aún no hay cuadrillas después de recargar")
            self._mostrar_error_dialog("Error cargando cuadrillas. Verifica tu conexión.")


    def _on_cuadrilla_selected_with_close(self, cuadrilla_data, dropdown_menu):
        """Callback cuando se selecciona una cuadrilla del dropdown con cierre automático"""
        print(f"✅ Cuadrilla seleccionada: {cuadrilla_data.get('numero_cuadrilla', 'N/A')}")

        # Cerrar dropdown primero
        if dropdown_menu:
            dropdown_menu.dismiss()

        numero = cuadrilla_data.get('numero_cuadrilla', 'N/A')
        actividad = cuadrilla_data.get('actividad', 'Sin actividad')

        # Guardar data de cuadrilla seleccionada
        self.selected_cuadrilla_data = cuadrilla_data

        # Actualizar botón de cuadrilla
        self.cuadrilla_field.text = f"Cuadrilla: {numero}"

        # Actualizar campo de actividad
        self.actividad_field.text = actividad

        # Limpiar herramientas para nuevas
        self._actualizar_herramientas_perdidas_dañadas()

    def _on_cuadrilla_selected(self, cuadrilla_data):
        """Callback cuando se selecciona una cuadrilla del dropdown (legacy)"""
        numero = cuadrilla_data.get('numero_cuadrilla', 'N/A')
        actividad = cuadrilla_data.get('actividad', 'Sin actividad')

        # Guardar data de cuadrilla seleccionada
        self.selected_cuadrilla_data = cuadrilla_data

        # Actualizar botón de cuadrilla
        self.cuadrilla_field.text = f"Cuadrilla: {numero}"

        # Actualizar campo de actividad
        self.actividad_field.text = actividad

        # Limpiar herramientas para nuevas
        self._actualizar_herramientas_perdidas_dañadas()

    def _validar_municipio(self, instance, text):
        """Validar que el municipio solo contenga letras y espacios"""
        # Permitir solo letras, espacios y acentos
        import re
        patron = re.compile(r'^[a-zA-ZñÑáéíóúÁÉÍÓÚ\s]*$')

        if not patron.match(text):
            # Remover caracteres inválidos
            texto_limpio = re.sub(r'[^a-zA-ZñÑáéíóúÁÉÍÓÚ\s]', '', text)
            instance.text = texto_limpio

    def _validar_distancia(self, instance, text):
        """Validar que la distancia sea solo números positivos"""
        if text and not text.isdigit():
            # Remover caracteres no numéricos
            texto_limpio = ''.join(filter(str.isdigit, text))
            instance.text = texto_limpio

    def _agregar_herramienta_inicial(self):
        """Agregar la primera herramienta (mínimo 1 obligatoria)"""
        self._agregar_herramienta_widget()

    def _agregar_nueva_herramienta(self, instance):
        """Agregar nueva herramienta al formulario"""
        self._agregar_herramienta_widget()
        # Sincronizar después de agregar
        self._sincronizar_herramientas_dañadas_perdidas()

    def _agregar_herramienta_widget(self):
        """Crear widget para una herramienta utilizada (solo nombre y cantidad)"""
        herramienta_id = len(self.herramientas_utilizadas)

        # Container principal de la herramienta
        herramienta_container = MDBoxLayout(
            orientation="vertical",
            spacing="5dp",
            adaptive_height=True,
            size_hint_y=None
        )

        # Header con título y botón eliminar
        header_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="30dp",
            spacing="10dp"
        )

        herramienta_title = MDLabel(
            text=f"Herramienta #{herramienta_id + 1}:",
            theme_text_color="Primary",
            font_style="Subtitle2",
            size_hint_x=0.8
        )

        # Botón eliminar (solo si hay más de 1)
        if len(self.herramientas_utilizadas) > 0:  # Permitir eliminar si hay más de 1
            eliminar_btn = MDIconButton(
                icon="close",
                size_hint_x=0.2,
                on_release=lambda x, idx=herramienta_id: self._eliminar_herramienta(idx)
            )
            header_layout.add_widget(herramienta_title)
            header_layout.add_widget(eliminar_btn)
        else:
            header_layout.add_widget(herramienta_title)

        # Layout horizontal: nombre + cantidad con botones
        content_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="50dp",
            spacing="10dp"
        )

        # Campo nombre de herramienta
        nombre_field = MDTextField(
            hint_text="Nombre de la herramienta...",
            size_hint_x=0.6,
            size_hint_y=None,
            height="50dp",
            on_text=lambda instance, text, idx=herramienta_id: self._on_nombre_herramienta_changed(idx, text)
        )

        # Botón menos
        cantidad_menos_btn = MDIconButton(
            icon="minus",
            size_hint_x=0.1,
            on_release=lambda x, idx=herramienta_id: self._cambiar_cantidad(idx, -1)
        )

        # Campo cantidad
        cantidad_field = MDTextField(
            text="1",
            input_filter="int",
            size_hint_x=0.2,
            size_hint_y=None,
            height="50dp",
            halign="center"
        )

        # Botón más
        cantidad_mas_btn = MDIconButton(
            icon="plus",
            size_hint_x=0.1,
            on_release=lambda x, idx=herramienta_id: self._cambiar_cantidad(idx, 1)
        )

        content_layout.add_widget(nombre_field)
        content_layout.add_widget(cantidad_menos_btn)
        content_layout.add_widget(cantidad_field)
        content_layout.add_widget(cantidad_mas_btn)

        # Agregar todo al container
        herramienta_container.add_widget(header_layout)
        herramienta_container.add_widget(content_layout)

        # Calcular altura total
        herramienta_container.height = "85dp"

        # Guardar referencias
        herramienta_data = {
            'container': herramienta_container,
            'nombre_field': nombre_field,
            'cantidad_field': cantidad_field,
            'id': herramienta_id,
            'tipo': 'utilizada'
        }

        self.herramientas_utilizadas.append(herramienta_data)
        self.herramientas_container.add_widget(herramienta_container)

    def _sincronizar_herramientas_dañadas_perdidas(self):
        """Sincronizar las herramientas utilizadas con las secciones de dañadas y perdidas"""
        # Verificar que los contenedores existan
        if not hasattr(self, 'dañadas_container') or not hasattr(self, 'perdidas_container'):
            return

        # Limpiar contenedores
        self.dañadas_container.clear_widgets()
        self.perdidas_container.clear_widgets()

        # Resetear listas
        self.herramientas_dañadas = []
        self.herramientas_perdidas = []

        # Crear widgets para cada herramienta utilizada en ambas secciones
        for idx, herramienta_utilizada in enumerate(self.herramientas_utilizadas):
            nombre = herramienta_utilizada['nombre_field'].text.strip()
            # Siempre sincronizar, aunque el nombre esté vacío
            # Crear widget para dañadas
            self._crear_widget_dañada_sincronizada(nombre, idx)
            # Crear widget para perdidas
            self._crear_widget_perdida_sincronizada(nombre, idx)

    def _crear_widget_dañada_sincronizada(self, nombre_herramienta, herramienta_idx):
        """Crear widget sincronizado para herramienta dañada"""
        # Layout horizontal: nombre + cantidad con botones
        content_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="50dp",
            spacing="10dp"
        )

        # Label con nombre (no editable)
        nombre_label = MDLabel(
            text=nombre_herramienta or "[Sin nombre]",
            size_hint_x=0.6,
            theme_text_color="Primary" if nombre_herramienta else "Hint"
        )

        # Botón menos
        cantidad_menos_btn = MDIconButton(
            icon="minus",
            size_hint_x=0.1,
            on_release=lambda x, idx=herramienta_idx: self._cambiar_cantidad_dañada(idx, -1)
        )

        # Campo cantidad
        cantidad_field = MDTextField(
            text="0",
            input_filter="int",
            size_hint_x=0.2,
            size_hint_y=None,
            height="50dp",
            halign="center"
        )

        # Botón más
        cantidad_mas_btn = MDIconButton(
            icon="plus",
            size_hint_x=0.1,
            on_release=lambda x, idx=herramienta_idx: self._cambiar_cantidad_dañada(idx, 1)
        )

        content_layout.add_widget(nombre_label)
        content_layout.add_widget(cantidad_menos_btn)
        content_layout.add_widget(cantidad_field)
        content_layout.add_widget(cantidad_mas_btn)

        # Guardar referencias
        herramienta_data = {
            'container': content_layout,
            'nombre': nombre_herramienta,
            'cantidad_field': cantidad_field,
            'id': herramienta_idx,
            'tipo': 'dañada'
        }

        self.herramientas_dañadas.append(herramienta_data)
        self.dañadas_container.add_widget(content_layout)

    def _crear_widget_perdida_sincronizada(self, nombre_herramienta, herramienta_idx):
        """Crear widget sincronizado para herramienta perdida"""
        # Layout horizontal: nombre + cantidad con botones
        content_layout = MDBoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height="50dp",
            spacing="10dp"
        )

        # Label con nombre (no editable)
        nombre_label = MDLabel(
            text=nombre_herramienta or "[Sin nombre]",
            size_hint_x=0.6,
            theme_text_color="Primary" if nombre_herramienta else "Hint"
        )

        # Botón menos
        cantidad_menos_btn = MDIconButton(
            icon="minus",
            size_hint_x=0.1,
            on_release=lambda x, idx=herramienta_idx: self._cambiar_cantidad_perdida(idx, -1)
        )

        # Campo cantidad
        cantidad_field = MDTextField(
            text="0",
            input_filter="int",
            size_hint_x=0.2,
            size_hint_y=None,
            height="50dp",
            halign="center"
        )

        # Botón más
        cantidad_mas_btn = MDIconButton(
            icon="plus",
            size_hint_x=0.1,
            on_release=lambda x, idx=herramienta_idx: self._cambiar_cantidad_perdida(idx, 1)
        )

        content_layout.add_widget(nombre_label)
        content_layout.add_widget(cantidad_menos_btn)
        content_layout.add_widget(cantidad_field)
        content_layout.add_widget(cantidad_mas_btn)

        # Guardar referencias
        herramienta_data = {
            'container': content_layout,
            'nombre': nombre_herramienta,
            'cantidad_field': cantidad_field,
            'id': herramienta_idx,
            'tipo': 'perdida'
        }

        self.herramientas_perdidas.append(herramienta_data)
        self.perdidas_container.add_widget(content_layout)

    def _on_nombre_herramienta_changed(self, herramienta_idx, nuevo_nombre):
        """Callback cuando cambia el nombre de una herramienta"""
        # Actualizar inmediatamente los nombres en dañadas y perdidas
        self._actualizar_nombres_sincronizados(herramienta_idx, nuevo_nombre)

        # Programar sincronización completa con delay más corto
        from kivy.clock import Clock
        Clock.unschedule(self._sincronizar_herramientas_dañadas_perdidas)
        Clock.schedule_once(lambda dt: self._sincronizar_herramientas_dañadas_perdidas(), 0.1)

    def _actualizar_nombres_sincronizados(self, herramienta_idx, nuevo_nombre):
        """Actualizar inmediatamente los nombres en las secciones sincronizadas"""
        # Actualizar en herramientas dañadas
        for herramienta in self.herramientas_dañadas:
            if herramienta['id'] == herramienta_idx:
                # Encontrar el label de nombre y actualizarlo
                container = herramienta['container']
                if container.children:
                    nombre_label = container.children[-1]  # Primer widget agregado (nombre)
                    if hasattr(nombre_label, 'text'):
                        nombre_label.text = nuevo_nombre or "[Sin nombre]"
                herramienta['nombre'] = nuevo_nombre
                break

        # Actualizar en herramientas perdidas
        for herramienta in self.herramientas_perdidas:
            if herramienta['id'] == herramienta_idx:
                # Encontrar el label de nombre y actualizarlo
                container = herramienta['container']
                if container.children:
                    nombre_label = container.children[-1]  # Primer widget agregado (nombre)
                    if hasattr(nombre_label, 'text'):
                        nombre_label.text = nuevo_nombre or "[Sin nombre]"
                herramienta['nombre'] = nuevo_nombre
                break

    # Funciones eliminadas - ahora se usan las sincronizadas

    def _cambiar_cantidad(self, herramienta_idx, delta):
        """Cambiar cantidad de herramienta utilizada con botones +/-"""
        if herramienta_idx < len(self.herramientas_utilizadas):
            herramienta = self.herramientas_utilizadas[herramienta_idx]
            cantidad_actual = int(herramienta['cantidad_field'].text or "1")
            nueva_cantidad = max(1, cantidad_actual + delta)  # Mínimo 1
            herramienta['cantidad_field'].text = str(nueva_cantidad)

    def _cambiar_cantidad_dañada(self, herramienta_idx, delta):
        """Cambiar cantidad de herramienta dañada con botones +/-"""
        # Buscar por ID de herramienta utilizada
        for herramienta in self.herramientas_dañadas:
            if herramienta['id'] == herramienta_idx:
                cantidad_actual = int(herramienta['cantidad_field'].text or "0")
                nueva_cantidad = max(0, cantidad_actual + delta)  # Mínimo 0
                herramienta['cantidad_field'].text = str(nueva_cantidad)
                break

    def _cambiar_cantidad_perdida(self, herramienta_idx, delta):
        """Cambiar cantidad de herramienta perdida con botones +/-"""
        # Buscar por ID de herramienta utilizada
        for herramienta in self.herramientas_perdidas:
            if herramienta['id'] == herramienta_idx:
                cantidad_actual = int(herramienta['cantidad_field'].text or "0")
                nueva_cantidad = max(0, cantidad_actual + delta)  # Mínimo 0
                herramienta['cantidad_field'].text = str(nueva_cantidad)
                break

    def _eliminar_herramienta(self, herramienta_idx):
        """Eliminar herramienta utilizada del formulario"""
        if len(self.herramientas_utilizadas) <= 1:
            self._mostrar_error_dialog("Debe mantener al menos una herramienta")
            return

        if herramienta_idx < len(self.herramientas_utilizadas):
            herramienta_data = self.herramientas_utilizadas[herramienta_idx]

            # Remover del layout
            self.herramientas_container.remove_widget(herramienta_data['container'])

            # Remover de la lista
            self.herramientas_utilizadas.pop(herramienta_idx)

            # Reindexar títulos
            self._reindexar_herramientas()

            # Resincronizar dañadas y perdidas
            self._sincronizar_herramientas_dañadas_perdidas()

    # Funciones eliminadas - las herramientas dañadas y perdidas se sincronizan automáticamente

    def _reindexar_herramientas(self):
        """Reindexar títulos de herramientas después de eliminar"""
        for idx, herramienta in enumerate(self.herramientas_utilizadas):
            # Actualizar ID
            herramienta['id'] = idx

            # Actualizar título en header
            header_layout = herramienta['container'].children[-1]  # Primer widget agregado
            if header_layout.children:
                title_label = header_layout.children[-1]  # Primer child del header
                if hasattr(title_label, 'text'):
                    title_label.text = f"Herramienta #{idx + 1}:"

    # Función eliminada - ya no se necesita validación cruzada

    def _actualizar_herramientas_perdidas_dañadas(self):
        """Limpiar campos de herramientas cuando cambia cuadrilla"""
        # Limpiar herramientas dañadas
        for herramienta in self.herramientas_dañadas:
            self.dañadas_container.remove_widget(herramienta['container'])
        self.herramientas_dañadas.clear()

        # Limpiar herramientas perdidas
        for herramienta in self.herramientas_perdidas:
            self.perdidas_container.remove_widget(herramienta['container'])
        self.herramientas_perdidas.clear()

    def _validar_y_guardar_reporte(self):
        """Validar todos los campos y guardar reporte"""
        # Validaciones básicas
        if not self.selected_cuadrilla_data or self.cuadrilla_field.text == "Seleccionar Cuadrilla *":
            self._mostrar_error_dialog("Debe seleccionar una cuadrilla")
            return

        if not self.municipio_field.text.strip():
            self._mostrar_error_dialog("Debe ingresar el municipio")
            return

        if not self.distancia_field.text.strip():
            self._mostrar_error_dialog("Debe ingresar la distancia")
            return

        # Validar herramientas utilizadas
        herramientas_utilizadas_validas = []
        for idx, herramienta in enumerate(self.herramientas_utilizadas):
            nombre = herramienta['nombre_field'].text.strip()
            if not nombre:
                self._mostrar_error_dialog(f"Debe ingresar el nombre de la herramienta utilizada #{idx + 1}")
                return

            try:
                cantidad = int(herramienta['cantidad_field'].text or "1")
                if cantidad < 1:
                    self._mostrar_error_dialog(f"La cantidad de {nombre} debe ser al menos 1")
                    return

                herramientas_utilizadas_validas.append({
                    'nombre': nombre,
                    'cantidad_utilizada': cantidad
                })

            except ValueError:
                self._mostrar_error_dialog(f"Error en los números de la herramienta utilizada #{idx + 1}")
                return

        # Validar herramientas dañadas
        herramientas_dañadas_validas = []
        for herramienta in self.herramientas_dañadas:
            nombre = herramienta['nombre']
            try:
                cantidad = int(herramienta['cantidad_field'].text or "0")
                if cantidad > 0:
                    herramientas_dañadas_validas.append({
                        'nombre': nombre,
                        'cantidad_dañada': cantidad
                    })
                elif cantidad < 0:
                    self._mostrar_error_dialog(f"La cantidad dañada de {nombre} no puede ser negativa")
                    return
            except ValueError:
                self._mostrar_error_dialog(f"Error en los números de la herramienta dañada {nombre}")
                return

        # Validar herramientas perdidas
        herramientas_perdidas_validas = []
        for herramienta in self.herramientas_perdidas:
            nombre = herramienta['nombre']
            try:
                cantidad = int(herramienta['cantidad_field'].text or "0")
                if cantidad > 0:
                    herramientas_perdidas_validas.append({
                        'nombre': nombre,
                        'cantidad_perdida': cantidad
                    })
                elif cantidad < 0:
                    self._mostrar_error_dialog(f"La cantidad perdida de {nombre} no puede ser negativa")
                    return
            except ValueError:
                self._mostrar_error_dialog(f"Error en los números de la herramienta perdida {nombre}")
                return

        # Crear objeto con todas las herramientas
        todas_herramientas = {
            'utilizadas': herramientas_utilizadas_validas,
            'dañadas': herramientas_dañadas_validas,
            'perdidas': herramientas_perdidas_validas
        }

        # Validación cruzada de herramientas
        error_validacion = self._validar_herramientas_cruzadas(todas_herramientas)
        if error_validacion:
            self._mostrar_error_dialog(error_validacion)
            return

        # Si llegamos aquí, todo está válido
        self._procesar_reporte(todas_herramientas)

    def _procesar_reporte(self, todas_herramientas):
        """Procesar y enviar reporte a la API"""
        # Consolidar herramientas en el formato que espera el backend
        herramientas_consolidadas = self._consolidar_herramientas(todas_herramientas)

        # Preparar datos del reporte
        reporte_data = {
            'cuadrilla': self.selected_cuadrilla_data.get('numero_cuadrilla', 'N/A'),
            'actividad': self.actividad_field.text,
            'municipio': self.municipio_field.text.strip(),
            'distancia_metros': int(self.distancia_field.text),
            'herramientas': herramientas_consolidadas,
            'detalles_adicionales': self.detalles_field.text.strip()
        }

        # Mostrar dialog de progreso
        self.progress_dialog = MDDialog(
            title="🔄 Generando Reporte",
            text="Procesando datos y generando PDF...\nPor favor espera un momento.",
            auto_dismiss=False
        )
        self.progress_dialog.open()

        # Enviar a la API en segundo plano
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._enviar_reporte_api(reporte_data), 0.5)

    def _consolidar_herramientas(self, todas_herramientas):
        """Consolidar las tres categorías en el formato que espera el backend"""
        herramientas_consolidadas = []

        # Crear un diccionario para combinar todas las herramientas por nombre
        herramientas_dict = {}

        # Procesar herramientas utilizadas
        for herramienta in todas_herramientas['utilizadas']:
            nombre = herramienta['nombre']
            herramientas_dict[nombre] = {
                'nombre': nombre,
                'cantidad_utilizada': herramienta['cantidad_utilizada'],
                'perdidas': 0,
                'dañadas': 0
            }

        # Añadir herramientas dañadas
        for herramienta in todas_herramientas['dañadas']:
            nombre = herramienta['nombre']
            cantidad = herramienta['cantidad_dañada']
            if nombre in herramientas_dict:
                herramientas_dict[nombre]['dañadas'] = cantidad
            else:
                # Herramienta solo dañada, no utilizada
                herramientas_dict[nombre] = {
                    'nombre': nombre,
                    'cantidad_utilizada': 0,
                    'perdidas': 0,
                    'dañadas': cantidad
                }

        # Añadir herramientas perdidas
        for herramienta in todas_herramientas['perdidas']:
            nombre = herramienta['nombre']
            cantidad = herramienta['cantidad_perdida']
            if nombre in herramientas_dict:
                herramientas_dict[nombre]['perdidas'] = cantidad
            else:
                # Herramienta solo perdida, no utilizada
                herramientas_dict[nombre] = {
                    'nombre': nombre,
                    'cantidad_utilizada': 0,
                    'perdidas': cantidad,
                    'dañadas': 0
                }

        # Convertir diccionario a lista
        herramientas_consolidadas = list(herramientas_dict.values())

        return herramientas_consolidadas

    def _validar_herramientas_cruzadas(self, todas_herramientas):
        """
        Validar que las herramientas perdidas y dañadas sean lógicamente consistentes
        con las herramientas utilizadas
        """
        # Consolidar herramientas para analizar
        herramientas_dict = {}

        # Procesar herramientas utilizadas
        for herramienta in todas_herramientas['utilizadas']:
            nombre = herramienta['nombre']
            herramientas_dict[nombre] = {
                'utilizada': herramienta['cantidad_utilizada'],
                'perdidas': 0,
                'dañadas': 0
            }

        # Añadir herramientas dañadas
        for herramienta in todas_herramientas['dañadas']:
            nombre = herramienta['nombre']
            cantidad = herramienta['cantidad_dañada']
            if nombre in herramientas_dict:
                herramientas_dict[nombre]['dañadas'] = cantidad
            else:
                # Herramienta dañada sin estar en utilizadas
                return f"Error: La herramienta '{nombre}' está marcada como dañada pero no fue registrada como utilizada.\n\nPor favor agregue '{nombre}' a las herramientas utilizadas primero."

        # Añadir herramientas perdidas
        for herramienta in todas_herramientas['perdidas']:
            nombre = herramienta['nombre']
            cantidad = herramienta['cantidad_perdida']
            if nombre in herramientas_dict:
                herramientas_dict[nombre]['perdidas'] = cantidad
            else:
                # Herramienta perdida sin estar en utilizadas
                return f"Error: La herramienta '{nombre}' está marcada como perdida pero no fue registrada como utilizada.\n\nPor favor agregue '{nombre}' a las herramientas utilizadas primero."

        # Validar que perdidas + dañadas no excedan utilizadas
        for nombre, datos in herramientas_dict.items():
            total_problemas = datos['perdidas'] + datos['dañadas']
            if total_problemas > datos['utilizada']:
                return f"Error en '{nombre}':\n\n" \
                       f"• Cantidad utilizada: {datos['utilizada']}\n" \
                       f"• Perdidas: {datos['perdidas']}\n" \
                       f"• Dañadas: {datos['dañadas']}\n" \
                       f"• Total problemas: {total_problemas}\n\n" \
                       f"Las herramientas perdidas + dañadas ({total_problemas}) no pueden exceder las utilizadas ({datos['utilizada']})."

        # Si llegamos aquí, todas las validaciones pasaron
        return None

    def _enviar_reporte_api(self, reporte_data):
        """Enviar reporte a la API"""
        try:
            # NUEVO v8.0: Usar cliente autenticado
            result = auth_client.post(
                "/api/reports/generales/generar",
                json_data=reporte_data,
                timeout=30
            )

            self.progress_dialog.dismiss()

            if result['success']:
                data = result['data']
                if data.get('success'):
                    reporte_info = data.get('reporte', {})
                    self._mostrar_exito_generacion(reporte_info)
                    # Volver a pantalla principal y actualizar lista
                    self._volver_pantalla_principal()
                    Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)
                else:
                    self._mostrar_error_dialog(f"Error: {data.get('error', 'Error desconocido')}")
            else:
                error_msg = result.get('message', 'Error del servidor')
                self._mostrar_error_dialog(f"Error: {error_msg}")

        except Exception as e:
            self.progress_dialog.dismiss()
            self._mostrar_error_dialog(f"Error de conexión: {str(e)}")

    def _mostrar_exito_generacion(self, reporte_info):
        """Mostrar mensaje de éxito al generar reporte"""
        numero_reporte = reporte_info.get('numero_reporte', 'N/A')
        cuadrilla = reporte_info.get('cuadrilla', 'N/A')

        success_dialog = MDDialog(
            title="✅ Reporte Generado",
            text=f"Reporte N°{numero_reporte} generado exitosamente.\n\nCuadrilla: {cuadrilla}\nPDF disponible en la lista.",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: success_dialog.dismiss()
                )
            ]
        )
        success_dialog.open()

    def _volver_pantalla_principal(self):
        """Volver a la pantalla principal de reportes"""
        if self.screen_stack:
            # Restaurar pantalla anterior
            previous_layout = self.screen_stack.pop()
            self.parent_layout.clear_widgets()
            self.parent_layout.add_widget(previous_layout)
            self.current_layout = previous_layout

            # Actualizar lista si estamos en la principal
            Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)
        else:
            # Fallback: recrear pantalla principal
            self.mostrar_reportes_generales()

    def _manejar_callback_item(self, accion, reporte_data):
        """Manejar callbacks de ReporteListItem"""
        if accion == 'abrir_pdf':
            self._abrir_reporte_desde_lista(reporte_data)
        elif accion == 'eliminar':
            self._confirmar_eliminacion_paso1(reporte_data)

    def _confirmar_eliminacion_paso1(self, reporte_data):
        """Primera confirmación - Básica"""
        numero_reporte = reporte_data.get('numero_reporte', 'N/A')
        cuadrilla = reporte_data.get('cuadrilla', 'Sin cuadrilla')

        self.dialog_confirmacion_1 = MDDialog(
            title="Confirmar Eliminación",
            text=f"¿Está seguro que desea eliminar el Reporte N°{numero_reporte}?\n\n"
                 f"Cuadrilla: {cuadrilla}\n"
                 f"Esta acción no se puede deshacer.",
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    theme_text_color="Primary",
                    on_release=lambda x: self.dialog_confirmacion_1.dismiss()
                ),
                MDRaisedButton(
                    text="ELIMINAR",
                    md_bg_color=(1, 0, 0, 1),
                    theme_text_color="Primary",
                    on_release=lambda x: self._confirmar_eliminacion_paso2(reporte_data)
                )
            ]
        )
        self.dialog_confirmacion_1.open()

    def _confirmar_eliminacion_paso2(self, reporte_data):
        """Segunda confirmación - Última advertencia"""
        # Cerrar primer dialog
        self.dialog_confirmacion_1.dismiss()

        numero_reporte = reporte_data.get('numero_reporte', 'N/A')

        self.dialog_confirmacion_2 = MDDialog(
            title="⚠️ ÚTIMA CONFIRMACIÓN",
            text=f"ADVERTENCIA: Esta acción es IRREVERSIBLE.\n\n"
                 f"El Reporte N°{numero_reporte} será eliminado permanentemente.\n\n"
                 f"¿Está completamente seguro?",
            buttons=[
                MDRaisedButton(
                    text="CANCELAR",
                    theme_text_color="Primary",
                    on_release=lambda x: self.dialog_confirmacion_2.dismiss()
                ),
                MDRaisedButton(
                    text="CONFIRMAR",
                    md_bg_color=(0.8, 0, 0, 1),
                    theme_text_color="Primary",
                    on_release=lambda x: self._ejecutar_eliminacion(reporte_data)
                )
            ]
        )
        self.dialog_confirmacion_2.open()

    def _ejecutar_eliminacion(self, reporte_data):
        """Ejecutar eliminación real del reporte"""
        # Cerrar segundo dialog
        self.dialog_confirmacion_2.dismiss()

        # Mostrar dialog de progreso
        self.progress_dialog_eliminacion = MDDialog(
            title="🗑️ Eliminando Reporte",
            text="Eliminando reporte...\nPor favor espera un momento.",
            auto_dismiss=False
        )
        self.progress_dialog_eliminacion.open()

        # Ejecutar eliminación en segundo plano
        Clock.schedule_once(lambda dt: self._eliminar_reporte_api(reporte_data), 0.5)

    def _eliminar_reporte_api(self, reporte_data):
        """Llamada API para eliminar reporte"""
        try:
            reporte_id = reporte_data.get('id', '')
            cuadrilla = reporte_data.get('cuadrilla', 'Sin cuadrilla')
            numero_reporte = reporte_data.get('numero_reporte', 'N/A')

            if not reporte_id:
                self.progress_dialog_eliminacion.dismiss()
                self._mostrar_error_dialog("Error: ID de reporte no válido")
                return

            # NUEVO v8.0: Realizar llamada DELETE al backend usando cliente autenticado
            result = auth_client.delete(
                f"/api/reports/generales/{reporte_id}",
                timeout=10
            )

            self.progress_dialog_eliminacion.dismiss()

            if result['success']:
                data = result['data']
                if data.get('success'):
                    # Éxito - mostrar mensaje y actualizar lista
                    self._mostrar_mensaje_exito(f"Reporte N°{numero_reporte} eliminado exitosamente")

                    # Actualizar lista automáticamente
                    Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)
                else:
                    self._mostrar_error_dialog(f"Error: {data.get('error', 'Error desconocido')}")
            else:
                error_msg = result.get('message', 'Error del servidor')
                self._mostrar_error_dialog(f"Error: {error_msg}")

        except Exception as e:
            self.progress_dialog_eliminacion.dismiss()
            self._mostrar_error_dialog(f"Error de conexión: {str(e)}")

    def _mostrar_error_dialog(self, mensaje):
        """Mostrar dialog de error"""
        error_dialog = MDDialog(
            title="❌ Error",
            text=mensaje,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: error_dialog.dismiss()
                )
            ]
        )
        error_dialog.open()

    def _mostrar_mensaje_exito(self, mensaje):
        """Mostrar mensaje de éxito"""
        exito_dialog = MDDialog(
            title="✅ Éxito",
            text=mensaje,
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: exito_dialog.dismiss()
                )
            ]
        )
        exito_dialog.open()

    def _refrescar_datos(self):
        """Refrescar datos de la pantalla actual"""
        if hasattr(self, 'creation_layout') and self.creation_layout in self.parent_layout.children:
            # Estamos en pantalla de creación, recargar cuadrillas
            self._cargar_cuadrillas_data()
        else:
            # Estamos en pantalla principal, recargar lista
            self._cargar_pantalla_principal()

    def _volver_menu_principal(self):
        """Volver al menú principal de reportes"""
        if hasattr(self.parent_layout, 'mostrar_menu_reportes'):
            self.parent_layout.mostrar_menu_reportes()
        elif hasattr(self.parent_layout, 'parent') and hasattr(self.parent_layout.parent, 'mostrar_menu_reportes'):
            self.parent_layout.parent.mostrar_menu_reportes()