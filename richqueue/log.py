import time

from rich.live import Live
from rich.panel import Panel
from rich.layout import Layout

from typing_extensions import Annotated
from typer import Typer, Argument, Option

from .console import console
from .layout import dual_layout
from .slurm import combined_df, get_user, PANEL_PADDING
from .table import job_table, log_table
from .tools import curry

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
    long: Annotated[bool, Option("-v", "--long", help="More detailed output")] = False,
    wisdom: Annotated[
        bool, Option("-w", "--wisdom", help="Show a confucius quote on exit")
    ] = False,
):

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
        return None

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
            if wisdom:
                from .wisdom import print_random_quote

                print_random_quote()


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


def guess_current_job(user: str, **kwargs):

    global JOB_DF
    JOB_DF = combined_df(user=user, **kwargs)

    assert len(JOB_DF), "No jobs found"

    pending = JOB_DF[JOB_DF["job_state"] == "PENDING"]
    running = JOB_DF[JOB_DF["job_state"] == "RUNNING"]
    history = JOB_DF[~JOB_DF["job_state"].isin(["PENDING", "RUNNING"])]

    # pick the single active job
    if len(running) == 1:
        return running.iloc[0]

    # pick the most recently submitted active job
    elif len(running) > 1:
        return running.sort_values(by="submit_time", ascending=False).iloc[0]

    # pick the single pending job
    elif len(pending) == 1:
        return pending.iloc[0]

    # pick the most recently submitted pending job
    elif len(pending) > 1:
        return pending.sort_values(by="submit_time", ascending=False).iloc[0]

    # pick the most recently submitted pending job
    else:
        return pending.sort_values(by="submit_time", ascending=False).iloc[0]

    return job


def get_specific_job(job: int, user: str, **kwargs):

    global JOB_DF
    JOB_DF = combined_df(user=user, **kwargs)

    assert len(JOB_DF), "No jobs found"

    matches = JOB_DF[JOB_DF["job_id"] == job]

    if not len(matches):
        console.print("[red bold]Could not find job with ID {job_id=}")
        return None

    elif len(matches) > 1:

        matches = matches[matches["command"].notna()]

        if len(matches) > 1:
            console.print(matches.to_dict(orient="records"))
            raise ValueError("Multiple job matches")

    return matches.iloc[0]


def main():
    app()


if __name__ == "__main__":
    main()
