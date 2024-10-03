from typer import Typer
import json
import datetime
from rich.console import Console
from rich.panel import Panel
from rich.layout import Layout
from pandas import DataFrame
import subprocess

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

def color_by_node_state(state):

    if state == "ALLOCATED":
        return "[orange1]Allocated"
    elif state == "MIXED":
        return "[bright_yellow]Mixed"
    elif state == "IDLE":
        return "[bright_green]Idle"
    else:
        return f"[red]{state}"

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


def extract_sacct_times(df):
    df["start_time"] = df.apply(
        lambda x: datetime.datetime.fromtimestamp(x["time"]["start"]), axis=1
    )
    df["end_time"] = df.apply(
        lambda x: datetime.datetime.fromtimestamp(x["time"]["end"]), axis=1
    )
    df["submit_time"] = df.apply(
        lambda x: datetime.datetime.fromtimestamp(x["time"]["submission"]), axis=1
    )


def extract_list(df, key):
    def inner(x):
        if len(x[key]) == 1:
            return x[key][0]
        else:
            return x[key]

    df[key] = df.apply(inner, axis=1)

def mem_string(mb):
    
    # gb, mb = divmod(mb, 1024)

    # return f"{gb}G {mb}M"

    return f"{mb/1024:.0f}G"

def node_table(
    df,
    title: str = None,
    box: bool = False,
    panel: bool = True,
    idle: bool = True,
):

    if idle:
        df = df[df["node"].isin(["IDLE", "MIXED"])]
        title = title or "idle nodes" 
    else:
        title = title or "nodes"

    from rich.table import Table

    if box:
        from rich.box import SIMPLE

        box = SIMPLE

    table = Table(title=title, box=box, header_style="")

    table.add_column("[bold underline]Node", justify='left', no_wrap=True, style="bold")
    table.add_column("[bold underline]State", justify='left', no_wrap=True, style="bold")
    table.add_column("[green_yellow underline]Partition", justify='left', no_wrap=True, style="green_yellow")
    table.add_column("[magenta underline]#C", justify='right', no_wrap=True, style="magenta")
    table.add_column("[magenta underline]Memory", justify='right', no_wrap=True, style="magenta")
    table.add_column("[dodger_blue2 underline]Features", justify='left', no_wrap=True, style="dodger_blue2")

    reservation = any(df["reservation"].values)

    if reservation:
        table.add_column("[bold underline]Reservation", justify='left', no_wrap=True, style="bold")

    for i,row in df.iterrows():

        values = []

        values.append(row.nodes)
        # values.append(row.nodes)
        values.append(color_by_node_state(row.node))
        values.append(row.partition)
        values.append(str(row.cpus_idle))
        values.append(mem_string(row.memory_free))
        values.append(row.features)

        if reservation:
            values.append(row.reservation)

        table.add_row(*values)

        # table.add_row(*[str(v) for v in row.values])

    if panel:
        return Panel(table, expand=False)

    return table

