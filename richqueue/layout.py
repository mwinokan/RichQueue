
from rich.layout import Layout
from rich.panel import Panel
from rich.text import Text

def dual_layout(function, **kwargs):

    layout = Layout()

    upper, lower = function(**kwargs)

    upper = Layout(renderable=upper, name="upper")
    lower = Layout(renderable=lower, name="lower")

    # upper.size = panel1.renderable.row_count + 4
    # lower.size = panel2.renderable.row_count + 4
    # layout_height = upper.size + lower.size

    # if layout_height > console.size:
    #     LOG.append("Layout too big")

    layout.split_column(
        upper,
        lower,
    )

    return layout

def simple_layout():

    raise NotImplementedError