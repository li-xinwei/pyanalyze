def validate(x):
    if not x:
        raise ValueError("empty")
    return x

def format_output(x):
    return f"Result: {x}"
