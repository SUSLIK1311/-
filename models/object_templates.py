"""Шаблоны сложных объектов трубопровода с компонентами"""
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class ComponentTemplate:
    """Шаблон компонента"""
    component_id: str  # ID из списка файлов (например "pipe.main", "pumps")
    name: str  # Человекочитаемое название
    required: bool  # Обязательный ли компонент
    component_type: str  # "pipe" или "equipment"
    
    # Параметры по умолчанию (будут подсказываться в диалоге)
    defaults: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.defaults is None:
            self.defaults = {}

@dataclass
class ObjectTemplate:
    """Шаблон сложного объекта (НПС, КС и т.д.)"""
    template_id: str  # "pump_station", "separator", etc.
    name: str  # "Насосная станция (НПС)"
    description: str  # Описание объекта
    fluid_type: str  # "oil" или "gas"
    icon: str = ""  # Имя файла иконки (опционально)
    
    # Компоненты объекта
    pipe_components: List[ComponentTemplate] = None
    equipment_components: List[ComponentTemplate] = None
    
    def __post_init__(self):
        if self.pipe_components is None:
            self.pipe_components = []
        if self.equipment_components is None:
            self.equipment_components = []
    
    @property
    def all_components(self) -> List[ComponentTemplate]:
        """Все компоненты объекта"""
        return self.pipe_components + self.equipment_components
    
    @property
    def required_components(self) -> List[ComponentTemplate]:
        """Только обязательные компоненты"""
        return [c for c in self.all_components if c.required]

# ============================================================================
# ШАБЛОНЫ ОБЪЕКТОВ ДЛЯ НЕФТИ (OIL)
# ============================================================================

OIL_TEMPLATES: Dict[str, ObjectTemplate] = {
    "pump_station": ObjectTemplate(
        template_id="pump_station",
        name="Насосная станция (НПС)",
        description="Участок с насосами, фильтрами и резервуарами для перекачки нефти",
        fluid_type="oil",
        icon="pump_station.png",
        pipe_components=[
            ComponentTemplate(
                component_id="pipe.main",
                name="Магистральная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 50.0, "diameter": 720.0, "thickness": 12.0}
            ),
            ComponentTemplate(
                component_id="pipe.medium", 
                name="Трубы между резервуарами",
                required=False,
                component_type="pipe",
                defaults={"length": 120.0, "diameter": 529.0, "thickness": 10.0}
            ),
        ],
        equipment_components=[
            ComponentTemplate(
                component_id="pumps",
                name="Насосы",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 15.0, "count": 3, "material": "09Г2С"}
            ),
            ComponentTemplate(
                component_id="filters",
                name="Фильтры",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 12.0, "count": 2, "material": "Ст20"}
            ),
            ComponentTemplate(
                component_id="reservoirs",
                name="Резервуары",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 14.0, "count": 4, "material": "09Г2С"}
            ),
        ]
    ),
    
    "separator": ObjectTemplate(
        template_id="separator",
        name="Отстойник/сепаратор",
        description="Разделяет нефть, воду и механические примеси",
        fluid_type="oil",
        icon="separator.png",
        pipe_components=[
            ComponentTemplate(
                component_id="dirty.oil",
                name="Труба грязной нефти (вход)",
                required=True,
                component_type="pipe",
                defaults={"length": 20.0, "diameter": 426.0, "thickness": 10.0}
            ),
            ComponentTemplate(
                component_id="clean.oil",
                name="Труба чистой нефти (выход)",
                required=True,
                component_type="pipe",
                defaults={"length": 20.0, "diameter": 426.0, "thickness": 10.0}
            ),
            ComponentTemplate(
                component_id="water",
                name="Дренажная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 15.0, "diameter": 219.0, "thickness": 8.0}
            ),
        ],
        equipment_components=[
            ComponentTemplate(
                component_id="separator.base",
                name="Корпус сепаратора",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 16.0, "count": 1, "material": "09Г2С"}
            ),
        ]
    ),
    
    "heater": ObjectTemplate(
        template_id="heater",
        name="Подогреватель",
        description="Подогревает нефть для снижения вязкости",
        fluid_type="oil",
        icon="heater.png",
        pipe_components=[
            ComponentTemplate(
                component_id="inlet.pipe",
                name="Входная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 15.0, "diameter": 426.0, "thickness": 10.0}
            ),
            ComponentTemplate(
                component_id="outlet.pipe",
                name="Выходная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 15.0, "diameter": 426.0, "thickness": 10.0}
            ),
        ],
        equipment_components=[
            ComponentTemplate(
                component_id="heater.base",
                name="Теплообменник",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 12.0, "count": 1, "material": "X60"}
            ),
        ]
    ),
    
    "reservoir": ObjectTemplate(
        template_id="reservoir",
        name="Резервуар",
        description="Отдельный резервуар для хранения нефти",
        fluid_type="oil",
        icon="reservoir.png",
        pipe_components=[
            ComponentTemplate(
                component_id="inlet.pipe",
                name="Входная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 25.0, "diameter": 529.0, "thickness": 11.0}
            ),
            ComponentTemplate(
                component_id="outlet.pipe",
                name="Выходная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 25.0, "diameter": 529.0, "thickness": 11.0}
            ),
        ],
        equipment_components=[
            ComponentTemplate(
                component_id="reservoir.base",
                name="Корпус резервуара",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 14.0, "count": 1, "material": "09Г2С"}
            ),
        ]
    ),
    
    "pipe": ObjectTemplate(
        template_id="pipe",
        name="Труба",
        description="Обычная надземная труба",
        fluid_type="oil",
        icon="pipe.png",
        pipe_components=[
            ComponentTemplate(
                component_id="pipe.paint",
                name="Труба",
                required=True,
                component_type="pipe",
                defaults={"length": 1000.0, "diameter": 720.0, "thickness": 10.0}
            ),
        ],
        equipment_components=[]
    ),
    
    "pipe_underground": ObjectTemplate(
        template_id="pipe_underground",
        name="Труба",
        description="Труба, проложенная под землёй",
        fluid_type="oil",
        icon="pipe_underground.png",
        pipe_components=[
            ComponentTemplate(
                component_id="pipe.underground",
                name="Подземная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 1000.0, "diameter": 720.0, "thickness": 12.0}
            ),
        ],
        equipment_components=[]
    ),
}

