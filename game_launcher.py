import sys
import json
import os
import cv2
import numpy as np
from PIL import Image, ImageGrab
import keyboard
import winreg
import vdf
import psutil
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from PyQt5.QtWidgets import *
from PyQt5.QtCore import *
from PyQt5.QtGui import *

class GameInfo:
    def __init__(self, name, path, playtime=0, icon_path=None):
        self.name = name
        self.path = path
        self.playtime = playtime
        self.icon_path = icon_path
        self.last_played = None

class Settings:
    def __init__(self):
        self.settings_file = "settings.json"
        self.default_settings = {
            'video': {
                'codec': 'H264',
                'container': 'MP4',
                'quality': 80,
                'bitrate': 5000,
                'resolution': 'Оригінальна',
                'width': 1920,
                'height': 1080,
                'fps': 30,
                'use_gpu': False,
                'record_audio': True,
                'show_cursor': True,
                'show_clicks': True
            },
            'screenshot': {
                'format': 'PNG',
                'quality': 90,
                'save_path': 'screenshots'
            },
            'interface': {
                'theme': 'dark',
                'language': 'uk',
                'window_size': [1000, 700],
                'show_game_time': True,
                'show_game_icons': True
            }
        }
        self.load_settings()

    def load_settings(self):
        try:
            if os.path.exists(self.settings_file):
                with open(self.settings_file, 'r', encoding='utf-8') as f:
                    saved_settings = json.load(f)
                    # Об'єднуємо збережені налаштування з дефолтними
                    self.settings = self.merge_settings(self.default_settings, saved_settings)
            else:
                self.settings = self.default_settings
        except Exception as e:
            print(f"Помилка завантаження налаштувань: {e}")
            self.settings = self.default_settings

    def merge_settings(self, default, saved):
        """Рекурсивно об'єднує збережені налаштування з дефолтними"""
        result = default.copy()
        for key, value in saved.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self.merge_settings(result[key], value)
            else:
                result[key] = value
        return result

    def save_settings(self):
        try:
            with open(self.settings_file, 'w', encoding='utf-8') as f:
                json.dump(self.settings, f, indent=4, ensure_ascii=False)
        except Exception as e:
            print(f"Помилка збереження налаштувань: {e}")

    def get_video_settings(self):
        return self.settings['video']

    def get_screenshot_settings(self):
        return self.settings['screenshot']

    def get_interface_settings(self):
        return self.settings['interface']

    def update_video_settings(self, settings):
        self.settings['video'].update(settings)
        self.save_settings()

    def update_screenshot_settings(self, settings):
        self.settings['screenshot'].update(settings)
        self.save_settings()

    def update_interface_settings(self, settings):
        self.settings['interface'].update(settings)
        self.save_settings()

