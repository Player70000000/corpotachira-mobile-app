#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
CORPOTACHIRA v8.0 - APK de Prueba Mínima
Sistema de Chat Empresarial
"""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.textinput import TextInput
from kivy.clock import Clock
import requests


class CorpotachiraApp(App):
    def build(self):
        self.title = "CORPOTACHIRA v8.0"

        # Layout principal
        main_layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Título
        title = Label(
            text='CORPOTACHIRA v8.0\nSistema de Chat Empresarial',
            font_size='20sp',
            size_hint_y=None,
            height='100dp',
            halign='center'
        )
        title.bind(size=title.setter('text_size'))

        # Status de conexión
        self.status_label = Label(
            text='Estado: Iniciando...',
            font_size='14sp',
            size_hint_y=None,
            height='50dp'
        )

        # Input de prueba
        self.text_input = TextInput(
            hint_text='Escribe un mensaje de prueba...',
            size_hint_y=None,
            height='40dp'
        )

        # Botones
        button_layout = BoxLayout(size_hint_y=None, height='50dp', spacing=10)

        test_btn = Button(text='Probar Conexión')
        test_btn.bind(on_press=self.test_connection)

        clear_btn = Button(text='Limpiar')
        clear_btn.bind(on_press=self.clear_input)

        # Área de mensajes
        self.messages_label = Label(
            text='¡Bienvenido a CORPOTACHIRA v8.0!\n\nEste es un APK de prueba del sistema de chat empresarial.',
            font_size='12sp',
            text_size=(None, None),
            halign='left',
            valign='top'
        )

        # Ensamblar layout
        button_layout.add_widget(test_btn)
        button_layout.add_widget(clear_btn)

        main_layout.add_widget(title)
        main_layout.add_widget(self.status_label)
        main_layout.add_widget(self.text_input)
        main_layout.add_widget(button_layout)
        main_layout.add_widget(self.messages_label)

        # Probar conexión al iniciar
        Clock.schedule_once(self.initial_test, 1)

        return main_layout

    def initial_test(self, dt):
        self.status_label.text = 'Estado: Probando conexión...'
        try:
            response = requests.get('https://chat-cv1i.onrender.com/', timeout=5)
            if response.status_code == 200:
                self.status_label.text = 'Estado: ✅ Conectado al servidor'
                self.messages_label.text += '\n\n✅ Conexión exitosa al backend de producción!'
            else:
                self.status_label.text = f'Estado: ⚠️ Respuesta: {response.status_code}'
        except Exception as e:
            self.status_label.text = f'Estado: ❌ Error de conexión'
            self.messages_label.text += f'\n\n❌ Error: {str(e)[:50]}...'

    def test_connection(self, instance):
        self.initial_test(None)
        if self.text_input.text:
            self.messages_label.text += f'\n\n📱 Mensaje: {self.text_input.text}'

    def clear_input(self, instance):
        self.text_input.text = ''
        self.messages_label.text = '¡Bienvenido a CORPOTACHIRA v8.0!\n\nEste es un APK de prueba del sistema de chat empresarial.'


if __name__ == '__main__':
    CorpotachiraApp().run()