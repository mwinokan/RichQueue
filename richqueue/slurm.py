from typer import Typer
import json
import datetime
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from pandas import DataFrame

console = Console()

METADATA = {}

app = Typer()

def color_by_state(state):

    if state == "RUNNING":
        return "[bold bright_green]Running"
    elif state == "PENDING":
        return "[bright_yellow]Pending"
    elif state == "CANCELLED":
        return "[orange3]Cancelled"
    elif state == "FAILED":
        return "[bold bright_red]Failed"
    elif state == "COMPLETED":
        return "[bold bright_green]Completed"
    else:
        return state

def extract_inner(df, key, inner):

    def _inner(x):
        d = x[key] 
        if "set" in d:
            if d["set"]:
                return d[inner]
            else:
                return None
        else:
            return d[inner]

    df[key] = df.apply(_inner, axis=1)

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

    num_nodes = "node_count" in df.columns
    num_cores = "cpus" in df.columns
    start_time = "start_time" in df.columns

    table = Table(title=title, box=box, header_style="")

    table.add_column(
        "[bold underline]Job Id", justify="right", style="bold", no_wrap=True
    )
    table.add_column(
        "[underline cyan]Job Name", justify="left", style="cyan", no_wrap=False
    )
    if num_nodes:
        table.add_column(
            "[underline magenta]#N", justify="right", style="magenta", no_wrap=True
        )
    if num_cores:
        table.add_column(
            "[underline magenta]#C", justify="right", style="magenta", no_wrap=True
        )

    if long and start_time:
        table.add_column(
            "[underline dodger_blue2]Start Time",
            justify="right",
            style="dodger_blue2",
            no_wrap=True,
        )

    if start_time:
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
        "[underline bold]State", justify="left", style=None, no_wrap=True
    )

    for i, row in df.iterrows():

        if start_time:
            start_time = human_datetime(row.start_time)
            run_time = human_timedelta(datetime.datetime.now() - row.start_time)

        values = [row.job_id, row["name"]]

        if num_nodes:
            values.append(row.node_count)
        if num_cores:
            values.append(row.cpus)

        if long and start_time:
            values.append(start_time)

        if start_time:
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

    command = "squeue"

    global METADATA

    METADATA = {
        "cluster_name": payload["meta"]["slurm"]["cluster"],
        "user": payload["meta"]["client"]["user"],
        "group": payload["meta"]["client"]["group"],
    }

    # parse payload
    df = DataFrame(payload["jobs"])

    # filter columns

    columns = COLUMNS[command]

    try:
        df = df[columns]

    except KeyError:

        for key in columns:
            if key not in df.columns:
                raise KeyError(key)

    extract_inner(df, "cpus", "number")
    extract_inner(df, "node_count", "number")
    extract_inner(df, "cpus_per_task", "number")
    extract_inner(df, "threads_per_core", "number")

    extract_time(df, "end_time")
    extract_time(df, "start_time")
    extract_time(df, "submit_time")
    extract_time(df, "time_limit")

    extract_list(df, "job_state")

    return df

def parse_sacct_json(payload: dict) -> "DataFrame":

    command = "sacct"

    global METADATA

    METADATA.update({
        "cluster_name": payload["meta"]["slurm"]["cluster"],
        "user": payload["meta"]["client"]["user"],
        "group": payload["meta"]["client"]["group"],
    })

    # parse payload
    df = DataFrame(payload["jobs"])

    # filter columns

    columns = COLUMNS[command]

    try:
        df = df[columns]

    except KeyError:

        for key in columns:
            if key not in df.columns:
                raise KeyError(key)

    df = df.rename(columns={"user":"user_name", "state":"job_state"})

    extract_inner(df, "job_state", "current")

    # extract_number(df, "cpus")
    # extract_number(df, "node_count")
    # extract_number(df, "cpus_per_task")
    # extract_number(df, "threads_per_core")

    # extract_time(df, "end_time")
    # extract_time(df, "start_time")
    # extract_time(df, "submit_time")
    # extract_time(df, "time_limit")

    extract_list(df, "job_state")

    df = df[df["job_state"] != "RUNNING"]

    return df

def show_queue(
    command: str,
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
        s_command = f"{command} -u {user} --json"
    else:
        s_command = f"{command} --json"

    x = subprocess.Popen([s_command], shell=True, stdout=subprocess.PIPE)
    output = x.communicate()

    payload = json.loads(output[0])

    parser = PARSERS[command]

    df = parser(payload)

    cluster = METADATA["cluster_name"]

    if command == "sacct":
        title = f"[bold]{user}'s history on {cluster}"

    elif user:
        df = df[df["user_name"] == user]
        title = f"[bold]{user}'s jobs on {cluster}"
    else:
        title = f"[bold]jobs on {cluster}"

    return job_table(df, title=title, long=long, return_table=return_table, box=box)

def dual_layout(
    user: None | str = None,
    long: bool = False,
    return_table: bool = True,
    box: bool = False,
):

    layout = Layout()

    panel1 = show_queue(user=user, command="squeue", long=long, return_table=True)
    panel2 = show_queue(user=user, command="sacct", long=long, return_table=True)

    upper = Layout(renderable=panel1, name="upper")
    lower = Layout(renderable=panel2, name="lower")

    upper.size = panel1.renderable.row_count+4
    lower.size = panel2.renderable.row_count+4

    layout.split_column(
        upper,
        lower,
    )

    if not return_table:
        console.print(layout)
    else:
        return layout

@app.command()
def show(user: None | str = None, long: bool = False):

    loop = True

    if loop:

        from rich.live import Live
        import time

        layout = dual_layout(user=user, long=long)

        with Live(layout, refresh_per_second=4, screen=True) as live:
            while True:

                layout = dual_layout(user=user, long=long)
                live.update(layout)

                time.sleep(1)

    else:
        layout = dual_layout(user=user, long=long)
        console.print(layout)
        # show_queue(command="squeue", user=user, long=long)
        # show_queue(command="sacct", user=user, long=long)


def main():
    app()
    
PARSERS = {"squeue":parse_squeue_json, "sacct":parse_sacct_json}

COLUMNS = {
"sacct":[
    "job_id",
    "state",
    "name",
    "nodes",
    "partition",
    "user",
],

"squeue":[
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
]}


if __name__ == "__main__":
    app()
