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

## Other options

To see more detail:

```rq --long```

To see someone else's queue:

```rq --user USER```

To see the last `X` weeks history:

```rq --hist X```

To list available nodes on the cluster:

```rq --idle```

To show a static view:

```rq --no-loop```
