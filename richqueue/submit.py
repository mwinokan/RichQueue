import sys
import subprocess
from os import environ
from pathlib import Path

from .main import show
from .console import console


def submit():

    sbatch_args = sys.argv[1:]

    if not sbatch_args:
        console.print("[red bold]Please provide sbatch arguments")
        console.print(
            "\n[bold yellow]Usage:[reset][bold] sb [SBATCH OPTIONS] SCRIPT [SCRIPT ARGS]...\n"
        )
        sys.exit(1)

    elif len(sbatch_args) == 1 and sbatch_args[0] in ["-h", "--help"]:
        console.print(
            "\n[bold]sb[reset]: a pretty wrapper to the sbatch command that places log files in the directory specified by the LOGS variable"
        )
        console.print(
            "\n[bold yellow]Usage:[reset][bold] sb [SBATCH OPTIONS] SCRIPT [SCRIPT ARGS]...\n"
        )
        sys.exit(1)

    log_dir = environ.get("LOGS")

    if not log_dir:
        console.print("[red bold]LOGS variable not set")
        sys.exit(1)

    log_dir = Path(log_dir)

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
