import datetime


def curry(function, payload):
    def f(*args, **kwargs):
        return function(payload, *args, **kwargs)

    return f


def human_timedelta(delta):

    bits = []

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