class AdvancedSettingsDialog(QDialog):
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self.settings = settings
        self.setWindowTitle("Розширені налаштування")
        self.setMinimumWidth(600)
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        
        # Вкладки налаштувань
        tabs = QTabWidget()
        
        # Вкладка відеозапису
        video_tab = QWidget()
        video_layout = QFormLayout(video_tab)
        
        # Налаштування відео
        self.codec_combo = QComboBox()
        self.codec_combo.addItems(['H264', 'XVID', 'MJPG', 'VP8', 'VP9'])
        self.codec_combo.setCurrentText(self.settings.get_video_settings()['codec'])
        video_layout.addRow("Кодек:", self.codec_combo)
        
        self.container_combo = QComboBox()
        self.container_combo.addItems(['MP4', 'AVI', 'MKV', 'MOV', 'WebM'])
        self.container_combo.setCurrentText(self.settings.get_video_settings()['container'])
        video_layout.addRow("Контейнер:", self.container_combo)
        
        # Якість
        quality_group = QGroupBox("Налаштування якості")
        quality_layout = QVBoxLayout()
        
        self.quality_slider = QSlider(Qt.Horizontal)
        self.quality_slider.setRange(1, 100)
        self.quality_slider.setValue(self.settings.get_video_settings()['quality'])
        quality_layout.addWidget(QLabel("Якість відео:"))
        quality_layout.addWidget(self.quality_slider)
        
        self.bitrate_spin = QSpinBox()
        self.bitrate_spin.setRange(1000, 50000)
        self.bitrate_spin.setSuffix(" Kbps")
        self.bitrate_spin.setValue(self.settings.get_video_settings()['bitrate'])
        quality_layout.addWidget(QLabel("Бітрейт:"))
        quality_layout.addWidget(self.bitrate_spin)
        
        quality_group.setLayout(quality_layout)
        video_layout.addRow(quality_group)
        
        # Роздільна здатність
        resolution_group = QGroupBox("Роздільна здатність")
        resolution_layout = QGridLayout()
        
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems(['Оригінальна', '4K', '1440p', '1080p', '720p', 'Користувацька'])
        self.resolution_combo.setCurrentText(self.settings.get_video_settings()['resolution'])
        resolution_layout.addWidget(self.resolution_combo, 0, 0, 1, 2)
        
        self.width_spin = QSpinBox()
        self.width_spin.setRange(1, 7680)
        self.width_spin.setValue(self.settings.get_video_settings()['width'])
        resolution_layout.addWidget(QLabel("Ширина:"), 1, 0)
        resolution_layout.addWidget(self.width_spin, 1, 1)
        
        self.height_spin = QSpinBox()
        self.height_spin.setRange(1, 4320)
        self.height_spin.setValue(self.settings.get_video_settings()['height'])
        resolution_layout.addWidget(QLabel("Висота:"), 2, 0)
        resolution_layout.addWidget(self.height_spin, 2, 1)
        
        resolution_group.setLayout(resolution_layout)
        video_layout.addRow(resolution_group)
        
        # Додаткові налаштування
        advanced_group = QGroupBox("Додаткові налаштування")
        advanced_layout = QVBoxLayout()
        
        self.gpu_check = QCheckBox("Використовувати апаратне прискорення GPU")
        self.gpu_check.setChecked(self.settings.get_video_settings()['use_gpu'])
        advanced_layout.addWidget(self.gpu_check)
        
        self.audio_check = QCheckBox("Записувати звук")
        self.audio_check.setChecked(self.settings.get_video_settings()['record_audio'])
        advanced_layout.addWidget(self.audio_check)
        
        self.cursor_check = QCheckBox("Показувати курсор")
        self.cursor_check.setChecked(self.settings.get_video_settings()['show_cursor'])
        advanced_layout.addWidget(self.cursor_check)
        
        self.clicks_check = QCheckBox("Показувати кліки миші")
        self.clicks_check.setChecked(self.settings.get_video_settings()['show_clicks'])
        advanced_layout.addWidget(self.clicks_check)
        
        advanced_group.setLayout(advanced_layout)
        video_layout.addRow(advanced_group)
        
        video_tab.setLayout(video_layout)
        tabs.addTab(video_tab, "Відео")
        
        # Вкладка скріншотів
        screenshot_tab = QWidget()
        screenshot_layout = QFormLayout(screenshot_tab)
        
        self.screenshot_format = QComboBox()
        self.screenshot_format.addItems(['PNG', 'JPG', 'BMP'])
        self.screenshot_format.setCurrentText(self.settings.get_screenshot_settings()['format'])
        screenshot_layout.addRow("Формат:", self.screenshot_format)
        
        self.screenshot_quality = QSlider(Qt.Horizontal)
        self.screenshot_quality.setRange(1, 100)
        self.screenshot_quality.setValue(self.settings.get_screenshot_settings()['quality'])
        screenshot_layout.addRow("Якість:", self.screenshot_quality)
        
        screenshot_tab.setLayout(screenshot_layout)
        tabs.addTab(screenshot_tab, "Скріншоти")
        
        layout.addWidget(tabs)
        
        # Кнопки
        buttons = QHBoxLayout()
        save_btn = QPushButton("Зберегти")
        save_btn.clicked.connect(self.save_settings)
        cancel_btn = QPushButton("Скасувати")
        cancel_btn.clicked.connect(self.reject)
        buttons.addWidget(save_btn)
        buttons.addWidget(cancel_btn)
        layout.addLayout(buttons)

    def save_settings(self):
        # Зберігаємо налаштування відео
        video_settings = {
            'codec': self.codec_combo.currentText(),
            'container': self.container_combo.currentText(),
            'quality': self.quality_slider.value(),
            'bitrate': self.bitrate_spin.value(),
            'resolution': self.resolution_combo.currentText(),
            'width': self.width_spin.value(),
            'height': self.height_spin.value(),
            'use_gpu': self.gpu_check.isChecked(),
            'record_audio': self.audio_check.isChecked(),
            'show_cursor': self.cursor_check.isChecked(),
            'show_clicks': self.clicks_check.isChecked()
        }
        self.settings.update_video_settings(video_settings)

        # Зберігаємо налаштування скріншотів
        screenshot_settings = {
            'format': self.screenshot_format.currentText(),
            'quality': self.screenshot_quality.value()
        }
        self.settings.update_screenshot_settings(screenshot_settings)

        self.accept()

