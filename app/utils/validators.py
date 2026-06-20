def is_number(value):
    try:
        float(value)
        return True
    except:
        return False


def clean_inputs(values):
    return [float(v) if v != "" else 0 for v in values]