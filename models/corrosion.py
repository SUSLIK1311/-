"""
Модели расчёта коррозии для нефтегазовой промышленности
Основано на моделях: де Вааля (CO2 коррозия) и Norsok M-506
"""

import math

# ============================================================================
# ФУНДАМЕНТАЛЬНЫЕ МОДЕЛИ КОРРОЗИИ
# ============================================================================

def de_waard_milliams_co2_rate(T_C: float, P_CO2_bar: float, pH: float, 
                                material_factor: float = 1.0) -> float:
    """
    Модель де Вааля-Милльямса для скорости CO2 коррозии (1995)
    
    Parameters:
    -----------
    T_C : температура, °C
    P_CO2_bar : парциальное давление CO2, бар
    pH : pH среды
    material_factor : коэффициент материала (0.2-1.0)
    
    Returns:
    --------
    corrosion_rate : скорость коррозии, мм/год
    
    Reference:
    ----------
    De Waard, C., Milliams, D.E. (1995) "Prediction of CO2 corrosion of carbon steel"
    """
    if P_CO2_bar <= 0:
        return 0.0
    
    T_K = T_C + 273.15  # Конвертация в Кельвины
    
    # Уравнение де Вааля-Милльямса (1995)
    log_V_corr = 5.8 - (1710 / T_K) + 0.67 * math.log10(P_CO2_bar)
    V_corr = 10**log_V_corr  # мм/год
    
    # Поправка на pH (фактор защитной плёнки)
    if pH < 3.5:
        f_pH = 1.0
    elif pH < 6.0:
        f_pH = 1.0 - 0.13 * (pH - 3.5)
    else:
        f_pH = 0.67
    
    # Поправка на масляную фазу (только для нефти)
    f_oil = 0.7  # Упрощённо - наличие нефти снижает коррозию на 30%
    
    return V_corr * f_pH * f_oil * material_factor


def norsok_m506_co2_rate(T_C: float, P_CO2_bar: float, P_H2S_bar: float, 
                          velocity_ms: float, pH: float, material_factor: float = 1.0) -> float:
    """
    Модель Norsok M-506 для CO2/H2S коррозии (2005)
    
    Parameters:
    -----------
    T_C : температура, °C
    P_CO2_bar : парциальное давление CO2, бар
    P_H2S_bar : парциальное давление H2S, бар
    velocity_ms : скорость потока, м/с
    pH : pH среды
    material_factor : коэффициент материала
    
    Returns:
    --------
    corrosion_rate : скорость коррозии, мм/год
    
    Reference:
    ----------
    Norsok Standard M-506 (2005) "CO2 corrosion rate calculation model"
    """
    T_K = T_C + 273.15
    
    # Основное уравнение Norsok
    log_V_corr = 5.45 - (1119 / T_K) + 0.58 * math.log10(P_CO2_bar + 0.1 * P_H2S_bar)
    V_corr = 10**log_V_corr  # мм/год
    
    # Поправка на pH
    if pH < 3.5:
        f_pH = 1.0
    elif pH < 6.0:
        f_pH = 0.67  # Норсок использует фиксированный коэффициент
    else:
        f_pH = 0.1   # При высоком pH образуется защитная плёнка
    
    # Поправка на скорость потока (эрозионная коррозия)
    if velocity_ms < 1.0:
        f_flow = 1.0
    elif velocity_ms < 10.0:
        f_flow = 1.0 + 0.1 * (velocity_ms - 1.0)
    elif velocity_ms < 20.0:
        f_flow = 2.0 + 0.3 * (velocity_ms - 10.0)
    else:
        f_flow = 5.0  # Сильная эрозия при высоких скоростях
    
    # Поправка на H2S (защитная сульфидная плёнка при определённых условиях)
    f_H2S = 1.0
    if P_H2S_bar > 0.01 and T_C < 100:
        if P_H2S_bar / P_CO2_bar > 0.01:  # Сульфидная плёнка может формироваться
            f_H2S = 0.5  # Снижение коррозии за счёт плёнки
    
    return V_corr * f_pH * f_flow * f_H2S * material_factor


