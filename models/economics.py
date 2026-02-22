"""Экономические расчёты для трубопровода"""

ECONOMIC_PARAMS = {
    "работа_руб_час": 1500,
    "транспорт_руб_км": 50,
    "накладные_процент": 15,
    "простой_руб_час": 10000,
    
    # ЦЕНЫ МАТЕРИАЛОВ (руб/тонна)
    "стоимость_материалов": {
        "Ст20": 45000,
        "Ст45": 52000,
        "09Г2С": 68000,
        "17Г1С": 72000,
        "X42": 85000,
        "X52": 95000,
        "X60": 110000,
        "X65": 125000,
        "X70": 140000,
        "13ХФА": 180000,
        "08Х18Н10Т": 320000,
        "AISI 304": 350000,
        "AISI 316": 480000
    },
    
    # СТОИМОСТЬ ПОКРЫТИЙ И ЗАЩИТЫ (руб/м²)
    "стоимость_покрытий": {
        "без защиты": 0,
        "ППУ изол.": 1200,
        "эпоксид. покр.": 800,
        "битум. изол.": 600,
        "катод. + изол.": 1500,
        "бетон. покр.": 900,
        "полимер. усил.": 1400,
        "катод. + протек.": 2000,
        "двойн. изол.": 2800,
        "комплекс. защ.": 3500
    },
    
    # БАЗОВЫЕ СТОИМОСТИ (учитываются в расчётах с множителями)
    "базовая_стоимость_замены_руб_м": 5000,
    "базовая_стоимость_ремонта_руб_м2": 1000,
    
    # КОЭФФИЦИЕНТЫ В ЗАВИСИМОСТИ ОТ СОСТОЯНИЯ (остаточной толщины в мм)
    "коэффициенты_состояния": {
        "отличное": {"коэффициент": 0.3, "метод": "обслуживание", "часы_на_м": 0.5},
        "хорошее": {"коэффициент": 0.5, "метод": "покраска", "часы_на_м": 1.0},
        "удовлетворительное": {"коэффициент": 0.8, "метод": "частичный_ремонт", "часы_на_м": 2.0},
        "плохое": {"коэффициент": 1.5, "метод": "полная_замена", "часы_на_м": 4.0},
        "аварийное": {"коэффициент": 2.5, "метод": "экстренная_замена", "часы_на_м": 6.0}
    },
    
    # ДОПОЛНИТЕЛЬНЫЕ КОЭФФИЦИЕНТЫ
    "коэффициенты_срочности": {
        "отличное": 1.0,    # плановый ремонт
        "хорошее": 1.0,
        "удовлетворительное": 1.2,  # повышенное внимание
        "плохое": 1.5,      # срочный ремонт
        "аварийное": 2.0     # экстренный ремонт
    },
    
    # Коэффициенты сложности по типам прокладки
    "сложность_ремонта": {
        "надземная": 1.0,
        "подземная": 2.5, 
        "подводная": 4.0,
        "в помещении": 0.8,
        "в агрессивной среде": 1.8
    },
    
    # Коэффициенты региона (логистика, климат)
    "региональные_коэффициенты": {
        "Поволжье": 1.0,
        "Сибирь": 1.4,
        "Крайний Север": 2.0,
        "Дальний Восток": 1.6,
        "Урал": 1.2
    }
}

def get_economic_summary(sections_data):
    """Сводная экономическая статистика по всем участкам"""
    urgent_repair = 0
    planned_repair = 0
    urgent_count = 0
    planned_count = 0
    
    for section in sections_data:
        # Определяем состояние участка
        is_complex = section.get("is_complex", False)
        
        if is_complex:
            # Для комплексных участков определяем состояние по худшему компоненту
            components = section.get("components", [])
            if components:
                from .corrosion import get_corrosion_level
                worst_level = "отличное"
                for comp in components:
                    remaining = comp.get("remaining", 
                                       comp.get("thickness", 
                                              comp.get("wall_thickness", 10)))
                    level, _ = get_corrosion_level(remaining)
                    # Приоритет состояний: аварийное (0), плохое (1), и т.д.
                    priority = {"аварийное": 0, "плохое": 1, "удовлетворительное": 2, 
                               "хорошее": 3, "отличное": 4}
                    if priority.get(level, 5) < priority.get(worst_level, 5):
                        worst_level = level
                section["corrosion_level"] = worst_level
            else:
                section["corrosion_level"] = "удовлетворительное"
        else:
            # Для простых участков определяем уровень коррозии
            remaining = section.get("remaining_thickness", section.get("thickness", 10))
            from .corrosion import get_corrosion_level
            level, _ = get_corrosion_level(remaining)
            section["corrosion_level"] = level
        
        # Расчёт стоимости
        cost, method = calculate_repair_cost_detailed(section)
        
        # Учёт комплексности
        if is_complex:
            components_count = len(section.get("components", []))
            cost *= min(2.0, 1.0 + (components_count * 0.1))
        
        # Распределение по срочности
        urgency = section.get("corrosion_level", "удовлетворительное")
        
        if urgency in ["плохое", "аварийное"]:
            urgent_repair += cost
            urgent_count += 1
        else:
            planned_repair += cost  
            planned_count += 1
    
    return {
        "urgent_repair_cost": round(urgent_repair),
        "planned_repair_cost": round(planned_repair),
        "total_repair_cost": round(urgent_repair + planned_repair),
        "urgent_count": urgent_count,
        "planned_count": planned_count
    }

