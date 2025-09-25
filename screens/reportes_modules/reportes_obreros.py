from kivymd.uix.boxlayout import MDBoxLayout
from kivymd.uix.scrollview import MDScrollView
from kivymd.uix.toolbar import MDTopAppBar
from kivymd.uix.button import MDRaisedButton, MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDLabel
from kivymd.uix.list import MDList
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.uix.widget import Widget

from utils.unified_api_client import unified_client as ReportesAPIClient
import requests
# NUEVO v8.0: Cliente autenticado
import sys, os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from utils.auth_client import auth_client


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
    """Item minimalista para lista de reportes: Texto del reporte + Botón Eliminar"""

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
        reporte_text = f"Reporte de Obreros N°{numero_reporte}"
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


class ReportesObrerosManager:
    """Gestor de reportes específicos para obreros"""

    def __init__(self, parent_layout):
        self.parent_layout = parent_layout
        self.api_client = ReportesAPIClient
        self.current_layout = None

    def mostrar_reportes_obreros(self):
        """Mostrar pantalla principal de reportes de obreros"""
        self.current_layout = MDBoxLayout(orientation="vertical", spacing="10dp")

        # Top bar
        top_bar = MDTopAppBar(
            title="👷‍♂️ Reportes de Obreros",
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
        self._cargar_resumen_obreros()

        # Mostrar en el layout principal
        self.parent_layout.clear_widgets()
        self.parent_layout.add_widget(self.current_layout)

    def _cargar_resumen_obreros(self):
        """Cargar resumen estadístico de obreros"""
        self.content_layout.clear_widgets()

        # Ejecutar directamente sin Clock para debug
        self._procesar_datos_obreros()

    def _procesar_datos_obreros(self):
        """Procesar y mostrar datos de obreros"""
        self.content_layout.clear_widgets()

        # Botón para generar nuevo reporte
        generar_button = MDRaisedButton(
            text="📊 GENERAR NUEVO REPORTE",
            md_bg_color=[0.2, 0.7, 0.3, 1],
            size_hint_y=None,
            height="50dp",
            on_release=lambda x: self._generar_nuevo_reporte()
        )

        # Título de lista
        lista_title = MDLabel(
            text="Lista de Reportes (Obreros)",
            theme_text_color="Primary",
            font_style="H6",
            size_hint_y=None,
            height="40dp"
        )

        # Scroll y lista para reportes
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
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)

    def _refrescar_datos(self):
        """Refrescar todos los datos"""
        self._cargar_resumen_obreros()

    def _generar_nuevo_reporte(self):
        """Generar nuevo reporte de obreros consultando la API"""
        # Mostrar dialog de confirmación primero
        self.confirmation_dialog = MDDialog(
            title="📊 Generar Nuevo Reporte",
            text="¿Deseas generar un nuevo reporte de obreros?\n\nEsto consultará todos los obreros activos en la base de datos.",
            buttons=[
                MDRaisedButton(
                    text="Cancelar",
                    on_release=lambda x: self.confirmation_dialog.dismiss()
                ),
                MDRaisedButton(
                    text="Generar",
                    md_bg_color=(0.2, 0.7, 0.3, 1),
                    on_release=lambda x: self._confirmar_generar_reporte()
                )
            ]
        )
        self.confirmation_dialog.open()

    def _confirmar_generar_reporte(self):
        """Confirmar y proceder con la generación del reporte"""
        self.confirmation_dialog.dismiss()

        # Mostrar dialog de progreso
        self.progress_dialog = MDDialog(
            title="🔄 Generando Reporte",
            text="Consultando base de datos y generando PDF...\nPor favor espera un momento.",
            auto_dismiss=False
        )
        self.progress_dialog.open()

        # Llamar a la API en segundo plano
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: self._llamar_api_generar(), 0.5)

    def _llamar_api_generar(self):
        """Llamar a la API para generar el reporte"""
        try:
            # NUEVO v8.0: Usar cliente autenticado
            result = auth_client.post(
                "/api/reports/obreros/generar",
                timeout=30
            )

            self.progress_dialog.dismiss()

            if result['success']:
                data = result['data']
                if data.get('success'):
                    reporte_info = data.get('reporte', {})
                    self._mostrar_exito_generacion(reporte_info)
                    # Actualizar la lista de reportes
                    self._cargar_lista_reportes()
                else:
                    self._mostrar_error_generacion(data.get('error', 'Error desconocido'))
            else:
                self._mostrar_error_generacion(f"Error del servidor: {response.status_code}")

        except Exception as e:
            self.progress_dialog.dismiss()
            self._mostrar_error_generacion(f"Error de conexión: {str(e)}")

    def _mostrar_exito_generacion(self, reporte_info):
        """Mostrar dialog de éxito con información del reporte"""
        numero_reporte = reporte_info.get('numero_reporte', 'N/A')
        total_obreros = reporte_info.get('total_obreros', 0)
        pdf_url = reporte_info.get('pdf_url', '')

        success_dialog = MDDialog(
            title="✅ Reporte Generado Exitosamente",
            text=f"Reporte N°{numero_reporte} creado con éxito\n\n📊 Obreros incluidos: {total_obreros}\n📄 PDF disponible para descargar\n\nEl reporte aparecerá en la lista a continuación.",
            buttons=[
                MDRaisedButton(
                    text="Ver PDF",
                    md_bg_color=(0.2, 0.6, 0.8, 1),
                    on_release=lambda x: self._abrir_pdf_reporte(pdf_url, success_dialog)
                ),
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: success_dialog.dismiss()
                )
            ]
        )
        success_dialog.open()

    def _mostrar_error_generacion(self, mensaje):
        """Mostrar dialog de error"""
        error_dialog = MDDialog(
            title="❌ Error Generando Reporte",
            text=f"No se pudo generar el reporte:\n\n{mensaje}\n\nPor favor intenta nuevamente.",
            buttons=[
                MDRaisedButton(
                    text="OK",
                    on_release=lambda x: error_dialog.dismiss()
                )
            ]
        )
        error_dialog.open()

    def _abrir_pdf_reporte(self, pdf_url, dialog):
        """Abrir PDF en el navegador"""
        dialog.dismiss()
        if pdf_url:
            import webbrowser
            full_url = f"{self.api_client.base_url}{pdf_url}"
            webbrowser.open(full_url)

    def _cargar_lista_reportes(self):
        """Cargar lista de reportes existentes desde la API"""
        try:
            # NUEVO v8.0: Usar cliente autenticado
            result = auth_client.get("/api/reports/obreros/listar", timeout=10)

            if result['success']:
                data = result['data']
                if data.get('success'):
                    reportes = data.get('reportes', [])
                    self._actualizar_lista_reportes(reportes)
                else:
                    self._mostrar_mensaje_lista("❌ Error cargando reportes")
            else:
                self._mostrar_mensaje_lista("❌ Error de conexión")

        except Exception as e:
            self._mostrar_mensaje_lista("⚠️ Sin conexión a servidor")

    def _actualizar_lista_reportes(self, reportes):
        """Actualizar la lista visual con los reportes usando diseño minimalista con botón eliminar"""
        self.reportes_list.clear_widgets()

        if not reportes:
            no_data_label = MDLabel(
                text="No hay reportes de obreros disponibles",
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

    def _mostrar_mensaje_lista(self, mensaje):
        """Mostrar mensaje informativo en la lista"""
        from kivymd.uix.list import OneLineListItem

        mensaje_item = OneLineListItem(
            text=mensaje,
            theme_text_color="Secondary"
        )
        self.reportes_list.clear_widgets()
        self.reportes_list.add_widget(mensaje_item)

    def _abrir_reporte_desde_lista(self, reporte_data):
        """Abrir PDF del reporte seleccionado desde la lista"""
        pdf_url = reporte_data.get('pdf_url', '')
        if pdf_url:
            import webbrowser
            full_url = f"{self.api_client.base_url}{pdf_url}"
            webbrowser.open(full_url)

    def _manejar_callback_item(self, accion, reporte_data):
        """Manejar callbacks de ReporteListItem"""
        if accion == 'abrir_pdf':
            self._abrir_reporte_desde_lista(reporte_data)
        elif accion == 'eliminar':
            self._confirmar_eliminacion_paso1(reporte_data)

    def _confirmar_eliminacion_paso1(self, reporte_data):
        """Primera confirmación - Básica"""
        numero_reporte = reporte_data.get('numero_reporte', 'N/A')
        total_obreros = reporte_data.get('total_obreros', 'Sin datos')

        self.dialog_confirmacion_1 = MDDialog(
            title="Confirmar Eliminación",
            text=f"¿Está seguro que desea eliminar el Reporte de Obreros N°{numero_reporte}?\n\n"
                 f"Total obreros: {total_obreros}\n"
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
                 f"El Reporte de Obreros N°{numero_reporte} será eliminado permanentemente.\n\n"
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
            text="Eliminando reporte de obreros...\nPor favor espera un momento.",
            auto_dismiss=False
        )
        self.progress_dialog_eliminacion.open()

        # Ejecutar eliminación en segundo plano
        Clock.schedule_once(lambda dt: self._eliminar_reporte_api(reporte_data), 0.5)

    def _eliminar_reporte_api(self, reporte_data):
        """Llamada API para eliminar reporte"""
        try:
            reporte_id = reporte_data.get('id', '')
            total_obreros = reporte_data.get('total_obreros', 'Sin datos')
            numero_reporte = reporte_data.get('numero_reporte', 'N/A')

            if not reporte_id:
                self.progress_dialog_eliminacion.dismiss()
                self._mostrar_error_dialog("Error: ID de reporte no válido")
                return

            # NUEVO v8.0: Realizar llamada DELETE al backend usando cliente autenticado
            result = auth_client.delete(
                f"/api/reports/obreros/{reporte_id}",
                timeout=10
            )

            self.progress_dialog_eliminacion.dismiss()

            if result['success']:
                data = result['data']
                if data.get('success'):
                    # Éxito - mostrar mensaje y actualizar lista
                    self._mostrar_mensaje_exito(f"Reporte de Obreros N°{numero_reporte} eliminado exitosamente")

                    # Actualizar lista automáticamente
                    Clock.schedule_once(lambda dt: self._cargar_lista_reportes(), 0.5)
                else:
                    self._mostrar_error_dialog(f"Error: {data.get('error', 'Error desconocido')}")
            else:
                self._mostrar_error_dialog(f"Error HTTP {response.status_code}")

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

    def _volver_menu_principal(self):
        """Volver al menú principal de reportes"""
        if hasattr(self.parent_layout, 'mostrar_menu_reportes'):
            self.parent_layout.mostrar_menu_reportes()
        elif hasattr(self.parent_layout, 'parent') and hasattr(self.parent_layout.parent, 'mostrar_menu_reportes'):
            self.parent_layout.parent.mostrar_menu_reportes()