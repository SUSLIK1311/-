import tkinter as tk
from tkinter import messagebox
import os
import math
import time
from typing import List, Tuple, Optional, Dict
from dataclasses import dataclass

try:
    import pygame
    from pygame.locals import *
    PYGAME_AVAILABLE = True
except ImportError:
    PYGAME_AVAILABLE = False


try:
    from models.corrosion import get_corrosion_level
except ImportError:
    # Запасная функция если не удалось импортировать
    def get_corrosion_level(remaining_thickness):
        if remaining_thickness >= 10.0:
            return "отличное", '#90EE90'
        elif remaining_thickness >= 8.0:
            return "хорошее", '#98FB98'
        elif remaining_thickness >= 6.0:
            return "удовлетворительное", '#FFD700'
        elif remaining_thickness >= 4.0:
            return "плохое", '#FFA500'
        else:
            return "аварийное", '#FF6B6B'
# ============================================================================
# РАСШИРЕННЫЙ МАППИНГ ДЛЯ ВСЕХ ОБЪЕКТОВ
# ============================================================================

OBJECT_TO_MODELS = {
    "oil": {
        "pipe": ["pipe_paint", "pipe_unpaint"],
        "pipe_underground": ["pipe_underground"],
        "pump_station": ["pump_station_pumps", "pump_station_filters", 
                        "pump_station_reservoirs", "pump_station_pipe_main", 
                        "pump_station_pipe_medium"],
        "heater": ["heater_base", "heater_inlet_pipe", "heater_outlet_pipe", "heater_unpaint"],
        "reservoir": ["reservoir_base", "reservoir_inlet_pipe", "reservoir_outlet_pipe"],
        "separator": ["separator_base", "separator_clean_oil", "separator_dirty_oil",
                     "separator_water", "separator_unpaint"],
        # Шаблоны
        "nps_template": ["pump_station_pumps", "pump_station_filters", "pump_station_reservoirs"],
        "tank_template": ["reservoir_base", "reservoir_inlet_pipe", "reservoir_outlet_pipe"],
        "heater_template": ["heater_base", "heater_inlet_pipe", "heater_outlet_pipe"],
        "separator_template": ["separator_base", "separator_dirty_oil", "separator_clean_oil", "separator_water"]
    },
    "gas": {
        "pipe": ["pipe_paint", "pipe_unpaint"],
        "pipe_underground": ["pipe_underground"],
        "compressor_station": ["compressor_station_builds", "compressor_station_main_pipe"],
        "grs": ["grs_filter", "grs_fork", "grs_main_pipe", 
               "grs_big_consumer_pipe", "grs_medium_consumer_pipe", "grs_small_consumer_pipe"],
        "dryer": ["dryer_adsorbers", "dryer_inlet_pipe", "dryer_outlet_pipe",
                 "dryer_separator", "dryer_transition_pipe", "dryer_unpaint"],
        "filter": ["filter_body", "filter_inlet_pipe", "filter_outlet_pipe", "filter_unpaint"],
        "consumer": ["consumer_dom_rodnoy", "consumer_pipe"],
        # Шаблоны
        "ks_template": ["compressor_station_builds", "compressor_station_main_pipe"],
        "grs_template": ["grs_filter", "grs_fork", "grs_main_pipe"],
        "dryer_template": ["dryer_adsorbers", "dryer_separator", "dryer_inlet_pipe", "dryer_outlet_pipe"],
        "filter_template": ["filter_body", "filter_inlet_pipe", "filter_outlet_pipe"],
        "consumer_template": ["consumer_dom_rodnoy", "consumer_pipe"]
    }
}

def get_3d_models(object_type: str, fluid_type: str):
    """Возвращает список моделей для объекта"""
    if fluid_type not in OBJECT_TO_MODELS:
        return [("pipe_paint", (0, 0, 0))]
    
    models = OBJECT_TO_MODELS[fluid_type].get(object_type, [])
    
    # Если не нашли, пробуем альтернативные имена
    if not models:
        # Список альтернативных названий
        alternatives = {
            "nps": "pump_station",
            "tank": "reservoir",
            "ks": "compressor_station",
            "насосная": "pump_station",
            "сепаратор": "separator",
            "резервуар": "reservoir",
            "подогреватель": "heater",
            "компрессорная": "compressor_station"
        }
        
        for alt, real in alternatives.items():
            if alt in object_type.lower():
                models = OBJECT_TO_MODELS[fluid_type].get(real, [])
                if models:
                    break
    
    # Если всё равно не нашли, возвращаем базовую трубу
    if not models:
        models = ["pipe_paint"]
    
    # Все модели в позиции (0,0,0) - они уже подогнаны
    return [(model, (0, 0, 0)) for model in models]

