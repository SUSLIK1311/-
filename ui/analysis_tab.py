"""Вкладка с анализом участков трубопровода (только сложные участки)"""
import tkinter as tk
from tkinter import ttk
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
import numpy as np
from models.corrosion import calculate_corrosion_oil, calculate_corrosion_gas, get_corrosion_level
from models.economics import (
    get_economic_summary,
    calculate_repair_cost,
    calculate_downtime_cost,
    calculate_repair_cost_detailed,
    calculate_detailed_repair_costs,
    get_repair_method_info,
    calculate_component_repair_cost
)

def create_corrosion_plot(parent_frame, section, fluid_type):
    """График прогноза коррозии для ВСЕХ компонентов сложного участка"""
    plot_frame = ttk.Frame(parent_frame)
    plot_frame.pack(fill="x", pady=10)
    
    components = section.get("components", [])
    if not components:
        # Пустой график, если нет компонентов
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "Нет данных о компонентах", 
               ha='center', va='center', fontsize=12, transform=ax.transAxes)
        ax.axis('off')
        canvas = FigureCanvasTkAgg(fig, plot_frame)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True, padx=10)
        return
    
    # Создаем подграфики для всех компонентов
    n_components = len(components)
    if n_components <= 3:
        rows, cols = 1, n_components
        fig_height = 4
    elif n_components <= 6:
        rows, cols = 2, (n_components + 1) // 2
        fig_height = 7
    else:
        rows, cols = 3, (n_components + 2) // 3
        fig_height = 10
    
    fig, axes = plt.subplots(rows, cols, figsize=(4*cols, fig_height))
    fig.suptitle(f'Прогноз коррозии для всех компонентов ({section["name"]})', fontsize=14, fontweight='bold')
    
    # Если только один компонент, axes не будет массивом
    if n_components == 1:
        axes = [axes]
    elif rows == 1:
        axes = axes
    else:
        axes = axes.flatten()
    
    years = list(range(0, 51, 5))
    colors = plt.cm.tab10(np.linspace(0, 1, min(10, n_components)))
    
    for idx, (component, ax, color) in enumerate(zip(components, axes[:n_components], colors)):
        # Получаем параметры компонента
        thickness = component.get("thickness", component.get("wall_thickness", 10))
        diameter = component.get("diameter", 100)
        material = component.get("material", "сталь")
        
        thickness_remaining = []
        corrosion_rates = []
        
        # Расчет для каждого года
        for year in years:
            if fluid_type == "oil":
                loss, rate = calculate_corrosion_oil(
                    year,
                    section.get("temperature", 60),          
                    section.get("water_content", 5),        
                    section.get("h2s_content", 50),         
                    section.get("viscosity", 15),           
                    section.get("flow_rate", 1000),           
                    thickness,
                    diameter,
                    material,
                    section.get("location", "надземная"),     
                    section.get("protection", "без защиты"), 
                    section.get("environment", "Поволжье")   
                )
            else:
                loss, rate = calculate_corrosion_gas(
                    year,
                    section.get("temperature", 20),           
                    section.get("pressure", 5),              
                    section.get("co2_content", 2),           
                    section.get("methane_content", 85),      
                    section.get("dew_point", -10),           
                    thickness,
                    diameter,
                    material,
                    section.get("location", "надземная"),     
                    section.get("protection", "без защиты"), 
                    section.get("environment", "Поволжье")    
                )
            
            remaining = max(0, thickness - loss)
            thickness_remaining.append(remaining)
            corrosion_rates.append(rate)
        
        # Отрисовка графика для компонента
        ax.plot(years, thickness_remaining, 'o-', color=color, linewidth=2, markersize=4,
               label=f'Толщ: {thickness}мм')
        
        # Критические уровни
        ax.axhline(y=5.0, color='r', linestyle='--', alpha=0.5, label='Крит. уровень' if idx == 0 else "")
        ax.axhline(y=8.0, color='y', linestyle='--', alpha=0.5, label='Внимание' if idx == 0 else "")
        ax.axhline(y=thickness, color='g', linestyle=':', alpha=0.5, label='Начальная' if idx == 0 else "")
        
        # Настройки подграфика
        comp_name = component.get("name", f"Компонент {idx+1}")
        ax.set_title(f'{comp_name}\n({component.get("component_type", "unknown")})', fontsize=10)
        ax.set_xlabel('Время (лет)')
        if idx % cols == 0:  # Только для первого столбца
            ax.set_ylabel('Остаточная толщина (мм)')
        ax.grid(True, alpha=0.3)
        ax.legend(loc='upper right', fontsize=8)
        
        # Добавляем текстовую информацию о скорости коррозии
        avg_rate = np.mean(corrosion_rates)
        ax.text(0.02, 0.98, f'Ср. скорость: {avg_rate:.3f} мм/год',
                transform=ax.transAxes, fontsize=8, verticalalignment='top',
                bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.5))
    
    # Скрываем пустые подграфики
    for i in range(n_components, len(axes)):
        axes[i].axis('off')
    
    plt.tight_layout(rect=[0, 0, 1, 0.96])  # Учитываем заголовок
    canvas = FigureCanvasTkAgg(fig, plot_frame)
    canvas.draw()
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10)

