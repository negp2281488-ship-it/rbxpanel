import os
import sys

def check_files():
    print("Проверка файлов...")
    
    required_files = [
        'app.py',
        'database.py',
        'auth.py',
        'config.py',
        'requirements.txt',
        'templates/admin_login.html',
        'templates/admin_dashboard.html',
        'templates/admin_cookies.html',
        'templates/admin_settings.html'
    ]
    
    missing = []
    for file in required_files:
        if not os.path.exists(file):
            missing.append(file)
    
    if missing:
        print(f"Отсутствуют файлы: {', '.join(missing)}")
        return False
    
    print("ОК\n")
    return True

def init_database():
    print("Инициализация базы данных...")
    try:
        import database
        print("ОК\n")
        return True
    except Exception as e:
        print(f"Ошибка: {e}\n")
        return False

def init_auth():
    print("Инициализация авторизации...")
    try:
        import config
        import auth
        print("ОК\n")
        return True
    except Exception as e:
        print(f"Ошибка: {e}\n")
        return False

def create_cookies_dir():
    print("Проверка директории cookies/...")
    try:
        if not os.path.exists('cookies'):
            os.makedirs('cookies')
        print("ОК\n")
        return True
    except Exception as e:
        print(f"Ошибка: {e}\n")
        return False

def check_dependencies():
    print("Проверка зависимостей...")
    
    dependencies = ['flask', 'requests']
    missing = []
    
    for dep in dependencies:
        try:
            __import__(dep)
        except ImportError:
            missing.append(dep)
    
    if missing:
        print(f"Установите: pip install {' '.join(missing)}")
        return False
    
    print("ОК\n")
    return True

def print_summary():
    print("\n" + "="*60)
    print("Админ панель инициализирована")
    print("="*60)
    print("\nURL: http://localhost/ljsdkjfsldkajfksdjflkjsdf")
    print("Логин: задайте через ADMIN_USERNAME")
    print("Пароль: задайте через ADMIN_PASSWORD или ADMIN_PASSWORD_HASH")
    print("\n" + "="*60)

def main():
    print("\n" + "="*60)
    print("ИНИЦИАЛИЗАЦИЯ АДМИН ПАНЕЛИ")
    print("="*60 + "\n")
    
    steps = [
        ("Проверка файлов", check_files),
        ("Проверка зависимостей", check_dependencies),
        ("Инициализация базы данных", init_database),
        ("Инициализация авторизации", init_auth),
        ("Создание директории для куков", create_cookies_dir)
    ]
    
    for step_name, step_func in steps:
        if not step_func():
            print(f"\nОшибка на этапе: {step_name}")
            sys.exit(1)
    
    print_summary()

if __name__ == '__main__':
    main()