def get_component_state(component):
    """Определяет состояние компонента по остаточной толщине"""
    from models.corrosion import get_corrosion_level
    
    # Получаем остаточную толщину
    remaining = component.get("remaining")
    if remaining is None:
        # Если нет остаточной, используем текущую толщину
        remaining = component.get("thickness", component.get("wall_thickness", 10))
    
    # Используем существующую функцию определения уровня коррозии
    level, _ = get_corrosion_level(remaining)
    return level

def calculate_component_repair_cost(component, section_params):
    """РАСЧЁТ СТОИМОСТИ РЕМОНТА КОМПОНЕНТА С УЧЁТОМ СОСТОЯНИЯ"""
    
    # 1. Определяем состояние компонента
    state = get_component_state(component)
    
    # 2. Получаем базовые параметры компонента
    comp_type = component.get("component_type", "pipe")
    diameter = component.get("diameter", 100)
    length = component.get("length", 1)
    thickness = component.get("thickness", component.get("wall_thickness", 10))
    material = component.get("material", "Ст20")
    
    # 3. Получаем параметры участка
    location = section_params.get("location", "надземная")
    protection = section_params.get("protection", "без защиты")
    environment = section_params.get("environment", "Поволжье")
    
    # 4. Коэффициенты из экономических параметров
    state_params = ECONOMIC_PARAMS["коэффициенты_состояния"].get(state, 
        {"коэффициент": 1.0, "метод": "ремонт", "часы_на_м": 2.0})
    
    urgency_mult = ECONOMIC_PARAMS["коэффициенты_срочности"].get(state, 1.0)
    location_mult = ECONOMIC_PARAMS["сложность_ремонта"].get(location, 1.0)
    region_mult = ECONOMIC_PARAMS["региональные_коэффициенты"].get(environment, 1.0)
    
    # 5. Расчёт трудозатрат
    if comp_type == "pipe":
        base_hours = state_params["часы_на_м"] * length
    elif comp_type in ["valve", "flange", "tee"]:
        base_hours = state_params["часы_на_м"] * (diameter / 100) * 2
    else:
        base_hours = 8  # минимальные трудозатраты для неизвестных компонентов
    
    labor_hours = base_hours * location_mult
    labor_cost = labor_hours * ECONOMIC_PARAMS["работа_руб_час"] * urgency_mult
    
    # 6. Расчёт стоимости материалов
    material_price = ECONOMIC_PARAMS["стоимость_материалов"].get(material, 50000)
    
    if comp_type == "pipe":
        # Для труб считаем вес
        volume = 3.14159 * (diameter/1000) * (thickness/1000) * length  # м³
        weight = volume * 7850  # кг (плотность стали)
        material_cost = (weight / 1000) * material_price * state_params["коэффициент"]
    else:
        # Для фитингов - упрощённый расчёт
        material_cost = diameter * 10 * material_price / 1000 * state_params["коэффициент"]
    
    # 7. Стоимость покрытия (если нужно восстановление)
    protection_cost = 0
    if state in ["плохое", "аварийное"] or protection == "без защиты":
        protection_price = ECONOMIC_PARAMS["стоимость_покрытий"].get(protection, 0)
        if protection_price > 0:
            area = 3.14159 * diameter * length / 1000  # м²
            protection_cost = area * protection_price * 1.5  # +50% за восстановление
    
    # 8. Транспорт и логистика
    transport_cost = length * 0.001 * ECONOMIC_PARAMS["транспорт_руб_км"] * region_mult
    
    # 9. Накладные расходы
    subtotal = labor_cost + material_cost + protection_cost + transport_cost
    overhead = subtotal * (ECONOMIC_PARAMS["накладные_процент"] / 100)
    
    # 10. Итоговая стоимость
    total_cost = subtotal + overhead
    
    return {
        "total_cost": round(total_cost),
        "state": state,
        "repair_method": state_params["метод"],
        "labor_hours": round(labor_hours, 1),
        "labor_cost": round(labor_cost),
        "material_cost": round(material_cost),
        "protection_cost": round(protection_cost),
        "transport_cost": round(transport_cost),
        "overhead": round(overhead),
        "state_coefficient": state_params["коэффициент"],
        "urgency_multiplier": urgency_mult,
        "location_multiplier": location_mult,
        "region_multiplier": region_mult
    }

