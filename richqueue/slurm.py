from pandas import concat, DataFrame, isnull
from rich.panel import Panel
from rich.text import Text
import subprocess
import json
import os
import re
from .console import console
from pathlib import Path
import datetime
from .table import running_job_table, history_job_table, node_table, job_table
from .tools import human_timedelta

# from numpy import isnat

METADATA = {}

SLURM_VERSION = None
CLUSTER_NAME = None

PANEL_PADDING = 4

### CONSTRUCT LAYOUT


def get_user() -> str:
    x = subprocess.Popen(["whoami"], shell=True, stdout=subprocess.PIPE)
    output = x.communicate()
    return output[0].strip().decode("utf-8")


def get_layout_pair(user: str | None, console_height=None, **kwargs):

    if user == "all":
        user = None
    elif user is None:
        user = get_user()

    df = combined_df(user=user, **kwargs)

    n_rows = len(df)
    n_running = len(df[df["job_state"] == "RUNNING"])
    n_pending = len(df[df["job_state"] == "PENDING"])

    hide_pending = False

    if console_height is None:
        console_height = console.size.height

    history_df = df[~df["job_state"].isin(["RUNNING", "PENDING"])]

    if n_running + n_pending > 0:

        running_df = df[df["job_state"].isin(["RUNNING", "PENDING"])]

        active_height = n_running + n_pending + PANEL_PADDING

        max_rows = console_height - 2 * PANEL_PADDING

        if n_rows > max_rows:

            # hide history?
            if active_height < console_height - PANEL_PADDING:
                history_limit = max(0, console_height - PANEL_PADDING - active_height)
                running_limit = None

            # hide pending?
            elif n_rows - n_pending < max_rows:
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

    else:

        history_limit = console_height - PANEL_PADDING - 3
        running = Panel(Text("No active jobs", style="bold"), expand=False)

    if history_limit == 0:
        history = Panel(
            Text(
                "history hidden, resize window or use smaller --hist value",
                style="bold",
            ),
            expand=False,
        )
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


def get_job_layout(job: int, **kwargs):

    df = get_squeue(job=job, **kwargs)

    if "end_time" not in df:
        df["end_time"] = None
    df["run_time"] = add_run_time(df)

    assert len(df) == 1

    table = job_table(df.iloc[0], job=job, **kwargs)

    return Panel(table, expand=False)


### GET QUEUE DFs