# ============================================================================
# ШАБЛОНЫ ОБЪЕКТОВ ДЛЯ ГАЗА (GAS)
# ============================================================================

GAS_TEMPLATES: Dict[str, ObjectTemplate] = {
    "compressor_station": ObjectTemplate(
        template_id="compressor_station",
        name="Компрессорная станция (КС)",
        description="Станция для сжатия газа и поддержания давления",
        fluid_type="gas",
        icon="compressor_station.png",
        pipe_components=[
            ComponentTemplate(
                component_id="pipe.main",
                name="Магистральная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 60.0, "diameter": 1020.0, "thickness": 14.0}
            ),
        ],
        equipment_components=[
            ComponentTemplate(
                component_id="builds",
                name="Компрессоры",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 18.0, "count": 4, "material": "X60"}
            ),
        ]
    ),
    
    "grs": ObjectTemplate(
        template_id="grs",
        name="Газораспределительная станция (ГРС)",
        description="Распределяет газ потребителям с регулировкой давления",
        fluid_type="gas",
        icon="grs.png",
        pipe_components=[
            ComponentTemplate(
                component_id="pipe.main",
                name="Магистральная труба (вход)",
                required=True,
                component_type="pipe",
                defaults={"length": 40.0, "diameter": 1020.0, "thickness": 13.0}
            ),
            ComponentTemplate(
                component_id="big.consumer.pipe",
                name="Труба к крупному потребителю",
                required=False,
                component_type="pipe",
                defaults={"length": 200.0, "diameter": 720.0, "thickness": 11.0}
            ),
            ComponentTemplate(
                component_id="medium.consumer.pipe",
                name="Труба к среднему потребителю",
                required=False,
                component_type="pipe",
                defaults={"length": 150.0, "diameter": 530.0, "thickness": 10.0}
            ),
            ComponentTemplate(
                component_id="small.consumer.pipe",
                name="Труба к мелкому потребителю",
                required=False,
                component_type="pipe",
                defaults={"length": 100.0, "diameter": 325.0, "thickness": 8.0}
            ),
        ],
        equipment_components=[
            ComponentTemplate(
                component_id="filter",
                name="Фильтр",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 12.0, "count": 2, "material": "X52"}
            ),
            ComponentTemplate(
                component_id="fork",
                name="Разветвитель",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 15.0, "count": 1, "material": "X60"}
            ),
        ]
    ),
    
    "dryer": ObjectTemplate(
        template_id="dryer",
        name="Осушитель",
        description="Удаляет влагу из газа",
        fluid_type="gas",
        icon="dryer.png",
        pipe_components=[
            ComponentTemplate(
                component_id="inlet.pipe",
                name="Входная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 20.0, "diameter": 820.0, "thickness": 12.0}
            ),
            ComponentTemplate(
                component_id="outlet.pipe",
                name="Выходная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 20.0, "diameter": 820.0, "thickness": 12.0}
            ),
            ComponentTemplate(
                component_id="transition.pipe",
                name="Переходная труба",
                required=False,
                component_type="pipe",
                defaults={"length": 15.0, "diameter": 630.0, "thickness": 10.0}
            ),
        ],
        equipment_components=[
            ComponentTemplate(
                component_id="adsorbers",
                name="Адсорберы",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 14.0, "count": 2, "material": "X60"}
            ),
            ComponentTemplate(
                component_id="separator",
                name="Сепаратор",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 16.0, "count": 1, "material": "X52"}
            ),
        ]
    ),
    
    "filter": ObjectTemplate(
        template_id="filter",
        name="Фильтр",
        description="Очистка газа от механических примесей",
        fluid_type="gas",
        icon="filter.png",
        pipe_components=[
            ComponentTemplate(
                component_id="inlet.pipe",
                name="Входная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 15.0, "diameter": 630.0, "thickness": 11.0}
            ),
            ComponentTemplate(
                component_id="outlet.pipe",
                name="Выходная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 15.0, "diameter": 630.0, "thickness": 11.0}
            ),
        ],
        equipment_components=[
            ComponentTemplate(
                component_id="filter.body",
                name="Корпус фильтра",
                required=True,
                component_type="equipment",
                defaults={"wall_thickness": 12.0, "count": 1, "material": "X52"}
            ),
        ]
    ),
    
    "pipe": ObjectTemplate(
        template_id="pipe",
        name="Труба",
        description="Обычная надземная труба",
        fluid_type="gas",
        icon="pipe.png",
        pipe_components=[
            ComponentTemplate(
                component_id="pipe.paint",
                name="Труба",
                required=True,
                component_type="pipe",
                defaults={"length": 1000.0, "diameter": 1020.0, "thickness": 13.0}
            ),
        ],
        equipment_components=[]
    ),
    
    "pipe_underground": ObjectTemplate(
        template_id="pipe_underground",
        name="Труба",
        description="Труба, проложенная под землёй",
        fluid_type="gas",
        icon="pipe_underground.png",
        pipe_components=[
            ComponentTemplate(
                component_id="pipe.underground",
                name="Подземная труба",
                required=True,
                component_type="pipe",
                defaults={"length": 1000.0, "diameter": 1020.0, "thickness": 15.0}
            ),
        ],
        equipment_components=[]
    ),
}

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def get_available_templates(fluid_type: str) -> Dict[str, ObjectTemplate]:
    """Возвращает доступные шаблоны для указанного типа среды"""
    if fluid_type == "oil":
        return OIL_TEMPLATES
    elif fluid_type == "gas":
        return GAS_TEMPLATES
    else:
        return {}

