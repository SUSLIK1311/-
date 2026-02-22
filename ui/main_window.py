"""Главное окно приложения с вкладками"""
import tkinter as tk
from tkinter import ttk
import os
from PIL import Image
import sys

# Определяем шрифты
TITLE_FONT = ("Arial", 16, "bold")
HEADER_FONT = ("Arial", 12, "bold") 
TEXT_FONT = ("Arial", 10)

def show_main_window(fluid_type):
    from ui.parameters_tab import create_parameters_tab
    from ui.scheme_tab import create_scheme_tab
    from ui.analysis_tab import create_analysis_tab

    root_main = tk.Tk()
    
    icon_path = "assets/icon1.ico"
    if not os.path.exists(icon_path):
        icon_path = "../assets/icon1.ico"
    
    if os.path.exists(icon_path):
        try:
            root_main.iconbitmap(icon_path)
        except Exception as e:
            print(f"❌ Ошибка иконки: {e}")
              
    fluid_name = "НЕФТЕ" if fluid_type == "oil" else "ГАЗО"
    root_main.title(f"ЦИФРОВОЙ ДВОЙНИК {fluid_name}ПРОВОДА")
    root_main.geometry("1200x950")
    root_main.configure(bg='#4F273A')
    
    # НАЧИНАЕМ С ПУСТОГО СПИСКА - пользователь сам добавит участки через интерфейс
    shared_sections_data = []
    
    # Главный фрейм
    main_frame = tk.Frame(root_main, bg='#4F273A')
    main_frame.pack(fill="both", expand=True, padx=10, pady=10)
    
    # Создаём свои "вкладки" через Frame и Button
    tab_frame = tk.Frame(main_frame, bg='#18171C')
    tab_frame.pack(fill="x", pady=(0, 10))
    
    # Фреймы для содержимого вкладок
    content_frame = tk.Frame(main_frame, bg='white')
    content_frame.pack(fill="both", expand=True)
    
    # Создаём вкладки
    parameters_content = tk.Frame(content_frame, bg='white')
    scheme_content = tk.Frame(content_frame, bg='white') 
    analysis_content = tk.Frame(content_frame, bg='white')
    
    # Переменные для callback функций
    update_scheme_callback = None
    update_analysis_callback = None
    
    def create_tab_button(text, content_frame):
        btn = tk.Button(tab_frame, text=text, 
                       bg='#18171C', fg='#FADADD', font=("Arial", 10, "bold"),
                       relief='flat', borderwidth=0,
                       command=lambda: show_tab(content_frame))
        btn.pack(side="left", padx=2)
        return btn
    
    # Кнопки вкладок
    create_tab_button("ПАРАМЕТРЫ", parameters_content)
    create_tab_button("ПЕРЕЧЕНЬ УЧАСТКОВ", scheme_content)
    create_tab_button("АНАЛИЗ", analysis_content)
    
    # Функция переключения вкладок
    def show_tab(tab_frame):
        for frame in [parameters_content, scheme_content, analysis_content]:
            frame.pack_forget()
            
        # ОБНОВЛЯЕМ ВКЛАДКУ ПРИ ПЕРЕХОДЕ
        if tab_frame == scheme_content and update_scheme_callback:
             update_scheme_callback()
        elif tab_frame == analysis_content and update_analysis_callback:
             update_analysis_callback()
            
        tab_frame.pack(fill="both", expand=True)
        
    def init_tabs():
        nonlocal update_scheme_callback, update_analysis_callback
    
        # Функция для обновления всех вкладок
        def update_all():
            if update_scheme_callback:
                update_scheme_callback()
            if update_analysis_callback:
                update_analysis_callback()

        # Создаём вкладку параметров
        create_parameters_tab(parameters_content, fluid_type, shared_sections_data, update_all)
    
        # Создаём вкладку схемы
        scheme_tab, update_scheme = create_scheme_tab(scheme_content, fluid_type, shared_sections_data)
        update_scheme_callback = update_scheme
    
        # Создаём вкладку анализа
        analysis_tab, update_analysis = create_analysis_tab(analysis_content, fluid_type, shared_sections_data)
        update_analysis_callback = update_analysis
        
    # Инициализируем вкладки
    init_tabs()
    
    # Показываем первую вкладку
    show_tab(parameters_content)
    
    # Кнопка возврата
    def return_to_selector():
        root_main.destroy()
        from ui.selector_window import show_selector
        show_selector()
    
    return_btn = tk.Button(main_frame, text="← ВЫБОР ТИПА СРЕДЫ", 
                          bg='#18171C', fg='#FADADD', font=("Arial", 10, "bold"),
                          relief='flat', borderwidth=0,
                          command=return_to_selector)
    return_btn.place(relx=1.0, rely=0.0, anchor="ne", x=-15, y=0)
    
    root_main.mainloop()