def get_display_name(model_name: str) -> str:
    """Генерирует читаемое имя для модели"""
    name_map = {
        "pipe_paint": "Труба (окрашенная)",
        "pipe_unpaint": "Труба (неокрашенная)",
        "pipe_underground": "Труба подземная",
        "heater_base": "Подогреватель (основание)",
        "heater_inlet_pipe": "Подогреватель (вход)",
        "heater_outlet_pipe": "Подогреватель (выход)",
        "heater_unpaint": "Подогреватель (каркас)",
        "reservoir_base": "Резервуар (основание)",
        "reservoir_inlet_pipe": "Резервуар (вход)",
        "reservoir_outlet_pipe": "Резервуар (выход)",
        "separator_base": "Сепаратор (основание)",
        "separator_clean_oil": "Сепаратор (чистая нефть)",
        "separator_dirty_oil": "Сепаратор (грязная нефть)",
        "separator_water": "Сепаратор (вода)",
        "separator_unpaint": "Сепаратор (каркас)",
        "pump_station_pumps": "Насосная станция (насосы)",
        "pump_station_filters": "Насосная станция (фильтры)",
        "pump_station_reservoirs": "Насосная станция (резервуары)",
        "pump_station_pipe_main": "Насосная станция (магистраль)",
        "pump_station_pipe_medium": "Насосная станция (промежуточная)",
        "compressor_station_builds": "КС (здания)",
        "compressor_station_main_pipe": "КС (магистраль)",
        "consumer_dom_rodnoy": "Потребитель (Дом родной)",
        "consumer_pipe": "Потребитель (труба)",
        "dryer_adsorbers": "Осушитель (адсорберы)",
        "dryer_inlet_pipe": "Осушитель (вход)",
        "dryer_outlet_pipe": "Осушитель (выход)",
        "dryer_separator": "Осушитель (сепаратор)",
        "dryer_transition_pipe": "Осушитель (переходная труба)",
        "dryer_unpaint": "Осушитель (каркас)",
        "filter_body": "Фильтр (корпус)",
        "filter_inlet_pipe": "Фильтр (вход)",
        "filter_outlet_pipe": "Фильтр (выход)",
        "filter_unpaint": "Фильтр (каркас)",
        "grs_big_consumer_pipe": "ГРС (труба крупного потребителя)",
        "grs_filter": "ГРС (фильтр)",
        "grs_fork": "ГРС (разветвление)",
        "grs_main_pipe": "ГРС (магистраль)",
        "grs_medium_consumer_pipe": "ГРС (труба среднего потребителя)",
        "grs_small_consumer_pipe": "ГРС (труба малого потребителя)"
    }
    
    return name_map.get(model_name, model_name.replace("_", " ").title())

# ============================================================================
# УЛУЧШЕННЫЙ ЗАГРУЗЧИК OBJ
# ============================================================================

class SmartOBJLoader:
    """Умный загрузчик OBJ файлов с кэшированием"""
    
    _cache = {}
    
    @staticmethod
    def load(filepath: str):
        """Загружает OBJ файл с кэшированием"""
        if filepath in SmartOBJLoader._cache:
            return SmartOBJLoader._cache[filepath]
        
        if not os.path.exists(filepath):
            # Пробуем найти файл в других местах
            alt_paths = [
                filepath.replace("assets/3D_models/", ""),
                filepath.split("/")[-1],
                os.path.join("..", filepath),
                os.path.join(".", filepath)
            ]
            
            for alt_path in alt_paths:
                if os.path.exists(alt_path):
                    filepath = alt_path
                    break
        
        if not os.path.exists(filepath):
            print(f"Файл не найден: {filepath}")
            SmartOBJLoader._cache[filepath] = (None, None)
            return None, None
        
        vertices = []
        faces = []
        
        try:
            with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    line = line.strip()
                    if line.startswith('v '):
                        parts = line.split()
                        if len(parts) >= 4:
                            try:
                                vertices.append((
                                    float(parts[1]),
                                    float(parts[2]), 
                                    float(parts[3])
                                ))
                            except ValueError:
                                continue
                    elif line.startswith('f '):
                        parts = line.split()
                        if len(parts) >= 4:
                            face_vertices = []
                            for part in parts[1:]:
                                indices = part.split('/')
                                if indices[0].isdigit():
                                    vertex_idx = int(indices[0]) - 1
                                    if 0 <= vertex_idx < len(vertices):
                                        face_vertices.append(vertex_idx)
                            
                            # Триангуляция
                            if len(face_vertices) >= 3:
                                for i in range(1, len(face_vertices) - 1):
                                    faces.append([
                                        face_vertices[0],
                                        face_vertices[i],
                                        face_vertices[i + 1]
                                    ])
        except Exception as e:
            print(f"Ошибка загрузки {filepath}: {e}")
            vertices, faces = [], []
        
        result = (vertices, faces) if vertices and faces else (None, None)
        SmartOBJLoader._cache[filepath] = result
        return result

# ============================================================================
# 3D ВЬЮЕР С ИСПРАВЛЕНИЯМИ
# ============================================================================

@dataclass
class Component3D:
    model_name: str
    display_name: str
    position: Tuple[float, float, float]
    scale: float = 1.0
    original_thickness: Optional[float] = None
    remaining_thickness: Optional[float] = None
    corrosion_level: str = "отличное"
    material: str = ""
    vertices: List[Tuple[float, float, float]] = None
    faces: List[List[int]] = None
    bounding_radius: float = 1.0

