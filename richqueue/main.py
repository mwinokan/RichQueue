from typer import Typer, Option
from typing import Optional
from typing_extensions import Annotated
from .layout import dual_layout
from rich.live import Live
import time
from .console import console
from .tools import curry
from .slurm import get_layout_pair, get_node_layout, get_hist_layout, get_job_layout

# set up singletons
app = Typer()

# main CLI command


@app.callback(invoke_without_command=True)
def show(
    user: Annotated[
        str, Option(help="Query jobs for this user. set to 'all' to see all jobs")
    ] = None,
    long: Annotated[bool, Option(help="More detailed output")] = False,
    idle: Annotated[bool, Option(help="Show available nodes")] = False,
    loop: Annotated[bool, Option(help="Show a live-updating screen")] = True,
    hist: Annotated[
        int, Option(help="Show historical jobs from the last X weeks")
    ] = None,
    hist_unit: Annotated[
        str, Option(help="Show historical jobs from the last X weeks")
    ] = "weeks",
    job: Annotated[int, Option(help="Show details for a specific job")] = None,
):

    screen = True
    disappear = not screen

    kwargs = {
        "user": user,
        "long": long,
        "idle": idle,
        "loop": loop,
        "hist": hist,
        "hist_unit": hist_unit,
        "screen": screen,
        "disappear": disappear,
        "job": job,
    }

    # console.print(kwargs)

    match (bool(idle), bool(hist), bool(job)):
        case (True, False, False):
            loop = False
            layout_func = get_node_layout
        case (False, True, False):
            loop = False
            layout_func = get_hist_layout
        case (False, False, True):
            layout_func = get_job_layout
        case (False, False, False):
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


@app.command()
def log(job: Annotated[int, Option(help="Show logs from a specific job")]):
    raise NotImplementedError


@app.command()
def dir(job: Annotated[int, Option(help="Get job directory")]):
    raise NotImplementedError


# start Typer app
def main():
    app()


# start Typer app
if __name__ == "__main__":
    app()