def create_component_analysis(parent_frame, components, fluid_type, section_params):
    """Создает детальный анализ для каждого компонента"""
    comp_frame = ttk.LabelFrame(parent_frame, text="ДЕТАЛЬНЫЙ АНАЛИЗ КОМПОНЕНТОВ", padding=10)
    comp_frame.pack(fill="x", padx=20, pady=10)
    
    # Создаем Notebook для вкладок по компонентам
    notebook = ttk.Notebook(comp_frame)
    notebook.pack(fill="both", expand=True, padx=5, pady=5)
    
    for idx, component in enumerate(components):
        comp_tab = ttk.Frame(notebook)
        notebook.add(comp_tab, text=component.get("name", f"Комп.{idx+1}"))
        
        # Фрейм с прокруткой для деталей
        canvas = tk.Canvas(comp_tab)
        scrollbar = ttk.Scrollbar(comp_tab, orient="vertical", command=canvas.yview)
        scrollable_frame = ttk.Frame(canvas)
        
        scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
        canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
        canvas.configure(yscrollcommand=scrollbar.set)
        canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        
        # Заголовок компонента
        ttk.Label(scrollable_frame, text=f"КОМПОНЕНТ: {component.get('name', 'Без имени')}", 
                 font=("Arial", 12, "bold")).pack(pady=(10, 5))
        
        # Параметры компонента
        params_frame = ttk.LabelFrame(scrollable_frame, text="ТЕХНИЧЕСКИЕ ПАРАМЕТРЫ", padding=10)
        params_frame.pack(fill="x", padx=10, pady=5)
        
        # Определяем тип компонента и соответствующие параметры
        comp_type = component.get("component_type", "unknown")
        
        param_text = ""
        if comp_type == "pipe":
            param_text = f"""• Тип: Труба
• Диаметр: {component.get('diameter', 0)} мм
• Длина: {component.get('length', 0)} м
• Толщина стенки: {component.get('wall_thickness', component.get('thickness', 0))} мм
• Материал: {component.get('material', 'сталь')}
• Площадь поверхности: {component.get('surface_area', 0):.1f} м²
• Объем: {component.get('volume', 0):.1f} м³"""
        elif comp_type == "valve":
            param_text = f"""• Тип: Задвижка/Клапан
• Диаметр: {component.get('diameter', 0)} мм
• Тип привода: {component.get('actuator_type', 'ручной')}
• Материал корпуса: {component.get('body_material', 'сталь')}
• Материал уплотнения: {component.get('seal_material', 'тефлон')}"""
        elif comp_type == "flange":
            param_text = f"""• Тип: Фланец
• Диаметр: {component.get('diameter', 0)} мм
• Класс давления: {component.get('pressure_class', 'PN16')}
• Тип уплотнения: {component.get('gasket_type', 'паронит')}
• Количество болтов: {component.get('bolt_count', 8)}"""
        elif comp_type == "tee":
            param_text = f"""• Тип: Тройник
• Основной диаметр: {component.get('main_diameter', 0)} мм
• Ответвление: {component.get('branch_diameter', 0)} мм
• Тип: {component.get('tee_type', 'равнопроходной')}"""
        else:
            param_text = f"""• Тип: {comp_type}
• Толщина: {component.get('thickness', component.get('wall_thickness', 0))} мм
• Материал: {component.get('material', 'сталь')}
• Количество: {component.get('count', 1)} шт."""
        
        ttk.Label(params_frame, text=param_text, font=("Arial", 9), justify="left").pack(anchor="w")
        
        # Прогноз коррозии для этого компонента
        corrosion_frame = ttk.LabelFrame(scrollable_frame, text="ПРОГНОЗ КОРРОЗИИ", padding=10)
        corrosion_frame.pack(fill="x", padx=10, pady=5)
        
        # Рассчитываем коррозию для разных периодов
        thickness = component.get("thickness", component.get("wall_thickness", 10))
        periods = [1, 5, 10, 20, 30]
        
        corrosion_text = "Остаточная толщина:\n"
        for period in periods:
            if fluid_type == "oil":
                loss, rate = calculate_corrosion_oil(
                    period,
                    section_params.get("temperature", 60),
                    section_params.get("water_content", 5),
                    section_params.get("h2s_content", 50),
                    section_params.get("viscosity", 15),
                    section_params.get("flow_rate", 1000),
                    thickness,
                    component.get("diameter", 100),
                    component.get("material", "сталь"),
                    section_params.get("location", "надземная"),
                    section_params.get("protection", "без защиты"),
                    section_params.get("environment", "Поволжье")
                )
            else:
                loss, rate = calculate_corrosion_gas(
                    period,
                    section_params.get("temperature", 20),
                    section_params.get("pressure", 5),
                    section_params.get("co2_content", 2),
                    section_params.get("methane_content", 85),
                    section_params.get("dew_point", -10),
                    thickness,
                    component.get("diameter", 100),
                    component.get("material", "сталь"),
                    section_params.get("location", "надземная"),
                    section_params.get("protection", "без защиты"),
                    section_params.get("environment", "Поволжье")
                )
            
            remaining = max(0, thickness - loss)
            corrosion_level, _ = get_corrosion_level(remaining)
            
            corrosion_text += f"• Через {period} лет: {remaining:.1f} мм ({corrosion_level})\n"
        
        ttk.Label(corrosion_frame, text=corrosion_text, font=("Arial", 9), justify="left").pack(anchor="w")
        
        # Рекомендации для компонента
        rec_frame = ttk.LabelFrame(scrollable_frame, text="РЕКОМЕНДАЦИИ ДЛЯ КОМПОНЕНТА", padding=10)
        rec_frame.pack(fill="x", padx=10, pady=5)
        
        # Определяем рекомендации в зависимости от типа компонента
        if comp_type == "pipe":
            recommendations = [
                "✓ Регулярный ультразвуковой контроль толщины",
                "✓ Проверка защитного покрытия раз в 2 года",
                "✓ Контроль опор и подвесок",
                "✓ Визуальный осмотр на наличие протечек"
            ]
        elif comp_type == "valve":
            recommendations = [
                "✓ Проверка герметичности уплотнений",
                "✓ Смазка штока и механизмов раз в год",
                "✓ Контроль плавности хода",
                "✓ Проверка индикаторов положения"
            ]
        elif comp_type == "flange":
            recommendations = [
                "✓ Контроль затяжки болтов по графику",
                "✓ Проверка состояния прокладок",
                "✓ Визуальный осмотр на коррозию",
                "✓ Замена уплотнений при плановых остановах"
            ]
        else:
            recommendations = [
                "✓ Регулярный визуальный осмотр",
                "✓ Контроль крепежных элементов",
                "✓ Проверка на вибрацию",
                "✓ Обновление защитного покрытия"
            ]
        
        for rec in recommendations:
            ttk.Label(rec_frame, text=rec, font=("Arial", 9), justify="left").pack(anchor="w", padx=5)

