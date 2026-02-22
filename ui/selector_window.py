"""Окно выбора типа среды (нефть/газ)"""
import tkinter as tk
from ui.main_window import show_main_window
import os
import sys

def show_selector():
    """Показывает окно выбора типа среды"""
    root_selector = tk.Tk()
     # Простой способ - ищем иконку относительно текущей директории
    icon_path = "assets/icon1.ico"
    if not os.path.exists(icon_path):
        # Пробуем на уровень выше
        icon_path = "../assets/icon1.ico"
    
    if os.path.exists(icon_path):
        try:
            root_selector.iconbitmap(icon_path)
            print(f"✅ Иконка загружена: {icon_path}")
        except Exception as e:
            print(f"❌ Ошибка иконки: {e}")
        
    root_selector.title("РОСНЕФТЬ")
    root_selector.geometry("400x300")
    root_selector.configure(bg='#4F273A')  
    
    fluid_type = [None]  # Храним выбор
    
    def choose_oil():
        fluid_type[0] = "oil"
        root_selector.destroy()
        show_main_window(fluid_type[0])
        
    def choose_gas():
        fluid_type[0] = "gas" 
        root_selector.destroy()
        show_main_window(fluid_type[0])
    
    label = tk.Label(root_selector, text="ВЫБЕРИТЕ ТИП СРЕДЫ:", 
                    font=("Arial", 14, "bold"), bg='#4F273A', fg="#FADADD",  pady=30)
    label.pack()
    
    btn_oil = tk.Button(root_selector, text="НЕФТЬ", command=choose_oil, 
                       width=15, height=2, bg='#18171C', fg="#FADADD", 
                       font=("Arial", 12))
    btn_oil.pack(pady=10)
    
    btn_gas = tk.Button(root_selector, text="ГАЗ", command=choose_gas,
                       width=15, height=2, bg='#18171C', fg="#FADADD", 
                       font=("Arial", 12)) 
    btn_gas.pack(pady=10)
    
    root_selector.eval('tk::PlaceWindow . center')
    root_selector.mainloop()
    
    return fluid_type[0]
