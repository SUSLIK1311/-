"""Вкладка с визуализацией перечня участков"""
import tkinter as tk
from tkinter import ttk
from PIL import Image, ImageTk
import os
import sys

# Функция для получения правильного пути к ресурсам в упакованном приложении
def get_resource_path(relative_path):
    """Получает правильный путь к ресурсам для упакованного приложения"""
    try:
        # PyInstaller создаёт временную папку в _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        # В режиме разработки используем текущую директорию
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

# Функции для определения цвета
def get_state_by_thickness(thickness):
    """Возвращает состояние по толщине"""
    if thickness >= 10.0:
        return "отличное"
    elif thickness >= 8.0:
        return "хорошее"
    elif thickness >= 6.0:
        return "удовлетворительное"
    elif thickness >= 4.0:
        return "плохое"
    else:
        return "аварийное"

def get_color_by_thickness(thickness):
    """Возвращает HEX-цвет по толщине"""
    if thickness >= 10.0:
        return "#90EE90"      # светло-зелёный
    elif thickness >= 8.0:
        return "#98FB98"      # зелёный
    elif thickness >= 6.0:
        return "#FFD700"      # жёлтый
    elif thickness >= 4.0:
        return "#FFA500"      # оранжевый
    else:
        return "#FF6B6B"      # красный

def get_corrosion_color(section):
    """Возвращает цвет по остаточной толщине"""
    is_complex = section.get("is_complex", False)
    
    if is_complex:
        # Для сложных объектов находим наихудшую остаточную толщину
        worst_thickness = 100.0  # очень большое число
        found = False
        
        # Сначала проверяем components_data
        components_data = section.get("components_data", [])
        for comp in components_data:
            remaining = comp.get("remaining")
            if remaining is not None:
                found = True
                if remaining < worst_thickness:
                    worst_thickness = remaining
        
        # Если не нашли в components_data, проверяем components
        if not found:
            components = section.get("components", [])
            for comp in components:
                remaining = comp.get("remaining")
                if remaining is None:
                    remaining = comp.get("thickness", comp.get("wall_thickness", 10.0))
                found = True
                if remaining < worst_thickness:
                    worst_thickness = remaining
        
        if not found:
            worst_thickness = 10.0
            
        return get_color_by_thickness(worst_thickness)
    else:
        # Для простых участков
        remaining = section.get("remaining_thickness")
        if remaining is None:
            remaining = section.get("thickness", 10.0)
        return get_color_by_thickness(remaining)

# Функции для работы с иконками
def apply_color_to_icon_pil(img, color):
    """Применяет цвет к иконке"""
    try:
        from PIL import Image
        # Создаём изображение с цветным фоном
        color_layer = Image.new('RGBA', img.size, color + (255,))
        
        # Используем маску исходного изображения
        if img.mode != 'RGBA':
            img = img.convert('RGBA')
        
        # Накладываем исходное изображение на цветной слой
        result = Image.alpha_composite(color_layer, img)
        return result
    except Exception as e:
        print(f"Ошибка применения цвета к иконке: {e}")
        return img

def create_debug_icon(color):
    """Создаёт простую иконку для отладки"""
    try:
        from PIL import Image, ImageDraw
        
        # Создаём изображение 64x64
        img = Image.new('RGBA', (64, 64), (255, 255, 255, 0))
        draw = ImageDraw.Draw(img)
        
        # Рисуем цветной круг
        if color and isinstance(color, str) and color.startswith('#'):
            hex_color = color.lstrip('#')
            rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
        else:
            rgb_color = (200, 200, 200)
        
        draw.ellipse([10, 10, 54, 54], fill=rgb_color, outline=(0, 0, 0), width=2)
        
        return img
    except Exception as e:
        print(f"Ошибка создания debug иконки: {e}")
        return None