def create_section_analysis(parent, section, fluid_type):
    """Создаёт детальный анализ для сложного участка с ВСЕМИ компонентами"""
    if not isinstance(section, dict):
        error_frame = ttk.Frame(parent)
        error_frame.pack(fill="both", expand=True)
        ttk.Label(error_frame, text=f"❌ Ошибка в данных участка: {section}", 
                 font=("Arial", 12, "bold"), foreground="red").pack(pady=50)
        return
    
    # Основной фрейм с прокруткой
    main_frame = ttk.Frame(parent)
    main_frame.pack(fill="both", expand=True)

    tk_canvas = tk.Canvas(main_frame)  
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=tk_canvas.yview)
    scrollable_frame = ttk.Frame(tk_canvas)

    scrollable_frame.bind("<Configure>", lambda e: tk_canvas.configure(scrollregion=tk_canvas.bbox("all")))  
    tk_canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    tk_canvas.configure(yscrollcommand=scrollbar.set)
    tk_canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")

    # Заголовок
    components = section.get("components", [])
    title_text = f"АНАЛИЗ: {section['name']}"
    if components:
        title_text += f" [{len(components)} комп.]"
    
    title_label = ttk.Label(scrollable_frame, text=title_text, font=("Arial", 16, "bold"))
    title_label.pack(pady=20)
    
    # ОСНОВНАЯ ИНФОРМАЦИЯ 
    info_frame = ttk.LabelFrame(scrollable_frame, text="ОСНОВНЫЕ ПАРАМЕТРЫ", padding=10)
    info_frame.pack(fill="x", padx=20, pady=10)
    
    # Операционные параметры участка
    ops_frame = ttk.LabelFrame(info_frame, text="ОПЕРАЦИОННЫЕ ПАРАМЕТРЫ", padding=10)
    ops_frame.pack(fill="x", padx=10, pady=5)
    
    if fluid_type == "oil":
        ops_text = f"""• Тип среды: Нефть
• Температура: {section.get('temperature', 60)} °C
• Содержание воды: {section.get('water_content', 5)} %
• Содержание H₂S: {section.get('h2s_content', 50)} ppm
• Вязкость: {section.get('viscosity', 15)} сСт
• Расход: {section.get('flow_rate', 1000)} м³/сут"""
    else:
        ops_text = f"""• Тип среды: Газ
• Температура: {section.get('temperature', 20)} °C
• Давление: {section.get('pressure', 5)} МПа
• Содержание CO₂: {section.get('co2_content', 2)} %
• Содержание метана: {section.get('methane_content', 85)} %
• Точка росы: {section.get('dew_point', -10)} °C"""
    
    ttk.Label(ops_frame, text=ops_text, font=("Arial", 9), justify="left").pack(anchor="w")
    
    # Параметры участка
    section_frame = ttk.LabelFrame(info_frame, text="ПАРАМЕТРЫ УЧАСТКА", padding=10)
    section_frame.pack(fill="x", padx=10, pady=5)
    
    section_text = f"""• Тип объекта: {section.get('object_type', 'трубопровод')}
• Прокладка: {section.get('location', 'надземная')}
• Защита: {section.get('protection', 'без защиты')}
• Регион: {section.get('environment', 'Поволжье')}
• Количество компонентов: {len(components)}"""
    
    ttk.Label(section_frame, text=section_text, font=("Arial", 9), justify="left").pack(anchor="w")
    
    # Сводная таблица компонентов
    if components:
        comp_frame = ttk.LabelFrame(scrollable_frame, text="СВОДНАЯ ТАБЛИЦА КОМПОНЕНТОВ", padding=10)
        comp_frame.pack(fill="x", padx=20, pady=10)
        
        columns = ("№", "Компонент", "Тип", "Материал", "Размеры", "Толщина", "Состояние")
        tree = ttk.Treeview(comp_frame, columns=columns, show="headings", height=min(8, len(components)))
        
        tree.column("№", width=40)
        tree.column("Компонент", width=150)
        tree.column("Тип", width=100)
        tree.column("Материал", width=100)
        tree.column("Размеры", width=120)
        tree.column("Толщина", width=80)
        tree.column("Состояние", width=100)
        
        for col in columns:
            tree.heading(col, text=col)
        
        # Заполняем таблицу компонентов
        for idx, comp in enumerate(components, 1):
            comp_name = comp.get("name", comp.get("component_id", f"Компонент {idx}"))
            comp_type = comp.get("component_type", "unknown")
            material = comp.get("material", "—")
            
            # Размер в зависимости от типа
            if comp_type == "pipe":
                length = comp.get("length", 0)
                diameter = comp.get("diameter", 0)
                size = f"L={length}м, Ø={diameter}мм"
            elif comp_type == "tee":
                main_dia = comp.get("main_diameter", 0)
                branch_dia = comp.get("branch_diameter", 0)
                size = f"Øосн={main_dia}мм, Øотв={branch_dia}мм"
            else:
                thickness = comp.get("wall_thickness", comp.get("thickness", 0))
                count = comp.get("count", 1)
                diameter = comp.get("diameter", 0)
                if diameter > 0:
                    size = f"Ø={diameter}мм, толщ.{thickness}мм" + (f" x{count}" if count > 1 else "")
                else:
                    size = f"толщ.{thickness}мм" + (f" x{count}" if count > 1 else "")
            
            # Толщина
            thickness_value = comp.get("thickness", comp.get("wall_thickness", 0))
            
            # Состояние компонента
            comp_remaining = comp.get("remaining", thickness_value)
            comp_level, _ = get_corrosion_level(comp_remaining)
            
            # Цвет строки в зависимости от состояния
            bg_color = ""
            if comp_level == "аварийное":
                bg_color = "#FFCCCC"
            elif comp_level == "плохое":
                bg_color = "#FFE6CC"
            elif comp_level == "удовлетворительное":
                bg_color = "#FFFFCC"
            
            item_id = tree.insert("", "end", values=(
                idx,
                comp_name, 
                comp_type, 
                material, 
                size, 
                f"{thickness_value:.1f} мм",
                comp_level
            ), tags=(comp_level,))
            
            if bg_color:
                tree.tag_configure(comp_level, background=bg_color)
        
        tree.pack(fill="x", pady=5)
        
        # Легенда состояний
        legend_frame = ttk.Frame(comp_frame)
        legend_frame.pack(fill="x", pady=5)
        
        for state, color in [("аварийное", "#FFCCCC"), ("плохое", "#FFE6CC"), 
                            ("удовлетворительное", "#FFFFCC"), ("хорошее", "#E6FFCC"), 
                            ("отличное", "#CCFFCC")]:
            if any(1 for item in tree.get_children() if tree.item(item, "values")[6] == state):
                frame = ttk.Frame(legend_frame)
                frame.pack(side="left", padx=10)
                tk.Label(frame, text="■", font=("Arial", 12), foreground=color).pack(side="left")
                ttk.Label(frame, text=state).pack(side="left", padx=2)
    
    # ГРАФИК КОРРОЗИИ ДЛЯ ВСЕХ КОМПОНЕНТОВ
    plot_frame = ttk.LabelFrame(scrollable_frame, text="ПРОГНОЗ КОРРОЗИИ ДЛЯ ВСЕХ КОМПОНЕНТОВ", padding=10)
    plot_frame.pack(fill="x", padx=20, pady=10)
    create_corrosion_plot(plot_frame, section, fluid_type)
    
    # ДЕТАЛЬНЫЙ АНАЛИЗ КАЖДОГО КОМПОНЕНТА
    if components:
        create_component_analysis(scrollable_frame, components, fluid_type, section)
    
    # РЕКОМЕНДАЦИИ ПО УЧАСТКУ
    rec_frame = ttk.LabelFrame(scrollable_frame, text="РЕКОМЕНДАЦИИ ПО УЧАСТКУ", padding=10)
    rec_frame.pack(fill="x", padx=20, pady=10)
    create_recommendations(rec_frame, section, fluid_type)
        
    # ЭКОНОМИКА - расчёт для всего участка
    cost_frame = ttk.LabelFrame(scrollable_frame, text="ДЕТАЛИЗИРОВАННАЯ СМЕТА РЕМОНТА", padding=10)
    cost_frame.pack(fill="x", padx=20, pady=10)

    # Рассчитываем детальные затраты для всего участка
    detailed_costs = calculate_detailed_repair_costs(section)
    repair_cost = detailed_costs["total_cost"]
    repair_method = detailed_costs["repair_method"]
    downtime_cost = calculate_downtime_cost(section)
    total_cost = repair_cost + downtime_cost

    # ИСПРАВЛЕННЫЙ БЛОК: Сводка по ремонту компонентов
    if components:
        comp_repair_frame = ttk.LabelFrame(cost_frame, text="РЕМОНТ КОМПОНЕНТОВ", padding=10)
        comp_repair_frame.pack(fill="x", padx=10, pady=5)
    
        repair_summary = {}
        component_repair_details = []
        total_components_cost = 0
    
        # ДОБАВЛЯЕМ ЭТОТ ЦИКЛ для расчёта стоимости каждого компонента
        for comp in components:
            comp_type = comp.get("component_type", "unknown")
            comp_name = comp.get("name", f"Компонент {len(component_repair_details)+1}")
        
            try:
                # ИСПОЛЬЗУЕМ НОВУЮ ФУНКЦИЮ из economics.py
                comp_cost_data = calculate_component_repair_cost(comp, section)
                comp_cost = comp_cost_data['total_cost']
                repair_method = comp_cost_data['repair_method']
                wear_percentage = comp_cost_data.get('wear_percentage', 0)
            
                # Сохраняем детали для отображения
                component_repair_details.append({
                    "name": comp_name,
                    "type": comp_type,
                    "cost": comp_cost,
                    "method": repair_method,
                    "wear_percentage": wear_percentage,
                    "remaining": comp.get("remaining", comp.get("thickness", comp.get("wall_thickness", 10)))
                })
            
                # Суммируем общую стоимость
                total_components_cost += comp_cost
            
                # Суммируем по типам компонентов
                repair_summary[comp_type] = repair_summary.get(comp_type, 0) + comp_cost
            
            except Exception as e:
                print(f"Ошибка расчета стоимости для компонента {comp_name}: {e}")
            continue
    
        if repair_summary:
            # Показываем суммарные затраты
            summary_text = f"ОБЩАЯ СТОИМОСТЬ РЕМОНТА КОМПОНЕНТОВ: {total_components_cost:,.0f} руб\n\n"
            summary_text += "Затраты по типам компонентов:\n"
            for comp_type, cost in repair_summary.items():
                percentage = (cost / total_components_cost * 100) if total_components_cost > 0 else 0
                summary_text += f"• {comp_type}: {cost:,.0f} руб ({percentage:.1f}%)\n"
        
            ttk.Label(comp_repair_frame, text=summary_text, font=("Arial", 9), justify="left").pack(anchor="w")
        
            # Показываем детали по критичным компонентам
            critical_components = [c for c in component_repair_details if c["remaining"] < 6]
            if critical_components:
                ttk.Label(comp_repair_frame, text="\nКРИТИЧНЫЕ КОМПОНЕНТЫ (требуют внимания):", 
                         font=("Arial", 9, "bold")).pack(anchor="w", pady=(5,0))
            
                for detail in critical_components:
                    detail_text = f"  - {detail['name']}: ост. толщ. {detail['remaining']:.1f} мм, износ {detail['wear_percentage']:.0f}%, стоимость {detail['cost']:,.0f} руб"
                    ttk.Label(comp_repair_frame, text=detail_text, font=("Arial", 8)).pack(anchor="w", padx=20)

    # ДЕТАЛЬНАЯ ТАБЛИЦА ЗАТРАТ
    columns = ("Статья затрат", "Ед. изм.", "Кол-во", "Стоимость ед., руб", "Общая стоимость, руб")
    tree = ttk.Treeview(cost_frame, columns=columns, show="headings", height=8)

    # Настраиваем колонки
    tree.column("Статья затрат", width=180)
    tree.column("Ед. изм.", width=80)
    tree.column("Кол-во", width=80)
    tree.column("Стоимость ед., руб", width=120)
    tree.column("Общая стоимость, руб", width=140)
  
    for col in columns:
            tree.heading(col, text=col)

    # Добавляем строки с детализацией
    # 1. Трудозатраты
    tree.insert("", "end", values=(
        "Рабочие", 
        "час", 
        f"{detailed_costs['labor_hours']:.1f}",
        f"{detailed_costs['labor_rate']:,.0f}",
        f"{detailed_costs['labor_cost']:,.0f}"
    ))

    # 2. Материалы (если есть)
    if detailed_costs['material_cost'] > 0:
        material_name = section.get('material', 'сталь')
        if components:
            # Используем материал первого компонента
            first_comp = components[0]
            material_name = first_comp.get('material', material_name)
        
        tree.insert("", "end", values=(
            f"Материал ({material_name})", 
            "тонна", 
            f"{detailed_costs['material_weight']:.1f}",
            f"{detailed_costs['material_price']:,.0f}",
            f"{detailed_costs['material_cost']:,.0f}"
        ))

    # 3. Защитные покрытия (если есть)
    if detailed_costs['protection_cost'] > 0:
        tree.insert("", "end", values=(
            f"Покрытие ({section.get('protection', 'без защиты')})", 
            "м²", 
            f"{detailed_costs['protection_area']:.0f}",
            f"{detailed_costs['protection_price']:,.0f}",
            f"{detailed_costs['protection_cost']:,.0f}"
        ))

    # 4. Транспорт
    tree.insert("", "end", values=(
        "Транспорт", 
        "км", 
        f"{detailed_costs['transport_distance']:.1f}",
        f"{detailed_costs['transport_rate']:,.0f}",
        f"{detailed_costs['transport_cost']:,.0f}"
    ))

    # 5. Накладные расходы
    tree.insert("", "end", values=(
        "Накладные расходы", 
        "%", 
        f"{detailed_costs['overhead_percent']}",
        "-",
        f"{detailed_costs['overhead_cost']:,.0f}"
    ))

    # 6. Коэффициент сложности
    tree.insert("", "end", values=(
        f"Коэф. сложности ({section.get('location', 'надземная')})", 
        "коэф.", 
        f"{detailed_costs['complexity']}",
        "-",
        f"{detailed_costs['complexity_cost']:,.0f}"
    ))

    # 7. Стоимость простоя (если есть)
    if downtime_cost > 0:
        tree.insert("", "end", values=(
            "Стоимость простоя системы", 
            "час", 
            "24",
            f"{detailed_costs['downtime_rate']:,.0f}",
            f"{downtime_cost:,.0f}"
        ))

    # 8. ИТОГО
    tree.insert("", "end", values=(
        "ИТОГО", 
        "", 
        "",
        "",
        f"{total_cost:,.0f}"
    ), tags=("total",))

    # Настраиваем стиль для итоговой строки
    tree.tag_configure("total", background="#FFE4B5", font=("Arial", 9, "bold"))

    tree.pack(fill="x", pady=10)

    # ИНФОРМАЦИЯ О МЕТОДЕ РЕМОНТА
    method_info = get_repair_method_info(repair_method)
    method_text = f"Рекомендуемый метод: {method_info['name']}\n{method_info['description']}\n\nДлительность: {method_info.get('duration', '3-5')} дней"
    
    method_label = ttk.Label(cost_frame, text=method_text, font=("Arial", 9), 
                                wraplength=800, justify="left")
    method_label.pack(anchor="w", pady=5)

    # Пояснение по простою
    if downtime_cost == 0:
        downtime_text = "Плановый ремонт - простой не учитывается"
    else:
        downtime_text = "Аварийный ремонт - учитывается простой системы"

    ttk.Label(cost_frame, text=downtime_text, font=("Arial", 9)).pack(anchor="w")