def get_squeue(
    user: str | None = None, job: int | None = None, **kwargs
) -> "pandas.DataFrame":

    if not has_json():
        return get_squeue_text(user=user, job=job, **kwargs)

    if job:
        assert isinstance(job, int)
        command = f"squeue --job={job} --json"
    elif user:
        command = f"squeue -u {user} --json"
    else:
        command = f"squeue --json"

    try:
        process = subprocess.Popen(
            [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = process.communicate()

        if job and "slurm_load_jobs error: Invalid job id specified" in str(output[1]):
            return get_sacct(user=user, job=job, **kwargs)

        payload = json.loads(output[0])

    except json.JSONDecodeError:
        raise NotOnClusterError("Could not get sinfo JSON. Not on a SLURM cluster?")

    global METADATA

    meta = payload["meta"]

    METADATA = {
        "cluster_name": meta.get("slurm", {}).get("cluster", "unknown HPC"),
        "user": meta.get("client", {}).get("user", "unknown user"),
        "group": meta.get("client", {}).get("group", "unknown group"),
    }

    # parse payload
    df = DataFrame(payload["jobs"])

    # filter columns
    columns = COLUMNS["squeue"]

    if not len(df):
        return DataFrame(columns=columns)

    if "exclusive" not in df.columns:
        columns = [c for c in columns if c != "exclusive"]

    try:
        df = df[columns]
    except KeyError:
        for key in columns:
            if key not in df.columns:
                print(df.iloc[0].to_dict())
                raise KeyError(key)

    extract_inner(df, "cpus", "number")
    extract_inner(df, "node_count", "number")
    extract_inner(df, "cpus_per_task", "number")
    extract_inner(df, "threads_per_core", "number")
    extract_inner(df, "memory_per_node", "number")
    extract_inner(df, "memory_per_cpu", "number")
    extract_inner(df, "tasks", "number")

    extract_time(df, "start_time")
    extract_time(df, "submit_time")
    # extract_inner(df, "time_limit", "number")
    extract_time_limit(df, "time_limit")

    extract_list(df, "job_state")

    if "exclusive" in columns:
        extract_list(df, "exclusive")
    # extract_json(df, "exclusive")

    return df


def get_sacct(
    user: str | None = None,
    hist: int | None = 4,
    job: int | None = None,
    hist_unit: str = "weeks",
    **kwargs,
) -> "pandas.DataFrame":

    hist = hist or 4

    if not has_json():
        return get_sacct_text(
            user=user, hist=hist, job=job, hist_unit=hist_unit, **kwargs
        )

    if job:
        command = f"sacct --job={job} --json"
    elif user:
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
        raise NotOnClusterError("Could not get sacct JSON. Not on a SLURM cluster?")

        # console.print('[orange1 bold]Warning: using example data')
        # if job:
        #     example = "sacct_job.json"
        # else:
        #     example = "sacct.json"

        # payload = json.load(
        #     open(Path(__file__).parent.parent / "example_data" / example, "rt")
        # )

    global METADATA

    meta = payload["meta"]

    METADATA = {
        "cluster_name": meta.get("slurm", {}).get("cluster", "unknown HPC"),
        "user": meta.get("client", {}).get("user", "unknown user"),
        "group": meta.get("client", {}).get("group", "unknown group"),
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

    if not has_json():
        return get_sinfo_text(**kwargs)

    command = "sinfo -N --json"

    try:
        process = subprocess.Popen(
            [command], shell=True, stdout=subprocess.PIPE, stderr=subprocess.PIPE
        )
        output = process.communicate()
        payload = json.loads(output[0])
    except json.JSONDecodeError:
        raise NotOnClusterError("Could not get sinfo JSON. Not on a SLURM cluster?")

    global METADATA

    meta = payload["meta"]

    METADATA = {
        "cluster_name": meta.get("slurm", {}).get("cluster", "unknown HPC"),
        "user": meta.get("client", {}).get("user", "unknown user"),
        "group": meta.get("client", {}).get("group", "unknown group"),
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

    if len(df1) and len(df2):
        df = concat([df1, df2], ignore_index=True)
    elif len(df1):
        df = df1
    elif len(df2):
        df = df2
    else:
        return None

    df["run_time"] = add_run_time(df)
    df = df.sort_values(by="submit_time", ascending=True)
    return df


### SLURM < 21.08 (NO --json)


def get_slurm_version() -> tuple:
    """(major, minor) from e.g. 'slurm 20.11.9', empty if unknown"""

    global SLURM_VERSION

    if SLURM_VERSION is None:
        try:
            output = subprocess.run(
                ["squeue", "--version"], capture_output=True, text=True
            ).stdout
        except OSError:
            output = ""
        # e.g. 'slurm-wlm 20.11.4' from Debian packages
        match = re.search(r"(\d+)\.(\d+)", output)
        SLURM_VERSION = (int(match[1]), int(match[2])) if match else ()

    return SLURM_VERSION


def has_json() -> bool:
    """squeue/sacct/sinfo --json were added in Slurm 21.08"""
    version = get_slurm_version()
    return not version or version >= (21, 8)


def get_cluster_name() -> str:
    """Text output has no metadata, so ask scontrol once"""

    global CLUSTER_NAME

    if CLUSTER_NAME is None:
        output = subprocess.run(
            ["scontrol", "show", "config"], capture_output=True, text=True
        ).stdout
        match = re.search(r"^ClusterName\s*=\s*(\S+)", output, re.MULTILINE)
        CLUSTER_NAME = match[1] if match else "unknown HPC"

    return CLUSTER_NAME


def run_text(command: list[str], columns: list[str]) -> "pandas.DataFrame":
    """Run a Slurm command that prints TEXT_SEP after every field"""

    # user's SQUEUE_*, SACCT_* and SINFO_* variables can filter or duplicate rows
    env = {
        k: v
        for k, v in os.environ.items()
        if not k.startswith(("SQUEUE_", "SACCT_", "SINFO_"))
    }
    env["SLURM_TIME_FORMAT"] = "standard"

    process = subprocess.run(command, capture_output=True, env=env)

    if process.returncode:
        stderr = process.stderr.decode(errors="replace").strip()
        raise NotOnClusterError(f"{command[0]} failed: {stderr}")

    # split on TEXT_SEP + newline in case a field contains a newline
    records = process.stdout.decode(errors="replace").split(TEXT_SEP + "\n")[:-1]
    rows = [record.split(TEXT_SEP) for record in records]
    return DataFrame(rows, columns=columns)


def get_squeue_text(
    user: str | None = None, job: int | None = None, **kwargs
) -> "pandas.DataFrame":

    fields = ",".join(f"{field}:0{TEXT_SEP}" for field in TEXT_FIELDS["squeue"])
    command = ["squeue", "--noheader", "--noconvert", "--array-unique", "-O", fields]

    if job:
        command.append(f"--jobs={job}")
    elif user:
        command += ["-u", user]

    columns = list(TEXT_FIELDS["squeue"].values())

    try:
        df = run_text(command, columns)
    except NotOnClusterError as e:
        if job and "Invalid job id specified" in str(e):
            return get_sacct(user=user, job=job, **kwargs)
        raise

    # recently finished jobs are known to slurmctld but hidden by default
    if job and not len(df):
        df = run_text(command + ["--states=all"], columns)

    if job and not len(df):
        return get_sacct(user=user, job=job, **kwargs)

    global METADATA

    METADATA = {"cluster_name": get_cluster_name()}

    if not len(df):
        return DataFrame(columns=COLUMNS["squeue"])

    for key in ["job_id", "node_count", "cpus", "tasks", "restart_cnt"]:
        df[key] = df[key].astype(int)

    for key in ["name", "qos", "command", "dependency"]:
        df[key] = df[key].replace("(null)", "")

    df["cpus_per_task"] = df["cpus_per_task"].map(
        lambda x: None if x == "N/A" else int(x)
    )
    df["threads_per_core"] = df["threads_per_core"].map(
        lambda x: None if x == "*" else int(x)
    )
    df[["memory_per_cpu", "memory_per_node"]] = df.apply(
        split_text_memory, axis=1, result_type="expand"
    )

    df["start_time"] = df["start_time"].map(parse_text_time)
    df["submit_time"] = df["submit_time"].map(parse_text_time)
    df["time_limit"] = df["time_limit"].map(parse_text_time_limit)

    df["requeue"] = df["requeue"] == "1"
    df["exclusive"] = df["exclusive"].map(lambda x: EXCLUSIVE.get(x, ""))

    df["standard_output"] = df.apply(
        lambda x: text_log_path(x, x["standard_output"]), axis=1
    )
    df["standard_error"] = df.apply(
        lambda x: text_log_path(x, x["standard_error"]), axis=1
    )

    return df[COLUMNS["squeue"]]


def get_sacct_text(
    user: str | None = None,
    hist: int | None = 4,
    job: int | None = None,
    hist_unit: str = "weeks",
    **kwargs,
) -> "pandas.DataFrame":

    fields = ",".join(TEXT_FIELDS["sacct"])
    command = [
        "sacct",
        "-X",
        "-p",
        "-n",
        f"--delimiter={TEXT_SEP}",
        f"--format={fields}",
    ]

    if job:
        command.append(f"--jobs={job}")
    else:
        command.append(f"--starttime=now-{hist}{hist_unit}")
        if user:
            command += ["-u", user]

    df = run_text(command, list(TEXT_FIELDS["sacct"].values()))

    global METADATA

    METADATA = {
        "cluster_name": get_cluster_name(),
        "hist": hist,
        "hist_unit": hist_unit,
    }

    df["job_id"] = df["job_id"].astype(int)

    # e.g. "CANCELLED by 1234"
    df["job_state"] = df["job_state"].str.split(" ").str[0]

    for key in ["submit_time", "start_time", "end_time"]:
        df[key] = df[key].map(parse_text_time)

    df = df[df["job_state"] != "RUNNING"]
    df = df[df["job_state"] != "PENDING"]

    return df


def get_sinfo_text(**kwargs) -> "pandas.DataFrame":

    fields = ",".join(f"{field}:0{TEXT_SEP}" for field in TEXT_FIELDS["sinfo"])
    command = ["sinfo", "-N", "--noheader", "-O", fields]

    df = run_text(command, list(TEXT_FIELDS["sinfo"].values()))

    global METADATA

    METADATA = {"cluster_name": get_cluster_name()}

    # e.g. "idle~", "down*"
    df["node_state"] = df["node_state"].str.rstrip("*~#%$@+").str.upper()

    # allocated/idle/other/total
    cpus = df["cpus"].str.split("/", expand=True).astype(int)
    df["cpus_allocated"] = cpus[0]
    df["cpus_idle"] = cpus[1]
    df["cpus_max"] = cpus[3]
    df["cpu_string"] = df.apply(lambda x: f"{x.cpus_idle}/{x.cpus_max}", axis=1)

    df["memory_max"] = df["memory_max"].astype(int)
    df["memory_free"] = df["memory_free"].replace("N/A", "0").astype(int)
    df["memory_allocated"] = df["memory_allocated"].astype(int)

    df["features"] = df["features"].replace("(null)", "")

    # sinfo has no per-node reservation field
    df["reservation"] = ""

    return df.drop(columns=["cpus"])


def parse_text_time(value: str) -> datetime.datetime:
    """Unset times print as N/A or Unknown, the JSON path gives them as 0"""
    try:
        return datetime.datetime.strptime(value, "%Y-%m-%dT%H:%M:%S")
    except ValueError:
        return datetime.datetime.fromtimestamp(0)


def parse_text_time_limit(value: str) -> str:
    """[days-]hours:minutes:seconds or minutes:seconds, or UNLIMITED etc."""

    if ":" not in value:
        return ""

    days, _, clock = value.rpartition("-")

    seconds = 0
    for part in clock.split(":"):
        seconds = 60 * seconds + int(part)

    return human_timedelta(datetime.timedelta(days=int(days or 0), seconds=seconds))


def mb_from_text(value: str) -> float:
    """e.g. '2500M', '1.50G' or '0'"""
    match = re.fullmatch(r"([\d.]+)([KMGTP]?)", value)
    return float(match[1]) * MB_PER_UNIT.get(match[2], 1)


def split_text_memory(row) -> tuple:
    """squeue doesn't say if min memory is per CPU or per node, so compare
    with the job's total memory in its TRES string"""

    memory = mb_from_text(row["min_memory"])
    total = re.search(r"mem=([\d.]+[KMGTP]?)", row["tres"])

    if total:
        total = mb_from_text(total[1])
        per_cpu = abs(total - memory * row["cpus"])
        per_node = abs(total - memory * row["node_count"])
        if per_cpu < per_node:
            return memory, None

    return None, memory


def text_log_path(row, path: str) -> str:
    """Expand squeue's raw stdout/stderr path like Slurm's slurm_get_job_stdout"""

    cwd = row["current_working_directory"]
    task = row["array_task_id"]

    # printed by squeue when unset
    default = f"{cwd}/slurm-{row['job_id']}.out"

    if path == "N/A" or (path == default and row["batch_flag"] == "0"):
        return ""

    if path == default:
        if task.isdigit():
            return f"{cwd}/slurm-{row['array_job_id']}_{task}.out"
        return default

    values = {
        "A": row["array_job_id"],
        "a": task if task.isdigit() else NO_VAL,
        "j": row["job_id"],
        "u": row["user_name"],
        "x": row["name"],
    }

    # e.g. %j, %4a or %% as in Slurm 23.11's _fname_format
    def substitute(match):
        if match[0] == "%%":
            return "%"
        value = str(values[match[2]])
        if match[2] in "Aaj":
            value = value.zfill(min(int(match[1] or 0), 10))
        return value

    path = re.sub(r"%%|%(\d*)([Aajux])", substitute, path)

    if path.startswith("/"):
        return path

    return f"{cwd}/{path}"


### ADD COLUMNS


def add_run_time(df):

    def inner(row):

        if row.job_state == "PENDING":
            return ""

        if "end_time" not in row or isnull(row.end_time):
            row.end_time = datetime.datetime.now()

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


def extract_json(df, key):

    def _inner(x):
        return json.loads(x[key])

    df[key] = df.apply(_inner, axis=1)


def extract_time(df, key):
    df[key] = df.apply(
        lambda x: datetime.datetime.fromtimestamp(x[key]["number"]), axis=1
    )


def extract_time_limit(df, key):
    df[key] = df.apply(
        lambda x: human_timedelta(datetime.timedelta(minutes=x[key]["number"])), axis=1
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

# ASCII unit separator, won't appear in names or paths
TEXT_SEP = "\x1f"

NO_VAL = 4294967294

# Slurm field: column, for text output
TEXT_FIELDS = {
    "squeue": {
        "jobid": "job_id",
        "arrayjobid": "array_job_id",
        "arraytaskid": "array_task_id",
        "batchflag": "batch_flag",
        "name": "name",
        "state": "job_state",
        "username": "user_name",
        "groupname": "group_name",
        "partition": "partition",
        "qos": "qos",
        "nodelist": "nodes",
        "numnodes": "node_count",
        "numcpus": "cpus",
        "numtasks": "tasks",
        "cpus-per-task": "cpus_per_task",
        "threads": "threads_per_core",
        "minmemory": "min_memory",
        "tres-alloc": "tres",
        "starttime": "start_time",
        "submittime": "submit_time",
        "timelimit": "time_limit",
        "command": "command",
        "workdir": "current_working_directory",
        "stdout": "standard_output",
        "stderr": "standard_error",
        "dependency": "dependency",
        "requeue": "requeue",
        "restartcnt": "restart_cnt",
        "oversubscribe": "exclusive",
        "derivedec": "derived_exit_code",
    },
    "sacct": {
        "JobIDRaw": "job_id",
        "State": "job_state",
        "JobName": "name",
        "NodeList": "nodes",
        "Partition": "partition",
        "User": "user_name",
        "Submit": "submit_time",
        "Start": "start_time",
        "End": "end_time",
    },
    "sinfo": {
        "NodeList": "node_name",
        "PartitionName": "partition",
        "StateLong": "node_state",
        "CPUsState": "cpus",
        "Memory": "memory_max",
        "FreeMem": "memory_free",
        "AllocMem": "memory_allocated",
        "Features": "features",
    },
}

# squeue oversubscribe: JSON exclusive
EXCLUSIVE = {"NO": "true", "YES": "false", "USER": "user", "MCS": "mcs"}

MB_PER_UNIT = {"K": 1 / 1024, "M": 1, "G": 1024, "T": 1024**2, "P": 1024**3}


class NotOnClusterError(Exception): ...
