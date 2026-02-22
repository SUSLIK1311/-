"""Общие константы приложения"""

# Стандартные диаметры труб (мм) для нефти и газа
PIPE_STANDARDS = {
    "oil": [159, 219, 273, 325, 377, 426, 478, 529, 630, 720, 820, 920, 1020, 1220],
    "gas": [159, 219, 273, 325, 377, 426, 478, 529, 630, 720, 820, 920, 1020, 1220, 1420]
}

# Стандартные толщины стенок для диаметров (мм)
PIPE_THICKNESS_STANDARD = {
    159: 5, 219: 6, 273: 6, 325: 7, 377: 7, 
    426: 8, 478: 8, 529: 9, 630: 9, 720: 10,
    820: 11, 920: 12, 1020: 13, 1220: 14, 1420: 15
}

def get_object_display_name(object_type):
    """Возвращает русское название для отображения"""
    # Маппинг object_type на русские названия
    display_names = {
        # Нефть
        "nps_template": "НПС",
        "pipe_above": "Труба",
        "pipe_underground": "Труба",
        "heater_template": "Подогрев",
        "tank_template": "Резервуар",
        "separator_template": "Отстойник",
        
        # Газ
        "ks_template": "КС",
        "filter_template": "Фильтр",
        "grs_template": "ГРС",
        "dryer_template": "Осушитель",
        "consumer_template": "Потребитель",
        
        # Общие
        "pipe": "Труба",
        "tank": "Резервуар",
        "nps": "НПС",
        "ks": "КС",
    }
    
    # Ищем полное совпадение
    if object_type in display_names:
        return display_names[object_type]
    
    # Ищем частичное совпадение
    for key, value in display_names.items():
        if key in object_type:
            return value
    
    # Если не нашли, пробуем извлечь из object_type
    if "nps" in object_type.lower():
        return "НПС"
    elif "ks" in object_type.lower():
        return "КС"
    elif "pipe" in object_type.lower():
        return "Труба"
    elif "heater" in object_type.lower():
        return "Подогрев"
    elif "tank" in object_type.lower():
        return "Резервуар"
    elif "separator" in object_type.lower():
        return "Отстойник"
    elif "filter" in object_type.lower():
        return "Фильтр"
    elif "grs" in object_type.lower():
        return "ГРС"
    elif "dryer" in object_type.lower():
        return "Осушитель"
    elif "consumer" in object_type.lower():
        return "Потребитель"
    
    return ""  # пустая строка если не определили

def get_recommended_thickness(diameter):
    """Возвращает рекомендуемую толщину стенки для диаметра"""
    return PIPE_THICKNESS_STANDARD.get(diameter, 10)

# Список доступных материалов с расшифровкой
PIPE_MATERIALS = [
    "Ст20",
    "Ст45", 
    "09Г2С",
    "17Г1С",
    "X42",
    "X52",
    "X60",
    "X65",
    "X70",
    "13ХФА",
    "08Х18Н10Т",
    "AISI 304",
    "AISI 316"
]

# Стандартные участки труб 
STANDARD_PIPE_SECTIONS = {
    "oil": [
        {"name": "Труба 720мм", "length": 5000, "diameter": 720, "thickness": 10, "material": "Ст20"},
        {"name": "Труба 529мм", "length": 3000, "diameter": 529, "thickness": 9, "material": "09Г2С"},
        {"name": "Труба 426мм", "length": 2000, "diameter": 426, "thickness": 8, "material": "17Г1С"}
    ],
    "gas": [
        {"name": "Труба 1020мм", "length": 6000, "diameter": 1020, "thickness": 13, "material": "X60"},
        {"name": "Труба 820мм", "length": 4000, "diameter": 820, "thickness": 11, "material": "X52"},
        {"name": "Труба 530мм", "length": 2000, "diameter": 530, "thickness": 10, "material": "X42"}
    ]
}
