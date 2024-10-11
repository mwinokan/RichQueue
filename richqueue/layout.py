from rich.layout import Layout
from rich.panel import Panel
from .slurm import PANEL_PADDING
from rich.text import Text


def dual_layout(function, **kwargs):

    layout = Layout()

    upper, lower = function(**kwargs)

    upper = Layout(renderable=upper, name="upper")
    lower = Layout(renderable=lower, name="lower")

    try:
        upper.size = upper.renderable.renderable.row_count + PANEL_PADDING
    except AttributeError:
        upper.size = 3 # + PANEL_PADDING

    try:
        lower.size = lower.renderable.renderable.row_count + PANEL_PADDING
    except AttributeError:
        lower.size = 3 # + PANEL_PADDING

    layout.split_column(
        upper,
        lower,
    )

    return layout


def simple_layout():

    raise NotImplementedError
