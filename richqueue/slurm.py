from typer import Typer
import json
import datetime
from rich.console import Console
from rich.panel import Panel

console = Console()

METADATA = {}

SQUEUE_COLUMNS = [
    "command",
    "cpus_per_task",
    "dependency",
    "derived_exit_code",
    "end_time",
    "group_name",
    "job_id",
    "job_state",
    "name",
    "nodes",
    "node_count",
    "cpus",
    "tasks",
    "partition",
    "memory_per_cpu",
    "memory_per_node",
    "qos",
    "restart_cnt",
    "requeue",
    "exclusive",
    "start_time",
    "standard_error",
    "standard_output",
    "submit_time",
    "time_limit",
    "threads_per_core",
    "user_name",
    "current_working_directory",
]

app = Typer()


def color_by_state(state):

    if state == "RUNNING":
        return "[bright_green]Running"
    elif state == "PENDING":
        return "[bright_yellow]Running"
    else:
        return state


def job_table(
    df,
    title: str = "jobs",
    long: bool = False,
    return_table: bool = False,
    box: bool = False,
    panel: bool = True,
):

    from rich.table import Table

    if box:
        from rich.box import SIMPLE

        box = SIMPLE

    from .tools import human_timedelta, human_datetime

    table = Table(title=title, box=box, header_style="")

    table.add_column(
        "[bold underline]Job Id", justify="right", style="bold", no_wrap=True
    )
    table.add_column(
        "[underline cyan]Job Name", justify="left", style="cyan", no_wrap=False
    )
    table.add_column(
        "[underline magenta]#N", justify="right", style="magenta", no_wrap=True
    )
    table.add_column(
        "[underline magenta]#C", justify="right", style="magenta", no_wrap=True
    )

    if long:
        table.add_column(
            "[underline dodger_blue2]Start Time",
            justify="right",
            style="dodger_blue2",
            no_wrap=True,
        )

    table.add_column(
        "[underline dodger_blue2]Run Time",
        justify="right",
        style="dodger_blue2",
        no_wrap=True,
    )

    if long:
        table.add_column(
            "[underline green_yellow]Partition",
            justify="right",
            style="green_yellow",
            no_wrap=True,
        )
        table.add_column(
            "[underline green_yellow]Nodes",
            justify="left",
            style="green_yellow",
            no_wrap=False,
        )

    table.add_column(
        "[underline bold]State", justify="left", style="bold", no_wrap=True
    )

    for i, row in df.iterrows():

        start_time = human_datetime(row.start_time)
        run_time = human_timedelta(datetime.datetime.now() - row.start_time)

        values = [row.job_id, row["name"], row.node_count, row.cpus]

        if long:
            values.append(start_time)

        values.append(run_time)

        if long:
            values += [row.partition, row.nodes]

        values.append(color_by_state(row.job_state))

        table.add_row(*[str(v) for v in values])

    if panel:
        table = Panel(table, expand=False)

    if return_table:
        return table

    console.print(table)


def parse_squeue_json(payload: dict) -> "DataFrame":

    from pandas import DataFrame

    global METADATA

    METADATA = {
        "cluster_name": payload["meta"]["slurm"]["cluster"],
        "user": payload["meta"]["client"]["user"],
        "group": payload["meta"]["client"]["group"],
    }

    # parse payload
    df = DataFrame(payload["jobs"])

    # filter columns
    df = df[SQUEUE_COLUMNS]

    def extract_number(df, key):

        def inner(x):
            if x[key]["set"]:
                return x[key]["number"]
            else:
                return None

        df[key] = df.apply(inner, axis=1)

    def extract_time(df, key):
        df[key] = df.apply(
            lambda x: datetime.datetime.fromtimestamp(x[key]["number"]), axis=1
        )

    def extract_list(df, key):
        def inner(x):
            if len(x[key]) == 1:
                return x[key][0]
            else:
                return x[key]

        df[key] = df.apply(inner, axis=1)

    extract_number(df, "cpus")
    extract_number(df, "node_count")
    extract_number(df, "cpus_per_task")
    extract_number(df, "threads_per_core")

    extract_time(df, "end_time")
    extract_time(df, "start_time")
    extract_time(df, "submit_time")
    extract_time(df, "time_limit")

    extract_list(df, "job_state")

    return df


def show_queue(
    user: None | str = None,
    long: bool = False,
    return_table: bool = False,
    box: bool = False,
):

    import subprocess

    if user == "all":
        user = None
    elif user is None:
        x = subprocess.Popen(["whoami"], shell=True, stdout=subprocess.PIPE)
        output = x.communicate()
        user = output[0].strip().decode("utf-8")

    if user:
        command = f"squeue -u {user} --json"
    else:
        command = f"squeue --json"

    x = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE)
    output = x.communicate()

    squeue = json.loads(output[0])

    df = parse_squeue_json(squeue)

    cluster = METADATA["cluster_name"]

    if user:
        df = df[df["user_name"] == user]
        title = f"[bold]{user}'s jobs on {cluster}"
    else:
        title = f"[bold]jobs on {cluster}"

    return job_table(df, title=title, long=long, return_table=return_table, box=box)


@app.command()
def show(user: None | str = None, long: bool = False, loop: bool = False):

    if loop:

        from rich.live import Live
        import time

        table = show_queue(user=user, long=long, return_table=True)

        with Live(table, refresh_per_second=4, screen=True) as live:
            while True:
                live.update(show_queue(user=user, long=long, return_table=True))
                time.sleep(1)

    else:
        show_queue(user=user, long=long)


def main():

    squeue = json.load(open("../example_data/squeue.json"))

    parse_squeue_json(squeue)


if __name__ == "__main__":
    app()
