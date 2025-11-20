from .slurm import combined_df


def guess_current_job(user: str, **kwargs):

    global JOB_DF
    JOB_DF = combined_df(user=user, **kwargs)

    assert len(JOB_DF), "No jobs found"

    pending = JOB_DF[JOB_DF["job_state"] == "PENDING"]
    running = JOB_DF[JOB_DF["job_state"] == "RUNNING"]
    history = JOB_DF[~JOB_DF["job_state"].isin(["PENDING", "RUNNING"])]

    # pick the single active job
    if len(running) == 1:
        return running.iloc[0]

    # pick the most recently submitted active job
    elif len(running) > 1:
        return running.sort_values(by="submit_time", ascending=False).iloc[0]

    # pick the single pending job
    elif len(pending) == 1:
        return pending.iloc[0]

    # pick the most recently submitted pending job
    elif len(pending) > 1:
        return pending.sort_values(by="submit_time", ascending=False).iloc[0]

    # pick the most recently submitted pending job
    else:
        return pending.sort_values(by="submit_time", ascending=False).iloc[0]

    return job


def get_specific_job(job: int, user: str, **kwargs):

    global JOB_DF
    JOB_DF = combined_df(user=user, **kwargs)

    assert len(JOB_DF), "No jobs found"

    matches = JOB_DF[JOB_DF["job_id"] == job]

    if not len(matches):
        console.print("[red bold]Could not find job with ID {job_id=}")
        return None

    elif len(matches) > 1:

        matches = matches[matches["command"].notna()]

        if len(matches) > 1:
            console.print(matches.to_dict(orient="records"))
            raise ValueError("Multiple job matches")

    return matches.iloc[0]