def get_template(template_id: str, fluid_type: str) -> ObjectTemplate:
    """Возвращает шаблон по ID и типу среды"""
    templates = get_available_templates(fluid_type)
    return templates.get(template_id)

def get_component_template(template_id: str, fluid_type: str, component_id: str) -> ComponentTemplate:
    """Возвращает шаблон конкретного компонента"""
    template = get_template(template_id, fluid_type)
    if not template:
        return None
    
    # Ищем в трубах
    for comp in template.pipe_components:
        if comp.component_id == component_id:
            return comp
    
    # Ищем в оборудовании
    for comp in template.equipment_components:
        if comp.component_id == component_id:
            return comp
    
    return None

def create_section_from_template(template_id: str, fluid_type: str, 
                                name: str, location: str, protection: str, 
                                environment: str) -> Dict:
    """
    Создаёт структуру данных для новой секции на основе шаблона
    
    Возвращает словарь, готовый для создания ComplexSection
    """
    template = get_template(template_id, fluid_type)
    if not template:
        return None
    
    section_data = {
        "name": name,
        "object_type": template_id,
        "location": location,
        "protection": protection,
        "environment": environment,
        "components": []
    }
    
    return section_data

def get_default_material(fluid_type: str, component_type: str) -> str:
    """Возвращает материал по умолчанию для компонента"""
    if fluid_type == "oil":
        if component_type == "pipe":
            return "Ст20"
        else:  # equipment
            return "09Г2С"
    else:  # gas
        if component_type == "pipe":
            return "X60"
        else:  # equipment
            return "X52"

# ============================================================================
# КОНВЕРТАЦИЯ СТАРЫХ ИМЁН ОБЪЕКТОВ В НОВЫЕ ШАБЛОНЫ
# ============================================================================

OLD_TO_NEW_MAPPING = {
    # Oil
    "НПС": "pump_station",
    "Отстойник": "separator",
    "Подогрев": "heater",
    "Резервуар": "reservoir",
    "Труба": "pipe",
    
    # Gas
    "КС": "compressor_station",
    "ГРС": "grs",
    "Осушитель": "dryer",
    "Фильтр": "filter",
    "Труба": "pipe",
}

def convert_old_object_name(old_name: str, fluid_type: str) -> str:
    """Конвертирует старое имя объекта в новый template_id"""
    # Если имя уже в новом формате
    if old_name in get_available_templates(fluid_type):
        return old_name
    
    # Пробуем маппинг
    return OLD_TO_NEW_MAPPING.get(old_name, "pipe")  # по умолчанию труба