def get_section_display_params(section):
    """Получает параметры для отображения с учётом ВСЕХ компонентов"""
    is_complex = section.get("is_complex", False)
    
    if not is_complex:
        # Простой участок
        return {
            "diameter": section.get("diameter", 500),
            "length": section.get("length", 100),
            "thickness": section.get("thickness", 10),
            "material": section.get("material", "Ст20"),
            "location": section.get("location", "надземная"),
            "protection": section.get("protection", "без защиты"),
            "environment": section.get("environment", "Поволжье")
        }
    
    # СЛОЖНЫЙ УЧАСТОК: анализируем все компоненты
    components = section.get("components", [])
    if not components:
        return {
            "diameter": 500,
            "length": 100,
            "thickness": 10,
            "material": "Ст20",
            "location": section.get("location", "надземная"),
            "protection": section.get("protection", "без защиты"),
            "environment": section.get("environment", "Поволжье")
        }
    
    # Собираем статистику по всем компонентам
    pipe_components = [c for c in components if c.get("component_type") == "pipe"]
    
    if pipe_components:
        # Если есть трубы, берём средние значения
        avg_diameter = sum(c.get("diameter", 100) for c in pipe_components) / len(pipe_components)
        total_length = sum(c.get("length", 1) for c in pipe_components)
        avg_thickness = sum(c.get("thickness", c.get("wall_thickness", 10)) for c in pipe_components) / len(pipe_components)
        
        # Материал самого критичного компонента
        materials = [c.get("material", "Ст20") for c in components]
        from collections import Counter
        material_counts = Counter(materials)
        most_common_material = material_counts.most_common(1)[0][0]
        
        return {
            "diameter": avg_diameter,
            "length": total_length,
            "thickness": avg_thickness,
            "material": most_common_material,
            "location": section.get("location", "надземная"),
            "protection": section.get("protection", "без защиты"),
            "environment": section.get("environment", "Поволжье")
        }
    else:
        # Если нет труб, берём первый компонент
        first_comp = components[0]
        return {
            "diameter": first_comp.get("diameter", 100),
            "length": first_comp.get("length", 1),
            "thickness": first_comp.get("thickness", first_comp.get("wall_thickness", 10)),
            "material": first_comp.get("material", "Ст20"),
            "location": section.get("location", "надземная"),
            "protection": section.get("protection", "без защиты"),
            "environment": section.get("environment", "Поволжье")
        }

def calculate_repair_cost_detailed(section):
    """Детальный расчет стоимости участка с учётом ВСЕХ компонентов"""
    is_complex = section.get("is_complex", False)
    
    if not is_complex:
        # Простой участок - считаем как компонент
        component_data = {
            "component_type": "pipe",
            "diameter": section.get("diameter", 500),
            "length": section.get("length", 100),
            "thickness": section.get("thickness", 10),
            "wall_thickness": section.get("thickness", 10),
            "material": section.get("material", "Ст20"),
            "remaining": section.get("remaining_thickness", section.get("thickness", 10))
        }
        result = calculate_component_repair_cost(component_data, section)
        return result["total_cost"], result["repair_method"]
    
    # СЛОЖНЫЙ УЧАСТОК: суммируем стоимость всех компонентов
    components = section.get("components", [])
    if not components:
        return 0, "техническое_обслуживание"
    
    total_cost = 0
    component_states = []
    
    for component in components:
        comp_result = calculate_component_repair_cost(component, section)
        total_cost += comp_result["total_cost"]
        component_states.append(comp_result["state"])
    
    # Определяем общий метод ремонта по худшему состоянию
    state_priority = {"аварийное": 0, "плохое": 1, "удовлетворительное": 2, "хорошее": 3, "отличное": 4}
    worst_state = min(component_states, key=lambda x: state_priority.get(x, 5))
    
    # Метод ремонта в зависимости от худшего состояния
    state_to_method = {
        "аварийное": "экстренный_комплексный_ремонт",
        "плохое": "комплексный_ремонт",
        "удовлетворительное": "плановый_ремонт",
        "хорошее": "техническое_обслуживание",
        "отличное": "диагностика"
    }
    
    repair_method = state_to_method.get(worst_state, "ремонт")
    
    return round(total_cost), repair_method