def create_recommendations(parent_frame, section, fluid_type):
    """Рекомендации по обслуживанию для сложных участков (улучшенная версия)"""
    rec_frame = ttk.LabelFrame(parent_frame, text="ИНТЕГРИРОВАННЫЕ РЕКОМЕНДАЦИИ", padding=10)
    rec_frame.pack(fill="x", pady=5)
    
    components = section.get("components", [])
    if not components:
        ttk.Label(rec_frame, text="Нет данных о компонентах", 
                 font=("Arial", 10), foreground="red").pack(anchor="w")
        return
    
    # Рассчитываем состояние каждого компонента
    component_states = []
    urgent_components = []
    
    for component in components:
        # Получаем остаточную толщину компонента
        if "remaining" in component:
            remaining = component["remaining"]
        elif "thickness" in component:
            remaining = component["thickness"]
        elif "wall_thickness" in component:
            remaining = component["wall_thickness"]
        else:
            remaining = 10
        
        # Определяем состояние
        if remaining >= 10.0:
            state = "отличное"
            priority = 4
        elif remaining >= 8.0:
            state = "хорошее"
            priority = 3
        elif remaining >= 6.0:
            state = "удовлетворительное"
            priority = 2
        elif remaining >= 4.0:
            state = "плохое"
            priority = 1
            urgent_components.append(component.get("name", "Компонент"))
        else:
            state = "аварийное"
            priority = 0
            urgent_components.append(component.get("name", "Компонент"))
        
        component_states.append((component.get("name", "Компонент"), state, remaining, priority))
    
    # Сортируем по приоритету (хуже - выше)
    component_states.sort(key=lambda x: x[3])
    
    # Определяем общее состояние (по худшему компоненту)
    worst_state = component_states[0]
    
    # Формируем рекомендацию
    if worst_state[1] == "аварийное":
        urgency = "КРИТИЧЕСКИЙ"
        color = "red"
        bg_color = "#FFCCCC"
        
        if urgent_components:
            rec_list = "\n".join([f"• {name}" for name in urgent_components])
            recommendation = f"ТРЕБУЕТСЯ НЕМЕДЛЕННЫЙ РЕМОНТ!\n\nАварийные компоненты:\n{rec_list}"
        else:
            recommendation = "ТРЕБУЕТСЯ НЕМЕДЛЕННЫЙ РЕМОНТ!"
            
    elif worst_state[1] == "плохое":
        urgency = "ВЫСОКИЙ"
        color = "orange"
        bg_color = "#FFE6CC"
        
        if urgent_components:
            rec_list = "\n".join([f"• {name}" for name in urgent_components])
            recommendation = f"ТРЕБУЕТСЯ ПЛАНОВЫЙ РЕМОНТ В БЛИЖАЙШЕЕ ВРЕМЯ!\n\nКомпоненты для ремонта:\n{rec_list}"
        else:
            recommendation = "ТРЕБУЕТСЯ ПЛАНОВЫЙ РЕМОНТ В БЛИЖАЙШЕЕ ВРЕМЯ!"
            
    elif worst_state[1] == "удовлетворительное":
        urgency = "СРЕДНИЙ"
        color = "#FFD700"  # золотой
        bg_color = "#FFFFCC"
        recommendation = "РЕКОМЕНДУЕТСЯ УСИЛЕННЫЙ КОНТРОЛЬ И ПЛАНОВЫЙ ОСМОТР"
        
    elif worst_state[1] == "хорошее":
        urgency = "НИЗКИЙ"
        color = "lightgreen"
        bg_color = "#E6FFCC"
        recommendation = "СОСТОЯНИЕ ХОРОШЕЕ. ПРОДОЛЖАЙТЕ ТЕКУЩЕЕ ОБСЛУЖИВАНИЕ"
        
    else:
        urgency = "НИЗКИЙ"
        color = "green"
        bg_color = "#CCFFCC"
        recommendation = "СОСТОЯНИЕ ОТЛИЧНОЕ. ОБЪЕКТ НЕ ТРЕБУЕТ ВМЕШАТЕЛЬСТВА"
    
    # Сводка по состояниям
    summary_frame = ttk.Frame(rec_frame)
    summary_frame.pack(fill="x", pady=5)
    
    # Левая часть - статистика
    stats_frame = ttk.Frame(summary_frame)
    stats_frame.pack(side="left", fill="y", padx=10)
    
    ttk.Label(stats_frame, text=f"Всего компонентов: {len(components)}", 
             font=("Arial", 10, "bold")).pack(anchor="w")
    
    # Считаем компоненты по состояниям
    state_counts = {}
    for _, state, _, _ in component_states:
        state_counts[state] = state_counts.get(state, 0) + 1
    
    for state in ["аварийное", "плохое", "удовлетворительное", "хорошее", "отличное"]:
        if state in state_counts:
            count = state_counts[state]
            percent = (count / len(components)) * 100
            ttk.Label(stats_frame, 
                     text=f"• {state}: {count} комп. ({percent:.0f}%)", 
                     font=("Arial", 9)).pack(anchor="w")
    
    # Правая часть - рекомендации
    rec_text_frame = ttk.Frame(summary_frame)
    rec_text_frame.pack(side="right", fill="both", expand=True, padx=10)
    
    # Заголовок с цветным фоном
    header_frame = ttk.Frame(rec_text_frame)
    header_frame.pack(fill="x")
    
    header_label = ttk.Label(header_frame, text=f"УРОВЕНЬ СРОЧНОСТИ: {urgency}", 
                           font=("Arial", 11, "bold"))
    header_label.pack(pady=5)
    # Устанавливаем цвет текста
    header_label.configure(foreground=color)
    
    # Основная рекомендация
    rec_label = ttk.Label(rec_text_frame, text=recommendation, 
                         font=("Arial", 10, "bold"), wraplength=400, 
                         justify="left")
    rec_label.pack(pady=5, anchor="w")
    
    # Дополнительные рекомендации в зависимости от типа среды
    additional_frame = ttk.Frame(rec_text_frame)
    additional_frame.pack(fill="x", pady=10)
    
    if fluid_type == "oil":
        additional_recs = [
            "✓ Увеличить частоту отбора проб на содержание воды",
            "✓ Проверить эффективность ингибиторов коррозии",
            "✓ Контролировать скорость потока для минимизации эрозии"
        ]
    else:
        additional_recs = [
            "✓ Контролировать точку росы для предотвращения конденсации",
            "✓ Проверить работу осушителей газа",
            "✓ Мониторить содержание CO₂ для коррекции ингибирования"
        ]
    
    ttk.Label(additional_frame, text="Дополнительные меры:", 
             font=("Arial", 9, "bold")).pack(anchor="w")
    
    for rec in additional_recs:
        ttk.Label(additional_frame, text=rec, font=("Arial", 9)).pack(anchor="w", padx=10)

