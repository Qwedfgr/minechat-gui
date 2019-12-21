# Чат

Чат с графическим интерфейсом.

## Как установить

Для работы нужен Python версии не ниже 3.7.


```bash
pip install -r requirements.txt
```

## Как запустить
Пример установки переменных окружения можно посмотреть в файле ```env_example```
```.env
HOST=minechat.dvmn.org
READER_PORT=5000
WRITER_PORT=5050
NICKNAME=default nick
HISTORY=history.txt
TOKEN=TOKEN
```
Для запуска чата:
```bash
python main.py
```
Для запуска регистрации нового пользователя:
```bash
python registration.py
```
Токен будет сохранен в файл `.env`