import datetime


def curry(function, payload, *args, **kwargs):
    def f(*args, **kwargs):
        return function(payload, *args, **kwargs)

    return f


def human_timedelta(delta):

    bits = []

    if delta.days < 0 or delta.seconds < 0:
        return ""

    days = delta.days

    s = delta.seconds

    m, s = divmod(s, 60)
    h, m = divmod(m, 60)

    if days:
        bits.append(f"{days}d")

    if h:
        bits.append(f"{h}h")

    if m:
        bits.append(f"{m}m")

    if s:
        bits.append(f"{s}s")

    bits = (str(b) for b in bits)

    return " ".join(bits)


def human_datetime(dt):

    now = datetime.datetime.now()

    bits = []

    bits.append(dt.strftime("%b"))

    day = dt.day

    match day % 10:
        case 1:
            suffix = "st"
        case 2:
            suffix = "nd"
        case 3:
            suffix = "rd"
        case _:
            suffix = "th"

    bits.append(f"{day}{suffix}")

    bits.append(dt.strftime("%H:%M"))

    bits = (str(b) for b in bits)

    return " ".join(bits)


def human_timedelta_to_seconds(s):

    values = s.split()

    seconds = 0

    for value in values:
        if value.endswith("s"):
            seconds += int(value[:-1])
        elif value.endswith("m"):
            seconds += 60 * int(value[:-1])
        elif value.endswith("h"):
            seconds += 60 * 60 * int(value[:-1])
        elif value.endswith("d"):
            seconds += 24 * 60 * 60 * int(value[:-1])

    return seconds
