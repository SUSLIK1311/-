"""Вкладка с параметрами трубопровода и расчётами"""
import tkinter as tk
from tkinter import ttk
from models.corrosion import calculate_corrosion_oil, calculate_corrosion_gas, get_corrosion_level, PROTECTION_TYPES, PIPELINE_LOCATION
from models.regions import REGION_AGGRESSION
from utils.constants import PIPE_STANDARDS, PIPE_THICKNESS_STANDARD, PIPE_MATERIALS
import os
import sys
try:
    from models.pipeline_data import ComponentType
    HAS_COMPONENT_TYPE = True
except ImportError:
    HAS_COMPONENT_TYPE = False
    class ComponentType:
        PIPE = "pipe"
        EQUIPMENT = "equipment"

def get_recommended_thickness(diameter):
    """Возвращает рекомендуемую толщину стенки для диаметра"""
    return PIPE_THICKNESS_STANDARD.get(diameter, 10)

def create_parameters_tab(parent, fluid_type, sections_data, update_scheme_callback):
    """Создаёт вкладку с параметрами"""
    tab = parent
    
    tab.grid_rowconfigure(1, weight=1)
    tab.grid_columnconfigure(0, weight=1)
    
    # Переменные для хранения данных
    fluid_entries = {}
    
    # РАЗДЕЛ: Время эксплуатации 
    frame_time = ttk.LabelFrame(tab, text="ВРЕМЯ ЭКСПЛУАТАЦИИ", padding=10)
    frame_time.pack(fill="x", padx=10, pady=5)

    # Метка текущего года
    current_year_label = ttk.Label(frame_time, text="Текущий год: 0", font=("Arial", 12, "bold"))
    current_year_label.pack(pady=5)

    # Ползунок времени
    year_slider = ttk.Scale(frame_time, from_=0, to=100, orient="horizontal")
    year_slider.set(0)
    year_slider.pack(fill="x", padx=10, pady=5)

    # Подписи
    label_frame = ttk.Frame(frame_time)
    label_frame.pack(fill="x", padx=10)
    ttk.Label(label_frame, text="0 лет").pack(side="left")
    ttk.Label(label_frame, text="100 лет").pack(side="right")

    # РАЗДЕЛ: Параметры среды
    frame_fluid = ttk.LabelFrame(tab, text="ПАРАМЕТРЫ СРЕДЫ", padding=10)
    frame_fluid.pack(fill="x", padx=10, pady=5)
    
    if fluid_type == "oil":
        # ПОЛЯ ДЛЯ НЕФТИ
        params = [
            ("Температура (°C):", "60.0"),
            ("Обводнённость (%):", "5.0"), 
            ("H₂S (ppm):", "50.0"),
            ("Вязкость (сСт):", "15.0"),
            ("Расход (м³/ч):", "1000.0")
        ]
    else:
        # ПОЛЯ ДЛЯ ГАЗА
        params = [
            ("Температура (°C):", "20.0"),
            ("Давление (МПа):", "5.0"),
            ("CO₂ (%):", "2.0"),
            ("Метан (%):", "85.0"), 
            ("Точка росы (°C):", "-10.0")
        ]
    
    for i, (label_text, default_val) in enumerate(params):
        ttk.Label(frame_fluid, text=label_text).grid(row=i, column=0, sticky="w", pady=2)
        entry = ttk.Entry(frame_fluid, width=15)
        entry.insert(0, default_val)
        entry.grid(row=i, column=1, padx=5, pady=2)
        fluid_entries[label_text] = entry

    # РАЗДЕЛ: Участки трубопровода
    frame_sections = ttk.LabelFrame(tab, text="УЧАСТКИ ТРУБОПРОВОДА", padding=10)
    frame_sections.pack(fill="both", expand=True, padx=10, pady=(5, 10))
    frame_sections.grid_rowconfigure(0, weight=1)
    frame_sections.grid_columnconfigure(0, weight=1)

    # Создаем контейнер для таблицы
    table_container = ttk.Frame(frame_sections)
    table_container.pack(fill="both", expand=True, pady=5)

    # Таблица участков с результатами расчёта
    columns = ("Название", "Длина (м)", "Диаметр (мм)", "Толщина (мм)", "Материал", "Кол-во", "Прокладка", "Защита", "Среда", "Остаток (мм)", "Статус")
    tree = ttk.Treeview(table_container, columns=columns, show="headings", height=8)

    tree.column("Название", width=180)
    tree.column("Длина (м)", width=60)
    tree.column("Диаметр (мм)", width=70)
    tree.column("Толщина (мм)", width=70)
    tree.column("Материал", width=90)
    tree.column("Кол-во", width=50) 
    tree.column("Прокладка", width=90)
    tree.column("Защита", width=120)
    tree.column("Среда", width=150)  
    tree.column("Остаток (мм)", width=90)
    tree.column("Статус", width=120)
        
    # Теги для цветов
    tree.tag_configure('excellent', background='#90EE90')  # отличное
    tree.tag_configure('good', background='#98FB98')       # хорошее  
    tree.tag_configure('satisfactory', background='#FFD700') # удовлетворительное
    tree.tag_configure('poor', background='#FFA500')       # плохое
    tree.tag_configure('critical', background='#FF6B6B')   # аварийное

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=90)

    # Прокрутка для таблицы
    scrollbar = ttk.Scrollbar(table_container, orient="vertical", command=tree.yview)
    tree.configure(yscrollcommand=scrollbar.set)

    # Сообщение при отсутствии данных
    empty_message_frame = ttk.Frame(table_container)
    
    message_label = ttk.Label(
        empty_message_frame,
        text="Участки не добавлены",
        font=("Arial", 16, "bold"),
        foreground="#666666"
    )
    message_label.pack(pady=20)
    
    info_label = ttk.Label(
        empty_message_frame,
        text="Используйте кнопку 'Добавить участок' для создания нового участка трубопровода",
        font=("Arial", 12),
        foreground="#888888",
        justify="center"
    )
    info_label.pack(pady=10)

    # Кнопки управления
    btn_frame = ttk.Frame(frame_sections)
    btn_frame.pack(fill="x", pady=5)

    # =========================================================================
    # ВНУТРЕННИЕ ФУНКЦИИ (должны быть ВНУТРИ create_parameters_tab)
    # =========================================================================

    def show_empty_message():
        """Показать сообщение о пустой таблице"""
        tree.pack_forget()
        scrollbar.pack_forget()
        empty_message_frame.pack(fill="both", expand=True, pady=20)
    
    def show_table():
        """Показать таблицу с данными"""
        empty_message_frame.pack_forget()
        tree.pack(side="left", fill="both", expand=True, pady=5)
        scrollbar.pack(side="right", fill="y", pady=5)

    def update_calculation():
        """Обновляет расчёт коррозии для всех участков (включая сложные)"""
        try:
            years = year_slider.get()
        
            # Собираем параметры среды 
            fluid_params = {}
            if fluid_type == "oil":
                fluid_params = {
                    "temperature": float(fluid_entries["Температура (°C):"].get()),
                    "water_content": float(fluid_entries["Обводнённость (%):"].get()),
                    "h2s_content": float(fluid_entries["H₂S (ppm):"].get()),
                    "viscosity": float(fluid_entries["Вязкость (сСт):"].get()),
                    "flow_rate": float(fluid_entries["Расход (м³/ч):"].get())
                }
            else:
                fluid_params = {
                    "temperature": float(fluid_entries["Температура (°C):"].get()),
                    "pressure": float(fluid_entries["Давление (МПа):"].get()),
                    "co2_content": float(fluid_entries["CO₂ (%):"].get()),
                    "methane_content": float(fluid_entries["Метан (%):"].get()),
                    "dew_point": float(fluid_entries["Точка росы (°C):"].get())
                }
        
            # Очищаем таблицу
            for item in tree.get_children():
                tree.delete(item)
        
            # Проверяем, есть ли данные
            if not sections_data:
                show_empty_message()
                return
            else:
                show_table()
        
            rows_added = 0  # Счётчик добавленных строк
            
            # ОБНОВЛЁННЫЙ КОД: каждый компонент как отдельная строка
            for section in sections_data:
                is_complex = section.get("is_complex", False)
            
                if is_complex:
                    # РАСЧЁТ ДЛЯ СЛОЖНОГО УЧАСТКА - КАЖДЫЙ КОМПОНЕНТ ОТДЕЛЬНО
                    components = section.get("components", [])
                
                    for i, component in enumerate(components):
                        # Определяем параметры компонента
                        comp_params = component

                        # ПОЛУЧАЕМ ИМЯ КОМПОНЕНТА
                        comp_id = comp_params.get("component_id", f"comp_{i}")
                        comp_name_display = comp_params.get("name", comp_id)

                        # Определяем количество для отображения
                        count = comp_params.get("count", 1)
                        if comp_params.get("component_type") == "pipe":
                            count_display = "1"  # для труб прочерк
                        else:
                            count_display = f"{count}"

                        # ОПРЕДЕЛЯЕМ ПЕРЕМЕННЫЕ ДЛЯ ЭТОГО КОМПОНЕНТА
                        thickness = 10.0  # значение по умолчанию
                        diameter = 0.0
                        length = 0.0
                        material = "Ст20"
                        
                        if comp_params.get("component_type") == "pipe":
                            thickness = comp_params.get("thickness", 10.0)
                            diameter = comp_params.get("diameter", 500.0)
                            length = comp_params.get("length", 0)
                            material = comp_params.get("material", "Ст20")
                        elif comp_params.get("component_type") == "equipment":
                            thickness = comp_params.get("wall_thickness", 12.0)
                            diameter = 0  # у оборудования нет диаметра
                            length = 0
                            material = comp_params.get("material", "09Г2С")
                        else:
                            # Для других типов или если component_type не указан
                            thickness = comp_params.get("thickness", comp_params.get("wall_thickness", 10.0))
                            diameter = comp_params.get("diameter", 0)
                            length = comp_params.get("length", 0)
                            material = comp_params.get("material", "Ст20")
                        
                        # Получаем тип компонента и тип объекта для специальных коэффициентов
                        comp_type = comp_params.get("component_type", "pipe")
                        object_type = section.get("object_type", "")
                        
                        # ТЕПЕРЬ ДЕЛАЕМ РАСЧЁТ ДЛЯ ЭТОГО КОМПОНЕНТА
                        if fluid_type == "oil":
                            thickness_loss, rate = calculate_corrosion_oil(
                                years, 
                                fluid_params["temperature"],
                                fluid_params["water_content"], 
                                fluid_params["h2s_content"],
                                fluid_params["viscosity"],
                                fluid_params["flow_rate"],
                                thickness,  # ТОЛЩИНА ЭТОГО КОМПОНЕНТА
                                diameter,   # ДИАМЕТР ЭТОГО КОМПОНЕНТА
                                material,   # МАТЕРИАЛ ЭТОГО КОМПОНЕНТА
                                section.get("location", "надземная"),
                                section.get("protection", "без защиты"),
                                section.get("environment", "Поволжье"),
                                component_type=comp_type,
                                component_id=comp_id,
                                object_type=object_type
                            )
                        else:
                            thickness_loss, rate = calculate_corrosion_gas(
                                years,
                                fluid_params["temperature"],
                                fluid_params["pressure"],
                                fluid_params["co2_content"],
                                fluid_params["methane_content"], 
                                fluid_params["dew_point"],
                                thickness,  # ТОЛЩИНА ЭТОГО КОМПОНЕНТА
                                diameter,   # ДИАМЕТР ЭТОГО КОМПОНЕНТА
                                material,   # МАТЕРИАЛ ЭТОГО КОМПОНЕНТА
                                section.get("location", "надземная"),
                                section.get("protection", "без защиты"),
                                section.get("environment", "Поволжье"),
                                component_type=comp_type,
                                component_id=comp_id,
                                object_type=object_type
                            )
                    
                        # Остаточная толщина ДЛЯ ЭТОГО КОМПОНЕНТА
                        comp_remaining = max(0.1, thickness - thickness_loss)
                        level, _ = get_corrosion_level(comp_remaining)
                    
                        # Определяем тег для цвета
                        if level == "отличное":
                            tag = 'excellent'
                        elif level == "хорошее":
                            tag = 'good'
                        elif level == "удовлетворительное":
                            tag = 'satisfactory'
                        elif level == "плохое":
                            tag = 'poor'
                        else:
                            tag = 'critical'
                    
                        # Название компонента
                        comp_name = f"{section['name']} - {comp_name_display}"

                        # Для оборудования показываем количество
                        if comp_params.get("count", 1) > 1:
                            comp_name += f" (x{comp_params['count']})"

                        # Добавляем запись в таблицу ДЛЯ ЭТОГО КОМПОНЕНТА
                        tree.insert("", "end", values=(
                            comp_name,
                            f"{length:.0f}" if length > 0 else "—",
                            f"{diameter:.0f}" if diameter > 0 else "—",
                            f"{thickness:.2f}",
                            material,
                            count_display,
                            section.get("location", "надземная"),
                            section.get("protection", "без защиты"),
                            section.get("environment", "Поволжье"),
                            f"{comp_remaining:.2f}",
                            level
                        ), tags=(tag,))
                        rows_added += 1
                    
                        # Сохраняем данные компонента для схемы
                        if "components_data" not in section:
                            section["components_data"] = []
                        # Проверяем, не существует ли уже данных для этого компонента
                        existing_idx = -1
                        for idx, data in enumerate(section["components_data"]):
                            if data.get("component_id") == comp_id:
                                existing_idx = idx
                                break
                        
                        if existing_idx >= 0:
                            # Обновляем существующие данные
                            section["components_data"][existing_idx] = {
                                "component_id": comp_params.get("component_id", f"comp_{i}"),
                                "remaining": comp_remaining,
                                "level": level
                            }
                        else:
                            # Добавляем новые данные
                            section["components_data"].append({
                                "component_id": comp_params.get("component_id", f"comp_{i}"),
                                "remaining": comp_remaining,
                                "level": level
                            })
                
                else:
                    # РАСЧЁТ ДЛЯ ПРОСТОГО УЧАСТКА 
                    if fluid_type == "oil":
                        thickness_loss, rate = calculate_corrosion_oil(
                            years, 
                            fluid_params["temperature"],
                            fluid_params["water_content"], 
                            fluid_params["h2s_content"],
                            fluid_params["viscosity"],
                            fluid_params["flow_rate"],
                            section["thickness"],     # ТОЛЩИНА СЕКЦИИ
                            section["diameter"],      # ДИАМЕТР СЕКЦИИ
                            section["material"],      # МАТЕРИАЛ СЕКЦИИ
                            section.get("location", "надземная"),
                            section.get("protection", "без защиты"),
                            section.get("environment", "Поволжье"),
                            component_type=section.get("component_type", "pipe"),
                            component_id=section.get("component_id", ""),
                            object_type=section.get("object_type", "")
                        )
                    else:
                        thickness_loss, rate = calculate_corrosion_gas(
                            years,
                            fluid_params["temperature"],
                            fluid_params["pressure"],
                            fluid_params["co2_content"],
                            fluid_params["methane_content"], 
                            fluid_params["dew_point"],
                            section["thickness"],     # ТОЛЩИНА СЕКЦИИ
                            section["diameter"],      # ДИАМЕТР СЕКЦИИ
                            section["material"],      # МАТЕРИАЛ СЕКЦИИ
                            section.get("location", "надземная"),
                            section.get("protection", "без защиты"),
                            section.get("environment", "Поволжье"),
                            component_type=section.get("component_type", "pipe"),
                            component_id=section.get("component_id", ""),
                            object_type=section.get("object_type", "")
                        )
                
                    initial_thickness = section["thickness"]
                    actual_remaining = max(0.1, initial_thickness - thickness_loss)
                    level, color = get_corrosion_level(actual_remaining)
                
                    # СОХРАНЯЕМ ДАННЫЕ ДЛЯ СХЕМЫ
                    section["remaining_thickness"] = actual_remaining
                    section["corrosion_level"] = level
                
                    # Определяем тег для цвета
                    if level == "отличное":
                        tag = 'excellent'
                    elif level == "хорошее":
                        tag = 'good'
                    elif level == "удовлетворительное":
                        tag = 'satisfactory'
                    elif level == "плохое":
                        tag = 'poor'
                    else:
                        tag = 'critical'
                
                    tree.insert("", "end", values=(
                        section["name"],
                        section["length"], 
                        section["diameter"],
                        section["thickness"],
                        section["material"],
                        "1",
                        section.get("location", "надземная"),
                        section.get("protection", "без защиты"),
                        section.get("environment", "Поволжье"),
                        f"{actual_remaining:.2f}",
                        level
                    ), tags=(tag,))
                    rows_added += 1
            
            # Если после расчётов строк не добавлено (все участки удалены)
            if rows_added == 0:
                show_empty_message()
            
        except ValueError as e:
            print(f"Ошибка ввода: {e}")
            import traceback
            traceback.print_exc()
        except KeyError as e:
            print(f"Ошибка ключа: {e}")
            import traceback
            traceback.print_exc()
        except Exception as e:
            print(f"Неизвестная ошибка в update_calculation: {e}")
            import traceback
            traceback.print_exc()

    def on_parameter_change(*args):
        update_calculation()
        if update_scheme_callback:
            update_scheme_callback()

    def on_slider_change(event):
        """При движении ползунка обновляем расчёт"""
        years = int(year_slider.get())
        current_year_label.config(text=f"Текущий год: {years}")
        update_calculation()

    def add_section():
        """Диалог добавления нового участка"""
        def on_section_added(new_section):
            """Callback при добавлении новой секции"""
            print("🔄 Вызван on_section_added")
    
            try:
                # Просто преобразуем в словарь
                section_dict = {
                    "name": new_section.name,
                    "object_type": getattr(new_section, 'object_type', 'unknown'),
                    "location": getattr(new_section, 'location', 'надземная'),
                    "protection": getattr(new_section, 'protection', 'без защиты'),
                    "environment": getattr(new_section, 'environment', 'Поволжье'),
                    "is_complex": True,
                    "components": []
                }
        
                # Преобразуем компоненты в словари
                for comp in new_section.components:
                    if isinstance(comp, dict):
                        comp_dict = comp.copy()
                    elif hasattr(comp, 'dict'):
                        comp_dict = comp.dict.copy()
                    else:
                        # Простой объект
                        comp_dict = {}
                        for attr in ['component_id', 'name', 'component_type', 'type',
                                   'material', 'length', 'diameter', 'thickness',
                                   'wall_thickness', 'count']:
                            if hasattr(comp, attr):
                                comp_dict[attr] = getattr(comp, attr)
            
                    # Убедимся, что есть component_type
                    if 'component_type' not in comp_dict and 'type' in comp_dict:
                        comp_dict['component_type'] = comp_dict['type']
            
                    # Убедимся, что есть thickness для расчётов
                    if 'thickness' not in comp_dict and 'wall_thickness' in comp_dict:
                        comp_dict['thickness'] = comp_dict['wall_thickness']
            
                    section_dict["components"].append(comp_dict)
                    print(f"   Добавлен компонент: {comp_dict.get('name', 'unknown')}")
        
                print(f"✅ Участок '{section_dict['name']}' добавлен")
                print(f"   Компонентов: {len(section_dict['components'])}")
        
                sections_data.append(section_dict)
        
            except Exception as e:
                print(f"🔥 ОШИБКА в on_section_added: {type(e).__name__}: {e}")
                import traceback
                traceback.print_exc()
                return
    
            # Обновляем интерфейс
            update_calculation()
            if update_scheme_callback:
                update_scheme_callback()
    
        # Показываем новый диалог
        try:
            from ui.add_section_dialog import show_add_dialog
            show_add_dialog(tab, fluid_type, sections_data, on_section_added)
        except ImportError as e:
            print(f"Ошибка импорта диалога: {e}")
            # Заглушка для тестирования
            from models.pipeline_data import ComplexSection
            test_section = ComplexSection(
                name="Тестовый участок",
                object_type="pipe",
                location="надземная",
                protection="без защиты",
                environment="Поволжье"
            )
            test_section.add_pipe("main_pipe", 100.0, 500.0, 10.0, "Ст20")
            on_section_added(test_section)

    def delete_section():
        """Удаление выбранного участка"""
        selected = tree.selection()
        if selected:
            # Получаем название из таблицы
            item = tree.item(selected[0])
            full_name = item['values'][0]
        
            # Извлекаем базовое название участка
            # Формат: "Название участка - Комponent 1" → "Название участка"
            if " - " in full_name:
                base_name = full_name.split(" - ")[0]
            else:
                base_name = full_name
        
            # Ищем и удаляем ВЕСЬ участок из данных
            for i, section in enumerate(sections_data):
                if section["name"] == base_name:
                    sections_data.pop(i)
                    print(f"🗑️ Удалён участок: {base_name}")
                    break
                
            update_calculation()
            if update_scheme_callback:
                update_scheme_callback()
        else:
            print("❌ Ничего не выбрано")

    # =========================================================================
    # ПРИВЯЗКА СОБЫТИЙ И РАЗМЕЩЕНИЕ ЭЛЕМЕНТОВ
    # =========================================================================
    
    # Привязываем события
    for entry in fluid_entries.values():
        entry.bind("<KeyRelease>", on_parameter_change)
    
    year_slider.bind("<B1-Motion>", on_slider_change)
    year_slider.bind("<ButtonRelease-1>", on_slider_change)

    # Кнопки
    add_btn = tk.Button(btn_frame, text="Добавить участок", 
                       bg='#18171C', fg='#FADADD', font=("Arial", 9, "bold"),
                       relief='flat', borderwidth=0,
                       command=add_section)
    add_btn.pack(side="left", padx=5)

    delete_btn = tk.Button(btn_frame, text="Удалить участок", 
                          bg='#18171C', fg='#FADADD', font=("Arial", 9, "bold"), 
                          relief='flat', borderwidth=0,
                          command=delete_section)
    delete_btn.pack(side="left", padx=5)

    # Первоначальный расчёт
    update_calculation()

    return tab

