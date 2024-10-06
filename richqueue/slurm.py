
from pandas import concat, DataFrame, isnull
from rich.panel import Panel
from rich.text import Text
import subprocess
import json
from .console import console
from pathlib import Path
import datetime
from .table import running_job_table
from .tools import human_timedelta
# from numpy import isnat

METADATA = {}

### MAIN FUNCTIONS

def get_squeue(user: str | None = None, **kwargs):

    if user:
        command = f"squeue -u {user} --json"
    else:
        command = f"squeue --json"

    try:
        process = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.communicate()
        payload = json.loads(output[0])
    except json.JSONDecodeError:
        # console.print('[orange1 bold]Warning: using example data')
        payload = json.load(open(Path(__file__).parent.parent/"example_data"/"squeue_long.json", 'rt'))

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

def get_sacct(user: str | None = None, hist: int | None = 4, hist_unit: str = "weeks", **kwargs):

    if user:
        command = f"sacct -u {user} --json -S now-{hist}{hist_unit}"
    else:
        command = f"sacct --json -S now-{hist}{hist_unit}"

    try:
        process = subprocess.Popen([command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        output = process.communicate()
        payload = json.loads(output[0])
    except json.JSONDecodeError:
        # console.print('[orange1 bold]Warning: using example data')
        payload = json.load(open(Path(__file__).parent.parent/"example_data"/"sacct.json", 'rt'))

    global METADATA

    METADATA = {
        "cluster_name": payload["meta"]["slurm"]["cluster"],
        "user": payload["meta"]["client"]["user"],
        "group": payload["meta"]["client"]["group"],
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

def combined_df(**kwargs) -> "DataFrame":
    """Get combined DataFrame of SLURM job information"""
    df1 = get_squeue(**kwargs)
    df2 = get_sacct(**kwargs)
    return concat([df1, df2], ignore_index=True)

def get_layout_pair(**kwargs):

    df = combined_df(**kwargs)
    df['run_time'] = add_run_time(df)

    running = Panel(running_job_table(df[df["job_state"] == "RUNNING"], **kwargs), expand=False)

    history = Panel(Text("history"), expand=False)

    return running, history

### ADD COLUMNS

def add_run_time(df):

    def inner(row):
        # print(f'{row.end_time=} {type(row.end_time)=}')
        if isnull(row.end_time):
            return human_timedelta(datetime.datetime.now() - row.start_time)
        else:
            return human_timedelta(row.end_time - row.start_time)

    return df.apply(inner,axis=1)


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