def get_icon_object_type(section_name, fluid_type):
    """Определяет тип объекта для загрузки иконки"""
    name_lower = section_name.lower()
    
    # Проверяем русские названия
    if "труба" in name_lower or "трубопровод" in name_lower or "магистраль" in name_lower:
        return "Труба"

    if fluid_type == "oil":
        if "нпс" in name_lower or "насос" in name_lower:
            return "НПС"
        elif "подогрев" in name_lower:
            return "Подогрев"
        elif "резервуар" in name_lower:
            return "Резервуар"
        elif "отстойник" in name_lower:
            return "Отстойник"
    else:  # gas
        if "кс" in name_lower or "компрессор" in name_lower:
            return "КС"
        elif "фильтр" in name_lower:
            return "Фильтр"
        elif "грс" in name_lower or "газораспред" in name_lower:
            return "ГРС"
        elif "осушитель" in name_lower:
            return "Осушитель"
        elif "потребитель" in name_lower:
            return "Потребитель"

    # По умолчанию
    return "Труба"

def load_png_icon(object_type, fluid_type, color):
    """Загружает PNG иконку из assets/icons/"""
    try:
        # Маппинг русских названий объектов на имена файлов
        icon_mapping = {
            # Общие для нефти и газа
            "Труба": "pipe.png",
            "труба": "pipe.png",
            "трубопровод": "pipe.png",
        
            # Нефть
            "НПС": "pump_station.png",
            "нпс": "pump_station.png",
            "насосная": "pump_station.png",
            "Подогрев": "heater.png",
            "подогрев": "heater.png",
            "Резервуар": "reservoir.png",
            "резервуар": "reservoir.png",
            "Отстойник": "separator.png",
            "отстойник": "separator.png",
        
            # Газ
            "КС": "compressor_station.png",
            "кс": "compressor_station.png",
            "компрессорная": "compressor_station.png",
            "Фильтр": "filter.png",
            "фильтр": "filter.png",
            "ГРС": "grs.png",
            "грс": "grs.png",
            "газораспределительная": "grs.png",
            "Осушитель": "dryer.png",
            "осушитель": "dryer.png",
            "Потребитель": "consumer.png",
            "потребитель": "consumer.png"
        }
    
        # Получаем имя файла по типу объекта
        filename = icon_mapping.get(object_type)
        
        if not filename:
            # Пробуем найти файл по имени объекта
            filename = f"{object_type.lower()}.png"
        
        # Список путей для поиска
        icon_paths = [
            get_resource_path(f"assets/icons/{fluid_type}/{filename}"),
            get_resource_path(f"assets/icons/{filename}"),
            f"assets/icons/{fluid_type}/{filename}",
            f"assets/icons/{filename}",
            f"icons/{fluid_type}/{filename}",
            f"icons/{filename}",
            filename  # Прямой путь
        ]
    
        for path in icon_paths:
            if os.path.exists(path):
                print(f"✅ Найдена иконка: {path}")
                img = Image.open(path)
                
                # Применяем цвет коррозии
                if color:
                    # Преобразуем HEX в RGB
                    hex_color = color.lstrip('#')
                    rgb_color = tuple(int(hex_color[i:i+2], 16) for i in (0, 2, 4))
                    img = apply_color_to_icon_pil(img, rgb_color)
                
                return img
        
        print(f"⚠️ Иконка не найдена для: {object_type}")
        return create_debug_icon(color)
    
    except Exception as e:
        print(f"❌ Ошибка загрузки PNG иконки {object_type}: {e}")
        import traceback
        traceback.print_exc()
        return create_debug_icon(color)

