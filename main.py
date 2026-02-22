
#!/usr/bin/env python3
"""
Точка входа в приложение
"""
import os
import sys
import traceback

def main():
    """Основная функция запуска приложения"""
    try:
        print("=" * 60)
        print("🚀 ЗАПУСК ЦИФРОВОГО ДВОЙНИКА ТРУБОПРОВОДА")
        print("=" * 60)
        
        # Проверяем наличие необходимых папок
        required_folders = ['assets', 'assets/icons', 'assets/3D_models', 'locales']
        for folder in required_folders:
            if not os.path.exists(folder):
                os.makedirs(folder, exist_ok=True)
                print(f"📁 Создана папка: {folder}")
        
        # Запускаем интро
        from ui.intro_window import show_intro
        show_intro()
        
    except Exception as e:
        print(f"❌ КРИТИЧЕСКАЯ ОШИБКА: {e}")
        traceback.print_exc()
        input("Нажмите Enter для выхода...")
        sys.exit(1)

if __name__ == "__main__":
    main()
