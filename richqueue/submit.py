import sys
import subprocess
from os import environ
from pathlib import Path

from .main import show
from .console import console


def submit():

    log_dir = environ.get("LOGS")

    if not log_dir:
        console.print("[red bold]LOGS variable not set")
        sys.exit(1)

    log_dir = Path(log_dir)

    sbatch_args = sys.argv[1:]

    commands = [
        "sbatch",
        "--output=" f"{log_dir.resolve()}/%j.log",
        "--error=" f"{log_dir.resolve()}/%j.log",
        *sbatch_args,
    ]

    print(" ".join(commands))

    x = subprocess.run(
        commands, shell=False, stdout=subprocess.PIPE, stderr=subprocess.PIPE
    )

    if x.returncode != 0:
        console.print(f"[red bold]{x.stderr.decode().strip()}")
        sys.exit(1)

    message = x.stdout.decode().strip()

    job_id = int(message.split()[-1])

    console.print(f"[bold green]{message}:")

    show(job=job_id, no_loop=True, hist=None)
    sys.exit(0)


def main():
    submit()


if __name__ == "__main__":
    main()
