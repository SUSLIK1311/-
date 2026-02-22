"""Модели данных для трубопровода"""
from dataclasses import dataclass, field
from typing import List, Dict, Optional, Union, Any
from enum import Enum

class ComponentType(Enum):
    """Типы компонентов"""
    PIPE = "pipe"
    EQUIPMENT = "equipment"

# ============================================================================
# Решение: делаем всё без наследования
# ============================================================================

@dataclass
class Component:
    """Универсальный компонент (может быть трубой или оборудованием)"""
    # Обязательные поля
    component_id: str
    component_type: ComponentType
    material: str
    
    # Поля для труб
    length: Optional[float] = None  # м
    diameter: Optional[float] = None  # мм
    thickness: Optional[float] = None  # мм
    
    # Поля для оборудования
    wall_thickness: Optional[float] = None  # мм
    count: int = 1
    
    # Коэффициенты
    special_coefficient: float = 1.0
    temperature: float = 20.0
    flow_velocity: float = 1.0
    
    # Вспомогательные методы
    def is_pipe(self) -> bool:
        return self.component_type == ComponentType.PIPE
    
    def is_equipment(self) -> bool:
        return self.component_type == ComponentType.EQUIPMENT
    
    @classmethod
    def create_pipe(cls, component_id: str, length: float, diameter: float, 
                   thickness: float, material: str, **kwargs):
        """Фабричный метод для создания трубы"""
        return cls(
            component_id=component_id,
            component_type=ComponentType.PIPE,
            material=material,
            length=length,
            diameter=diameter,
            thickness=thickness,
            **kwargs
        )
    
    @classmethod
    def create_equipment(cls, component_id: str, wall_thickness: float,
                        material: str, count: int = 1, **kwargs):
        """Фабричный метод для создания оборудования"""
        return cls(
            component_id=component_id,
            component_type=ComponentType.EQUIPMENT,
            material=material,
            wall_thickness=wall_thickness,
            count=count,
            **kwargs
        )

@dataclass
class ComplexSection:
    """Сложный участок (НПС, КС, ГРС и т.д.)"""
    # Обязательные
    name: str
    object_type: str
    location: str
    protection: str
    environment: str
    
    # Дефолтные
    components: List[Component] = field(default_factory=list)
    
    @property
    def total_length(self) -> float:
        return sum(c.length for c in self.components if c.is_pipe() and c.length)
    
    @property
    def total_components(self) -> int:
        total = 0
        for comp in self.components:
            if comp.is_equipment():
                total += comp.count
            else:
                total += 1
        return total
    
    def add_pipe(self, component_id: str, length: float, diameter: float,
                thickness: float, material: str, **kwargs):
        """Добавляет трубу"""
        pipe = Component.create_pipe(
            component_id=component_id,
            length=length,
            diameter=diameter,
            thickness=thickness,
            material=material,
            **kwargs
        )
        self.components.append(pipe)
    
    def add_equipment(self, component_id: str, wall_thickness: float,
                     material: str, count: int = 1, **kwargs):
        """Добавляет оборудование"""
        equipment = Component.create_equipment(
            component_id=component_id,
            wall_thickness=wall_thickness,
            material=material,
            count=count,
            **kwargs
        )
        self.components.append(equipment)

# ============================================================================
# СТАРЫЕ КЛАССЫ (оставляем как есть)
# ============================================================================

@dataclass
class SimpleSection:
    """Простая труба (старый формат)"""
    name: str
    length: float
    diameter: float
    thickness: float
    material: str
    location: str = "надземная"
    protection: str = "без защ."
    environment: str = "Поволжье"
    
    def to_dict(self):
        return {
            "name": self.name,
            "length": self.length,
            "diameter": self.diameter,
            "thickness": self.thickness,
            "material": self.material,
            "location": self.location,
            "protection": self.protection,
            "environment": self.environment,
            "is_simple": True
        }

@dataclass  
class OilParameters:
    temperature: float = 60.0
    water_content: float = 5.0
    h2s_content: float = 50.0
    viscosity: float = 15.0
    flow_rate: float = 1000.0

@dataclass
class GasParameters:
    temperature: float = 20.0
    pressure: float = 5.0
    co2_content: float = 2.0
    methane_content: float = 85.0
    dew_point: float = -10.0

@dataclass
class PipelineProject:
    fluid_type: str
    simple_sections: List[SimpleSection] = field(default_factory=list)
    complex_sections: List[ComplexSection] = field(default_factory=list)
    fluid_params: Union[OilParameters, GasParameters] = field(default_factory=OilParameters)

@dataclass
class CorrosionResult:
    section_name: str
    component_id: Optional[str] = None
    component_type: Optional[ComponentType] = None
    initial_thickness: float = 0.0
    remaining_thickness: float = 0.0  
    corrosion_rate: float = 0.0
    corrosion_level: str = "отличное"
    color: str = "green"

# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ
# ============================================================================

def create_simple_section(name: str, length: float, diameter: float,
                         thickness: float, material: str, **kwargs):
    return SimpleSection(
        name=name,
        length=length,
        diameter=diameter,
        thickness=thickness,
        material=material,
        **kwargs
    )

def create_complex_section(name: str, object_type: str, location: str,
                          protection: str, environment: str):
    return ComplexSection(
        name=name,
        object_type=object_type,
        location=location,
        protection=protection,
        environment=environment
    )
