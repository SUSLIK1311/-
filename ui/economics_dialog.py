import tkinter as tk
from tkinter import ttk
from models.economics import ECONOMIC_PARAMS
import os

def create_economics_settings_dialog(parent, update_callback=None):
    """Диалог настройки экономических параметров"""
    dialog = tk.Toplevel(parent)
    dialog.title("Настройка стоимости работ и материалов")
    dialog.geometry("400x800")  
    dialog.resizable(False, False)
    dialog.transient(parent)
    dialog.grab_set()

    # ДОБАВЛЯЕМ ИКОНКУ ДЛЯ ДИАЛОГА
    icon_path = "assets/icon1.ico"
    if not os.path.exists(icon_path):
        icon_path = "../assets/icon1.ico"
    
    if os.path.exists(icon_path):
        try:
            dialog.iconbitmap(icon_path)
            print(f"✅ Иконка загружена для диалога: {icon_path}")
        except Exception as e:
            print(f"❌ Ошибка иконки диалога: {e}")
    
    # Центрируем диалог
    dialog.geometry("+%d+%d" % (parent.winfo_rootx() + 100, parent.winfo_rooty() + 50))
    
    # Создаем скроллируемый фрейм
    canvas = tk.Canvas(dialog)
    scrollbar = ttk.Scrollbar(dialog, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    main_frame = ttk.Frame(scrollable_frame, padding=20)
    main_frame.pack(fill="both", expand=True)
    
    # Заголовок
    ttk.Label(main_frame, text="НАСТРОЙКА СТОИМОСТИ", 
              font=("Arial", 14, "bold")).pack(pady=(0, 20))
    
    entries = {}
    
    # РАЗДЕЛ: Основные ставки
    labor_frame = ttk.LabelFrame(main_frame, text="СТАВКИ И РАСЦЕНКИ", padding=15)
    labor_frame.pack(fill="x", pady=(0, 15))
    
    labor_params = [
        ("Ставка рабочего (руб/час):", "работа_руб_час", 1500),
        ("Транспорт (руб/км):", "транспорт_руб_км", 50),
        ("Накладные расходы (%):", "накладные_процент", 15),
        ("Стоимость простоя (руб/час):", "простой_руб_час", 10000),
    ]
    
    for i, (label, key, default) in enumerate(labor_params):
        row_frame = ttk.Frame(labor_frame)
        row_frame.pack(fill="x", pady=5)
        
        ttk.Label(row_frame, text=label, width=25, anchor="w").pack(side="left")
        entry = ttk.Entry(row_frame, width=15, font=("Arial", 10))
        entry.insert(0, str(ECONOMIC_PARAMS.get(key, default)))
        entry.pack(side="right", padx=(10, 0))
        entries[key] = entry
    
    # РАЗДЕЛ: Стоимость материалов (руб/тонна)
    materials_frame = ttk.LabelFrame(main_frame, text="СТОИМОСТЬ МАТЕРИАЛОВ (руб/тонна)", padding=15)
    materials_frame.pack(fill="x", pady=(0, 15))
    
    materials = [
        ("Сталь 20", "Ст20", 45000),
        ("Сталь 45", "Ст45", 52000),
        ("09Г2С", "09Г2С", 68000),
        ("17Г1С", "17Г1С", 72000),
        ("X42", "X42", 85000),
        ("X52", "X52", 95000),
        ("X60", "X60", 110000),
        ("X65", "X65", 125000),
        ("X70", "X70", 140000),
        ("13ХФА", "13ХФА", 180000),
        ("08Х18Н10Т", "08Х18Н10Т", 320000),
        ("AISI 304", "AISI 304", 350000),
        ("AISI 316", "AISI 316", 480000),
    ]
    
    for i, (label, material, default) in enumerate(materials):
        row_frame = ttk.Frame(materials_frame)
        row_frame.pack(fill="x", pady=3)
        
        ttk.Label(row_frame, text=label, width=15, anchor="w").pack(side="left")
        entry = ttk.Entry(row_frame, width=12, font=("Arial", 9))
        current_val = ECONOMIC_PARAMS["стоимость_материалов"].get(material, default)
        entry.insert(0, str(current_val))
        entry.pack(side="right", padx=(10, 0))
        entries[f"материал_{material}"] = entry
    
    # РАЗДЕЛ: Стоимость покрытий (руб/м²)
    coatings_frame = ttk.LabelFrame(main_frame, text="СТОИМОСТЬ ПОКРЫТИЙ (руб/м²)", padding=15)
    coatings_frame.pack(fill="x", pady=(0, 15))
    
    coatings = [
        ("Без защиты", "без защиты", 0),
        ("ППУ изоляция", "ППУ изоляц.", 1200),
        ("Эпоксидное покрытие", "эпоксид. покр.", 800),
        ("Битумная изоляция", "битум. изоляц.", 600),
        ("Катод. защита + изол.", "катод. з. + изоляц.", 1500),
        ("Бетонное покрытие", "бетонное покрытие", 900),
        ("Полимер. изол. усил.", "полимер. изоляц. усилен.", 1400),
        ("Катод. защита + протек.", "катод. защ. + протекторы", 2000),
        ("Двойная изоляция", "двойная изоляция + мониторинг", 2800),
        ("Комплексная защита", "комплекс. защ.", 3500),
    ]
    
    for i, (label, coating, default) in enumerate(coatings):
        row_frame = ttk.Frame(coatings_frame)
        row_frame.pack(fill="x", pady=3)
        
        ttk.Label(row_frame, text=label, width=22, anchor="w").pack(side="left")
        entry = ttk.Entry(row_frame, width=12, font=("Arial", 9))
        current_val = ECONOMIC_PARAMS["стоимость_покрытий"].get(coating, default)
        entry.insert(0, str(current_val))
        entry.pack(side="right", padx=(10, 0))
        entries[f"покрытие_{coating}"] = entry
    
    # РАЗДЕЛ: Коэффициенты сложности
    complexity_frame = ttk.LabelFrame(main_frame, text="КОЭФФИЦИЕНТЫ СЛОЖНОСТИ", padding=15)
    complexity_frame.pack(fill="x", pady=(0, 20))
    
    complexity_params = [
        ("Надземная прокладка:", "надземная", 1.0),
        ("Подземная прокладка:", "подземная", 2.5),
        ("Подводная прокладка:", "подводная", 4.0),  # x4 как вы хотели
    ]
    
    for i, (label, location, default) in enumerate(complexity_params):
        row_frame = ttk.Frame(complexity_frame)
        row_frame.pack(fill="x", pady=5)
        
        ttk.Label(row_frame, text=label, width=20, anchor="w").pack(side="left")
        entry = ttk.Entry(row_frame, width=10, font=("Arial", 10))
        current_val = ECONOMIC_PARAMS["сложность_ремонта"].get(location, default)
        entry.insert(0, str(current_val))
        entry.pack(side="right", padx=(10, 0))
        entries[f"сложность_{location}"] = entry
    
    # РАЗДЕЛ: Кнопки управления
    button_frame = ttk.Frame(main_frame)
    button_frame.pack(fill="x", pady=10)
    
    def save_settings():
        """Сохраняет настройки в ECONOMIC_PARAMS"""
        try:
            # Основные параметры
            for key, entry in entries.items():
                if key.startswith("сложность_"):
                    location = key.replace("сложность_", "")
                    ECONOMIC_PARAMS["сложность_ремонта"][location] = float(entry.get())
                elif key.startswith("материал_"):
                    material = key.replace("материал_", "")
                    ECONOMIC_PARAMS["стоимость_материалов"][material] = float(entry.get())
                elif key.startswith("покрытие_"):
                    coating = key.replace("покрытие_", "")
                    ECONOMIC_PARAMS["стоимость_покрытий"][coating] = float(entry.get())
                else:
                    ECONOMIC_PARAMS[key] = float(entry.get())
            
            if update_callback:
                update_callback()
            
            dialog.destroy()
            print("✅ Экономические параметры сохранены")
            
        except ValueError as e:
            print(f"❌ Ошибка ввода данных: {e}")
            tk.messagebox.showerror("Ошибка", "Проверьте правильность введенных числовых значений")
    
    def reset_to_defaults():
        """Сброс к значениям по умолчанию"""
        defaults = {
            "работа_руб_час": 1500,
            "материал_руб_кг": 250,
            "транспорт_руб_км": 50,
            "накладные_процент": 15,
            "простой_руб_час": 10000,
            "стоимость_замены_трубы_руб_м": 8000,
            "стоимость_изоляции_руб_м2": 1500,
            "стоимость_катодной_защиты_руб": 500000,
            "стоимость_ппу_руб_м": 1200,
            "стоимость_эпоксида_руб_м": 800,
            "сложность_надземная": 1.0,
            "сложность_подземная": 2.5,
            "сложность_подводная": 4.0,
        }
        
        for key, entry in entries.items():
            if key in defaults:
                entry.delete(0, tk.END)
                entry.insert(0, str(defaults[key]))
    
    # КНОПКИ
    save_btn = tk.Button(button_frame, text="Сохранить",
                        bg='#18171C', fg='#FADADD', font=("Arial", 9, "bold"),
                        relief='flat', borderwidth=0,
                        command=save_settings)
    save_btn.pack(side="left", padx=(0, 10))
    
    reset_btn = tk.Button(button_frame, text="По умолчанию",
                         bg='#18171C', fg='FADADD', font=("Arial", 9, "bold"),
                         relief='flat', borderwidth=0,
                         command=reset_to_defaults)
    reset_btn.pack(side="left", padx=(0, 10))
    
    cancel_btn = tk.Button(button_frame, text="Отмена",
                          bg='#18171C', fg='FADADD', font=("Arial", 9, "bold"),
                          relief='flat', borderwidth=0,
                          command=dialog.destroy)
    cancel_btn.pack(side="right")

    return dialog

