"""Interfaz de Streamlit para el ranking de palabras.

Lee datos agregados desde Redis (sorted set y hash) y renderiza:
- Metricas clave (total repos, total palabras, palabra #1).
- Grafico de barras horizontal con el top-N de palabras.
- Tabla con los datos del ranking.

Se refresca automaticamente cada UI_REFRESH_SECONDS segundos.
"""

from __future__ import annotations

import time

import streamlit as st

from visualizer.charts import create_ranking_bar_chart
from visualizer.redis_store import RedisStore
from visualizer.settings import load_settings

# -- Configuracion de la pagina --
st.set_page_config(
    page_title="GitHub Method Word Ranker",
    page_icon="📊",
    layout="wide",
)

# -- Cargar settings y store --
settings = load_settings()
store = RedisStore(settings)

# -- Titulo y descripcion --
st.title("📊 GitHub Method Word Ranker")
st.caption(
    "Ranking en tiempo casi real de las palabras mas usadas "
    "en nombres de funciones y metodos de Python y Java."
)

# -- Sidebar: parametros --
st.sidebar.header("⚙️ Parametros")
top_n = st.sidebar.slider(
    "Top N palabras",
    min_value=5,
    max_value=100,
    value=settings.top_n_default,
    step=5,
)

auto_refresh = st.sidebar.checkbox("Auto-refresh", value=True)

# -- Datos del ranking --
top_words = store.get_top_words(top_n)
stats = store.get_stats()
total_unique = store.get_total_words()

# -- Metricas --
col1, col2, col3, col4 = st.columns(4)

with col1:
    total_repos = int(stats.get("total_repos", "0"))
    st.metric("Repos procesados", f"{total_repos:,}")

with col2:
    st.metric("Palabras unicas", f"{total_unique:,}")

with col3:
    py_files = int(stats.get("total_python_files", "0"))
    java_files = int(stats.get("total_java_files", "0"))
    st.metric("Archivos analizados", f"{py_files + java_files:,}")

with col4:
    if top_words:
        st.metric("Palabra #1", top_words[0][0], f"{int(top_words[0][1]):,} usos")
    else:
        st.metric("Palabra #1", "—")

st.divider()

# -- Grafico y tabla --
if top_words:
    words = [w for w, _ in top_words]
    counts = [c for _, c in top_words]

    # Grafico de barras.
    fig = create_ranking_bar_chart(words, counts, top_n)
    st.plotly_chart(fig, use_container_width=True)

    # Tabla de datos.
    with st.expander("📋 Ver tabla de datos", expanded=False):
        table_data = [
            {"Posicion": i + 1, "Palabra": w, "Frecuencia": int(c)}
            for i, (w, c) in enumerate(top_words)
        ]
        st.table(table_data)
else:
    st.info(
        "⏳ Esperando datos del miner... "
        "El ranking se actualizara automaticamente cuando haya datos disponibles."
    )

# -- Info del ultimo repo --
last_repo = stats.get("last_repo", "")
if last_repo:
    last_stars = stats.get("last_repo_stars", "?")
    st.sidebar.divider()
    st.sidebar.subheader("🔎 Ultimo repo")
    st.sidebar.text(f"{last_repo}")
    st.sidebar.text(f"⭐ {last_stars} stars")

# -- Detalle de archivos --
if stats:
    st.sidebar.divider()
    st.sidebar.subheader("📁 Archivos por lenguaje")
    st.sidebar.text(f"Python:  {stats.get('total_python_files', '0')}")
    st.sidebar.text(f"Java:    {stats.get('total_java_files', '0')}")

# -- Auto-refresh --
if auto_refresh:
    time.sleep(settings.ui_refresh_seconds)
    st.rerun()