class VideoRecorder(QThread):
    finished = pyqtSignal()
    error = pyqtSignal(str)

    def __init__(self, settings):
        super().__init__()
        self.settings = settings
        self.is_recording = False
        self.output_filename = None

    def run(self):
        try:
            # Створюємо папку для записів якщо її немає
            if not os.path.exists("recordings"):
                os.makedirs("recordings")

            # Генеруємо ім'я файлу
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            self.output_filename = os.path.join("recordings", f"recording_{timestamp}.{self.settings['container'].lower()}")

            # Отримуємо розміри екрану
            screen = ImageGrab.grab()
            width = height = 0

            if self.settings['resolution'] == 'Оригінальна':
                width, height = screen.size
            elif self.settings['resolution'] == '4K':
                width, height = 3840, 2160
            elif self.settings['resolution'] == '1440p':
                width, height = 2560, 1440
            elif self.settings['resolution'] == '1080p':
                width, height = 1920, 1080
            elif self.settings['resolution'] == '720p':
                width, height = 1280, 720
            else:  # Користувацька
                width = self.settings['width']
                height = self.settings['height']

            # Налаштування відеозапису
            fourcc = cv2.VideoWriter_fourcc(*self.get_codec())
            out = cv2.VideoWriter(
                self.output_filename,
                fourcc,
                30,  # FPS
                (width, height)
            )

            # Завантажуємо стандартні курсори
            cursor_normal = cv2.imread("cursors/normal.png", cv2.IMREAD_UNCHANGED)
            cursor_click = cv2.imread("cursors/click.png", cv2.IMREAD_UNCHANGED)
            
            if cursor_normal is None:
                # Якщо файли курсорів не знайдено, створюємо їх
                self.save_default_cursors()
                cursor_normal = cv2.imread("cursors/normal.png", cv2.IMREAD_UNCHANGED)
                cursor_click = cv2.imread("cursors/click.png", cv2.IMREAD_UNCHANGED)

            self.is_recording = True
            while self.is_recording:
                # Захоплення екрану
                frame = ImageGrab.grab(bbox=(0, 0, width, height))
                frame = cv2.cvtColor(np.array(frame), cv2.COLOR_RGB2BGR)

                # Додавання курсора якщо потрібно
                if self.settings['show_cursor']:
                    cursor_pos = QCursor.pos()
                    cursor_x, cursor_y = cursor_pos.x(), cursor_pos.y()

                    # Визначаємо, який курсор використовувати
                    current_cursor = cursor_click if self.settings['show_clicks'] and keyboard.is_pressed('mouse') else cursor_normal

                    # Перевіряємо чи курсор в межах екрану
                    if 0 <= cursor_x < width and 0 <= cursor_y < height:
                        # Отримуємо розміри курсору
                        cursor_h, cursor_w = current_cursor.shape[:2]
                        
                        # Обчислюємо координати для накладання курсору
                        x1 = cursor_x
                        y1 = cursor_y
                        x2 = min(x1 + cursor_w, width)
                        y2 = min(y1 + cursor_h, height)
                        
                        # Обрізаємо курсор, якщо він виходить за межі екрану
                        cursor_w = x2 - x1
                        cursor_h = y2 - y1
                        
                        if cursor_w > 0 and cursor_h > 0:
                            cursor_area = current_cursor[:cursor_h, :cursor_w]
                            
                            # Створюємо маску з альфа-каналу
                            if cursor_area.shape[2] == 4:  # Якщо є альфа-канал
                                alpha = cursor_area[:, :, 3] / 255.0
                                alpha = np.repeat(alpha[:, :, np.newaxis], 3, axis=2)
                                
                                # Накладаємо курсор з урахуванням прозорості
                                cursor_rgb = cursor_area[:, :, :3]
                                frame_area = frame[y1:y2, x1:x2]
                                frame[y1:y2, x1:x2] = frame_area * (1 - alpha) + cursor_rgb * alpha

                # Запис кадру
                out.write(frame)

                # Перевірка клавіші для зупинки
                if keyboard.is_pressed('f9'):  # F9 для зупинки запису
                    self.is_recording = False

            out.release()
            self.finished.emit()

        except Exception as e:
            self.error.emit(str(e))
            self.is_recording = False

    def save_default_cursors(self):
        """Створює файли курсорів за замовчуванням"""
        if not os.path.exists("cursors"):
            os.makedirs("cursors")
        
        # Створюємо зображення для звичайного курсору
        normal_cursor = np.zeros((32, 32, 4), dtype=np.uint8)
        
        # Малюємо курсор у вигляді трикутника
        triangle_points = np.array([[0, 0], [0, 24], [16, 16]], np.int32)
        
        # Заливка білим кольором
        cv2.fillPoly(normal_cursor, [triangle_points], (255, 255, 255, 255))
        
        # Чорна обводка
        cv2.polylines(normal_cursor, [triangle_points], True, (0, 0, 0, 255), 1)
        
        cv2.imwrite("cursors/normal.png", normal_cursor)
        
        # Створюємо зображення для курсору кліку
        click_cursor = normal_cursor.copy()
        # Додаємо червоний кружок
        cv2.circle(click_cursor, (20, 20), 5, (0, 0, 255, 255), -1)
        cv2.imwrite("cursors/click.png", click_cursor)

    def stop(self):
        self.is_recording = False

    def get_codec(self):
        codec_map = {
            'H264': 'avc1',
            'XVID': 'XVID',
            'MJPG': 'MJPG',
            'VP8': 'VP80',
            'VP9': 'VP90'
        }
        return codec_map.get(self.settings['codec'], 'avc1')