def calculate_ph(T_C: float, P_CO2_bar: float, bicarbonate_mmol: float = 1.0) -> float:
    """
    Расчёт pH водной фазы с учётом растворённого CO2
    
    Parameters:
    -----------
    T_C : температура, °C
    P_CO2_bar : парциальное давление CO2, бар
    bicarbonate_mmol : концентрация бикарбоната, ммоль/л
    
    Returns:
    --------
    pH : расчётное значение pH
    
    Reference:
    ----------
    Simplified from "Corrosion Engineering" by Fontana
    """
    # Константа диссоциации угольной кислоты при температуре
    T_K = T_C + 273.15
    # Температурная зависимость
    pKa1 = 6.35 - 0.01 * (T_C - 25)  # Первая константа диссоциации H2CO3
    
    # Растворимость CO2 по Генри
    K_H = 0.034 * math.exp(2400 * (1/T_K - 1/298.15))  # Моль/(л*атм)
    
    # Концентрация растворённого CO2
    C_CO2 = K_H * P_CO2_bar  # моль/л
    
    # Упрощённый расчёт pH для системы CO2-H2O-HCO3
    if bicarbonate_mmol > 0:
        # Буферный раствор
        pH = pKa1 + math.log10(bicarbonate_mmol / (C_CO2 * 1000))
    else:
        # Чистая вода, насыщенная CO2
        pH = 0.5 * (pKa1 - math.log10(C_CO2))
    
    return max(3.0, min(7.0, pH))  # Ограничиваем разумными пределами


# ============================================================================
# УЛУЧШЕННЫЕ ФУНКЦИИ РАСЧЁТА
# ============================================================================

def calculate_corrosion_oil(years, temperature, water_content, h2s_content, 
                            viscosity, flow_rate, pipe_thickness, pipe_diameter, 
                            pipe_material, location="надземная", protection="без защиты",
                            environment="Поволжье", component_type="pipe", 
                            component_id="", object_type=""):
    """
    Расчёт коррозии для нефтяных систем на основе моделей де Вааля и Norsok
    """
    
    # 1. ПРЕОБРАЗОВАНИЕ ВХОДНЫХ ДАННЫХ
    # Парциальное давление CO2 (типично для нефтяных месторождений)
    P_CO2_bar = 0.5  # Бар - типичное значение
    
    # Парциальное давление H2S (из ppm)
    P_H2S_bar = h2s_content * 1e-6 * 10  # Упрощённый перевод
    
    # Скорость потока в м/с
    area = math.pi * (pipe_diameter / 1000)**2 / 4  # м²
    velocity_ms = flow_rate / 3600 / area if area > 0 else 1.0
    
    # Расчёт pH
    # В нефтяных системах часто есть бикарбонатный буфер
    bicarbonate = 5.0 if water_content > 10 else 1.0  # ммоль/л
    pH = calculate_ph(temperature, P_CO2_bar, bicarbonate)
    
    # Коэффициент материала
    material_factor = get_material_factor(pipe_material)
    
    # 2. ВЫБОР МОДЕЛИ РАСЧЁТА
    # При высоком H2S используем Norsok, иначе де Вааля
    if P_H2S_bar > 0.001:  # > 100 ppm H2S
        base_rate = norsok_m506_co2_rate(
            T_C=temperature,
            P_CO2_bar=P_CO2_bar,
            P_H2S_bar=P_H2S_bar,
            velocity_ms=velocity_ms,
            pH=pH,
            material_factor=material_factor
        )
        model_name = "Norsok M-506"
    else:
        base_rate = de_waard_milliams_co2_rate(
            T_C=temperature,
            P_CO2_bar=P_CO2_bar,
            pH=pH,
            material_factor=material_factor
        )
        model_name = "De Waard-Milliams"
    
    # 3. ПОПРАВОЧНЫЕ КОЭФФИЦИЕНТЫ
    # 3.1. Обводнённость (коррозия только в водной фазе)
    water_factor = water_content / 100
    
    # 3.2. Вязкость (высокая вязкость снижает массоперенос)
    if viscosity > 100:
        viscosity_factor = 0.3
    elif viscosity > 50:
        viscosity_factor = 0.5
    elif viscosity > 20:
        viscosity_factor = 0.7
    elif viscosity > 10:
        viscosity_factor = 0.8
    else:
        viscosity_factor = 1.0
    
    # 3.3. Условия прокладки
    from .regions import REGION_AGGRESSION, WATER_BODIES
    
    if location == "подводная":
        environment_factor = WATER_BODIES.get(environment, 1.0)
    else:
        environment_factor = REGION_AGGRESSION.get(environment, 1.0)
    
    location_factor = PIPELINE_LOCATION.get(location, 1.0)
    protection_factor = PROTECTION_TYPES.get(protection, 1.0)
    
    # 3.4. Специальный коэффициент для компонента
    special_factor = get_special_coefficient(component_type, component_id, object_type)
    
    # 4. ИТОГОВАЯ СКОРОСТЬ КОРРОЗИИ
    corrosion_rate = base_rate * water_factor * viscosity_factor * \
                    location_factor * environment_factor * protection_factor * special_factor
    
    # 5. ПОТЕРЯ ТОЛЩИНЫ
    thickness_loss = corrosion_rate * years
    
    # 6. ЛОГГИРОВАНИЕ (для отладки и демонстрации)
    print(f"\n📊 МОДЕЛЬ КОРРОЗИИ ДЛЯ НЕФТИ:")
    print(f"   Использована модель: {model_name}")
    print(f"   Параметры: T={temperature}°C, P_CO2={P_CO2_bar} бар, pH={pH:.2f}")
    print(f"   Базовая скорость: {base_rate:.3f} мм/год")
    print(f"   Поправочные коэффициенты:")
    print(f"     - Обводнённость: {water_factor:.2f}")
    print(f"     - Вязкость: {viscosity_factor:.2f}")
    print(f"     - Локация: {location_factor:.2f}")
    print(f"     - Защита: {protection_factor:.2f}")
    print(f"     - Специальный: {special_factor:.2f}")
    print(f"   Итоговая скорость: {corrosion_rate:.3f} мм/год")
    
    return thickness_loss, corrosion_rate


