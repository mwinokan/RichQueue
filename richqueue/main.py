
from typer import Typer
from .layout import dual_layout
from rich.live import Live
import time
from .console import console
from .tools import curry
from .slurm import get_layout_pair

# set up singletons
app = Typer()

# main CLI command

@app.command()
def show(
    user: None | str = None, 
    long: bool = False, 
    idle: bool = False, 
    loop: bool = True,
    hist: int | None = None, 
    hist_unit: str = "weeks",
    screen: bool = True,
    disappear: bool = True,
):

    kwargs = {
        "user":user,
        "long":long,
        # "idle":idle,
        # "loop":loop,
        "hist":hist,
        "hist_unit":hist_unit,
        # "screen":screen,
        # "disappear":disappear,
    }

    console.print(kwargs)

    match (bool(idle), bool(hist)):
        case (True, False):
            # layout_func = idle_layout
            raise NotImplementedError
        case (False, True):
            # layout_func = hist_layout
            raise NotImplementedError
        case (False, False):
            layout_func = curry(dual_layout, get_layout_pair)
        case _:
            raise Exception("Unsupported CLI options")

    # live updating layout
    if loop:

        layout = layout_func(**kwargs)

        with Live(
            layout,
            refresh_per_second=4,
            screen=screen,
            transient=disappear,
            vertical_overflow="visible",
        ) as live:

            try:
                while True:
                    layout = layout_func(**kwargs)
                    live.update(layout)
                    time.sleep(1)
            except KeyboardInterrupt:
                live.stop()

    # static layout
    else:

        layout = layout_func(**kwargs)
        console.print(layout)

# start Typer app
def main():
    app()

# start Typer app
if __name__ == "__main__":
    app()