def create_economic_summary(parent_frame, sections_data, fluid_type):
    """Создаёт раздел экономической сводки для общего анализа"""
    econ_frame = ttk.LabelFrame(parent_frame, text="ЭКОНОМИЧЕСКАЯ СВОДКА", padding=15)
    econ_frame.pack(fill="x", padx=20, pady=10)

    # ЗАГОЛОВОК С КНОПКОЙ НАСТРОЙКИ
    header_frame = ttk.Frame(econ_frame)
    header_frame.pack(fill="x", pady=(0, 10))
    
    ttk.Label(header_frame, text="ЭКОНОМИЧЕСКИЕ РАСЧЕТЫ", 
              font=("Arial", 11, "bold")).pack(side="left")

    # ФРЕЙМ ДЛЯ КНОПОК СПРАВА
    buttons_frame = ttk.Frame(header_frame)
    buttons_frame.pack(side="right")
    
    # КНОПКА ЭКСПОРТА
    def open_export():
        """Функция для открытия диалога экспорта"""
        try:
            from utils.export import create_export_dialog
            root = tk._default_root
            if root:
                create_export_dialog(root, fluid_type, sections_data)
        except Exception as e:
            print(f"❌ Ошибка открытия диалога экспорта: {e}")
    
    export_btn = tk.Button(buttons_frame, text="Экспорт",
                          bg='#18171C', fg='#FADADD', font=("Arial", 9, "bold"),
                          relief='flat', borderwidth=0,
                          command=open_export)
    export_btn.pack(side="left", padx=(0, 10))
    
    # КНОПКА НАСТРОЙКИ ЦЕН
    def open_economics_dialog():
        """Функция для открытия настроек экономики"""
        try:
            from ui.economics_dialog import create_economics_settings_dialog
            root = tk._default_root
            if root:
                create_economics_settings_dialog(root)
        except Exception as e:
            print(f"❌ Ошибка открытия настроек: {e}")
    
    settings_btn = tk.Button(buttons_frame, text="Настроить цены",
                            bg='#18171C', fg='#FADADD', font=("Arial", 9, "bold"),
                            relief='flat', borderwidth=0,
                            command=open_economics_dialog)
    settings_btn.pack(side="left")

    summary = get_economic_summary(sections_data)
    
    # ТАБЛИЦА ЭКОНОМИКИ
    columns = ("Категория", "Кол-во участков", "Общая стоимость, руб")
    tree = ttk.Treeview(econ_frame, columns=columns, show="headings", height=6)

    for col in columns:
        tree.heading(col, text=col)
        tree.column(col, width=150)

    tree.insert("", "end", values=(
        "СРОЧНЫЙ ремонт", 
        f"{summary['urgent_count']} участков", 
        f"{summary['urgent_repair_cost']:,.0f}"
    ))

    tree.insert("", "end", values=(
        "ПЛАНОВЫЙ ремонт", 
        f"{summary['planned_count']} участков", 
        f"{summary['planned_repair_cost']:,.0f}"
    ))

    tree.insert("", "end", values=(
        "ОБЩАЯ стоимость", 
        f"{len(sections_data)} участков", 
        f"{summary['total_repair_cost']:,.0f}"
    ))

    tree.pack(fill="x", pady=10)

    # ТЕКСТОВАЯ СВОДКА
    if summary['urgent_count'] > 0:
        urgency_text = f"Требуется срочное финансирование: {summary['urgent_repair_cost']:,.0f} руб"
    else:
        urgency_text = "Срочный ремонт не требуется"

    ttk.Label(econ_frame, text=urgency_text, font=("Arial", 10, "bold")).pack(anchor="w", pady=5)

    # РЕКОМЕНДАЦИЯ ПО БЮДЖЕТУ
    budget_text = f"Рекомендуемый бюджет на ремонты: {summary['total_repair_cost']:,.0f} руб"
    ttk.Label(econ_frame, text=budget_text, font=("Arial", 10)).pack(anchor="w")
        
