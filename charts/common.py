"""Thin plotly wrappers so every chart shares the same look."""
from __future__ import annotations

import pandas as pd
import plotly.express as px

HEIGHT = 380
MARGIN = dict(l=40, r=20, t=50, b=40)


def _finish(figure, title: str, x_title: str | None, y_title: str | None):
    figure.update_layout(
        title=title,
        height=HEIGHT,
        margin=MARGIN,
        legend_title_text="",
        hovermode="x unified",
    )
    if x_title:
        figure.update_xaxes(title_text=x_title)
    if y_title:
        figure.update_yaxes(title_text=y_title)
    return figure


def line(
    frame: pd.DataFrame,
    x: str,
    y,
    title: str,
    color: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
):
    figure = px.line(frame, x=x, y=y, color=color, markers=False)
    return _finish(figure, title, x_title, y_title)


def bar(
    frame: pd.DataFrame,
    x: str,
    y,
    title: str,
    color: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
    barmode: str = "stack",
):
    figure = px.bar(frame, x=x, y=y, color=color, barmode=barmode)
    return _finish(figure, title, x_title, y_title)


def scatter(
    frame: pd.DataFrame,
    x: str,
    y: str,
    title: str,
    color: str | None = None,
    x_title: str | None = None,
    y_title: str | None = None,
):
    figure = px.scatter(frame, x=x, y=y, color=color)
    figure.update_layout(hovermode="closest")
    return _finish(figure, title, x_title, y_title)


def pie(frame: pd.DataFrame, names: str, values: str, title: str):
    figure = px.pie(frame, names=names, values=values, hole=0.45)
    figure.update_layout(title=title, height=HEIGHT, margin=MARGIN)
    return figure