def calculate_corrosion_gas(years, temperature, pressure, co2_content, 
                            methane_content, dew_point, pipe_thickness, 
                            pipe_diameter, pipe_material, location="надземная", 
                            protection="без защиты", environment="Поволжье",
                            component_type="pipe", component_id="", object_type=""):
    """
    Расчёт коррозии для газовых систем на основе моделей де Вааля и Norsok
    """
    
    # 1. ПРЕОБРАЗОВАНИЕ ВХОДНЫХ ДАННЫХ
    # Парциальное давление CO2
    P_CO2_bar = pressure * (co2_content / 100) * 10  # МПа -> бар
    
    # Для газа H2S обычно мал, но учитываем если есть
    P_H2S_bar = 0.001  # Типично для газа
    
    # Скорость потока для газа (оценочно)
    velocity_ms = 15.0  # Типичная скорость в газопроводах
    
    # Расчёт pH (газ обычно кислее из-за CO2)
    bicarbonate = 0.1  # Мало бикарбонатов в газе
    pH = calculate_ph(temperature, P_CO2_bar, bicarbonate)
    
    # Конденсация влаги
    condensation_factor = 2.0 if temperature <= dew_point else 1.0
    
    # Коэффициент материала
    material_factor = get_material_factor(pipe_material)
    
    # 2. ВЫБОР МОДЕЛИ РАСЧЁТА
    if P_CO2_bar > 10:  # Высокое давление CO2
        base_rate = norsok_m506_co2_rate(
            T_C=temperature,
            P_CO2_bar=P_CO2_bar,
            P_H2S_bar=P_H2S_bar,
            velocity_ms=velocity_ms,
            pH=pH,
            material_factor=material_factor
        )
        model_name = "Norsok M-506"
    else:
        base_rate = de_waard_milliams_co2_rate(
            T_C=temperature,
            P_CO2_bar=P_CO2_bar,
            pH=pH,
            material_factor=material_factor
        )
        model_name = "De Waard-Milliams"
    
    # 3. ПОПРАВОЧНЫЕ КОЭФФИЦИЕНТЫ
    # 3.1. Конденсация
    # 3.2. Содержание метана (инертный газ)
    methane_factor = 1.0 - 0.005 * methane_content
    
    # 3.3. Условия прокладки
    from .regions import REGION_AGGRESSION, WATER_BODIES
    
    if location == "подводная":
        environment_factor = WATER_BODIES.get(environment, 1.0)
    else:
        environment_factor = REGION_AGGRESSION.get(environment, 1.0)
    
    location_factor = PIPELINE_LOCATION.get(location, 1.0)
    protection_factor = PROTECTION_TYPES.get(protection, 1.0)
    
    # 3.4. Специальный коэффициент
    special_factor = get_special_coefficient(component_type, component_id, object_type)
    
    # 4. ИТОГОВАЯ СКОРОСТЬ КОРРОЗИИ
    corrosion_rate = base_rate * condensation_factor * methane_factor * \
                    location_factor * environment_factor * protection_factor * special_factor
    
    # 5. ПОТЕРЯ ТОЛЩИНЫ
    thickness_loss = corrosion_rate * years
    
    # 6. ЛОГГИРОВАНИЕ
    print(f"\n📊 МОДЕЛЬ КОРРОЗИИ ДЛЯ ГАЗА:")
    print(f"   Использована модель: {model_name}")
    print(f"   Параметры: T={temperature}°C, P_CO2={P_CO2_bar:.1f} бар, pH={pH:.2f}")
    print(f"   Конденсация: {'да' if condensation_factor > 1 else 'нет'}")
    print(f"   Базовая скорость: {base_rate:.3f} мм/год")
    print(f"   Итоговая скорость: {corrosion_rate:.3f} мм/год")
    
    return thickness_loss, corrosion_rate


# ============================================================================
# ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ (обновлённые)
# ============================================================================

