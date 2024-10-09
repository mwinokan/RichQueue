from pandas import concat, DataFrame, isnull
from rich.panel import Panel
from rich.text import Text
import subprocess
import json
from .console import console
from pathlib import Path
import datetime
from .table import running_job_table, history_job_table, node_table
from .tools import human_timedelta

# from numpy import isnat

METADATA = {}

PANEL_PADDING = 4

### CONSTRUCT LAYOUT


def get_layout_pair(user: str | None, **kwargs):

    if user == "all":
        user = None
    elif user is None:
        x = subprocess.Popen(["whoami"], shell=True, stdout=subprocess.PIPE)
        output = x.communicate()
        user = output[0].strip().decode("utf-8")

    df = combined_df(user=user, **kwargs)

    n_rows = len(df)
    n_running = len(df[df["job_state"] == "RUNNING"])
    n_pending = len(df[df["job_state"] == "PENDING"])

    hide_pending = False

    running_df = df[df["job_state"].isin(["RUNNING", "PENDING"])]
    history_df = df[~df["job_state"].isin(["RUNNING", "PENDING"])]

    console_height = console.size.height
    max_rows = console_height - 2 * PANEL_PADDING

    if n_rows > max_rows:

        # hide history?
        if n_running + n_pending + PANEL_PADDING + 1 < console_height:
            history_limit = 0
            running_limit = None

        # hide pending?
        elif n_rows - n_pending < max_rows:
            # running_df = running_df[running_df["job_state"]=="RUNNING"]
            running_limit = None
            history_limit = None
            hide_pending = n_pending

        # fallback clip
        else:
            running_limit = 5
            history_limit = 5

    else:
        running_limit = None
        history_limit = None

    running = Panel(
        running_job_table(
            running_df,
            limit=running_limit,
            hide_pending=hide_pending,
            user=user,
            **kwargs,
        ),
        expand=False,
    )

    if history_limit == 0:
        history = Text("history hidden, resize window or use --hist")
    else:
        history = Panel(
            history_job_table(history_df, limit=history_limit, user=user, **kwargs),
            expand=False,
        )

    return running, history


def get_hist_layout(user: str | None, **kwargs):

    if user == "all":
        user = None
    elif user is None:
        x = subprocess.Popen(["whoami"], shell=True, stdout=subprocess.PIPE)
        output = x.communicate()
        user = output[0].strip().decode("utf-8")

    df = combined_df(user=user, **kwargs)

    history_df = df[~df["job_state"].isin(["RUNNING", "PENDING"])]

    history = Panel(
        history_job_table(history_df, limit=None, user=user, **kwargs),
        expand=False,
    )

    return history


def get_node_layout(idle: bool = True, **kwargs):

    df = get_sinfo(**kwargs)

    if idle:
        df = df[df["node_state"].isin(["IDLE", "MIXED"])]

    table = node_table(df, **kwargs)

    return Panel(table, expand=False)


### GET QUEUE DFs


