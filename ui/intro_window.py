import tkinter as tk
from tkinter import ttk
import time

class IntroWindow:
    def __init__(self):
        self.root = tk.Tk()
        self.root.title("РОСНЕФТЬ")
        self.root.geometry("600x400")
        self.root.configure(bg='#18171C')
        self.root.overrideredirect(True)
        self.root.eval('tk::PlaceWindow . center')
        
        # Переменные для анимации
        self.current_alpha = 0.0
        self.text_alpha = 0.0
        
        self.create_intro_elements()
        
    def create_intro_elements(self):
        """Создает элементы с возможностью управления прозрачностью"""
        # Основной заголовок
        self.title_label = tk.Label(
            self.root, 
            text="ЦИФРОВОЙ ДВОЙНИК ТРУБОПРОВОДА",
            font=("Arial", 20, "bold"),
            bg='#18171C',
            fg='#FADADD'
        )
        self.title_label.place(relx=0.5, rely=0.4, anchor="center")
        self.title_label.configure(fg=self.hex_to_rgba('#FADADD', 0)) 
        
        # Подзаголовок
        self.subtitle_label = tk.Label(
            self.root,
            text="ПРОМЫШЛЕННАЯ СИСТЕМА АНАЛИЗА КОРРОЗИИ",
            font=("Arial", 12),
            bg='#18171C',
            fg='#FADADD'
        )
        self.subtitle_label.place(relx=0.5, rely=0.5, anchor="center")
        self.subtitle_label.configure(fg=self.hex_to_rgba('#FADADD', 0))
        
        # Информация о разработчике
        self.dev_label = tk.Label(
            self.root,
            text="by SUSLIK",
            font=("Arial", 11),
            bg='#18171C',
            fg='#FADADD',
            justify="center"
        )
        self.dev_label.place(relx=0.5, rely=0.6, anchor="center")
        self.dev_label.configure(fg=self.hex_to_rgba('#FADADD', 0))
        
        # Версия
        self.version_label = tk.Label(
            self.root,
            text="Версия 1.1 | 2026",
            font=("Arial", 10),
            bg='#18171C',
            fg='#FADADD'
        )
        self.version_label.place(relx=0.5, rely=0.9, anchor="center")
        self.version_label.configure(fg=self.hex_to_rgba('#FADADD', 0))
        
        # Начальная прозрачность окна
        self.root.attributes('-alpha', 0.0)
        
    def hex_to_rgba(self, hex_color, alpha):
        """Конвертирует hex цвет в rgba с альфой"""
        hex_color = hex_color.lstrip('#')
        rgb = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        return f'#{rgb[0]:02x}{rgb[1]:02x}{rgb[2]:02x}'
        
    def fade_window_in(self):
        """Плавное появление всего окна"""
        for i in range(0, 101, 5): 
            alpha = i / 100
            self.root.attributes('-alpha', alpha)
            self.root.update()
            time.sleep(0.05) 
            
    def fade_text_in(self):
        """Плавное появление текста"""
        # Заголовок появляется первым
        for i in range(0, 101, 4):
            alpha = i / 100
            self.title_label.configure(fg=self.hex_to_rgba('#FADADD', alpha))
            self.root.update()
            time.sleep(0.05)  
        
        # Подзаголовок появляется вторым
        for i in range(0, 101, 4):
            alpha = i / 100
            self.subtitle_label.configure(fg=self.hex_to_rgba('#FADADD', alpha))
            self.root.update()
            time.sleep(0.05)
        
        # Информация о разработчике появляется последней
        for i in range(0, 101, 4):
            alpha = i / 100
            self.dev_label.configure(fg=self.hex_to_rgba('#FADADD', alpha))
            self.root.update()
            time.sleep(0.05)
            
    def fade_text_out(self):
        """Плавное исчезновение текста"""
        for i in range(100, -1, -5):
            alpha = i / 100
            self.title_label.configure(fg=self.hex_to_rgba('#FADADD', alpha))
            self.subtitle_label.configure(fg=self.hex_to_rgba('#FADADD', alpha))
            self.dev_label.configure(fg=self.hex_to_rgba('#FADADD', alpha))
            self.root.update()
            time.sleep(0.04)
            
    def fade_window_out(self):
        """Плавное исчезновение всего окна"""
        for i in range(100, -1, -5):
            alpha = i / 100
            self.root.attributes('-alpha', alpha)
            self.root.update()
            time.sleep(0.04)
            
    def show(self):
        """Показывает анимированное интро"""
        # 1. Появление окна
        self.fade_window_in()
        
        # 2. Появление текста
        self.fade_text_in()
        
        # 3. Пауза с видимым текстом
        time.sleep(1)
        
        # 4. Исчезновение текста
        self.fade_text_out()
        
        # 5. Исчезновение окна
        self.fade_window_out()
        
        # 6. Запуск основного приложения
        self.root.destroy()
        from ui.selector_window import show_selector
        show_selector()

def show_intro():
    """Функция для запуска интро"""
    intro = IntroWindow()
    intro.show()

if __name__ == "__main__":
    show_intro()