class Fixed3DViewer:
    def __init__(self, width=1024, height=768, title="3D Просмотр"):
        self.width = width
        self.height = height
        self.title = title
        self.components = []
        self.running = False
        
        # Камера
        self.camera_dist = 20.0
        self.camera_rot = [-30, 45]
        self.camera_target = [0, 0, 0]
        
        # Управление
        self.dragging = False
        self.last_mouse = (0, 0)
        self.zoom_speed = 1.2
        
        # Тултипы
        self.tooltip_component = None
        self.tooltip_pos = (0, 0)
        
        # Добавляем переменные для группировки
        self.object_groups = {}  # Словарь для группировки компонентов по объектам
        self.hovered_object = None  # Весь объект, над которым курсор
        self.current_section_data = None  # Данные секции для отображения в тултипе
        
        # Цвета (совпадают с таблицей в параметрах)
        self.bg_color = (40, 45, 60)
        
        # Шрифты
        self.font = None
        self.title_font = None
    
    def initialize(self):
        """Инициализация Pygame"""
        if not PYGAME_AVAILABLE:
            return False
        
        try:
            pygame.init()
            self.screen = pygame.display.set_mode((self.width, self.height))
            pygame.display.set_caption(self.title)
            
            pygame.font.init()
            self.font = pygame.font.SysFont('Arial', 12)
            self.title_font = pygame.font.SysFont('Arial', 16, bold=True)
            
            self.clock = pygame.time.Clock()
            self.running = True
            return True
        except Exception as e:
            print(f"Ошибка инициализации Pygame: {e}")
            return False
    
    def load_model(self, model_name: str, fluid_type: str):
        """Загружает модель из файла"""
        # Пробуем разные пути
        base_paths = [
            f"assets/3D_models/{fluid_type}/{model_name}.obj",
            f"../assets/3D_models/{fluid_type}/{model_name}.obj",
            f"./assets/3D_models/{fluid_type}/{model_name}.obj",
            f"../../assets/3D_models/{fluid_type}/{model_name}.obj",
            f"3D_models/{fluid_type}/{model_name}.obj",
            f"{fluid_type}/{model_name}.obj",
            f"{model_name}.obj"  # прямой путь
        ]
        
        for path in base_paths:
            if os.path.exists(path):
                print(f"Загружаем: {path}")
                return SmartOBJLoader.load(path)
        
        print(f"Файл не найден: {model_name}.obj")
        return None, None
    
    def add_component(self, component: Component3D, fluid_type: str, section_data=None):
        """Добавляет компонент с загрузкой модели"""
        # Загружаем модель
        vertices, faces = self.load_model(component.model_name, fluid_type)
        
        if vertices and faces:
            component.vertices = vertices
            component.faces = faces
            
            # Вычисляем ограничивающий радиус
            max_dist = 0
            for v in vertices:
                dist = math.sqrt(v[0]**2 + v[1]**2 + v[2]**2)
                if dist > max_dist:
                    max_dist = dist
            component.bounding_radius = max(0.5, max_dist)
        else:
            # Создаём простую геометрию для отладки
            print(f"Создаю упрощённую модель для {component.model_name}")
            component.vertices, component.faces = self.create_simple_geometry(component.model_name)
            component.bounding_radius = 1.0
        
        self.components.append(component)
        
        # Сохраняем данные секции для тултипов (только если переданы и еще не сохранены)
        if section_data is not None and self.current_section_data is None:
            self.current_section_data = section_data
            print(f"  Сохранены данные секции: {section_data.get('name', 'Без имени')}")
        
        print(f"  Добавлен: {component.model_name}")

    def check_tooltip(self, mouse_pos):
        """Проверяет, находится ли мышь над объектом"""
        self.hovered_object = None
        
        # Для сложных объектов (НПС, КС и т.д.) группируем все компоненты
        if self.current_section_data and self.current_section_data.get("is_complex", False):
            # Проверяем, находится ли курсор над любым компонентом сложного объекта
            for component in self.components:
                # Пропускаем неокрашиваемые объекты
                model_lower = component.model_name.lower()
                if "unpaint" in model_lower or "dom_rodnoy" in model_lower:
                    continue
                
                # Проецируем центр
                center_2d, depth = self.project_3d_to_2d(component.position)
                
                if not center_2d:
                    continue
                
                # Проверяем расстояние
                distance = math.sqrt(
                    (mouse_pos[0] - center_2d[0])**2 +
                    (mouse_pos[1] - center_2d[1])**2
                )
                
                # Учитываем размер компонента
                radius_2d = component.bounding_radius * 500 / depth if depth > 0 else 30
                
                if distance < max(30, radius_2d):
                    # Курсор над сложным объектом
                    self.hovered_object = self.current_section_data
                    self.tooltip_pos = mouse_pos
                    return
        else:
            # Для простых объектов (труб) показываем тултип для конкретного компонента
            for component in self.components:
                # Пропускаем неокрашиваемые объекты
                model_lower = component.model_name.lower()
                if "unpaint" in model_lower or "dom_rodnoy" in model_lower:
                    continue
                
                # Пропускаем объекты без данных
                if component.remaining_thickness is None:
                    continue
                
                # Проецируем центр
                center_2d, depth = self.project_3d_to_2d(component.position)
                
                if not center_2d:
                    continue
                
                # Проверяем расстояние
                distance = math.sqrt(
                    (mouse_pos[0] - center_2d[0])**2 +
                    (mouse_pos[1] - center_2d[1])**2
                )
                
                # Учитываем размер компонента
                radius_2d = component.bounding_radius * 500 / depth if depth > 0 else 30
                
                if distance < max(30, radius_2d):
                    self.tooltip_component = component
                    self.tooltip_pos = mouse_pos
                    break
    
    def create_simple_geometry(self, model_name: str):
        """Создаёт простую геометрию для отладки"""
        if "pipe" in model_name.lower():
            return self.create_pipe()
        elif "separator" in model_name.lower():
            return self.create_separator()
        elif "pump" in model_name.lower():
            return self.create_pump_station()
        elif "compressor" in model_name.lower():
            return self.create_compressor_station()
        elif "grs" in model_name.lower():
            return self.create_grs()
        elif "dryer" in model_name.lower():
            return self.create_dryer()
        elif "filter" in model_name.lower():
            return self.create_filter()
        elif "consumer" in model_name.lower():
            return self.create_consumer()
        else:
            return self.create_cube()
    
    def create_cube(self):
        """Создаёт куб"""
        vertices = [
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
        ]
        faces = [
            [0, 1, 2], [2, 3, 0],
            [4, 5, 6], [6, 7, 4],
            [0, 3, 7], [7, 4, 0],
            [1, 5, 6], [6, 2, 1],
            [0, 1, 5], [5, 4, 0],
            [3, 2, 6], [6, 7, 3]
        ]
        return vertices, faces
    
    def create_pipe(self):
        """Создаёт модель трубы"""
        vertices = []
        faces = []
        
        segments = 12
        radius = 0.5
        length = 3
        
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            z = radius * math.sin(angle)
            
            vertices.append((x, -length/2, z))
            vertices.append((x, length/2, z))
        
        for i in range(segments):
            next_i = (i + 1) % segments
            v1 = i * 2
            v2 = i * 2 + 1
            v3 = next_i * 2 + 1
            v4 = next_i * 2
            
            faces.append([v1, v2, v3])
            faces.append([v3, v4, v1])
        
        return vertices, faces
    
    def create_separator(self):
        """Создаёт модель сепаратора"""
        vertices = []
        faces = []
        
        # Горизонтальный цилиндр
        segments = 16
        radius = 1.0
        length = 4
        
        for i in range(segments):
            angle = 2 * math.pi * i / segments
            x = radius * math.cos(angle)
            y = radius * math.sin(angle)
            
            vertices.append((x, y, -length/2))
            vertices.append((x, y, length/2))
        
        for i in range(segments):
            next_i = (i + 1) % segments
            v1 = i * 2
            v2 = i * 2 + 1
            v3 = next_i * 2 + 1
            v4 = next_i * 2
            
            faces.append([v1, v2, v3])
            faces.append([v3, v4, v1])
        
        return vertices, faces
    
    def create_pump_station(self):
        """Создаёт модель насосной станции"""
        vertices = []
        faces = []
        
        # Несколько объектов рядом
        objects = [
            ((-2, 0, 0), 1.5, 2, 1.5),  # Насосы
            ((0, 0, 0), 2, 1.5, 2),     # Фильтры
            ((2, 0, 0), 2, 2.5, 2),     # Резервуары
        ]
        
        for (x, y, z), w, h, d in objects:
            offset = len(vertices)
            
            # Вершины куба
            cube_vertices = [
                (x - w/2, y - h/2, z - d/2), (x + w/2, y - h/2, z - d/2),
                (x + w/2, y + h/2, z - d/2), (x - w/2, y + h/2, z - d/2),
                (x - w/2, y - h/2, z + d/2), (x + w/2, y - h/2, z + d/2),
                (x + w/2, y + h/2, z + d/2), (x - w/2, y + h/2, z + d/2)
            ]
            
            cube_faces = [
                [0, 1, 2], [2, 3, 0],
                [4, 5, 6], [6, 7, 4],
                [0, 3, 7], [7, 4, 0],
                [1, 5, 6], [6, 2, 1],
                [0, 1, 5], [5, 4, 0],
                [3, 2, 6], [6, 7, 3]
            ]
            
            vertices.extend(cube_vertices)
            
            for face in cube_faces:
                faces.append([v + offset for v in face])
        
        return vertices, faces
    
    def create_compressor_station(self):
        """Создаёт модель компрессорной станции"""
        return self.create_pump_station()  # Аналогично
    
    def create_grs(self):
        """Создаёт модель ГРС"""
        vertices = []
        faces = []
        
        # Центральный узел
        offset = len(vertices)
        vertices.extend([
            (-1, -1, -1), (1, -1, -1), (1, 1, -1), (-1, 1, -1),
            (-1, -1, 1), (1, -1, 1), (1, 1, 1), (-1, 1, 1)
        ])
        
        faces.extend([
            [0, 1, 2], [2, 3, 0],
            [4, 5, 6], [6, 7, 4],
            [0, 3, 7], [7, 4, 0],
            [1, 5, 6], [6, 2, 1],
            [0, 1, 5], [5, 4, 0],
            [3, 2, 6], [6, 7, 3]
        ])
        
        # Трубы отходящие
        pipes = [
            ((-2, 0, 0), 2, 0.3, 0.3),  # Большой потребитель
            ((0, 2, 0), 0.3, 2, 0.3),   # Средний потребитель
            ((2, 0, 0), 2, 0.3, 0.3),   # Малый потребитель
        ]
        
        for (x, y, z), length, radius, _ in pipes:
            offset = len(vertices)
            
            # Простая труба
            segments = 8
            for i in range(segments):
                angle = 2 * math.pi * i / segments
                dx = radius * math.cos(angle)
                dz = radius * math.sin(angle)
                
                vertices.append((x + dx, y - length/2, z + dz))
                vertices.append((x + dx, y + length/2, z + dz))
            
            for i in range(segments):
                next_i = (i + 1) % segments
                v1 = offset + i * 2
                v2 = offset + i * 2 + 1
                v3 = offset + next_i * 2 + 1
                v4 = offset + next_i * 2
                
                faces.append([v1, v2, v3])
                faces.append([v3, v4, v1])
        
        return vertices, faces
    
    def create_dryer(self):
        """Создаёт модель осушителя"""
        return self.create_pump_station()  # Аналогично
    
    def create_filter(self):
        """Создаёт модель фильтра"""
        return self.create_separator()  # Аналогично
    
    def create_consumer(self):
        """Создаёт модель потребителя"""
        vertices = []
        faces = []
        
        # Дом
        offset = len(vertices)
        vertices.extend([
            (-1, -0.5, -1), (1, -0.5, -1), (1, 1.5, -1), (-1, 1.5, -1),
            (-1, -0.5, 1), (1, -0.5, 1), (1, 1.5, 1), (-1, 1.5, 1),
            (0, 2.5, 0)  # Крыша
        ])
        
        faces.extend([
            [0, 1, 2], [2, 3, 0],  # Задняя стена
            [4, 5, 6], [6, 7, 4],  # Передняя стена
            [0, 3, 7], [7, 4, 0],  # Левая стена
            [1, 5, 6], [6, 2, 1],  # Правая стена
            [0, 1, 5], [5, 4, 0],  # Пол
            [3, 2, 6], [6, 7, 3],  # Потолок
            [3, 2, 8], [2, 1, 8], [1, 0, 8], [0, 3, 8]  # Крыша
        ])
        
        return vertices, faces
    
    def calculate_corrosion_level(self, component: Component3D) -> str:
        """Рассчитывает уровень коррозии"""
        if component.remaining_thickness is None:
            return "отличное"
        
        # Используем общую функцию
        level, _ = get_corrosion_level(component.remaining_thickness)
        return level
    
    def get_component_color(self, component: Component3D):
        """Возвращает цвет компонента по остаточной толщине"""
        model_lower = component.model_name.lower()
        
        # 1. НЕ ОКРАШИВАЕМЫЕ объекты - серый
        if "unpaint" in model_lower or "dom_rodnoy" in model_lower:
            return (180, 180, 180)  # Серый
        
        # 2. Если нет данных о толщине - светло-серый
        if component.remaining_thickness is None:
            # Для труб пытаемся подставить значения по умолчанию
            if "pipe" in model_lower:
                component.remaining_thickness = 10.0
                level, _ = get_corrosion_level(10.0)
                return self.get_color_by_level(level)
            return (200, 200, 200)  # Светло-серый
        
        # 3. Определяем уровень коррозии по остаточной толщине
        level, _ = get_corrosion_level(component.remaining_thickness)
        
        # 4. Возвращаем цвет
        return self.get_color_by_level(level)
    
    def get_color_by_level(self, level: str):
        """Возвращает цвет по уровню (RGB)"""
        colors = {
            "отличное": (144, 238, 144),      # #90EE90
            "хорошее": (152, 251, 152),       # #98FB98
            "удовлетворительное": (255, 215, 0), # #FFD700
            "плохое": (255, 165, 0),          # #FFA500
            "аварийное": (255, 107, 107)      # #FF6B6B
        }
        return colors.get(level, (200, 200, 200))
    
    def project_3d_to_2d(self, point):
        """Проецирует 3D точку на 2D экран"""
        x, y, z = point
        
        # Вращение по осям
        angle_y = math.radians(self.camera_rot[1])
        cos_y = math.cos(angle_y)
        sin_y = math.sin(angle_y)
        
        x1 = x * cos_y - z * sin_y
        z1 = x * sin_y + z * cos_y
        
        angle_x = math.radians(self.camera_rot[0])
        cos_x = math.cos(angle_x)
        sin_x = math.sin(angle_x)
        
        y1 = y * cos_x - z1 * sin_x
        z2 = y * sin_x + z1 * cos_x
        
        # Перспектива
        z_depth = z2 + self.camera_dist
        if z_depth < 0.1:
            z_depth = 0.1
        
        factor = 500 / z_depth
        screen_x = self.width // 2 + (x1 + self.camera_target[0]) * factor
        screen_y = self.height // 2 - (y1 + self.camera_target[1]) * factor
        
        return (int(screen_x), int(screen_y)), z_depth
    
    def draw_component(self, component: Component3D):
        """Рисует компонент"""
        if not component.vertices or not component.faces:
            return
        
        color = self.get_component_color(component)
        
        # Рисуем все полигоны
        for face in component.faces:
            if len(face) < 3:
                continue
            
            points = []
            for vertex_idx in face:
                if vertex_idx < len(component.vertices):
                    v = component.vertices[vertex_idx]
                    # Применяем позицию и масштаб
                    x = v[0] * component.scale + component.position[0]
                    y = v[1] * component.scale + component.position[1]
                    z = v[2] * component.scale + component.position[2]
                    
                    point_2d, _ = self.project_3d_to_2d((x, y, z))
                    points.append(point_2d)
            
            if len(points) >= 3:
                # Заливка
                pygame.draw.polygon(self.screen, color, points)
                # Контур
                darker = (max(0, color[0] - 40), max(0, color[1] - 40), max(0, color[2] - 40))
                pygame.draw.polygon(self.screen, darker, points, 1)
    
    def draw_components(self):
        """Рисует все компоненты с сортировкой по глубине"""
        # Сортируем по расстоянию до камеры
        if not self.components:
            return
        
        sorted_components = sorted(
            self.components,
            key=lambda c: math.sqrt(
                (c.position[0] - self.camera_target[0])**2 +
                (c.position[1] - self.camera_target[1])**2 +
                (c.position[2] - self.camera_target[2])**2
            ),
            reverse=True
        )
        
        for component in sorted_components:
            self.draw_component(component)
    
    def check_tooltip(self, mouse_pos):
        """Проверяет, находится ли мышь над окрашиваемым компонентом"""
        self.tooltip_component = None
        
        for component in self.components:
            # Пропускаем неокрашиваемые объекты
            model_lower = component.model_name.lower()
            if "unpaint" in model_lower or "dom_rodnoy" in model_lower:
                continue
            
            # Пропускаем объекты без данных (кроме труб, у которых есть значения по умолчанию)
            if component.original_thickness is None and "pipe" not in model_lower:
                continue
            
            # Проецируем центр
            center_2d, depth = self.project_3d_to_2d(component.position)
            
            if not center_2d:
                continue
            
            # Проверяем расстояние
            distance = math.sqrt(
                (mouse_pos[0] - center_2d[0])**2 +
                (mouse_pos[1] - center_2d[1])**2
            )
            
            # Учитываем размер компонента
            radius_2d = component.bounding_radius * 500 / depth if depth > 0 else 30
            
            if distance < max(30, radius_2d):
                self.tooltip_component = component
                self.tooltip_pos = mouse_pos
                break
    
    def draw_tooltip(self):
        """Рисует тултип с информацией - ДЛЯ СЛОЖНЫХ ОБЪЕКТОВ"""
        if self.hovered_object and self.hovered_object.get("is_complex", False):
            self.draw_complex_object_tooltip()
        elif self.tooltip_component:
            self.draw_simple_component_tooltip()

    def draw_simple_component_tooltip(self):
        """Рисует тултип для простых компонентов (труб)"""
        if not self.tooltip_component:
            return
        
        component = self.tooltip_component
        
        # Собираем информацию
        lines = [f"► {component.display_name}"]
        
        # Уровень коррозии
        corrosion_level = self.calculate_corrosion_level(component)
        lines.append(f"Состояние: {corrosion_level}")
        
        # Материал
        if component.material:
            lines.append(f"Материал: {component.material}")
        
        # Толщина стенки
        if component.original_thickness is not None:
            lines.append(f"Толщина стенки: {component.original_thickness:.1f} мм")
            
            if component.remaining_thickness is not None:
                lines.append(f"Остаточная толщина: {component.remaining_thickness:.1f} мм")
        
        # Определяем размер тултипа
        max_width = 0
        for line in lines:
            text_surf = self.font.render(line, True, (255, 255, 255))
            max_width = max(max_width, text_surf.get_width())
        
        padding = 10
        line_height = 16
        tooltip_w = max_width + 2 * padding
        tooltip_h = len(lines) * line_height + 2 * padding
        
        # Позиция тултипа
        tooltip_x = self.tooltip_pos[0] + 20
        tooltip_y = self.tooltip_pos[1]
        
        if tooltip_x + tooltip_w > self.width:
            tooltip_x = self.tooltip_pos[0] - tooltip_w - 20
        if tooltip_y + tooltip_h > self.height:
            tooltip_y = self.tooltip_pos[1] - tooltip_h
        
        # Фон тултипа
        pygame.draw.rect(self.screen, (20, 25, 35), 
                        (tooltip_x, tooltip_y, tooltip_w, tooltip_h))
        pygame.draw.rect(self.screen, (60, 80, 100), 
                        (tooltip_x, tooltip_y, tooltip_w, tooltip_h), 1)
        
        # Текст
        for i, line in enumerate(lines):
            color = (240, 240, 240) if i == 0 else (200, 200, 200)
            text = self.font.render(line, True, color)
            self.screen.blit(text, 
                           (tooltip_x + padding, tooltip_y + padding + i * line_height))

    def draw_complex_object_tooltip(self):
        """Рисует тултип для сложных объектов (НПС, КС и т.д.)"""
        if not self.hovered_object:
            return
        
        section = self.hovered_object
        
        # Собираем информацию
        lines = [f"► {section.get('name', 'Объект')}"]
        lines.append(f"Тип: {section.get('object_type', 'Сложный объект')}")
        
        # Определяем общее состояние (наихудшее среди компонентов)
        components = section.get("components", [])
        components_data = section.get("components_data", [])
        
        if components:
            lines.append(f"Компонентов: {len(components)}")
            
            # Находим наихудшее состояние
            worst_state = "отличное"
            worst_thickness = 10.0
            
            for i, comp in enumerate(components):
                # Получаем остаточную толщину
                remaining = None
                
                # Сначала ищем в components_data
                if i < len(components_data):
                    remaining = components_data[i].get("remaining")
                
                # Если не нашли, используем значение из компонента
                if remaining is None:
                    remaining = comp.get("remaining", 
                                        comp.get("thickness", 
                                                comp.get("wall_thickness", 10.0)))
                
                # Определяем состояние для этого компонента
                comp_state, _ = get_corrosion_level(remaining)
                
                # Обновляем наихудшее состояние
                state_order = ["отличное", "хорошее", "удовлетворительное", "плохое", "аварийное"]
                if state_order.index(comp_state) > state_order.index(worst_state):
                    worst_state = comp_state
                    worst_thickness = remaining
            
            lines.append(f"Общее состояние: {worst_state}")
            lines.append(f"Наихудшая толщина: {worst_thickness:.1f} мм")
            
            # Список основных компонентов
            lines.append("Основные компоненты:")
            
            # Ограничиваем количество отображаемых компонентов
            max_components = 6
            for i, comp in enumerate(components[:max_components]):
                comp_name = comp.get("name", f"Компонент {i+1}")
                # Получаем остаточную толщину
                remaining = None
                if i < len(components_data):
                    remaining = components_data[i].get("remaining")
                if remaining is None:
                    remaining = comp.get("remaining", 
                                        comp.get("thickness", 
                                                comp.get("wall_thickness", 10.0)))
                
                comp_state, _ = get_corrosion_level(remaining)
                lines.append(f"  • {comp_name}: {remaining:.1f} мм ({comp_state})")
            
            if len(components) > max_components:
                lines.append(f"  ... и ещё {len(components) - max_components}")
        else:
            lines.append("Нет данных о компонентах")
        
        # Определяем размер тултипа
        max_width = 0
        for line in lines:
            text_surf = self.font.render(line, True, (255, 255, 255))
            max_width = max(max_width, text_surf.get_width())
        
        padding = 10
        line_height = 16
        tooltip_w = max_width + 2 * padding
        tooltip_h = len(lines) * line_height + 2 * padding
        
        # Позиция тултипа
        tooltip_x = self.tooltip_pos[0] + 20
        tooltip_y = self.tooltip_pos[1]
        
        if tooltip_x + tooltip_w > self.width:
            tooltip_x = self.tooltip_pos[0] - tooltip_w - 20
        if tooltip_y + tooltip_h > self.height:
            tooltip_y = self.tooltip_pos[1] - tooltip_h
        
        # Фон тултипа
        pygame.draw.rect(self.screen, (20, 25, 35), 
                        (tooltip_x, tooltip_y, tooltip_w, tooltip_h))
        pygame.draw.rect(self.screen, (60, 80, 100), 
                        (tooltip_x, tooltip_y, tooltip_w, tooltip_h), 1)
        
        # Текст
        for i, line in enumerate(lines):
            if i == 0:
                color = (240, 240, 240)
            elif line.startswith("  •"):
                color = (180, 200, 180)
            elif ":" in line:
                color = (200, 220, 200)
            else:
                color = (220, 220, 220)
            
            text = self.font.render(line, True, color)
            self.screen.blit(text, 
                           (tooltip_x + padding, tooltip_y + padding + i * line_height))
    
    def draw_ui(self):
        """Рисует элементы интерфейса"""
        # Заголовок
        title = self.title_font.render(self.title, True, (240, 240, 240))
        self.screen.blit(title, (10, 10))
        
        # Информация
        colored_count = sum(1 for c in self.components 
                          if "unpaint" not in c.model_name.lower() 
                          and "dom_rodnoy" not in c.model_name.lower())
        
        info_text = f"Компонентов: {len(self.components)} (окрашено: {colored_count})"
        info_surf = self.font.render(info_text, True, (200, 200, 200))
        self.screen.blit(info_surf, (self.width - info_surf.get_width() - 10, 10))
        
        # Инструкция
        controls = [
            "Управление:",
            "ЛКМ + движение - вращение",
            "Колесо мыши - масштабирование",
            "R - сброс камеры",
            "ESC - выход"
        ]
        
        for i, text in enumerate(controls):
            surf = self.font.render(text, True, (200, 200, 200))
            self.screen.blit(surf, (10, 40 + i * 18))
        
        # Легенда цветов
        legend_y = self.height - 160
        legend_items = [
            ((144, 238, 144), "Отличное (≥90%)"),
            ((152, 251, 152), "Хорошее (≥80%)"),
            ((255, 215, 0), "Удовлетворительное (≥70%)"),
            ((255, 165, 0), "Плохое (≥50%)"),
            ((255, 107, 107), "Аварийное (<50%)")
        ]
        
        # Фон легенды
        pygame.draw.rect(self.screen, (30, 35, 45), 
                        (10, legend_y - 10, 280, 185))
        pygame.draw.rect(self.screen, (60, 70, 85), 
                        (10, legend_y - 10, 280, 185), 1)
        
        legend_title = self.font.render("Индикация состояния:", True, (220, 220, 220))
        self.screen.blit(legend_title, (15, legend_y - 5))
        
        for i, (color, text) in enumerate(legend_items):
            pygame.draw.rect(self.screen, color, (20, legend_y + 20 + i * 25, 12, 12))
            text_surf = self.font.render(text, True, (200, 200, 200))
            self.screen.blit(text_surf, (40, legend_y + 20 + i * 25))
    
    def run(self):
        """Главный цикл"""
        if not self.running:
            return
        
        while self.running:
            # Обработка событий
            for event in pygame.event.get():
                if event.type == QUIT:
                    self.running = False
                    break
                
                elif event.type == MOUSEBUTTONDOWN:
                    if event.button == 1:  # ЛКМ
                        self.dragging = True
                        self.last_mouse = pygame.mouse.get_pos()
                    elif event.button == 4:  # Колесо вверх
                        self.camera_dist = max(10, self.camera_dist / self.zoom_speed)
                    elif event.button == 5:  # Колесо вниз
                        self.camera_dist = min(50, self.camera_dist * self.zoom_speed)
                
                elif event.type == MOUSEBUTTONUP:
                    if event.button == 1:
                        self.dragging = False
                
                elif event.type == MOUSEMOTION:
                    if self.dragging:
                        mouse = pygame.mouse.get_pos()
                        dx = mouse[0] - self.last_mouse[0]
                        dy = mouse[1] - self.last_mouse[1]
                        
                        self.camera_rot[1] += dx * 0.5
                        self.camera_rot[0] -= dy * 0.5
                        self.camera_rot[0] = max(-85, min(85, self.camera_rot[0]))
                        
                        self.last_mouse = mouse
                
                elif event.type == KEYDOWN:
                    if event.key == K_ESCAPE:
                        self.running = False
                        break
                    elif event.key == K_r:  # Сброс камеры
                        self.camera_dist = 20.0
                        self.camera_rot = [-30, 45]
                        self.camera_target = [0, 0, 0]
            
            # Проверка тултипов
            mouse_pos = pygame.mouse.get_pos()
            self.check_tooltip(mouse_pos)
            
            # Очистка экрана
            self.screen.fill(self.bg_color)
            
            # Отрисовка компонентов
            self.draw_components()
            
            # Отрисовка тултипа
            self.draw_tooltip()
            
            # Отрисовка UI
            self.draw_ui()
            
            # Обновление экрана
            pygame.display.flip()
            self.clock.tick(60)
        
        pygame.quit()

