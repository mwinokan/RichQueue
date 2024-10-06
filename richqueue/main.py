
from rich.console import Console
from typer import Typer
from .layout import dual_layout
from rich.live import Live
import time

# set up singletons
app = Typer()
console = Console()

@app.command()
def show(
    user: None | str = None, 
    long: bool = False, 
    idle: bool = False, 
    loop: bool = True,
    hist: int | None = None, 
    hist_unit: str = "weeks",
    screen: bool = True,
):

    kwargs = {
        "user":user,
        "long":long,
        "idle":idle,
        "loop":loop,
        "hist":hist,
        "hist_unit":hist_unit,
        "screen":screen,
    }

    console.print(kwargs)

    layout = dual_layout()

    console.print(layout)

    # loop = True

    # if hist:

    #     show_queue(user=user, command="sacct", long=long, hist=hist, hist_unit=hist_unit)

    # elif idle:
    #     idle_queue()

    match (bool(idle), bool(hist)):
        case (True, False):
            # layout_func = idle_layout
            pass
        case (False, True):
            # layout_func = hist_layout
            pass
        case (False, False):
            layout_func = dual_layout
        case _:
            raise Exception("Unsupported CLI options")

    # live updating layout
    if loop:

        layout = layout_func(**kwargs)

        with Live(
            layout,
            refresh_per_second=4,
            screen=screen,
            transient=True,
            vertical_overflow="visible",
        ) as live:
            try:
                while True:
                    layout = layout_func(**kwargs)
                    live.update(layout)
                    time.sleep(1)
            except KeyboardInterrupt:
                live.stop()
                pass

    # static layout
    else:

        layout = layout_func(**kwargs)
        console.print(layout)

def main():
    app()

if __name__ == "__main__":
    app()