def get_material_factor(material: str) -> float:
    """
    Коэффициенты коррозионной стойкости материалов
    на основе стандартов NACE MR0175/ISO 15156
    """
    material_factors = {
        # Углеродистые стали
        "Ст20": 1.00, "Ст45": 0.95,
        # Низколегированные
        "09Г2С": 0.85, "17Г1С": 0.80, "10Г2": 0.88,
        # Трубные стали API
        "X42": 0.90, "X46": 0.88, "X52": 0.85,
        "X56": 0.82, "X60": 0.80, "X65": 0.75,
        "X70": 0.70, "X80": 0.65,
        # Нержавеющие стали
        "13ХФА": 0.50, "08Х18Н10Т": 0.30,
        "AISI 304": 0.25, "AISI 316": 0.20,
        "Duplex 2205": 0.15, "Super Duplex 2507": 0.10,
        # Сплавы
        "Inconel 625": 0.05, "Hastelloy C276": 0.03,
    }
    
    for key, value in material_factors.items():
        if key.upper() in material.upper():
            return value
    
    # Если материал не найден, оцениваем по категориям
    material_upper = material.upper()
    if any(x in material_upper for x in ["Х", "CR", "NI", "MO", "INCONEL"]):
        return 0.30  # Нержавеющая/коррозионностойкая
    elif any(x in material_upper for x in ["Г", "MN", "X"]):
        return 0.80  # Низколегированная
    else:
        return 1.00  # Углеродистая


def get_corrosion_level(remaining_thickness):
    """Определяет уровень коррозии по остаточной толщине"""
    if remaining_thickness >= 10.0:
        return "отличное", "green"
    elif remaining_thickness >= 8.0:
        return "хорошее", "lightgreen" 
    elif remaining_thickness >= 6.0:
        return "удовлетворительное", "yellow"
    elif remaining_thickness >= 4.0:
        return "плохое", "orange"
    else:
        return "аварийное", "red"


# ============================================================================
# КОЭФФИЦИЕНТЫ (обновлённые с ссылками на стандарты)
# ============================================================================

PROTECTION_TYPES = {
    "без защиты": 1.00,
    "ППУ изоляц.": 0.05,  # ГОСТ 30732-2006, эффективность 95%
    "эпоксид. покр.": 0.03,  # ГОСТ Р 51164, эффективность 97%
    "битум. изоляц.": 0.30,  # ГОСТ 9.602-2005, эффективность 70%
    "катод. з. + изоляц.": 0.01,  # СНИП 2.03.11-85, эффективность 99%
    "бетонное покрытие": 0.20,  # для подводных переходов
    "полимер. изоляц. усилен.": 0.02,  # с армированием стеклотканью
    "катод. защ. + протекторы": 0.005,  # комбинированная защита
    "двойная изоляция + мониторинг": 0.001,  # для ответственных объектов
    "комплекс. защ.": 0.0001,  # изоляция + катодная + ингибиторы
}

PIPELINE_LOCATION = {
    "надземная": 1.0,  # атмосферная коррозия
    "подземная": 3.0,  # почвенная коррозия + блуждающие токи
    "подводная": 2.0,  # водная коррозия + обрастание
}

# Специальные коэффициенты для сложных объектов
SPECIAL_COEFFICIENTS = {
    # Базовые условия
    "pipe": 1.0,
    "equipment": 1.2,
    
    # Нефть
    "pump_station_pumps": 1.8,      # Кавитация + вибрация
    "pump_station_filters": 1.3,    # Абразивный износ
    "pump_station_reservoirs": 2.0, # Донная зона + осадок
    "separator_dirty_oil": 1.6,     # Эмульсия вода-нефть
    "separator_water": 3.0,         # Водная фаза + H2S
    "separator_clean_oil": 0.8,     # Обезвоженная нефть
    "heater_base": 2.5,             # Высокая температура
    "reservoir_base": 1.5,          # Переменный уровень
    
    # Газ
    "compressor_station": 2.2,      # Высокое давление + температура
    "dryer_adsorbers": 1.8,         # Циклические нагрузки
    "grs_filter": 1.4,              # Конденсация + загрязнения
    "grs_fork": 1.2,                # Турбулентность потока
}

def get_special_coefficient(component_type="", component_id="", object_type=""):
    """Возвращает специальный коэффициент для компонента"""
    # Приоритет 1: точное совпадение component_id
    if component_id and component_id in SPECIAL_COEFFICIENTS:
        return SPECIAL_COEFFICIENTS[component_id]
    
    # Приоритет 2: ищем по ключевым словам
    search_keys = []
    if component_id:
        search_keys.append(component_id)
    if object_type:
        search_keys.append(object_type)
    
    for key in search_keys:
        for coeff_key in SPECIAL_COEFFICIENTS:
            if key in coeff_key or coeff_key in key:
                return SPECIAL_COEFFICIENTS[coeff_key]
    
    # Приоритет 3: по типу компонента
    if component_type in ["equipment", "tank", "separator", "compressor"]:
        return 1.2
    elif component_type == "pipe":
        return 1.0
    
    return 1.0
