import os
import sys
import numpy as np
from PIL import Image, ImageTk
import tkinter as tk

def get_resource_path(relative_path):
    """Универсальный путь к ресурсам"""
    if getattr(sys, 'frozen', False):
        base_path = sys._MEIPASS
    else:
        base_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    return os.path.join(base_path, relative_path)

def load_icon_image(fluid_type, icon_name):
    """Загружает одну иконку как PIL Image"""
    icon_files = {
        "oil": {
            "НПС": "pump_station.png",
            "Резервуар": "reservoir.png", 
            "Подогрев": "heater.png",
            "Отстойник": "separator.png",
            "Труба": "pipe.png"
        },
        "gas": {
            "КС": "compressor_station.png", 
            "Осушитель": "dryer.png",
            "Фильтр": "filter.png",
            "ГРС": "grs.png",
            "Потребитель": "consumer.png",
            "Труба": "pipe.png"
        }
    }
    
    if fluid_type not in icon_files or icon_name not in icon_files[fluid_type]:
        return None
        
    filename = icon_files[fluid_type][icon_name]
    icon_path = get_resource_path(os.path.join("assets", "icons", fluid_type, filename))
    
    if os.path.exists(icon_path):
        try:
            img = Image.open(icon_path)
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            return img
        except Exception as e:
            print(f"❌ Ошибка загрузки {filename}: {e}")
    
    return None

def load_all_icons(fluid_type):
    """Загружает все иконки для типа среды"""
    icons = {}
    icon_names = ["НПС", "Резервуар", "Подогрев", "Отстойник", "Труба"] if fluid_type == "oil" else ["КС", "Осушитель", "Фильтр", "ГРС", "Потребитель", "Труба"]
    
    for name in icon_names:
        icons[name] = load_icon_image(fluid_type, name)
    
    return icons

def apply_color_to_icon_pil(icon_img, color):
    """Окрашивает PIL Image в нужный цвет"""
    if icon_img is None:
        return None
        
    try:
        # Создаем цветную маску
        if color == "green":
            tint_color = (0, 128, 0, 255)
        elif color == "lightgreen":
            tint_color = (144, 238, 144, 255)
        elif color == "yellow":
            tint_color = (255, 255, 0, 255)
        elif color == "orange":
            tint_color = (255, 165, 0, 255)
        elif color == "red":
            tint_color = (255, 0, 0, 255)
        else:
            tint_color = (128, 128, 128, 255)
        
        # Создаем цветное изображение
        colored_bg = Image.new('RGBA', icon_img.size, tint_color)
        
        # Используем альфа-канал оригинального изображения как маску
        result = Image.composite(colored_bg, icon_img, icon_img)
        
        return result
    except Exception as e:
        print(f"❌ Ошибка окраски иконки: {e}")
        return icon_img

def create_tk_icon(icon_img, size=(80, 80)):
    """Создает Tkinter-совместимую иконку"""
    if icon_img is None:
        return None
        
    try:
        # Масштабируем изображение
        icon_img = icon_img.resize(size, Image.Resampling.LANCZOS)
        return ImageTk.PhotoImage(icon_img)
    except Exception as e:
        print(f"❌ Ошибка создания Tk иконки: {e}")
        return None
