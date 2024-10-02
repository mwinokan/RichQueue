
from typer import Typer

from pandas import DataFrame
import json
from rich import print
import datetime

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

def job_table(df, title: str='jobs', long: bool = False):

	from rich.table import Table
	from rich.box import SIMPLE
	from .tools import human_timedelta, human_datetime

	table = Table(title=title, box=SIMPLE)

	table.add_column("Job Id", justify="right", style="bold", no_wrap=True)
	table.add_column("Job Name", justify="left", style="cyan", no_wrap=False)
	table.add_column("#N", justify="right", style="magenta", no_wrap=True)
	table.add_column("#C", justify="right", style="magenta", no_wrap=True)

	if long: 
		table.add_column("Start Time", justify="right", style="blue", no_wrap=True)

	table.add_column("Run Time", justify="right", style="blue", no_wrap=True)
	table.add_column("State", justify="center", style="bold", no_wrap=True)

	if long:
		table.add_column("Partition", justify="right", style="green", no_wrap=True)
		table.add_column("Nodes", justify="left", style="green", no_wrap=False)

	for i,row in df.iterrows():
		
		start_time = human_datetime(row.start_time)
		run_time = human_timedelta(datetime.datetime.now() - row.start_time)

		values = [row.job_id, row["name"], row.node_count, row.cpus]
		
		if long:
			values.append(start_time)

		values += [run_time, color_by_state(row.job_state)]

		if long:
			values += [row.partition, row.nodes]

		table.add_row(*[str(v) for v in values])

	print(table)

def parse_squeue_json(payload: dict) -> DataFrame:

	global METADATA

	METADATA = {
		"cluster_name":payload["meta"]["slurm"]["cluster"],
		"user":payload["meta"]["client"]["user"],
		"group":payload["meta"]["client"]["group"],
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
		df[key] = df.apply(lambda x: datetime.datetime.fromtimestamp(x[key]["number"]), axis=1)

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

@app.command()
def show(user: None | str = None, long: bool = False):

	print()
	
	squeue = json.load(open("example_data/squeue.json"))
	df = parse_squeue_json(squeue)

	cluster = METADATA["cluster_name"]

	if user == "all":
		user = None
	elif user is None:
		user = METADATA["user"]

	if user:
		df = df[df["user_name"] == user]
		title = f"[bold]{user}'s jobs on {cluster}"
	else:
		title = f"[bold]jobs on {cluster}"

	job_table(df, title=title, long=long)

def main():
	
	squeue = json.load(open("../example_data/squeue.json"))

	parse_squeue_json(squeue)

if __name__ == '__main__':
	app()
