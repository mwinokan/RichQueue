from rich.table import Table
from .tools import human_datetime
from pandas import isnull

### TABLES

def running_job_table(
    df: "DataFrame", 
    long: bool = False, 
    limit: int | None = None, 
    hide_pending: bool | int = False,
    user: str | None = None,
    **kwargs,
):

    if hide_pending:
        pending_df = df[df["job_state"] == "PENDING"]
        df = df[df["job_state"] == "RUNNING"]

    if limit:
        df = df[-limit:]

    from .slurm import METADATA

    if not user:
        title = f"all running jobs on {METADATA['cluster_name']}"
    else:
        title = f"{user}'s running jobs on {METADATA['cluster_name']}"

    table = Table(title=title, box=None, header_style="")

    columns = RUNNING_JOB_COLUMNS[long]

    for col in columns:
        col_data = COLUMNS[col]
        table.add_column(**col_data)

    for i, row in df.iterrows():
        row_values = []
        for col in columns:
            value = row[col]
            formatter = FORMATTERS.get(col, str)
            value = formatter(value)
            row_values.append(value)
        table.add_row(*row_values)

    if hide_pending:
        row = {
            "job_id":f"(x{hide_pending})",
            "name":"",
            "node_count":f"{int(sum(pending_df['node_count'].values))}",
            "cpus":f"{int(sum(pending_df['cpus'].values))}",
            "submit_time":"",
            "start_time":"",
            "run_time":"",
            "partition":"",
            "nodes":"",
            "job_state":"[bright_yellow bold]Pending",
        }
        row_values = []
        for col in columns:
            value = row[col]
            row_values.append(value)
        table.add_row(*row_values)

    return table

def history_job_table(    
    df: "DataFrame", 
    long: bool = False, 
    limit: int | None = None, 
    user: str | None = None,
    **kwargs,
):

    if limit:
        df = df[-limit:]

    from .slurm import METADATA

    if not user:
        title = f"all previous jobs on {METADATA['cluster_name']}"
    else:
        title = f"{user}'s previous jobs on {METADATA['cluster_name']}"

    table = Table(title=title, box=None, header_style="")

    columns = HISTORY_JOB_COLUMNS[long]

    for col in columns:
        col_data = COLUMNS[col]
        table.add_column(**col_data)

    for i, row in df.iterrows():
        row_values = []
        for col in columns:
            value = row[col]
            formatter = FORMATTERS.get(col, str)
            value = formatter(value)
            row_values.append(value)
        table.add_row(*row_values)

    return table

### FORMATTERS

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

def int_if_not_nan(value):
    if isnull(value):
        return ""
    else:
        return str(int(value))

### SPECIFICATION

RUNNING_JOB_COLUMNS = {
    True: [
        "job_id",
        "name",
        "node_count",
        "cpus",
        "submit_time",
        "start_time",
        "run_time",
        "partition",
        "nodes",
        "job_state",
    ],
    False: [
        "job_id",
        "name",
        "node_count",
        "cpus",
        "start_time",
        "run_time",
        "job_state",
    ],
}

HISTORY_JOB_COLUMNS = {
    True: [
        "job_id",
        "name",
        # "node_count",
        # "cpus",
        "submit_time",
        "start_time",
        "run_time",
        "partition",
        "nodes",
        "job_state",
    ],
    False: [
        "job_id",
        "name",
        # "node_count",
        # "cpus",
        "start_time",
        "run_time",
        "job_state",
    ],
}


COLUMNS = {
    "job_id": {
        "header": "[bold underline]Job Id",
        "justify": "right",
        "style": "bold",
        "no_wrap": True,
    },
    "name": {
        "header": "[underline cyan]Job Name",
        "justify": "left",
        "style": "cyan",
        "no_wrap": False,
    },
    "node_count": {
        "header": "[underline magenta]#N",
        "justify": "right",
        "style": "magenta",
        "no_wrap": True,
    },
    "cpus": {
        "header": "[underline magenta]#C",
        "justify": "right",
        "style": "magenta",
        "no_wrap": True,
    },
    "job_state": {
        "header": "[bold underline]State",
        "justify": "left",
        "style": None,
        "no_wrap": True,
    },
    "submit_time": {
        "header": "[underline dodger_blue2]Submitted",
        "justify": "right",
        "style": "dodger_blue2",
        "no_wrap": True,
    },
    "start_time": {
        "header": "[underline dodger_blue2]Started",
        "justify": "right",
        "style": "dodger_blue2",
        "no_wrap": True,
    },
    "run_time": {
        "header": "[underline dodger_blue2]Run Time",
        "justify": "right",
        "style": "dodger_blue2",
        "no_wrap": True,
    },
    "partition": {
        "header": "[underline green_yellow]Partition",
        "justify": "right",
        "style": "green_yellow",
        "no_wrap": True,
    },
    "nodes": {
        "header": "[underline green_yellow]Nodes",
        "justify": "left",
        "style": "green_yellow",
        "no_wrap": False,
    },
}

FORMATTERS = {
    "node_count": int_if_not_nan,
    "cpus": int_if_not_nan,
    "job_state": color_by_state,
    "submit_time": human_datetime,
    "start_time": human_datetime,
}
