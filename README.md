# Internet Speed Meter

Python-скрипт для замера скорости интернета через последовательные HTTP-запросы к указанному URL (например, тяжелой картинке).

Скрипт:
- делает `N` последовательных запросов (по умолчанию `10`);
- дожидается полного ответа каждого запроса;
- считает среднее время запроса;
- считает общий объем скачанных данных;
- выводит приблизительную скорость в `MB/s`.

## Требования

- Python 3.9+ (внешние зависимости не нужны).

## Запуск

```bash
python internet_speed_meter.py "<URL_большого_файла>"
```

Пример:

```bash
python internet_speed_meter.py "https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg"
```

## Полезные параметры

- `-n`, `--requests` — количество запросов (по умолчанию `10`)
- `-t`, `--timeout` — таймаут одного запроса в секундах (по умолчанию `30`)

Пример:

```bash
python internet_speed_meter.py "https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg" -n 10 -t 60
```

## Интерпретация результата

- **Average request time** — среднее время одного запроса.
- **Total downloaded** — общий объем скачанных данных за все запросы.
- **Approximate speed** — средняя скорость загрузки в `MB/s` по формуле:

`(общий_объем_байт / общее_время_сек) / (1024*1024)`

## Публикация в GitHub

Если репозиторий еще не создан:

```bash
git init
git add .
git commit -m "Add internet speed meter script"
gh repo create internet-speed-meter --public --source . --remote origin --push
```

После этого репозиторий будет доступен по ссылке вида:

`https://github.com/<your-username>/internet-speed-meter`
