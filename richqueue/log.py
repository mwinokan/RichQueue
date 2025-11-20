import sys
import time

from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout

from typing_extensions import Annotated
from typer import Typer, Argument, Option

from .console import console
from .layout import dual_layout
from .slurm import get_user, PANEL_PADDING
from .table import job_table, log_table
from .tools import curry
from .job import guess_current_job, get_specific_job

# access logs

JOB_DF = None

app = Typer()


@app.callback(invoke_without_command=True)
def show_log(
    job: Annotated[int, Argument(help="Show logs for this job")] = None,
    user: Annotated[
        str,
        Option(
            "-u",
            "--user",
            help="Query jobs for another user",
        ),
    ] = None,
    cwd: Annotated[
        bool,
        Option("-d", "--dir", help="Print job's current working directory and exit"),
    ] = False,
    install_jd: Annotated[
        bool, Option("--install-jd", help="Print function to create jd wrapper")
    ] = False,
    long: Annotated[bool, Option("-v", "--long", help="More detailed output")] = False,
):

    if install_jd:
        print(
            """
jd() { 
    target="$(res --dir "$@")"
    cd "$target" 
}
        """
        )
        sys.exit(0)

    if user is None:
        user = get_user()

    job_id = job

    if job_id is None:

        def job_getter():
            return guess_current_job(user=user)

    else:

        def job_getter():
            return get_specific_job(job=job_id, user=None)

    job = job_getter()

    if job is None:
        print("Could not get job")
        return None

    if cwd:
        cwd = job.get("current_working_directory")

        if not cwd:
            print("Could not get job's 'current_working_directory'")
            sys.exit(1)

        print(cwd)
        sys.exit(0)

    layout_func = curry(dual_layout, log_layout_pair)

    layout = layout_func(job_getter=job_getter, long=long)

    with Live(
        layout,
        refresh_per_second=1,
        screen=True,
        transient=True,
        vertical_overflow="visible",
    ) as live:

        try:
            while True:
                layout = layout_func(job_getter=job_getter, long=long)
                live.update(layout)
                time.sleep(1)
        except KeyboardInterrupt:
            live.stop()


def log_layout_pair(job_getter, **kwargs):
    job = job_getter()
    # console.print(job)

    upper = job_table(row=job, job=job.job_id, **kwargs)
    upper = Panel(upper, expand=False)

    limit = console.size.height - 2 * PANEL_PADDING - upper.renderable.row_count

    lower = log_table(
        job_id=job.job_id,
        stdout=job.standard_output,
        stderr=job.standard_error,
        limit=limit,
    )
    lower = Panel(lower, expand=False)

    return upper, lower


def main():
    app()


if __name__ == "__main__":
    main()
