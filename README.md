# RichQueue

> 💰 RichQueue: A colourful and pythonic SLURM queue viewer

Installation from a modern python environment (>3.10) should be as simple as:

```shell

pip install --upgrade richqueue
```

To see your live-updating SLURM queue:

```shell
rq
```

![queue_example](https://github.com/user-attachments/assets/d99ca5e9-7675-4853-ab28-2d7b4da855f2)

## Other `rq` options

To see more detail:

```rq --long```

To see someone else's queue:

```rq --user USER```

To see the last `X` weeks history:

```rq --hist X```

To see history for a given time period, e.g.:

```rq --hist '3 days'```

To list available nodes on the cluster:

```rq --idle```

To show a static view:

```rq --no-loop```

## Monitoring log files

If you keep your SLURM log files in a specific directory exported as the `LOGS` variable, you can use RichQueue to monitor results as they come in with

```
res <JOB_ID>
```

<img width="569" height="737" alt="Screenshot 2025-11-20 at 09 05 48" src="https://github.com/user-attachments/assets/1b0f6457-d769-4a1a-b331-bb7f121b5864" />

## Changing to the working directory of a job

To change to the submission/working directory of a job:

```
cd $(res --dir <JOB_ID>)
```

You might find it convenient to add a shortcut to this to your login profile, e.g. `.bashrc_user` or `.bash_profile`:

```
res --install-jd >> ~/.bashrc_user
source ~/.bashrc_user
```

This will make the `jd` executable available. Change to the directory of the single active or most recently submitted job:

```
jd
```

Change to a specific job's directory:

```
jd <JOB_ID>
```

## Submitting SLURM jobs

RichQueue also provides a convenient wrapper to the `sbatch` command which makes sure your log files end up in the directory specified by the `LOGS` variable, and prints a pretty summary of the submitted job. Just replace `sbatch` with `sb`. E.g.:

```
sb --job-name test script.sh --script-arg1
```

Would run this under the hood:

```
sbatch --output=$LOGS/%j.log --error=$LOGS/%j.log --job-name test script.sh --script-arg1
```

and display the following:

<img width="474" height="255" alt="Screenshot 2025-11-20 at 10 37 19" src="https://github.com/user-attachments/assets/4464f813-841a-45bd-864e-00dd3dabf924" />