def create_general_analysis(parent, fluid_type, sections_data):
    """Создаёт общий анализ системы"""
    print(f"🔍 В create_general_analysis:")
    print(f"   fluid_type: {fluid_type}")
    print(f"   sections_data тип: {type(sections_data)}")
    print(f"   sections_data длина: {len(sections_data) if sections_data else 0}")
    
    if sections_data and len(sections_data) > 0:
        print(f"   Первый элемент тип: {type(sections_data[0])}")
        print(f"   Первый элемент: {sections_data[0].get('name', 'No name')}")
    
    # Проверяем, что есть данные для анализа
    if not sections_data:
        # НЕТ УЧАСТКОВ - показываем красивое сообщение
        message_frame = ttk.Frame(parent)
        message_frame.pack(fill="both", expand=True)
        
        message_label = ttk.Label(
            message_frame,
            text="Добавьте участки во вкладке 'Параметры'",
            font=("Arial", 16, "bold"),
            foreground="#666666"
        )
        message_label.pack(pady=40)
        
        info_label = ttk.Label(
            message_frame,
            text="Перейдите на вкладку 'Параметры', чтобы добавить новые участки трубопровода\nи рассчитать их состояние",
            font=("Arial", 12),
            foreground="#888888",
            justify="center"
        )
        info_label.pack(pady=10)
        
        separator = ttk.Separator(message_frame, orient="horizontal")
        separator.pack(fill="x", pady=30, padx=50)
        
        hint_label = ttk.Label(
            message_frame,
            text="Используйте кнопку 'Добавить участок' для создания нового участка",
            font=("Arial", 10, "italic"),
            foreground="#999999"
        )
        hint_label.pack(pady=10)
        return
    
    # Проверяем, что sections_data содержит словари
    if not all(isinstance(s, dict) for s in sections_data):
        # Создаем заглушку
        error_frame = ttk.Frame(parent)
        error_frame.pack(fill="both", expand=True)
        ttk.Label(error_frame, text="❌ Ошибка в данных участков", 
                font=("Arial", 14, "bold"), foreground="red").pack(pady=50)
        return
    
    # Основной фрейм с прокруткой
    main_frame = ttk.Frame(parent)
    main_frame.pack(fill="both", expand=True)
    
    canvas = tk.Canvas(main_frame)
    scrollbar = ttk.Scrollbar(main_frame, orient="vertical", command=canvas.yview)
    scrollable_frame = ttk.Frame(canvas)
    
    scrollable_frame.bind("<Configure>", lambda e: canvas.configure(scrollregion=canvas.bbox("all")))
    canvas.create_window((0, 0), window=scrollable_frame, anchor="nw")
    canvas.configure(yscrollcommand=scrollbar.set)
    canvas.pack(side="left", fill="both", expand=True)
    scrollbar.pack(side="right", fill="y")
    
    # Заголовок
    title_label = ttk.Label(scrollable_frame, text="ОБЩИЙ АНАЛИЗ СИСТЕМЫ", 
                           font=("Arial", 16, "bold"))
    title_label.pack(pady=20)
    
    # Сводная статистика
    stats_frame = ttk.LabelFrame(scrollable_frame, text="СВОДНАЯ СТАТИСТИКА", padding=15)
    stats_frame.pack(fill="x", padx=20, pady=10)
    
    total_sections = len(sections_data)
    total_components = 0
    
    for section in sections_data:
        components = section.get("components", [])
        total_components += len(components)
    
    # Подсчёт состояний
    from models.corrosion import get_corrosion_level
    status_counts = {"отличное": 0, "хорошее": 0, "удовлетворительное": 0, "плохое": 0, "аварийное": 0}
    
    # Считаем состояния по компонентам
    component_status_counts = {"отличное": 0, "хорошее": 0, "удовлетворительное": 0, "плохое": 0, "аварийное": 0}
    
    for section in sections_data:
        components = section.get("components", [])
        
        for component in components:
            # Получаем толщину компонента
            thickness = component.get("remaining", 
                                    component.get("thickness", 
                                                component.get("wall_thickness", 10)))
            level, _ = get_corrosion_level(thickness)
            component_status_counts[level] += 1
    
    # Преобразуем в сводное состояние участка (по худшему компоненту)
    for section in sections_data:
        components = section.get("components", [])
        if not components:
            continue
            
        # Находим худшее состояние среди компонентов
        worst_level = "отличное"
        for component in components:
            thickness = component.get("remaining", 
                                    component.get("thickness", 
                                                component.get("wall_thickness", 10)))
            level, _ = get_corrosion_level(thickness)
            
            # Определяем приоритет состояния
            priorities = {"аварийное": 0, "плохое": 1, "удовлетворительное": 2, "хорошее": 3, "отличное": 4}
            if priorities.get(level, 5) < priorities.get(worst_level, 5):
                worst_level = level
        
        status_counts[worst_level] += 1
    
    stats_text = (
        f"• Всего участков: {total_sections}\n"
        f"• Всего компонентов: {total_components}\n"
        f"• Отличное состояние: {status_counts['отличное']} участков ({component_status_counts['отличное']} комп.)\n"
        f"• Хорошее состояние: {status_counts['хорошее']} участков ({component_status_counts['хорошее']} комп.)\n"
        f"• Удовлетворительное: {status_counts['удовлетворительное']} участков ({component_status_counts['удовлетворительное']} комп.)\n"
        f"• Плохое: {status_counts['плохое']} участков ({component_status_counts['плохое']} комп.)\n"
        f"• Аварийное: {status_counts['аварийное']} участков ({component_status_counts['аварийное']} комп.)"
    )
    
    stats_label = ttk.Label(stats_frame, text=stats_text, font=("Arial", 11))
    stats_label.pack(anchor="w")
    
    # Рекомендации по системе
    rec_frame = ttk.LabelFrame(scrollable_frame, text="РЕКОМЕНДАЦИИ ПО СИСТЕМЕ", padding=15)
    rec_frame.pack(fill="x", padx=20, pady=10)
    
    if status_counts["аварийное"] > 0:
        recommendation = "СРОЧНЫЙ РЕМОНТ! Имеются аварийные участки, требующие немедленного вмешательства."
        color = "red"
    elif status_counts["плохое"] > 0:
        recommendation = "ПЛАНОВЫЙ РЕМОНТ! Имеются участки в плохом состоянии, требуется ремонт в ближайшее время."
        color = "orange"
    elif status_counts["удовлетворительное"] > 0:
        recommendation = "УСИЛЕННЫЙ КОНТРОЛЬ! Рекомендуется усилить мониторинг участков в удовлетворительном состоянии."
        color = "darkorange"
    else:
        recommendation = "СИСТЕМА В НОРМЕ! Все участки в хорошем или отличном состоянии. Продолжайте плановое обслуживание."
        color = "green"
    
    # Дополнительная информация
    if total_components > 0:
        recommendation += f"\n\nВсего в системе: {total_components} компонентов, из которых {component_status_counts['аварийное'] + component_status_counts['плохое']} требуют ремонта."
    
    rec_label = ttk.Label(rec_frame, text=recommendation, font=("Arial", 11), wraplength=800)
    rec_label.pack(anchor="w")
    rec_label.configure(foreground=color)

    create_economic_summary(scrollable_frame, sections_data, fluid_type)