def job_table(
    df,
    title: str = "jobs",
    long: bool = False,
    force_submit_time: bool = False,
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
    end_time = "end_time" in df.columns
    submit_time = "submit_time" in df.columns

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

    if force_submit_time or long and submit_time:
        table.add_column(
            "[underline dodger_blue2]Submitted",
            justify="right",
            style="dodger_blue2",
            no_wrap=True,
        )

    if long and start_time:
        table.add_column(
            "[underline dodger_blue2]Started",
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

    table.add_column("[underline bold]State", justify="left", style=None, no_wrap=True)

    for i, row in df.iterrows():

        if submit_time:
            submit_time = human_datetime(row.submit_time)

        if start_time:
            start_time = human_datetime(row.start_time)

            if end_time:
                run_time = human_timedelta(row.end_time - row.start_time)
            else:
                run_time = human_timedelta(datetime.datetime.now() - row.start_time)

        values = [row.job_id, row["name"]]

        if num_nodes:
            values.append(row.node_count)
        if num_cores:
            values.append(row.cpus)

        if force_submit_time or long and submit_time:
            values.append(submit_time)

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

    extract_time(df, "start_time")
    extract_time(df, "submit_time")
    extract_time(df, "time_limit")

    extract_list(df, "job_state")

    return df


def parse_sacct_json(payload: dict) -> "DataFrame":

    command = "sacct"

    global METADATA

    METADATA.update(
        {
            "cluster_name": payload["meta"]["slurm"]["cluster"],
            "user": payload["meta"]["client"]["user"],
            "group": payload["meta"]["client"]["group"],
        }
    )

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

    df = df.rename(columns={"user": "user_name", "state": "job_state"})

    extract_inner(df, "job_state", "current")

    extract_sacct_times(df)

    extract_list(df, "job_state")

    df = df[df["job_state"] != "RUNNING"]

    return df


def show_queue(
    command: str,
    user: None | str = None,
    long: bool = False,
    return_table: bool = False,
    hist: int = 2,
    hist_unit: str= "weeks",
    box: bool = False,
):

    if user == "all":
        user = None
    elif user is None:
        x = subprocess.Popen(["whoami"], shell=True, stdout=subprocess.PIPE)
        output = x.communicate()
        user = output[0].strip().decode("utf-8")

    if user:
        s_command = f"{command} -u {user} --json"
    else:
        s_command = f"{command} -u {user} --json"

    if command == "sacct":
        s_command += f" -S now-{hist}{hist_unit}"

    x = subprocess.Popen([s_command], shell=True, stdout=subprocess.PIPE)
    output = x.communicate()

    payload = json.loads(output[0])

    parser = PARSERS[command]

    df = parser(payload)

    cluster = METADATA["cluster_name"]

    if command == "sacct":
        title = f"[bold]{user}'s previous jobs (last {hist} {hist_unit})"

    elif user:
        df = df[df["user_name"] == user]
        title = f"[bold]{user}'s jobs on {cluster}"
    else:
        title = f"[bold]jobs on {cluster}"

    force_submit_time = command == "sacct"

    return job_table(
        df,
        title=title,
        long=long,
        force_submit_time=force_submit_time,
        return_table=return_table,
        box=box,
    )


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

    upper.size = panel1.renderable.row_count + 4
    lower.size = panel2.renderable.row_count + 4

    layout.split_column(
        upper,
        lower,
    )

    if not return_table:
        console.print(layout)
    else:
        return layout

def parse_sinfo_json(payload: dict) -> "DataFrame":

    df = DataFrame(payload['sinfo'])

    df2 = df.drop(columns=["port", "weight", "disk", "sockets", "threads", "cluster", "comment", "extra", "gres", "reason", "cores"])
    df2["node"] = df2.apply(lambda x: x["node"]["state"][0], axis=1)
    df2["nodes"] = df2.apply(lambda x: x["nodes"]["nodes"][0], axis=1)
    df2["cpus_max"] = df2.apply(lambda x: x["cpus"]["maximum"], axis=1)
    df2["cpus_idle"] = df2.apply(lambda x: x["cpus"]["idle"], axis=1)
    df2["cpus_allocated"] = df2.apply(lambda x: x["cpus"]["allocated"], axis=1)
    df2["memory_max"] = df2.apply(lambda x: x["memory"]["maximum"], axis=1)
    df2["memory_free"] = df2.apply(lambda x: x["memory"]["free"]["maximum"]["number"], axis=1)
    df2["memory_allocated"] = df2.apply(lambda x: x["memory"]["allocated"], axis=1)
    df2["features"] = df2.apply(lambda x: x["features"]["total"], axis=1)
    df2["partition"] = df2.apply(lambda x: x["partition"]["name"], axis=1)

    df2.drop(columns=["cpus", "memory"], inplace=True)

    return df2

def idle_queue():

    s_command = "sinfo -N --json"

    x = subprocess.Popen([s_command], shell=True, stdout=subprocess.PIPE)
    output = x.communicate()

    payload = json.loads(output[0])

    df = parse_sinfo_json(payload)

    table = node_table(df)

    console.print(table)

@app.command()
def show(user: None | str = None, long: bool = False, idle: bool = False, hist: int | None = None, hist_unit: str = "weeks"):

    loop = True

    if hist:

        show_queue(user=user, command="sacct", long=long, hist=hist, hist_unit=hist_unit)

    elif idle:
        idle_queue()

    elif loop:

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

PARSERS = {"squeue": parse_squeue_json, "sacct": parse_sacct_json}

COLUMNS = {
    "sacct": [
        "job_id",
        "state",
        "name",
        "nodes",
        "partition",
        "user",
        "time",
    ],
    "squeue": [
        "command",
        "cpus_per_task",
        "dependency",
        "derived_exit_code",
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
    ],
}


if __name__ == "__main__":
    app()
