# Internet Speed Meter

Проект для замера скорости интернета:
- CLI-скрипт;
- визуальное веб-приложение на Streamlit.

Измерение происходит через последовательные HTTP-запросы к указанному URL (например, тяжелой картинке).

## Требования

- Python 3.9+
- для визуального приложения: зависимости из `requirements.txt`

## Запуск CLI

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
- `--retries` — число повторов при ответе `429 Too Many Requests` (по умолчанию `2`)
- `--pause` — пауза между запросами в секундах (по умолчанию `0.8`)

Пример:

```bash
python internet_speed_meter.py "https://upload.wikimedia.org/wikipedia/commons/3/3f/Fronalpstock_big.jpg" -n 10 -t 60
```

## Интерпретация результата

- **Average request time** — среднее время одного запроса.
- **Total downloaded** — общий объем скачанных данных за все запросы.
- **Approximate speed** — средняя скорость загрузки в `MB/s` по формуле:

`(общий_объем_байт / общее_время_сек) / (1024*1024)`

## Визуальное приложение (Streamlit)

Установка зависимостей:

```bash
pip install -r requirements.txt
```

Запуск UI:

```bash
streamlit run app.py
```

Быстрый запуск по двойному клику:

- откройте `start_speedtest.py` двойным кликом (или командой ниже);
- скрипт сам запустит Streamlit и откроет браузер.

```bash
python start_speedtest.py
```

Для Windows также добавлен `start_speedtest.bat`:
- двойной клик по `start_speedtest.bat` запускает приложение сразу.
- если `streamlit` не установлен, `.bat` автоматически поставит зависимости из `requirements.txt`.

В приложении можно:
- указать URL файла;
- выбрать один из стабильных пресетов URL;
- выбрать число запросов и таймаут;
- настроить повторы при `429`;
- настроить паузу между запросами;
- получить итоговые метрики (среднее время, объем, MB/s);
- посмотреть таблицу и график по каждому запросу.
