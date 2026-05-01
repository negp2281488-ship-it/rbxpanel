import sys
import os
import argparse

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    import crypto_utils
except ImportError:
    print("❌ Ошибка: Не удалось импортировать модуль crypto_utils")
    print("Убедитесь, что файл crypto_utils.py находится в той же директории")
    sys.exit(1)

def decode_cookie(encrypted_cookie):
    try:
        decrypted = crypto_utils.decrypt_cookie(encrypted_cookie)
        return decrypted
    except Exception as e:
        return f"❌ Ошибка расшифровки: {str(e)}"

def decode_from_file(file_path):
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            encrypted_cookie = f.read().strip()
        return decode_cookie(encrypted_cookie)
    except FileNotFoundError:
        return f"❌ Файл не найден: {file_path}"
    except Exception as e:
        return f"❌ Ошибка чтения файла: {str(e)}"

def main():
    parser = argparse.ArgumentParser(
        description='Расшифровка зашифрованных cookies',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Примеры использования:

1. Расшифровать cookie из командной строки:
   python decode_cookie.py "gAAAAABh..."

2. Расшифровать cookie из файла:
   python decode_cookie.py --file cookies/1234567890_1234567890.txt

3. Интерактивный режим:
   python decode_cookie.py --interactive

4. Расшифровать несколько cookies из файла (каждая на новой строке):
   python decode_cookie.py --file cookies.txt --multiple
        """
    )
    
    parser.add_argument(
        'cookie',
        nargs='?',
        help='Зашифрованная cookie для расшифровки'
    )
    
    parser.add_argument(
        '--file', '-f',
        help='Путь к файлу с зашифрованной cookie'
    )
    
    parser.add_argument(
        '--interactive', '-i',
        action='store_true',
        help='Интерактивный режим'
    )
    
    parser.add_argument(
        '--multiple', '-m',
        action='store_true',
        help='Расшифровать несколько cookies (каждая на новой строке)'
    )
    
    parser.add_argument(
        '--output', '-o',
        help='Сохранить результат в файл'
    )
    
    args = parser.parse_args()
    
    if args.interactive:
        print("🔐 Режим расшифровки cookies")
        print("=" * 50)
        print("Введите зашифрованную cookie (или 'exit' для выхода):")
        print()
        
        while True:
            try:
                encrypted = input("> ").strip()
                
                if encrypted.lower() in ['exit', 'quit', 'q']:
                    print("Выход...")
                    break
                
                if not encrypted:
                    continue
                
                decrypted = decode_cookie(encrypted)
                print(f"✅ Расшифрованная cookie:")
                print(decrypted)
                print()
                print("-" * 50)
                print()
                
            except KeyboardInterrupt:
                print("\n\nВыход...")
                break
            except Exception as e:
                print(f"❌ Ошибка: {str(e)}")
                print()
        
        return
    
    if args.file:
        if args.multiple:
            try:
                with open(args.file, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                results = []
                for i, line in enumerate(lines, 1):
                    encrypted = line.strip()
                    if not encrypted:
                        continue
                    
                    print(f"Расшифровка cookie #{i}...")
                    decrypted = decode_cookie(encrypted)
                    results.append(f"=== Cookie #{i} ===\n{decrypted}\n\n")
                    print(f"✅ Cookie #{i} расшифрована\n")
                
                output = "".join(results)
                
                if args.output:
                    with open(args.output, 'w', encoding='utf-8') as f:
                        f.write(output)
                    print(f"✅ Результаты сохранены в {args.output}")
                else:
                    print("=" * 50)
                    print(output)
                    
            except FileNotFoundError:
                print(f"❌ Файл не найден: {args.file}")
                sys.exit(1)
            except Exception as e:
                print(f"❌ Ошибка: {str(e)}")
                sys.exit(1)
        else:
            decrypted = decode_from_file(args.file)
            
            if args.output:
                with open(args.output, 'w', encoding='utf-8') as f:
                    f.write(decrypted)
                print(f"✅ Результат сохранен в {args.output}")
            else:
                print("=" * 50)
                print("✅ Расшифрованная cookie:")
                print("=" * 50)
                print(decrypted)
        
        return
    
    if args.cookie:
        decrypted = decode_cookie(args.cookie)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(decrypted)
            print(f"✅ Результат сохранен в {args.output}")
        else:
            print("=" * 50)
            print("✅ Расшифрованная cookie:")
            print("=" * 50)
            print(decrypted)
        
        return
    
    parser.print_help()

if __name__ == '__main__':
    main()