def create_analysis_tab(parent, fluid_type, sections_data):
    """Создаёт вкладку анализа с внутренними вкладками"""
    tab = parent
    
    # Внутренние вкладки анализа
    analysis_notebook = ttk.Notebook(tab)
    
    def update_analysis():
        """Полностью пересоздаёт вкладки анализа"""      
        # Удаляем все существующие вкладки
        for tab_id in analysis_notebook.tabs():
            analysis_notebook.forget(tab_id)
        
        if not sections_data:
            # НЕТ УЧАСТКОВ - показываем красивое сообщение
            message_frame = ttk.Frame(analysis_notebook)
            message_frame.pack(fill="both", expand=True)
            
            message_label = ttk.Label(
                message_frame,
                text="Добавьте участки во вкладке 'Параметры'",
                font=("Arial", 16, "bold"),
                foreground="#666666"
            )
            message_label.pack(pady=40)
            
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
            separator.pack(fill="x", pady=30, padx=50)
            
            # Подсказка
            hint_label = ttk.Label(
                message_frame,
                text="Используйте кнопку 'Добавить участок' для создания нового участка",
                font=("Arial", 10, "italic"),
                foreground="#999999"
            )
            hint_label.pack(pady=10)
            
            analysis_notebook.add(message_frame, text="Нет данных")
            return
        elif not all(isinstance(s, dict) for s in sections_data):
            # Ошибка в данных
            error_frame = ttk.Frame(analysis_notebook)
            error_frame.pack(fill="both", expand=True)
            ttk.Label(error_frame, text="❌ Ошибка в данных участков", 
                     font=("Arial", 14, "bold"), foreground="red").pack(pady=50)
            analysis_notebook.add(error_frame, text="ОШИБКА")
            return
        
        # Пересоздаём вкладки с актуальными данными
        general_frame = ttk.Frame(analysis_notebook)
        create_general_analysis(general_frame, fluid_type, sections_data)
        analysis_notebook.add(general_frame, text="ОБЩИЙ АНАЛИЗ")
        
        # СОЗДАЕМ ВКЛАДКИ ДЛЯ КАЖДОГО УЧАСТКА
        for section in sections_data:
            if isinstance(section, dict):  
                section_frame = ttk.Frame(analysis_notebook)
                create_section_analysis(section_frame, section, fluid_type)
                # Сокращаем имя для вкладки
                tab_name = section["name"]
                if len(tab_name) > 20:
                    tab_name = tab_name[:17] + "..."
                analysis_notebook.add(section_frame, text=tab_name)
            else:
                print(f"❌ Пропускаем не-словарь: {section} (тип: {type(section)})")
    
    # ПЕРВОНАЧАЛЬНОЕ СОЗДАНИЕ ВКЛАДОК 
    if not sections_data:
        # НЕТ УЧАСТКОВ - показываем красивое сообщение
        message_frame = ttk.Frame(analysis_notebook)
        message_frame.pack(fill="both", expand=True)
        
        message_label = ttk.Label(
            message_frame,
            text="Добавьте участки во вкладке 'Параметры'",
            font=("Arial", 16, "bold"),
            foreground="#666666"
        )
        message_label.pack(pady=40)
        
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
        separator.pack(fill="x", pady=30, padx=50)
        
        # Подсказка
        hint_label = ttk.Label(
            message_frame,
            text="Используйте кнопку 'Добавить участок' для создания нового участка",
            font=("Arial", 10, "italic"),
            foreground="#999999"
        )
        hint_label.pack(pady=10)
        
        analysis_notebook.add(message_frame, text="Нет данных")
    elif not all(isinstance(s, dict) for s in sections_data):
        # Ошибка в данных
        error_frame = ttk.Frame(analysis_notebook)
        error_frame.pack(fill="both", expand=True)
        ttk.Label(error_frame, text="❌ Ошибка в данных участков", 
                 font=("Arial", 14, "bold"), foreground="red").pack(pady=50)
        analysis_notebook.add(error_frame, text="ОШИБКА")
    else:
        # 1. Общий анализ
        general_frame = ttk.Frame(analysis_notebook)
        create_general_analysis(general_frame, fluid_type, sections_data)
        analysis_notebook.add(general_frame, text="ОБЩИЙ АНАЛИЗ")
        
        # 2. Детальный анализ по участкам
        for section in sections_data:
            section_frame = ttk.Frame(analysis_notebook)
            create_section_analysis(section_frame, section, fluid_type)
            # Сокращаем имя для вкладки
            tab_name = section["name"]
            if len(tab_name) > 20:
                tab_name = tab_name[:17] + "..."
            analysis_notebook.add(section_frame, text=tab_name)
    
    analysis_notebook.pack(fill="both", expand=True)
    
    # Первоначальное обновление
    update_analysis()
    
    return tab, update_analysis
    
