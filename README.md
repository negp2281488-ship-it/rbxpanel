# RBXPanel

Панель состоит из двух Python-сервисов:

- `site/` - Flask-сайт и админ-панель.
- `roblox_api/` - локальный API-сервис на порту `8081`.

## Что не хранится в репозитории

Секреты, базы и рабочие файлы исключены через `.gitignore`:

- `.env`, `.secret_key`, `.session_nonce`, `.encryption_salt`
- `admin_password.json`, `admin_panel.db`
- `proxies.txt`
- `__pycache__/`, `logs/`

Пустая база создаётся автоматически при первом запуске `site/database.py`.

## Быстрый запуск на Windows

1. Установите Python 3.10+.
2. Установите зависимости:

```powershell
cd roblox_api
pip install -r requirements.txt

cd ..\site
pip install -r requirements.txt
```

3. Создайте локальный конфиг:

```powershell
cd ..\site
Copy-Item .env.example .env
notepad .env
```

Минимально нужно задать:

```env
ADMIN_PASSWORD=change-me
BOT_TOKEN=
CHAT_IDS=
```

4. Запустите сервисы:

```powershell
cd ..
.\start.bat
```

## Быстрый запуск на Linux

```bash
cd roblox_api
python3 -m venv venv
./venv/bin/pip install -r requirements.txt

cd ../site
python3 -m venv venv
./venv/bin/pip install -r requirements.txt
cp .env.example .env
nano .env
```

Запуск без systemd:

```bash
cd ..
./start.sh
```

Установка через systemd:

```bash
sudo bash setup.sh
```

## Переменные окружения

| Переменная | Обязательная | Назначение |
| --- | --- | --- |
| `ADMIN_PASSWORD` | Да, при первом запуске | Пароль админ-панели, из него будет создан локальный hash |
| `ADMIN_PASSWORD_HASH` | Альтернатива | Готовый bcrypt hash пароля |
| `ADMIN_USERNAME` | Нет | Логин админ-панели, по умолчанию `admin` |
| `SECRET_KEY` | Нет | Секрет Flask-сессий, если пусто - создаётся локальный `.secret_key` |
| `ENCRYPTION_SECRET` | Нет | Секрет шифрования cookies, если пусто - используется `SECRET_KEY` |
| `BOT_TOKEN` | Нет | Токен Telegram-бота |
| `CHAT_IDS` | Нет | ID чатов через запятую |
| `API_URL` | Нет | URL API-проверки, по умолчанию `http://127.0.0.1:8081/api/v1/check` |

## Сброс базы

Чтобы пересоздать пустую базу:

```powershell
Remove-Item site\admin_panel.db -Force -ErrorAction SilentlyContinue
cd site
python -c "import database"
```

Проверка, что таблицы пустые:

```powershell
python -c "import sqlite3; c=sqlite3.connect('admin_panel.db'); cur=c.cursor(); print(cur.execute('SELECT COUNT(*) FROM valid_cookies').fetchone()[0]); print(cur.execute('SELECT COUNT(*) FROM daily_stats').fetchone()[0]); print(cur.execute('SELECT COUNT(*) FROM all_requests').fetchone()[0]); c.close()"
```

Ожидаемый вывод:

```text
0
0
0
```

## Админ-панель

Путь админ-панели задаётся в `site/config.py` через `ADMIN_URL_PATH`.

По умолчанию:

```text
/ljsdkjfsldkajfksdjflkjsdf
```

## Проверка перед публикацией

Перед пушем на GitHub проверьте, что в выдаче нет секретов:

```powershell
rg -n -i "(token|api_key|secret|password|bearer|authorization|private_key|client_secret)" .
```

В репозиторий должны попадать только исходники, шаблоны и `.env.example`.
