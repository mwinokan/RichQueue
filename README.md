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
