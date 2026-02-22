"""Диалог добавления сложного участка трубопровода"""
import tkinter as tk
from tkinter import ttk
import json
import os
from models.object_templates import get_available_templates, get_template
try:
    from .pipeline_data import Component, ComplexSection, SimpleSection, ComponentType
    HAS_NEW_MODELS = True
except ImportError:
    HAS_NEW_MODELS = False
    # Определяем заглушки для обратной совместимости
    class ComponentType:
        PIPE = "pipe"
        EQUIPMENT = "equipment"
    
    class Component:
        pass
    
    class ComplexSection:
        pass
    
    class SimpleSection:
        pass
from models.regions import REGION_AGGRESSION, WATER_BODIES
from utils.constants import PIPE_STANDARDS, PIPE_MATERIALS

class AddSectionDialog:
    """Диалог добавления участка с поддержкой сложных объектов"""
    
    def __init__(self, parent, fluid_type, sections_data, callback):
        """
        Инициализация диалога
        
        Args:
            parent: родительское окно
            fluid_type: "oil" или "gas"
            sections_data: список существующих участков (для проверки уникальности)
            callback: функция, которая вызывается после добавления
        """
        self.parent = parent
        self.fluid_type = fluid_type
        self.sections_data = sections_data
        self.callback = callback
        
        # Данные формы
        self.current_template = None
        self.components_data = {}  # component_id -> данные компонента
        
        # Создаем диалог
        self.dialog = tk.Toplevel(parent)
        self.dialog.title("Добавить участок")
        self.dialog.geometry("500x700")
        self.dialog.resizable(False, False)
        self.dialog.transient(parent)
        self.dialog.grab_set()

        # ДОБАВЛЯЕМ ИКОНКУ ДИАЛОГУ
        icon_path = "assets/icon1.ico"
        if not os.path.exists(icon_path):
            icon_path = "../assets/icon1.ico"
        
        if os.path.exists(icon_path):
            try:
                self.dialog.iconbitmap(icon_path)
            except Exception as e:
                print(f"❌ Ошибка загрузки иконки диалога: {e}")
        else:
            print(f"⚠️ Иконка не найдена по пути: {icon_path}")
        
        # УМНЫЕ ОГРАНИЧЕНИЯ 
        self.PROTECTION_BY_LOCATION = {
            "надземная": ["без защ.", "ППУ изол.", "эпоксид. покр.", "битум. изол."],
            "подземная": ["без защ.", "ППУ изол.", "битум. изол.", "катод. + изол."],
            "подводная": ["бетон. покр.", "полимер. усил.", "катод. + протек.", "двойн. изол.", "комплекс. защ."]
        }
        
        self.setup_ui()
        
    def setup_ui(self):
        """Настройка интерфейса диалога"""
        # Основной фрейм с прокруткой
        main_frame = ttk.Frame(self.dialog)
        main_frame.pack(fill="both", expand=True, padx=10, pady=10)
        
        # Canvas для прокрутки
        canvas = tk.Canvas(main_frame)
        scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
        self.scrollable_frame = ttk.Frame(canvas)
        
        self.scrollable_frame.bind(
            "<Configure>",
            lambda e: canvas.configure(scrollregion=canvas.bbox("all"))
        )
        
        canvas.create_window((0, 0), window=self.scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # 1. ОСНОВНАЯ ИНФОРМАЦИЯ
        basic_frame = ttk.LabelFrame(self.scrollable_frame, text="ОСНОВНАЯ ИНФОРМАЦИЯ", padding=10)
        basic_frame.pack(fill="x", pady=(0, 10))
        
        # Название участка
        ttk.Label(basic_frame, text="Название участка:").grid(row=0, column=0, sticky="w", pady=5)
        self.name_entry = ttk.Entry(basic_frame, width=30)
        self.name_entry.grid(row=0, column=1, padx=5, pady=5)
        self.name_entry.insert(0, "Новый участок")
        
        # 2. ТИП ПРОКЛАДКИ И ОБЪЕКТА
        type_frame = ttk.LabelFrame(self.scrollable_frame, text="ТИП ПРОКЛАДКИ И ОБЪЕКТА", padding=10)
        type_frame.pack(fill="x", pady=(0, 10))
        
        # Тип прокладки
        ttk.Label(type_frame, text="Тип прокладки:").grid(row=0, column=0, sticky="w", pady=5)
        self.location_var = tk.StringVar(value="надземная")
        self.location_combo = ttk.Combobox(type_frame, textvariable=self.location_var, 
                                          values=["надземная", "подземная", "подводная"], 
                                          width=20, state="readonly")
        self.location_combo.grid(row=0, column=1, padx=5, pady=5)
        self.location_combo.bind("<<ComboboxSelected>>", self.on_location_change)
        
        # Тип объекта (из шаблонов)
        ttk.Label(type_frame, text="Тип объекта:").grid(row=1, column=0, sticky="w", pady=5)
        
        # Получаем доступные шаблоны
        templates = get_available_templates(self.fluid_type)
        template_names = [(templates[tid].name, tid) for tid in templates]
        template_names.sort()  # Сортируем по имени
        
        self.object_var = tk.StringVar()
        self.object_combo = ttk.Combobox(type_frame, textvariable=self.object_var, 
                                        values=[name for name, _ in template_names], 
                                        width=25, state="readonly")
        self.object_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Словарь для обратного поиска template_id
        self.name_to_id = {name: tid for name, tid in template_names}
        
        # Устанавливаем первый доступный объект
        if template_names:
            first_name, first_id = template_names[0]
            self.object_combo.set(first_name)
            self.current_template = templates[first_id]
        
        self.object_combo.bind("<<ComboboxSelected>>", self.on_object_change)
        
        # 3. СРЕДА И ЗАЩИТА
        env_frame = ttk.LabelFrame(self.scrollable_frame, text="СРЕДА И ЗАЩИТА", padding=10)
        env_frame.pack(fill="x", pady=(0, 10))
        
        # Среда (регион/водоём)
        ttk.Label(env_frame, text="Среда:").grid(row=0, column=0, sticky="w", pady=5)
        self.environment_var = tk.StringVar()
        self.environment_combo = ttk.Combobox(env_frame, textvariable=self.environment_var, 
                                             width=25, state="readonly")
        self.environment_combo.grid(row=0, column=1, padx=5, pady=5)
        
        # Защита
        ttk.Label(env_frame, text="Защита:").grid(row=1, column=0, sticky="w", pady=5)
        self.protection_var = tk.StringVar()
        self.protection_combo = ttk.Combobox(env_frame, textvariable=self.protection_var,
                                            width=25, state="readonly")
        self.protection_combo.grid(row=1, column=1, padx=5, pady=5)
        
        # Инициализируем зависимости
        self.update_dependencies()
        
        # 4. КОМПОНЕНТЫ ОБЪЕКТА - создаём контейнер ДО вызова update_dependencies
        self.components_frame = ttk.LabelFrame(self.scrollable_frame, text="КОМПОНЕНТЫ", padding=10)
        self.components_frame.pack(fill="x", pady=(0, 10))
    
        # Здесь будут динамически добавляться компоненты
        self.components_container = ttk.Frame(self.components_frame)
        self.components_container.pack(fill="x")
    
        # 5. КНОПКИ
        button_frame = ttk.Frame(self.scrollable_frame)
        button_frame.pack(fill="x", pady=20)
        
        tk.Button(button_frame, text="Добавить", 
                 bg='#18171C', fg='#FADADD', font=("Arial", 9, "bold"),
                 relief='flat', borderwidth=0,
                 command=self.confirm_add).pack(side="left", padx=10)
        
        tk.Button(button_frame, text="Отмена", 
                 bg='#18171C', fg='#FADADD', font=("Arial", 9, "bold"),
                 relief='flat', borderwidth=0,
                 command=self.dialog.destroy).pack(side="left", padx=10)

        self.update_dependencies()
        
        # Обновляем компоненты при старте
        self.update_components()
        
    def on_location_change(self, event=None):
        """При изменении типа прокладки"""
        self.update_dependencies()
        
    def on_object_change(self, event=None):
        """При изменении типа объекта"""
        selected_name = self.object_var.get()
        if selected_name in self.name_to_id:
            template_id = self.name_to_id[selected_name]
            templates = get_available_templates(self.fluid_type)
        
            # ВАЖНО: Если выбрана "труба", нужно определить КАКУЮ именно
            if selected_name.lower() == "труба":
                location = self.location_var.get()
                # Для подземной/подводной выбираем pipe_underground
                if location in ["подземная", "подводная"]:
                    # Ищем подземную трубу
                    for tid, template in templates.items():
                        if "underground" in tid or "подзем" in template.name.lower():
                            template_id = tid
                            break
                else:
                    # Для надземной выбираем pipe_above
                    for tid, template in templates.items():
                        if "above" in tid or "надзем" in template.name.lower():
                            template_id = tid
                            break
        
            self.current_template = templates.get(template_id)
        
            # Обновляем список компонентов
            self.update_components()
    
    def update_dependencies(self):
        """Обновляет доступные опции с правильными ограничениями"""
        location = self.location_var.get()
    
        # 1. СРЕДА (не меняем)
        if location == "подводная":
            environments = list(WATER_BODIES.keys())
        else:
            environments = list(REGION_AGGRESSION.keys())
    
        self.environment_combo['values'] = environments
        if environments:
            self.environment_combo.set(environments[0])
    
        # 2. ЗАЩИТА (не меняем)
        protections = self.PROTECTION_BY_LOCATION.get(location, ["без защ."])
    
        # Под водой нельзя без защиты
        if location == "подводная" and "без защ." in protections:
            protections = [p for p in protections if p != "без защ."]
            if not protections:
                protections = ["комплекс. защ."]
    
        self.protection_combo['values'] = protections
        if protections:
            self.protection_combo.set(protections[0])
    
        # 3. ФИЛЬТРАЦИЯ ОБЪЕКТОВ ПО ТИПУ ПРОКЛАДКИ
        templates = get_available_templates(self.fluid_type)
        filtered_templates = []
        self.name_to_id = {}
    
        # Словарь для отслеживания уже добавленных имён (чтобы избежать дублей)
        seen_names = set()
    
        for template_id, template in templates.items():
            template_name = template.name  # "труба", "нпс" и т.д.

            # Если подземная или подводная - ТОЛЬКО ТРУБЫ
            if location in ["подземная", "подводная"]:
                if "труба" in template_name.lower():
                    # Для труб проверяем, не добавили ли уже "трубу"
                    if "труба" not in seen_names:
                        filtered_templates.append((template_name, template_id))
                        self.name_to_id[template_name] = template_id
                        seen_names.add("труба")
            else:
            # Для надземной - ВСЕ объекты
                if "труба" in template_name.lower():
                    if "труба" not in seen_names:
                        filtered_templates.append((template_name, template_id))
                        self.name_to_id[template_name] = template_id
                        seen_names.add("труба")
                else:
                    # Для не-труб добавляем как есть
                    filtered_templates.append((template_name, template_id))
                    self.name_to_id[template_name] = template_id
                    seen_names.add(template_name)
    
        # Сортируем: сначала не-трубы, потом трубы
        def sort_key(item):
            name, _ = item
            return (0 if "труба" not in name.lower() else 1, name)
    
        filtered_templates.sort(key=sort_key)
        self.object_combo['values'] = [name for name, _ in filtered_templates]
    
        if filtered_templates:
            first_name, first_id = filtered_templates[0]
            self.object_combo.set(first_name)
            self.current_template = templates[first_id]
        else:
            # Нет подходящих объектов
            self.object_combo.set("")
            self.object_combo['values'] = [f"Нет объектов для {location} прокладки"]
            self.current_template = None
    
        # 4. Обновляем компоненты
        self.update_components()
    
    def update_components(self):
        """Обновляет список компонентов в зависимости от выбранного объекта"""
        # Проверяем, что контейнер создан
        if not hasattr(self, 'components_container'):
            return  # Выходим, если контейнер ещё не создан
        
        # Очищаем контейнер
        for widget in self.components_container.winfo_children():
            widget.destroy()
    
        if not self.current_template:
            ttk.Label(self.components_container, text="Выберите тип объекта").pack()
            return
        
        # Очищаем данные компонентов
        self.components_data.clear()
        
        row = 0
        
        # 1. Трубы
        if self.current_template.pipe_components:
            pipe_label = ttk.Label(self.components_container, 
                                  text="ТРУБЫ:", 
                                  font=("Arial", 10, "bold"))
            pipe_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(0, 5))
            row += 1
            
            for comp in self.current_template.pipe_components:
                self.create_pipe_component_ui(comp, row)
                row += 1
        
        # 2. Оборудование
        if self.current_template.equipment_components:
            eq_label = ttk.Label(self.components_container,
                                text="ОБОРУДОВАНИЕ:",
                                font=("Arial", 10, "bold"))
            eq_label.grid(row=row, column=0, columnspan=2, sticky="w", pady=(10, 5))
            row += 1
            
            for comp in self.current_template.equipment_components:
                self.create_equipment_component_ui(comp, row)
                row += 1
        
        # Если компонентов нет
        if not self.current_template.all_components:
            ttk.Label(self.components_container, 
                     text="У этого объекта нет компонентов").grid(row=row, column=0, pady=10)
    
    def create_pipe_component_ui(self, component, row):
        """Создает UI для компонента-трубы"""
        # Фрейм для компонента
        comp_frame = ttk.Frame(self.components_container, relief="groove", borderwidth=1)
        comp_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        comp_frame.grid_columnconfigure(1, weight=1)
        
        # Заголовок
        title = f"{component.name}" + (" (обязательный)" if component.required else "")
        ttk.Label(comp_frame, text=title, font=("Arial", 9)).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
        
        # Данные по умолчанию
        defaults = component.defaults
        
        # Длина
        ttk.Label(comp_frame, text="Длина (м):").grid(row=1, column=0, sticky="w", padx=5)
        length_var = tk.StringVar(value=str(defaults.get("length", 100.0)))
        length_entry = ttk.Entry(comp_frame, textvariable=length_var, width=10)
        length_entry.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Диаметр
        ttk.Label(comp_frame, text="Диаметр (мм):").grid(row=2, column=0, sticky="w", padx=5)
        diameter_var = tk.StringVar(value=str(defaults.get("diameter", 720.0)))
        diameter_combo = ttk.Combobox(comp_frame, textvariable=diameter_var, 
                                     values=PIPE_STANDARDS[self.fluid_type], width=10)
        diameter_combo.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Толщина
        ttk.Label(comp_frame, text="Толщина (мм):").grid(row=3, column=0, sticky="w", padx=5)
        thickness_var = tk.StringVar(value=str(defaults.get("thickness", 10.0)))
        thickness_combo = ttk.Combobox(comp_frame, textvariable=thickness_var,
                                      values=[5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15], width=10)
        thickness_combo.grid(row=3, column=1, sticky="w", padx=5, pady=2)
        
        # Материал
        ttk.Label(comp_frame, text="Материал:").grid(row=4, column=0, sticky="w", padx=5)
        material_var = tk.StringVar(value=defaults.get("material", "Ст20"))
        material_combo = ttk.Combobox(comp_frame, textvariable=material_var,
                                     values=PIPE_MATERIALS, width=10)
        material_combo.grid(row=4, column=1, sticky="w", padx=5, pady=(2, 5))
        
        # Сохраняем данные
        self.components_data[component.component_id] = {
            "type": "pipe",
            "vars": {
                "length": length_var,
                "diameter": diameter_var,
                "thickness": thickness_var,
                "material": material_var
            },
            "required": component.required
        }
    
    def create_equipment_component_ui(self, component, row):
        """Создает UI для компонента-оборудования"""
        # Фрейм для компонента
        comp_frame = ttk.Frame(self.components_container, relief="groove", borderwidth=1)
        comp_frame.grid(row=row, column=0, columnspan=2, sticky="ew", padx=5, pady=2)
        comp_frame.grid_columnconfigure(1, weight=1)
        
        # Заголовок
        title = f"{component.name}" + (" (обязательный)" if component.required else "")
        ttk.Label(comp_frame, text=title, font=("Arial", 9)).grid(row=0, column=0, columnspan=2, sticky="w", pady=2)
        
        # Данные по умолчанию
        defaults = component.defaults
        
        # Толщина стенки
        ttk.Label(comp_frame, text="Толщина стенки (мм):").grid(row=1, column=0, sticky="w", padx=5)
        thickness_var = tk.StringVar(value=str(defaults.get("wall_thickness", 12.0)))
        thickness_combo = ttk.Combobox(comp_frame, textvariable=thickness_var,
                                      values=[8, 10, 12, 14, 16, 18, 20], width=10)
        thickness_combo.grid(row=1, column=1, sticky="w", padx=5, pady=2)
        
        # Количество
        ttk.Label(comp_frame, text="Количество:").grid(row=2, column=0, sticky="w", padx=5)
        count_var = tk.StringVar(value=str(defaults.get("count", 1)))
        count_spinbox = ttk.Spinbox(comp_frame, textvariable=count_var,
                                   from_=1, to=20, width=8)
        count_spinbox.grid(row=2, column=1, sticky="w", padx=5, pady=2)
        
        # Материал
        ttk.Label(comp_frame, text="Материал:").grid(row=3, column=0, sticky="w", padx=5)
        material_var = tk.StringVar(value=defaults.get("material", "09Г2С"))
        material_combo = ttk.Combobox(comp_frame, textvariable=material_var,
                                     values=PIPE_MATERIALS, width=10)
        material_combo.grid(row=3, column=1, sticky="w", padx=5, pady=(2, 5))
        
        # Сохраняем данные
        self.components_data[component.component_id] = {
            "type": "equipment",
            "vars": {
                "wall_thickness": thickness_var,
                "count": count_var,
                "material": material_var
            },
            "required": component.required
        }
    
    def validate_input(self):
        """Проверяет корректность введенных данных"""
        # Проверяем название
        name = self.name_entry.get().strip()
        if not name:
            tk.messagebox.showerror("Ошибка", "Введите название участка")
            return False
    
        # Проверяем, что такого названия ещё нет
        for section in self.sections_data:
            if section.get("name") == name:
                tk.messagebox.showerror("Ошибка", "Участок с таким именем уже существует")
                return False
    
        # Проверяем обязательные компоненты
        for comp_id, comp_data in self.components_data.items():
            if comp_data["required"]:
                # Проверяем, что все поля заполнены
                for var_name, var in comp_data["vars"].items():
                    value = var.get().strip()
                    if not value:
                        tk.messagebox.showerror("Ошибка", 
                                               f"Заполните все поля для компонента {comp_id}")
                        return False
                
                    # ПРОВЕРЯЕМ ТОЛЬКО ЧИСЛОВЫЕ ПОЛЯ!
                    if var_name in ["length", "diameter", "thickness", "wall_thickness", "count"]:
                        try:
                            float(value)
                        except ValueError:
                            tk.messagebox.showerror("Ошибка", 
                                                   f"Некорректное числовое значение в поле '{var_name}' для {comp_id}")
                            return False
                        
                    if var_name == "material":
                        if value not in PIPE_MATERIALS:
                            tk.messagebox.showwarning("Внимание", 
                                                     f"Материал '{value}' не в стандартном списке")
                            # Не блокируем, просто предупреждаем
    
        return True
    
    def collect_data(self):
        """Собирает данные из формы"""
        try:
            print("🎯 НАЧАЛО collect_data()")
        
            # Основные данные
            section_name = self.name_entry.get().strip()
            location = self.location_var.get()
            protection = self.protection_var.get()
            environment = self.environment_var.get()
        
            # Получаем template_id
            selected_name = self.object_var.get()
            template_id = self.name_to_id.get(selected_name, "pipe")
        
            # ПРОСТО ДОБАВЛЯЕМ ТИП К НАЗВАНИЮ
            # Определяем русское название по selected_name (из выпадающего списка)
            type_display_name = selected_name.split()[0]  # Берём первое слово из выбранного имени
            print(f"🔍 type_display_name из selected_name: '{type_display_name}'")
        
            # Проверяем, есть ли уже такой префикс
            if not section_name.startswith(type_display_name + ":"):
                section_name = f"{type_display_name}: {section_name}"
                print(f"📝 Добавлен тип к названию: '{section_name}'")
        
            print(f"📝 Создаю ComplexSection с параметрами:")
            print(f"   name: {section_name}")
            print(f"   object_type: {template_id}")
            print(f"   location: {location}")
            print(f"   protection: {protection}")
            print(f"   environment: {environment}")
        
            # Создаем сложную секцию
            if HAS_NEW_MODELS:
                print("✅ Использую импортированный ComplexSection")
                complex_section = ComplexSection(
                    name=section_name,
                    object_type=template_id,
                    location=location,
                    protection=protection,
                    environment=environment
                )
            else:
                # Заглушка для тестирования
                print("⚠️ Использую заглушку ComplexSection")
                class TempSection:
                    def __init__(self, **kwargs):
                        for key, value in kwargs.items():
                            setattr(self, key, value)
                        self.components = []
                complex_section = TempSection(
                    name=section_name,
                    object_type=template_id,
                    location=location,
                    protection=protection,
                    environment=environment
                )
        
            # ВАЖНО: Получаем шаблон для имён компонентов
            templates = get_available_templates(self.fluid_type)
            template = templates.get(template_id)
        
            # Добавляем компоненты с ПРАВИЛЬНЫМИ данными из формы
            for comp_id, comp_data in self.components_data.items():
                if comp_data["type"] == "pipe":
                    # Получаем данные из полей ввода
                    vars = comp_data["vars"]
                
                    # Проверяем заполненность
                    if not all(var.get().strip() for var in vars.values()):
                        continue
                
                    print(f"   🔧 Добавляю трубу {comp_id}")

                    # Находим имя компонента из шаблона
                    comp_name = comp_id
                    if template:
                        for comp in template.all_components:
                            if comp.component_id == comp_id:
                                comp_name = comp.name
                                break
                
                    if HAS_NEW_MODELS:
                        # ПРАВИЛЬНЫЙ способ: создаём Component через create_pipe
                        pipe_component = Component.create_pipe(
                            component_id=comp_id,
                            length=float(vars["length"].get()),
                            diameter=float(vars["diameter"].get()),
                            thickness=float(vars["thickness"].get()),
                            material=vars["material"].get()
                        )
                        # Добавляем имя для отображения
                        pipe_component.name = comp_name
                        complex_section.components.append(pipe_component)
                    else:
                        # Заглушка с ПОЛНЫМИ данными
                        pipe_component = {
                            "component_id": comp_id,
                            "name": comp_name,
                            "component_type": "pipe",
                            "type": "pipe",  # для совместимости
                            "length": float(vars["length"].get()),
                            "diameter": float(vars["diameter"].get()),
                            "thickness": float(vars["thickness"].get()),
                            "material": vars["material"].get()
                        }
                        
                        complex_section.components.append(pipe_component)
                        print(f"      Данные: дл={pipe_component['length']}, "
                              f"диам={pipe_component['diameter']}, "
                              f"толщ={pipe_component['thickness']}")
                    
                else:  # equipment
                    # Получаем данные из полей ввода
                    vars = comp_data["vars"]
                
                    if not all(var.get().strip() for var in vars.values()):
                        continue
                
                    print(f"   🔧 Добавляю оборудование {comp_id} с данными из формы")
                
                    # Находим имя компонента из шаблона
                    comp_name = comp_id
                    if template:
                        for comp in template.all_components:
                            if comp.component_id == comp_id:
                                comp_name = comp.name
                                break
                
                    if HAS_NEW_MODELS:
                        equipment_component = Component.create_equipment(
                            component_id=comp_id,
                            wall_thickness=float(vars["wall_thickness"].get()),
                            material=vars["material"].get(),
                            count=int(vars["count"].get())
                        )
                        # Добавляем имя для отображения
                        equipment_component.name = comp_name
                        complex_section.components.append(equipment_component)
                    else:
                        # Заглушка с ПОЛНЫМИ данными
                        equipment_component = {
                            "component_id": comp_id,
                            "name": comp_name,
                            "component_type": "equipment",
                            "type": "equipment",  # для совместимости
                            "wall_thickness": float(vars["wall_thickness"].get()),
                            "thickness": float(vars["wall_thickness"].get()),  # дублируем для удобства
                            "count": int(vars["count"].get()),
                            "material": vars["material"].get()
                        }
                        complex_section.components.append(equipment_component)
                        print(f"      Данные: толщ={equipment_component['wall_thickness']}, "
                              f"кол-во={equipment_component['count']}")
                        
            print(f"✅ ComplexSection создан! Компонентов: {len(complex_section.components)}")
            return complex_section
        
            # ОТЛАДКА: выводим все данные
            print("\n📊 ПРОВЕРКА ДАННЫХ:")
            for i, comp in enumerate(complex_section.components):
                print(f"   Компонент {i}:")
                if isinstance(comp, dict):
                    for key, value in comp.items():
                        print(f"      {key}: {value}")
                elif hasattr(comp, 'dict'):
                    for key, value in comp.dict.items():
                        print(f"      {key}: {value}")
                else:
                    print(f"      Тип: {type(comp)}")
        
            return complex_section
        
        except Exception as e:
            print(f"🔥 ОШИБКА в collect_data: {type(e).name}: {e}")
            import traceback
            traceback.print_exc()
            raise  # Пробрасываем ошибку дальше
    
    def confirm_add(self):
        """Добавляет участок и закрывает диалог"""
        try:
            if not self.validate_input():
                return
    
            # Собираем данные
            new_section = self.collect_data()
    
            # Проверяем, что есть хотя бы один компонент
            if not new_section.components:
                tk.messagebox.showerror("Ошибка", "Добавьте хотя бы один компонент")
                return
    
            # Вызываем callback с новой секцией
            self.callback(new_section)
    
            # Закрываем диалог
            self.dialog.destroy()
    
        except ValueError as e:
            tk.messagebox.showerror("Ошибка ввода", f"Проверьте числовые значения:\n{e}")
        except Exception as e:
            tk.messagebox.showerror("Ошибка", f"Неизвестная ошибка:\n{e}")
        
def show_add_dialog(parent, fluid_type, sections_data, callback):
    """
    Показывает диалог добавления участка
    
    Args:
        parent: родительское окно
        fluid_type: "oil" или "gas"
        sections_data: список существующих участков
        callback: функция, которая будет вызвана с новой секцией
    
    Returns:
        None
    """
    dialog = AddSectionDialog(parent, fluid_type, sections_data, callback)
    return dialog.dialog