def calculate_detailed_repair_costs(section):
    """Детальный расчет всех составляющих стоимости ремонта участка"""
    is_complex = section.get("is_complex", False)
    
    if not is_complex:
        # Для простых участков используем функцию компонента
        component_data = {
            "component_type": "pipe",
            "diameter": section.get("diameter", 500),
            "length": section.get("length", 100),
            "thickness": section.get("thickness", 10),
            "wall_thickness": section.get("thickness", 10),
            "material": section.get("material", "Ст20"),
            "remaining": section.get("remaining_thickness", section.get("thickness", 10))
        }
        
        result = calculate_component_repair_cost(component_data, section)
        
        # Добавляем параметры для совместимости
        result.update({
            "material_weight": calculate_material_weight(component_data),
            "material_price": ECONOMIC_PARAMS["стоимость_материалов"].get(
                component_data["material"], 50000
            ),
            "protection_area": calculate_protection_area(component_data),
            "protection_price": ECONOMIC_PARAMS["стоимость_покрытий"].get(
                section.get("protection", "без защиты"), 0
            ),
            "transport_distance": section.get("length", 100) * 0.001,
            "transport_rate": ECONOMIC_PARAMS["транспорт_руб_км"],
            "complexity": ECONOMIC_PARAMS["сложность_ремонта"].get(
                section.get("location", "надземная"), 1.0
            ),
            "complexity_cost": result["total_cost"] * (
                ECONOMIC_PARAMS["сложность_ремонта"].get(
                    section.get("location", "надземная"), 1.0
                ) - 1
            ),
            "overhead_percent": ECONOMIC_PARAMS["накладные_процент"],
            "downtime_rate": ECONOMIC_PARAMS["простой_руб_час"],
            "base_cost": result["material_cost"] + result["labor_cost"]
        })
        
        return result
    
    # СЛОЖНЫЙ УЧАСТОК: агрегируем данные всех компонентов
    components = section.get("components", [])
    
    total_labor_hours = 0
    total_labor_cost = 0
    total_material_cost = 0
    total_protection_cost = 0
    total_transport_cost = 0
    component_states = []
    
    for component in components:
        comp_result = calculate_component_repair_cost(component, section)
        
        total_labor_hours += comp_result["labor_hours"]
        total_labor_cost += comp_result["labor_cost"]
        total_material_cost += comp_result["material_cost"]
        total_protection_cost += comp_result.get("protection_cost", 0)
        total_transport_cost += comp_result["transport_cost"]
        component_states.append(comp_result["state"])
    
    # Определяем общее состояние
    state_priority = {"аварийное": 0, "плохое": 1, "удовлетворительное": 2, "хорошее": 3, "отличное": 4}
    worst_state = min(component_states, key=lambda x: state_priority.get(x, 5))
    
    # Суммируем субтотал
    subtotal = total_labor_cost + total_material_cost + total_protection_cost + total_transport_cost
    
    # Коэффициент сложности (максимальный из компонентов)
    location = section.get("location", "надземная")
    complexity = ECONOMIC_PARAMS["сложность_ремонта"].get(location, 1.0)
    
    # Для сложных участков добавляем коэффициент координации
    coordination_mult = 1.2  # +20% за координацию работ
    
    total_before_overhead = subtotal * complexity * coordination_mult
    complexity_cost = total_before_overhead - subtotal
    
    # Накладные расходы
    overhead_percent = ECONOMIC_PARAMS["накладные_процент"]
    overhead_cost = total_before_overhead * (overhead_percent / 100)
    
    # Итоговая стоимость
    total_cost = total_before_overhead + overhead_cost
    
    # Определяем метод ремонта
    state_to_method = {
        "аварийное": "экстренный_комплексный_ремонт",
        "плохое": "комплексный_ремонт",
        "удовлетворительное": "плановый_ремонт",
        "хорошее": "техническое_обслуживание",
        "отличное": "диагностика"
    }
    repair_method = state_to_method.get(worst_state, "ремонт")
    
    return {
        "repair_method": repair_method,
        "labor_hours": round(total_labor_hours, 1),
        "labor_rate": ECONOMIC_PARAMS["работа_руб_час"],
        "labor_cost": round(total_labor_cost),
        "material_weight": sum(calculate_material_weight(c) for c in components),
        "material_price": ECONOMIC_PARAMS["стоимость_материалов"].get(
            section.get("material", "Ст20"), 50000
        ),
        "material_cost": round(total_material_cost),
        "protection_area": sum(calculate_protection_area(c) for c in components if c.get("component_type") == "pipe"),
        "protection_price": ECONOMIC_PARAMS["стоимость_покрытий"].get(
            section.get("protection", "без защиты"), 0
        ),
        "protection_cost": round(total_protection_cost),
        "base_cost": round(total_material_cost + total_labor_cost),
        "transport_distance": sum(c.get("length", 1) for c in components if c.get("component_type") == "pipe") * 0.001,
        "transport_rate": ECONOMIC_PARAMS["транспорт_руб_км"],
        "transport_cost": round(total_transport_cost),
        "complexity": round(complexity, 2),
        "complexity_cost": round(complexity_cost),
        "overhead_percent": overhead_percent,
        "overhead_cost": round(overhead_cost),
        "total_cost": round(total_cost),
        "downtime_rate": ECONOMIC_PARAMS["простой_руб_час"],
        "component_count": len(components),
        "worst_state": worst_state
    }