class GameLauncher(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Game Launcher")
        self.settings = Settings()
        
        # Встановлюємо розмір вікна з налаштувань
        window_size = self.settings.get_interface_settings()['window_size']
        self.setMinimumSize(*window_size)
        
        # Завантаження стилів
        with open('styles.qss', 'r') as f:
            self.setStyleSheet(f.read())
        
        self.games = []
        self.recorder = None
        self.recording = False
        self.setup_ui()
        self.load_games()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)
        
        # Верхня панель
        top_panel = QHBoxLayout()
        
        search_box = QLineEdit()
        search_box.setPlaceholderText("Пошук ігор...")
        search_box.textChanged.connect(self.filter_games)
        top_panel.addWidget(search_box)
        
        refresh_btn = QPushButton("Оновити")
        refresh_btn.clicked.connect(self.load_games)
        top_panel.addWidget(refresh_btn)
        
        settings_btn = QPushButton("Налаштування")
        settings_btn.clicked.connect(self.show_settings)
        top_panel.addWidget(settings_btn)
        
        layout.addLayout(top_panel)
        
        # Список ігор
        self.games_list = QListWidget()
        self.games_list.setViewMode(QListWidget.IconMode)
        self.games_list.setIconSize(QSize(128, 128))
        self.games_list.setSpacing(10)
        self.games_list.setResizeMode(QListWidget.Adjust)
        self.games_list.itemDoubleClicked.connect(self.launch_game)
        layout.addWidget(self.games_list)
        
        # Нижня панель
        bottom_panel = QHBoxLayout()
        
        screenshot_btn = QPushButton("Скріншот")
        screenshot_btn.clicked.connect(self.take_screenshot)
        bottom_panel.addWidget(screenshot_btn)
        
        record_btn = QPushButton("Почати запис")
        record_btn.clicked.connect(self.toggle_recording)
        bottom_panel.addWidget(record_btn)
        
        layout.addLayout(bottom_panel)
        
    def load_games(self):
        self.games.clear()
        self.games_list.clear()
        
        # Steam ігри
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\Wow6432Node\Valve\Steam") as key:
                steam_path = winreg.QueryValueEx(key, "InstallPath")[0]
                
                if os.path.exists(steam_path):
                    libraryfolders_path = os.path.join(steam_path, "steamapps", "libraryfolders.vdf")
                    if os.path.exists(libraryfolders_path):
                        with open(libraryfolders_path, 'r', encoding='utf-8') as f:
                            data = vdf.load(f)
                            
                            for library in data.get('libraryfolders', {}).values():
                                if isinstance(library, dict):
                                    library_path = library.get('path')
                                    if library_path:
                                        apps_path = os.path.join(library_path, "steamapps")
                                        if os.path.exists(apps_path):
                                            for manifest in os.listdir(apps_path):
                                                if manifest.startswith("appmanifest"):
                                                    manifest_path = os.path.join(apps_path, manifest)
                                                    with open(manifest_path, 'r', encoding='utf-8') as mf:
                                                        app_data = vdf.load(mf)
                                                        if 'AppState' in app_data:
                                                            name = app_data['AppState'].get('name', '')
                                                            install_dir = app_data['AppState'].get('installdir', '')
                                                            
                                                            game_path = os.path.join(apps_path, "common", install_dir)
                                                            if os.path.exists(game_path):
                                                                for root, dirs, files in os.walk(game_path):
                                                                    for file in files:
                                                                        if file.endswith('.exe'):
                                                                            exe_path = os.path.join(root, file)
                                                                            playtime = self.get_steam_playtime(app_data['AppState'].get('appid', ''))
                                                                            game = GameInfo(name, exe_path, playtime)
                                                                            self.games.append(game)
                                                                            break
        except Exception as e:
            print(f"Помилка при завантаженні Steam ігор: {e}")
        
        # Epic Games
        try:
            with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, r"SOFTWARE\WOW6432Node\Epic Games\EpicGamesLauncher") as key:
                epic_path = winreg.QueryValueEx(key, "AppDataPath")[0]
                manifest_path = os.path.join(os.path.dirname(epic_path), "Manifests")
                
                if os.path.exists(manifest_path):
                    for file in os.listdir(manifest_path):
                        if file.endswith('.item'):
                            with open(os.path.join(manifest_path, file), 'r', encoding='utf-8') as f:
                                try:
                                    manifest = json.load(f)
                                    if 'InstallLocation' in manifest and 'DisplayName' in manifest:
                                        game_path = manifest['InstallLocation']
                                        for root, dirs, files in os.walk(game_path):
                                            for file in files:
                                                if file.endswith('.exe'):
                                                    exe_path = os.path.join(root, file)
                                                    game = GameInfo(manifest['DisplayName'], exe_path)
                                                    self.games.append(game)
                                                    break
                                except:
                                    continue
        except Exception as e:
            print(f"Помилка при завантаженні Epic Games: {e}")
        
        # Оновлення списку
        self.update_games_list()
    
    def update_games_list(self):
        self.games_list.clear()
        for game in self.games:
            item = QListWidgetItem(game.name)
            item.setData(Qt.UserRole, game)
            
            # Отримання іконки
            icon = self.get_game_icon(game.path)
            item.setIcon(icon)
            
            # Додавання інформації про час гри
            if game.playtime > 0:
                hours = game.playtime / 60
                item.setToolTip(f"Зіграно: {hours:.1f} годин")
            
            self.games_list.addItem(item)
    
    def get_game_icon(self, path):
        icon = QFileIconProvider().icon(QFileInfo(path))
        return icon
    
    def get_steam_playtime(self, app_id):
        try:
            # Тут можна додати логіку отримання часу гри через Steam Web API
            return 0
        except:
            return 0
    
    def filter_games(self, text):
        for i in range(self.games_list.count()):
            item = self.games_list.item(i)
            item.setHidden(text.lower() not in item.text().lower())
    
    def launch_game(self, item):
        game = item.data(Qt.UserRole)
        try:
            QProcess.startDetached(game.path, [], os.path.dirname(game.path))
        except Exception as e:
            QMessageBox.critical(self, "Помилка", f"Не вдалося запустити гру: {str(e)}")
    
    def take_screenshot(self):
        screen = QApplication.primaryScreen()
        screenshot = screen.grabWindow(0)
        
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"screenshot_{timestamp}.png"
        
        if not os.path.exists("screenshots"):
            os.makedirs("screenshots")
        
        filepath = os.path.join("screenshots", filename)
        screenshot.save(filepath, "PNG", quality=100)
        
        QMessageBox.information(self, "Скріншот", f"Скріншот збережено: {filepath}")
    
    def toggle_recording(self):
        if not self.recording:
            # Отримуємо налаштування з діалогу
            dialog = AdvancedSettingsDialog(self.settings, self)
            if dialog.exec_() == QDialog.Accepted:
                settings = self.settings.get_video_settings()
                # Створюємо та запускаємо recorder
                self.recorder = VideoRecorder(settings)
                self.recorder.finished.connect(self.recording_finished)
                self.recorder.error.connect(self.recording_error)
                self.recorder.start()
                self.recording = True

                # Оновлюємо текст кнопки
                sender = self.sender()
                if isinstance(sender, QPushButton):
                    sender.setText("Зупинити запис (F9)")

                QMessageBox.information(self, "Запис", "Запис почато. Натисніть F9 для зупинки.")
        else:
            self.stop_recording()

    def recording_finished(self):
        self.recording = False
        sender = self.findChild(QPushButton, "")
        if sender:
            sender.setText("Почати запис")
        QMessageBox.information(self, "Запис", f"Запис збережено: {self.recorder.output_filename}")

    def recording_error(self, error_msg):
        self.recording = False
        sender = self.findChild(QPushButton, "")
        if sender:
            sender.setText("Почати запис")
        QMessageBox.critical(self, "Помилка", f"Помилка запису: {error_msg}")

    def stop_recording(self):
        if self.recorder:
            self.recorder.stop()
            self.recording = False
            sender = self.sender()
            if isinstance(sender, QPushButton):
                sender.setText("Почати запис")

    def show_settings(self):
        dialog = AdvancedSettingsDialog(self.settings, self)
        if dialog.exec_() == QDialog.Accepted:
            # Оновлюємо інтерфейс відповідно до нових налаштувань
            self.update_interface()

    def update_interface(self):
        """Оновлює інтерфейс відповідно до налаштувань"""
        interface_settings = self.settings.get_interface_settings()
        
        # Оновлюємо розмір вікна
        if 'window_size' in interface_settings:
            self.resize(*interface_settings['window_size'])
        
        # Оновлюємо відображення часу гри
        if 'show_game_time' in interface_settings:
            self.update_games_list()
        
        # Оновлюємо відображення іконок
        if 'show_game_icons' in interface_settings:
            self.update_games_list()

    def closeEvent(self, event):
        """Зберігаємо налаштування при закритті програми"""
        # Зберігаємо розмір вікна
        self.settings.update_interface_settings({
            'window_size': [self.width(), self.height()]
        })
        super().closeEvent(event)

if __name__ == '__main__':
    app = QApplication(sys.argv)
    
    # Встановлюємо глобальні налаштування анімації
    app.setEffectEnabled(Qt.UI_AnimateCombo, True)
    app.setEffectEnabled(Qt.UI_AnimateTooltip, True)
    app.setEffectEnabled(Qt.UI_FadeTooltip, True)
    
    window = GameLauncher()
    window.show()
    sys.exit(app.exec_())