# ============================================================================
# ГЛАВНАЯ ФУНКЦИЯ С ИСПРАВЛЕНИЯМИ
# ============================================================================

def show_3d_viewer(section_data, fluid_type="oil"):
    """
    Показывает 3D просмотрщик для секции трубопровода
    
    Args:
        section_data: dict с данными секции (из parameters_tab.py)
        fluid_type: "oil" или "gas"
    """
    if not PYGAME_AVAILABLE:
        root = tk.Tk()
        root.withdraw()
        messagebox.showerror("Ошибка", 
            "Библиотека Pygame не установлена.\n"
            "Установите: pip install pygame")
        root.destroy()
        return
    
    # Получаем данные секции
    section_name = section_data.get("name", "3D Модель")
    object_type = section_data.get("object_type", "pipe")
    is_complex = section_data.get("is_complex", False)
    
    print(f"\n{'='*60}")
    print(f"Запуск 3D просмотрщика для: {section_name}")
    print(f"Тип объекта: {object_type}")
    print(f"Тип жидкости: {fluid_type}")
    print(f"Сложный объект: {is_complex}")
    print(f"{'='*60}")
    
    # Создаём просмотрщик
    viewer = Fixed3DViewer(1024, 768, f"3D: {section_name}")
    
    if not viewer.initialize():
        messagebox.showerror("Ошибка", 
            "Не удалось инициализировать 3D просмотрщик.\n"
            "Убедитесь, что установлен pygame: pip install pygame")
        return
    
    # Получаем список моделей для объекта
    model_configs = get_3d_models(object_type, fluid_type)
    print(f"Найдено моделей для '{object_type}': {len(model_configs)}")
    for model, pos in model_configs:
        print(f"  - {model}")
    
    # Получаем данные компонентов
    components_data = []
    original_components = []
    
    if is_complex:
        # Для сложных объектов
        components_data = section_data.get("components_data", [])
        original_components = section_data.get("components", [])
        
        print(f"Данных коррозии: {len(components_data)}")
        print(f"Исходных компонентов: {len(original_components)}")
    else:
        # Для простых труб
        components_data = [{
            "component_id": "pipe",
            "remaining": section_data.get("remaining_thickness", section_data.get("thickness", 10.0)),
            "level": section_data.get("corrosion_level", "отличное")
        }]
        original_components = [{
            "component_id": "pipe",
            "thickness": section_data.get("thickness", 10.0),
            "material": section_data.get("material", ""),
            "wall_thickness": section_data.get("thickness", 10.0)
        }]
    
    # Создаём маппинг для быстрого поиска
    corrosion_map = {}
    for comp in components_data:
        comp_id = comp.get("component_id", "").replace(".", "_")
        if comp_id:
            corrosion_map[comp_id] = comp
    
    thickness_map = {}
    for comp in original_components:
        comp_id = comp.get("component_id", "").replace(".", "_")
        if comp_id:
            thickness_map[comp_id] = comp
    
    # Добавляем все компоненты
    for i, (model_name, position) in enumerate(model_configs):
        print(f"\nОбработка модели {i+1}/{len(model_configs)}: {model_name}")
        
        # Ищем данные для этой модели
        component_info = None
        thickness_info = None
        
        # Пробуем разные стратегии сопоставления
        model_lower = model_name.lower()
        
        # 1. Прямое совпадение
        for key in corrosion_map:
            if key in model_lower or model_lower in key:
                component_info = corrosion_map[key]
                print(f"  Найдены данные коррозии по ключу '{key}'")
                break
        
        # 2. Поиск по частям имени
        if not component_info:
            model_parts = model_name.split('_')
            for key in corrosion_map:
                for part in model_parts:
                    if part and part in key:
                        component_info = corrosion_map[key]
                        print(f"  Найдены данные коррозии по части '{part}'")
                        break
                if component_info:
                    break
        
        # 3. По порядку (если количество совпадает)
        if not component_info and i < len(components_data):
            component_info = components_data[i]
            print(f"  Назначены данные коррозии по порядку")
        
        # То же самое для толщины
        for key in thickness_map:
            if key in model_lower or model_lower in key:
                thickness_info = thickness_map[key]
                print(f"  Найдены данные толщины по ключу '{key}'")
                break
        
        if not thickness_info:
            model_parts = model_name.split('_')
            for key in thickness_map:
                for part in model_parts:
                    if part and part in key:
                        thickness_info = thickness_map[key]
                        print(f"  Найдены данные толщины по части '{part}'")
                        break
                if thickness_info:
                    break
        
        if not thickness_info and i < len(original_components):
            thickness_info = original_components[i]
            print(f"  Назначены данные толщины по порядку")
        
        # Извлекаем данные
        original_thickness = None
        remaining_thickness = None
        corrosion_level = "отличное"
        material = ""
        
        if thickness_info:
            original_thickness = thickness_info.get("thickness") or thickness_info.get("wall_thickness")
            material = thickness_info.get("material", "")
            print(f"  Исходная толщина: {original_thickness}")
        
        if component_info:
            remaining_thickness = component_info.get("remaining")
            corrosion_level = component_info.get("level", "отличное")
            print(f"  Остаточная толщина: {remaining_thickness}, Уровень: {corrosion_level}")
        
        # Для труб без данных устанавливаем значения по умолчанию
        if "pipe" in model_lower:
            if original_thickness is None:
                original_thickness = 10.0
                print(f"  Установлена толщина по умолчанию для трубы: {original_thickness}")
            if remaining_thickness is None:
                remaining_thickness = original_thickness
                print(f"  Установлена остаточная толщина по умолчанию: {remaining_thickness}")
        
        # Создаём компонент
        component = Component3D(
            model_name=model_name,
            display_name=get_display_name(model_name),
            position=position,
            scale=1.0,
            original_thickness=original_thickness,
            remaining_thickness=remaining_thickness,
            corrosion_level=corrosion_level,
            material=material
        )
        
        # Передаём данные секции только при добавлении первого компонента
        if i == 0:
            viewer.add_component(component, fluid_type, section_data)
        else:
            viewer.add_component(component, fluid_type)
    
    print(f"\n{'='*60}")
    print(f"Загрузка завершена! Всего компонентов: {len(viewer.components)}")
    print(f"{'='*60}")
    
    # Запускаем просмотрщик
    viewer.run()

