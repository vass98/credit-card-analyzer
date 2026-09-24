import streamlit as st

# Validated categorical palette (light mode) -- see the dataviz skill's
# palette.md. Slot order is the CVD-safety mechanism; never reorder per-chart.
SLOTS = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300", "#4a3aa7", "#e34948"]
OTHER_GRAY = "#c3c2b7"
SURFACE = "#fcfcfb"
GRID = "#e1e0d9"
INK_PRIMARY = "#0b0b0b"
INK_SECONDARY = "#52514e"
INK_MUTED = "#898781"
STATUS = {"warning": "#fab219", "serious": "#ec835a", "critical": "#d03b3b", "good": "#0ca30c"}


def style_chart(fig, height=420):
    fig.update_layout(
        height=height,
        plot_bgcolor=SURFACE,
        paper_bgcolor=SURFACE,
        font=dict(family="system-ui, -apple-system, 'Segoe UI', sans-serif", color=INK_PRIMARY, size=13),
        margin=dict(l=10, r=10, t=30, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="left", x=0, font=dict(color=INK_SECONDARY)),
    )
    fig.update_xaxes(showgrid=True, gridcolor=GRID, gridwidth=1, zeroline=False, linecolor=GRID, tickfont=dict(color=INK_MUTED))
    fig.update_yaxes(showgrid=False, zeroline=False, linecolor=GRID, tickfont=dict(color=INK_MUTED))
    return fig


def stat_tile(label: str, value: str, accent: str):
    st.markdown(
        f"""
        <div style="border-left:4px solid {accent}; padding:0.4rem 0.9rem; background:{SURFACE};
                    border-radius:6px; box-shadow:0 1px 2px rgba(11,11,11,0.06);">
            <div style="color:{INK_MUTED}; font-size:0.8rem;">{label}</div>
            <div style="color:{INK_PRIMARY}; font-size:1.5rem; font-weight:600;">{value}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(accent: str, title: str, body: str):
    st.markdown(
        f"""
        <div style="border-left:4px solid {accent}; padding:0.6rem 1rem; background:{SURFACE};
                    border-radius:6px; box-shadow:0 1px 2px rgba(11,11,11,0.06); margin-bottom:0.6rem;">
            <div style="color:{INK_PRIMARY}; font-weight:600; margin-bottom:0.2rem;">{title}</div>
            <div style="color:{INK_SECONDARY}; font-size:0.92rem;">{body}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def category_tag(category: str, color: str):
    return (
        f'<span style="background:{color}22; color:{INK_PRIMARY}; border-left:3px solid {color}; '
        f'padding:2px 8px; border-radius:4px; font-size:0.85rem;">{category}</span>'
    )
