import numpy as np
import threading
import time
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.spinner import Spinner
from kivy.clock import Clock, mainthread
import logging
from datetime import datetime
import os

class SoundHunter:
    def __init__(self):
        print("Инициализация SoundHunter...")
        self.sample_rate = 44100
        self.chunk_size = 1024
        self.calibration_constant = 60.0
        self.scanning = False
        self.max_db = -np.inf
        self.best_distance = 0
        self.sensitivity = 5
        self.screech_threshold = 0.5
        self.min_db_level = 0
        self.scan_results = []
        self.target_frequencies = [800, 1200, 2500, 3500, 5000]
        
        # Папка для результатов
        self.results_dir = "SoundHunter_Results"
        os.makedirs(self.results_dir, exist_ok=True)
        
        # Логирование
        self.setup_logging()
        self.adjust_parameters_by_sensitivity()
        
        self.logger.info("SoundHunter инициализирован")
        self.logger.info(f"Чувствительность: {self.sensitivity}/10")
    
    def setup_logging(self):
        self.logger = logging.getLogger('SoundHunter')
        self.logger.setLevel(logging.INFO)
    
    def set_sensitivity(self, level):
        if 1 <= level <= 10:
            self.sensitivity = level
            self.adjust_parameters_by_sensitivity()
            self.logger.info(f"Чувствительность установлена на: {level}")
            return True
        return False
    
    def adjust_parameters_by_sensitivity(self):
        sensitivity_map = {
            1: {'threshold': 0.9, 'min_db': -20},
            2: {'threshold': 0.8, 'min_db': -15},
            3: {'threshold': 0.7, 'min_db': -10},
            4: {'threshold': 0.6, 'min_db': -5},
            5: {'threshold': 0.5, 'min_db': 0},
            6: {'threshold': 0.4, 'min_db': 5},
            7: {'threshold': 0.3, 'min_db': 10},
            8: {'threshold': 0.2, 'min_db': 15},
            9: {'threshold': 0.1, 'min_db': 20},
            10: {'threshold': 0.05, 'min_db': 25}
        }
        params = sensitivity_map.get(self.sensitivity, sensitivity_map[5])
        self.screech_threshold = params['threshold']
        self.min_db_level = params['min_db']
    
    def simulate_audio_capture(self):
        """Симуляция захвата аудио с имитацией скрипов"""
        sample_count = 0
        while self.scanning:
            try:
                # Генерируем базовый сигнал
                t = np.linspace(0, 0.1, self.chunk_size)
                signal = (0.05 * np.sin(2 * np.pi * 60 * t) +
                         0.03 * np.sin(2 * np.pi * 120 * t) +
                         0.02 * np.random.randn(self.chunk_size))
                
                # Периодически добавляем скрипы
                if sample_count % 50 == 0:
                    screech_strength = 0.3 + (self.sensitivity * 0.07)
                    screech = (screech_strength * np.sin(2 * np.pi * 2500 * t) +
                              0.2 * np.sin(2 * np.pi * 3500 * t))
                    signal += screech
                    self.logger.info(f"Сгенерирован скрип (сила: {screech_strength:.2f})")
                
                sample_count += 1
                time.sleep(0.05)
                
            except Exception as e:
                self.logger.error(f"Ошибка симуляции аудио: {e}")
                break
    
    def calibrate_microphone(self, update_callback=None):
        """Калибровка микрофона"""
        if update_callback:
            update_callback("Калибровка... Обеспечьте тишину.")
        
        for i in range(3):
            time.sleep(1)
            if update_callback:
                update_callback(f"Калибровка... {i+1}/3")
        
        self.calibration_constant = 60.0 + np.random.uniform(-2, 2)
        self.logger.info(f"Калибровка завершена! Константа: {self.calibration_constant:.2f}")
        
        if update_callback:
            update_callback(f"Калибровка завершена! Константа: {self.calibration_constant:.2f}")
    
    def start_scanning(self, duration=60, update_callback=None):
        """Запуск процесса сканирования"""
        self.logger.info(f"Начало сканирования на {duration} секунд")
        self.scanning = True
        self.max_db = -np.inf
        self.scan_results = []
        
        if update_callback:
            update_callback("Сканирование начато...")
        
        # Запускаем симуляцию аудио
        audio_thread = threading.Thread(target=self.simulate_audio_capture, daemon=True)
        audio_thread.start()
        
        start_time = time.time()
        detections = 0
        
        while time.time() - start_time < duration and self.scanning:
            # Имитация обнаружения скрипов
            if int(time.time() - start_time) % 10 == 0:
                detections += 1
                current_db = 60 + np.random.uniform(-5, 5) + self.sensitivity
                distance = np.random.uniform(0.1, 5.0)
                confidence = 0.7 + np.random.uniform(-0.2, 0.2)
                
                if current_db > self.max_db:
                    self.max_db = current_db
                    self.best_distance = distance
                
                result = {
                    'timestamp': datetime.now().isoformat(),
                    'db_level': float(current_db),
                    'distance': float(distance),
                    'confidence': float(confidence),
                    'sensitivity': self.sensitivity
                }
                self.scan_results.append(result)
                
                message = f"Скрип обнаружен! {current_db:.1f} dB, {distance:.1f} м, уверенность: {confidence:.2f}"
                self.logger.info(message)
                
                if update_callback:
                    update_callback(message)
            
            time.sleep(1)
        
        self.scanning = False
        
        summary = f"Сканирование завершено. Скрипов: {detections}\nМакс. уровень: {self.max_db:.1f} dB\nРасстояние: {self.best_distance:.1f} м"
        self.logger.info(summary)
        
        if update_callback:
            update_callback(summary)

class SoundHunterApp(App):
    def build(self):
        self.hunter = SoundHunter()
        self.status_text = "Готов к работе"
        
        layout = BoxLayout(orientation='vertical', padding=10, spacing=10)
        
        self.status_label = Label(text=self.status_text, size_hint_y=0.2)
        layout.add_widget(self.status_label)
        
        # Чувствительность
        sens_layout = BoxLayout(size_hint_y=0.1)
        sens_label = Label(text="Чувствительность:")
        self.sens_spinner = Spinner(text="5", values=[str(i) for i in range(1, 11)])
        sens_layout.add_widget(sens_label)
        sens_layout.add_widget(self.sens_spinner)
        layout.add_widget(sens_layout)
        
        # Кнопки
        buttons = [
            ("Калибровать микрофон", self.on_calibrate),
            ("Начать сканирование", self.on_start_scan),
            ("Остановить сканирование", self.on_stop_scan)
        ]
        
        for text, callback in buttons:
            btn = Button(text=text)
            btn.bind(on_press=callback)
            layout.add_widget(btn)
        
        return layout

    def on_calibrate(self, instance):
        threading.Thread(target=self.calibrate_thread).start()
    
    def calibrate_thread(self):
        self.update_status("Калибровка начата...")
        self.hunter.calibrate_microphone(self.update_status)
    
    def on_start_scan(self, instance):
        if not self.hunter.scanning:
            # Установим чувствительность из спиннера
            self.hunter.set_sensitivity(int(self.sens_spinner.text))
            threading.Thread(target=self.scan_thread).start()
    
    def scan_thread(self):
        self.update_status("Сканирование начато...")
        self.hunter.start_scanning(update_callback=self.update_status)
    
    def on_stop_scan(self, instance):
        self.hunter.scanning = False
        self.update_status("Сканирование остановлено")
    
    @mainthread
    def update_status(self, text):
        self.status_text = text
        self.status_label.text = text

if __name__ == "__main__":
    SoundHunterApp().run()