# ============================================================================
# ТЕСТОВАЯ ФУНКЦИЯ
# ============================================================================

def test_3d_viewer():
    """Тестирование 3D просмотрщика"""
    
    # Тест 1: Газовая труба
    print("\n" + "="*60)
    print("ТЕСТ 1: ГАЗОВАЯ ТРУБА (простая)")
    print("="*60)
    
    test_pipe = {
        "name": "Газовая труба Г-1",
        "object_type": "pipe",
        "is_complex": False,
        "thickness": 12.0,
        "remaining_thickness": 10.5,
        "corrosion_level": "хорошее",
        "material": "Сталь 20"
    }
    
    show_3d_viewer(test_pipe, "gas")

if __name__ == "__main__":
    # Проверяем наличие папок с моделями
    print("Проверка наличия 3D моделей...")
    
    for fluid in ["oil", "gas"]:
        path = f"assets/3D_models/{fluid}"
        if os.path.exists(path):
            files = [f for f in os.listdir(path) if f.endswith('.obj')]
            print(f"  {fluid.upper()}: {len(files)} файлов")
            for file in files[:5]:  # Покажем первые 5 файлов
                print(f"    - {file}")
            if len(files) > 5:
                print(f"    ... и ещё {len(files) - 5} файлов")
        else:
            print(f"  {fluid.upper()}: папка не найдена - {path}")
    
    # Запускаем тест
    test_3d_viewer()