# Основная функция создания вкладки
def create_scheme_tab(parent, fluid_type, sections_data):
    """Создаёт вкладку с визуализацией схемы"""
    tab = parent
    
    # Создаём основной фрейм с прокруткой
    main_frame = ttk.Frame(tab)
    main_frame.pack(fill="both", expand=True)
    
    # Создаём Canvas для прокрутки
    tk_canvas = tk.Canvas(main_frame, bg="#f0f0f0")
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tk_canvas.yview)
    scrollable_frame = ttk.Frame(tk_canvas, padding=20)
    
    scrollable_frame.bind(
        "<Configure>",
        lambda e: tk_canvas.configure(scrollregion=tk_canvas.bbox("all"))
    )
    
    tk_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    tk_canvas.configure(yscrollcommand=scrollbar.set)
    tk_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Заголовок
    title_label = ttk.Label(scrollable_frame, 
                           text="ПЕРЕЧЕНЬ УЧАСТКОВ ТРУБОПРОВОДА", 
                           font=("Arial", 14, "bold"))
    title_label.pack(pady=(0, 20))
    
    # Создаём основной контейнер для содержимого
    content_container = ttk.Frame(scrollable_frame)
    content_container.pack(fill="both", expand=True)
    
    # Фрейм для сообщения об отсутствии данных
    message_frame = ttk.Frame(content_container)
    
    # Фрейм для сетки с иконками
    grid_frame = ttk.Frame(content_container)
    
    # Функция для показа сообщения об отсутствии данных
    def show_no_data_message():
        """Показывает сообщение об отсутствии участков"""
        # Очищаем оба фрейма
        for widget in message_frame.winfo_children():
            widget.destroy()
        for widget in grid_frame.winfo_children():
            widget.destroy()
        
        # Скрываем grid_frame, показываем message_frame
        grid_frame.pack_forget()
        message_frame.pack(fill="both", expand=True, pady=50)
        
        # Создаем сообщение
        message_label = ttk.Label(
            message_frame,
            text="Добавьте участки во вкладке 'Параметры'",
            font=("Arial", 16, "bold"),
            foreground="#666666"
        )
        message_label.pack(pady=20)
        
        # Иконка или дополнительный текст
        info_label = ttk.Label(
            message_frame,
            text="Перейдите на вкладку 'Параметры', чтобы добавить новые участки трубопровода\nи рассчитать их состояние",
            font=("Arial", 12),
            foreground="#888888",
            justify="center"
        )
        info_label.pack(pady=10)
        
        # Разделительная линия
        separator = ttk.Separator(message_frame, orient="horizontal")
        separator.pack(fill="x", pady=20, padx=50)
        
        # Подсказка
        hint_label = ttk.Label(
            message_frame,
            text="Используйте кнопку 'Добавить участок' для создания нового участка",
            font=("Arial", 10, "italic"),
            foreground="#999999"
        )
        hint_label.pack(pady=10)
    
    # Функция для создания одной иконки
    def create_icon_widget(parent_frame, section, row, col):
        """Создаёт виджет с иконкой"""
        # Фрейм для одной иконки
        icon_frame = ttk.Frame(parent_frame, relief="solid", borderwidth=1)
        icon_frame.grid(row=row, column=col, padx=10, pady=10, sticky="nsew")
        
        # Получаем тип объекта
        section_name = section["name"]
        object_type = get_icon_object_type(section_name, fluid_type)
        
        # Получаем цвет
        color = get_corrosion_color(section)
        
        # Создаём канвас для иконки
        canvas = tk.Canvas(icon_frame, width=80, height=80, bg="white", highlightthickness=0)
        canvas.pack(pady=(10, 5))
        
        # Пробуем загрузить PNG иконку
        try:
            png_icon = load_png_icon(object_type, fluid_type, color)
            
            if png_icon:
                # Конвертируем в PhotoImage
                png_icon = png_icon.resize((60, 60), Image.Resampling.LANCZOS)
                tk_img = ImageTk.PhotoImage(png_icon)
                
                # Сохраняем ссылку
                canvas.image = tk_img
                
                # Рисуем иконку
                canvas.create_image(40, 40, image=tk_img)
            else:
                # Если PNG нет - создаём цветной прямоугольник с буквой
                canvas.create_rectangle(10, 10, 70, 70, fill=color, outline="black", width=2)
                letter = object_type[0].upper() if object_type else "?"
                canvas.create_text(40, 40, text=letter, 
                                  font=("Arial", 14, "bold"), fill="black")
        
        except Exception as e:
            print(f"Ошибка отрисовки иконки: {e}")
            # Запасной вариант - цветной прямоугольник
            canvas.create_rectangle(10, 10, 70, 70, fill=color, outline="black", width=2)
            canvas.create_text(40, 40, text="?", font=("Arial", 14, "bold"))
        
        # Название участка
        display_name = section_name
        if len(display_name) > 20:
            display_name = display_name[:17] + "..."
        
        name_label = ttk.Label(icon_frame, text=display_name, 
                              font=("Arial", 9), wraplength=100, justify="center")
        name_label.pack(pady=(0, 5))
        
        # Информация о состоянии
        is_complex = section.get("is_complex", False)
        
        if is_complex:
            # Находим наихудшее состояние
            components_data = section.get("components_data", [])
            if components_data:
                worst_thickness = min([comp.get("remaining", 10.0) for comp in components_data])
                worst_state = get_state_by_thickness(worst_thickness)
                components_count = len(components_data)
                status_text = f"{worst_state} ({components_count} комп.)"
            else:
                status_text = "нет данных"
        else:
            remaining = section.get("remaining_thickness", section.get("thickness", 10.0))
            state = get_state_by_thickness(remaining)
            status_text = state
        
        status_label = ttk.Label(icon_frame, text=status_text, 
                                font=("Arial", 8), foreground="gray")
        status_label.pack()
        
        # Кнопка просмотра 3D
        def on_button_click():
            try:
                from ui.viewer3d_dialog import show_3d_viewer
                show_3d_viewer(section, fluid_type)
            except Exception as e:
                print(f"Ошибка открытия 3D просмотра: {e}")
                import traceback
                traceback.print_exc()
                tk.messagebox.showerror("Ошибка", f"Не удалось открыть 3D просмотр:\n{e}")
        
        button = ttk.Button(icon_frame, text="Просмотр", 
                           command=on_button_click, width=12)
        button.pack(pady=(5, 10))
    
    # Функция для создания сетки с ФИКСИРОВАННЫМИ 5 колонками
    def create_fixed_grid():
        """Создаёт сетку иконок с фиксированными 5 колонками"""
        # Очищаем старые виджеты
        for widget in grid_frame.winfo_children():
            widget.destroy()
        
        # Проверяем, есть ли данные
        if not sections_data:
            show_no_data_message()
            return
        
        # Если есть данные, скрываем сообщение, показываем сетку
        message_frame.pack_forget()
        grid_frame.pack(fill="both", expand=True)
        
        # Фиксированное количество колонок
        COLS = 5
        
        # Настраиваем 5 колонок с равным весом
        for i in range(COLS):
            grid_frame.grid_columnconfigure(i, weight=1, minsize=120)
        
        print(f"Создаём сетку: {COLS} колонок, {len(sections_data)} секций")
        
        # Создаём сетку
        for i, section in enumerate(sections_data):
            row = i // COLS
            col = i % COLS
            
            # Создаём виджет иконки
            create_icon_widget(grid_frame, section, row, col)
        
        # Настраиваем строки (автоматически по количеству)
        rows_needed = (len(sections_data) + COLS - 1) // COLS
        for r in range(rows_needed):
            grid_frame.grid_rowconfigure(r, weight=0)
    
    # Создаём начальную сетку или сообщение
    create_fixed_grid()
    
    # Функция обновления схемы (вызывается извне)
    def update_scheme():
        """Обновляет схему при изменении данных"""
        print("🔄 Обновление схемы...")
        create_fixed_grid()
    
    # Принудительное обновление после отображения
    def on_tab_visible():
        """Вызывается, когда вкладка становится видимой"""
        tab.after(100, create_fixed_grid)  # 100ms задержка
    
    # Привязываем событие отображения вкладки
    tab.bind("<Visibility>", lambda e: on_tab_visible())
    
    return tab, update_scheme
