from rich.table import Table
from .tools import human_datetime


def running_job_table(df, long: bool = False, **kwargs):

    from .slurm import METADATA

    title = f"{METADATA['user']}'s running jobs on {METADATA['cluster_name']}"

    table = Table(title=title, box=None, header_style="")

    columns = running_job_columns(long=long)

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


def running_job_columns(long: bool = False):

    if long:
        return [
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
        ]
    else:
        return [
            "job_id",
            "name",
            "node_count",
            "cpus",
            "start_time",
            "run_time",
            "job_state",
        ]


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
    "node_count": lambda x: str(int(x)),
    "cpus": lambda x: str(int(x)),
    "job_state": color_by_state,
    "submit_time": human_datetime,
    "start_time": human_datetime,
}