# Остальные функции остаются с небольшими доработками...

def get_repair_method_info(method):
    """Возвращает описание метода ремонта с учётом состояния"""
    methods = {
        "экстренный_комплексный_ремонт": {
            "name": "ЭКСТРЕННЫЙ комплексный ремонт",
            "description": "Немедленная замена всех аварийных компонентов. Требуется остановка системы.",
            "duration": "1-3 дня",
            "urgency": "КРИТИЧЕСКАЯ"
        },
        "комплексный_ремонт": {
            "name": "Комплексный ремонт участка",
            "description": "Замена повреждённых компонентов и усиление защиты.",
            "duration": "3-7 дней",
            "urgency": "ВЫСОКАЯ"
        },
        "плановый_ремонт": {
            "name": "Плановый ремонт",
            "description": "Частичная замена изношенных элементов по графику.",
            "duration": "7-14 дней",
            "urgency": "СРЕДНЯЯ"
        },
        "техническое_обслуживание": {
            "name": "Техническое обслуживание",
            "description": "Профилактические работы: покраска, очистка, диагностика.",
            "duration": "1-2 дня",
            "urgency": "НИЗКАЯ"
        },
        "диагностика": {
            "name": "Диагностика и мониторинг",
            "description": "Контроль состояния, замеры толщины, анализ коррозии.",
            "duration": "1 день",
            "urgency": "МИНИМАЛЬНАЯ"
        }
    }
    
    # Добавляем старые методы для обратной совместимости
    old_methods = {
        "замена_участка": {
            "name": "Замена участка трубы",
            "description": "Удаление поврежденного участка и установка нового.",
            "duration": "2-5 дней",
            "urgency": "ВЫСОКАЯ"
        },
        "усиление_изоляции": {
            "name": "Усиление изоляции",
            "description": "Нанесение дополнительных защитных покрытий.",
            "duration": "1-3 дня",
            "urgency": "СРЕДНЯЯ"
        }
    }
    
    methods.update(old_methods)
    return methods.get(method, {"name": method, "description": "Стандартный метод ремонта", "duration": "3-5 дней", "urgency": "СРЕДНЯЯ"})

# Существующие вспомогательные функции остаются
def calculate_material_weight(params):
    """Рассчитывает вес материала в кг"""
    if isinstance(params, dict) and "diameter" in params:
        diameter = params["diameter"] / 1000  # метры
        thickness = params.get("thickness", params.get("wall_thickness", 10)) / 1000
        length = params.get("length", 1)
        volume = 3.14159 * diameter * thickness * length
        return volume * 7850
    return 0

def calculate_protection_area(params):
    """Рассчитывает площадь покрытия в м²"""
    if isinstance(params, dict) and "diameter" in params:
        diameter = params["diameter"] / 1000
        length = params.get("length", 1)
        return 3.14159 * diameter * length
    return 0

def calculate_repair_cost(section):
    """Базовая функция для обратной совместимости"""
    cost, _ = calculate_repair_cost_detailed(section)
    return cost

def calculate_downtime_cost(section, downtime_hours=24):
    """Стоимость простоя системы (если еще нет в файле)"""
    return 0  # Простая заглушка
