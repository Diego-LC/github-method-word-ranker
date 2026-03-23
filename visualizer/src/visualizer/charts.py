"""Funciones auxiliares para generar graficos con Plotly.

Provee graficos reutilizables para la interfaz de Streamlit:
- Grafico de barras horizontal con el ranking de palabras.
"""

from __future__ import annotations

import plotly.graph_objects as go


def create_ranking_bar_chart(
    words: list[str],
    counts: list[float],
    top_n: int,
) -> go.Figure:
    """Crea un grafico de barras horizontal con el ranking de palabras.

    Las barras se ordenan de mayor a menor (la mas frecuente arriba).
    """
    # Invertir para que la palabra #1 quede arriba en el grafico.
    words_rev = list(reversed(words))
    counts_rev = list(reversed(counts))

    fig = go.Figure(
        go.Bar(
            x=counts_rev,
            y=words_rev,
            orientation="h",
            marker=dict(
                color=counts_rev,
                colorscale="Viridis",
                showscale=False,
            ),
            text=[f"{int(c):,}" for c in counts_rev],
            textposition="outside",
        )
    )

    fig.update_layout(
        title=dict(
            text=f"Top {top_n} palabras en nombres de funciones/metodos",
            font=dict(size=18),
        ),
        xaxis_title="Frecuencia",
        yaxis_title="Palabra",
        height=max(400, top_n * 32),
        margin=dict(l=100, r=60, t=60, b=40),
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
        font=dict(size=13),
    )

    return fig