def get_squeue(user: str | None = None, **kwargs) -> "pandas.DataFrame":

    if user:
        command = f"squeue -u {user} --json"
    else:
        command = f"squeue --json"

    try:
        process = subprocess.Popen(
            [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = process.communicate()
        payload = json.loads(output[0])
    except json.JSONDecodeError:
        # console.print('[orange1 bold]Warning: using example data')
        payload = json.load(
            open(
                Path(__file__).parent.parent / "example_data" / "squeue_long.json", "rt"
            )
        )

    global METADATA

    METADATA = {
        "cluster_name": payload["meta"]["slurm"]["cluster"],
        "user": payload["meta"]["client"]["user"],
        "group": payload["meta"]["client"]["group"],
    }

    # parse payload
    df = DataFrame(payload["jobs"])

    # filter columns
    columns = COLUMNS["squeue"]

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


def get_sacct(
    user: str | None = None, hist: int | None = 4, hist_unit: str = "weeks", **kwargs
) -> "pandas.DataFrame":

    hist = hist or 4

    if user:
        command = f"sacct -u {user} --json -S now-{hist}{hist_unit}"
    else:
        command = f"sacct --json -S now-{hist}{hist_unit}"

    try:
        process = subprocess.Popen(
            [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = process.communicate()
        payload = json.loads(output[0])
    except json.JSONDecodeError:
        # console.print('[orange1 bold]Warning: using example data')
        payload = json.load(
            open(Path(__file__).parent.parent / "example_data" / "sacct.json", "rt")
        )

    global METADATA

    METADATA = {
        "cluster_name": payload["meta"]["slurm"]["cluster"],
        "user": payload["meta"]["client"]["user"],
        "group": payload["meta"]["client"]["group"],
        "hist": hist,
        "hist_unit": hist_unit,
    }

    # parse payload
    df = DataFrame(payload["jobs"])

    # filter columns
    columns = COLUMNS["sacct"]

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
    df = df[df["job_state"] != "PENDING"]

    return df


def get_sinfo(**kwargs) -> "pandas.DataFrame":

    command = "sinfo -N --json"

    try:
        process = subprocess.Popen(
            [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = process.communicate()
        payload = json.loads(output[0])
    except json.JSONDecodeError:
        payload = json.load(
            open(Path(__file__).parent.parent / "example_data" / "sinfo_N.json", "rt")
        )

    global METADATA

    METADATA = {
        "cluster_name": payload["meta"]["slurm"]["cluster"],
        "user": payload["meta"]["client"]["user"],
        "group": payload["meta"]["client"]["group"],
    }

    df = DataFrame(payload["sinfo"])

    df.drop(
        columns=[
            "port",
            "weight",
            "disk",
            "sockets",
            "threads",
            "cluster",
            "comment",
            "extra",
            "gres",
            "reason",
            "cores",
        ],
        inplace=True,
    )

    df["node"] = df.apply(lambda x: x["node"]["state"][0], axis=1)
    df["nodes"] = df.apply(lambda x: x["nodes"]["nodes"][0], axis=1)
    df["cpus_max"] = df.apply(lambda x: x["cpus"]["maximum"], axis=1)
    df["cpus_idle"] = df.apply(lambda x: x["cpus"]["idle"], axis=1)
    df["cpus_allocated"] = df.apply(lambda x: x["cpus"]["allocated"], axis=1)
    df["cpu_string"] = df.apply(lambda x: f"{x.cpus_idle}/{x.cpus_max}", axis=1)
    df["memory_max"] = df.apply(lambda x: x["memory"]["maximum"], axis=1)
    df["memory_free"] = df.apply(
        lambda x: x["memory"]["free"]["maximum"]["number"], axis=1
    )
    df["memory_allocated"] = df.apply(lambda x: x["memory"]["allocated"], axis=1)
    df["features"] = df.apply(lambda x: x["features"]["total"], axis=1)
    df["partition"] = df.apply(lambda x: x["partition"]["name"], axis=1)

    df.drop(columns=["cpus", "memory"], inplace=True)

    df.rename(columns={"node": "node_state", "nodes": "node_name"}, inplace=True)

    return df


def combined_df(**kwargs) -> "DataFrame":
    """Get combined DataFrame of SLURM job information"""
    df1 = get_squeue(**kwargs)
    df2 = get_sacct(**kwargs)
    df = concat([df1, df2], ignore_index=True)
    df["run_time"] = add_run_time(df)
    df = df.sort_values(by="submit_time", ascending=True)
    return df


### ADD COLUMNS


def add_run_time(df):

    def inner(row):
        # print(f'{row.end_time=} {type(row.end_time)=}')

        if row.job_state == "PENDING":
            return ""

        if isnull(row.end_time):
            return human_timedelta(datetime.datetime.now() - row.start_time)
        else:
            return human_timedelta(row.end_time - row.start_time)

    return df.apply(inner, axis=1)


### EXTRACTORS


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
