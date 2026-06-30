from __future__ import annotations

import urllib.error

import pandas as pd
import streamlit as st

from internet_speed_meter import format_bytes, run_measurement


st.set_page_config(page_title="Internet Speed Meter", page_icon="🚀", layout="centered")
PRESET_URLS = [
    "https://speed.cloudflare.com/__down?bytes=10000000",
    "https://proof.ovh.net/files/10Mb.dat",
    "https://speedtest.tele2.net/10MB.zip",
]
DEFAULT_URL = PRESET_URLS[0]

st.title("🚀 Speed Test")
st.write("Нажмите кнопку и дождитесь завершения измерения.")

with st.expander("Настройки теста", expanded=False):
    preset_url = st.selectbox("Пресет URL", options=PRESET_URLS, index=0)
    url = st.text_input("URL файла для скачивания", value=preset_url)
    requests_count = st.slider("Количество запросов", min_value=3, max_value=30, value=10)
    timeout = st.slider("Таймаут запроса (сек)", min_value=5, max_value=120, value=30)
    retries = st.slider("Повторы при 429", min_value=0, max_value=5, value=2)
    pause_between_requests = st.slider("Пауза между запросами (сек)", min_value=0.0, max_value=3.0, value=0.8, step=0.1)

start_test = st.button("Начать тест", type="primary", use_container_width=True)

if start_test:
    progress_bar = st.progress(0, text="Подготовка...")
    status_placeholder = st.empty()

    def on_progress(current_index: int, total_count: int, elapsed_seconds: float, bytes_downloaded: int) -> None:
        percent = int((current_index / total_count) * 100)
        progress_bar.progress(
            percent,
            text=f"Запрос {current_index}/{total_count} | {elapsed_seconds:.3f} сек | {format_bytes(bytes_downloaded)}",
        )
        status_placeholder.info(f"Идет замер... шаг {current_index} из {total_count}")

    try:
        result = run_measurement(
            url=url.strip(),
            requests_count=int(requests_count),
            timeout=float(timeout),
            progress_callback=on_progress,
            max_retries=int(retries),
            pause_between_requests=float(pause_between_requests),
            fallback_urls=PRESET_URLS,
        )
    except urllib.error.HTTPError as exc:
        progress_bar.empty()
        if exc.code == 429:
            status_placeholder.error("Источник заблокировал тест (429) даже после повторов и fallback URL.")
        else:
            status_placeholder.error(f"HTTP ошибка: {exc}")
        st.stop()
    except urllib.error.URLError as exc:
        progress_bar.empty()
        status_placeholder.error(f"Ошибка запроса: {exc}")
        st.stop()
    except TimeoutError:
        progress_bar.empty()
        status_placeholder.error("Один из запросов превысил таймаут.")
        st.stop()
    except ValueError as exc:
        progress_bar.empty()
        status_placeholder.error(str(exc))
        st.stop()

    progress_bar.progress(100, text="Тест завершен")
    status_placeholder.success("Измерение завершено")

    st.subheader("Результат")
    speed_value = f"{result['speed_mib_s']:.3f} MB/s"
    st.markdown(f"## {speed_value}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Среднее время", f"{result['average_time_seconds']:.3f} сек")
    col2.metric("Объем данных", format_bytes(int(result["total_bytes"])))
    col3.metric("Всего запросов", str(result["requests_count"]))
    if result.get("fallback_used"):
        st.info(f"Первичный URL был ограничен, тест продолжен через: {result['effective_url']}")

    per_request = result["per_request"]
    rows = [
        {
            "Запрос": item["index"],
            "Время (сек)": round(float(item["elapsed_seconds"]), 4),
            "Данные (читаемо)": format_bytes(int(item["bytes_downloaded"])),
            "Источник": item["used_url"],
        }
        for item in per_request
    ]
    df = pd.DataFrame(rows)

    st.subheader("График времени ответа")
    st.line_chart(df.set_index("Запрос")["Время (сек)"])
    st.subheader("Детали по каждому запросу")
    st.dataframe(df, use_container_width=True, hide_index=True)

    st.caption("Формула: (общий объем байт / общее время сек) / (1024*1024)")
