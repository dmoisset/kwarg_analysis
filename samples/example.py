def f1(**kwargs):
    # Pick arguments with get('name')
    x = kwargs.get('x', 0)
    y = kwargs.get('y', 1)
    return x+y


def f2(**kwargs):
    # Pick arguments with ['name'] (__getitem__('name'))
    return kwargs['x'] * 2


def f3(**kwargs):
    # Check for arguments with "in name" (__contains__('name'))
    if 'x' in kwargs:
        return kwargs['y'] * 2


def f4(**kwargs):
    # Pick arguments with [var] (__getitem__(var))
    d = {}
    for argname in ('arg', 'blargh', 'cuack', 'doofus'):
        d[argname] = kwargs.get(argname)
    return d


def f5(**kwargs):
    # Parse with .items()
    d = {}
    for arg, value in kwargs.items():
        if arg in ('arg', 'blargh', 'cuack', 'doofus'):
            d[arg] = value
    return d


def f6(**kwargs):
    # remove items with pop()
    x = kwargs.pop('x')
    y = kwargs.pop('y')
    return x + y


def f7(**kwargs):
    # Use some argument, then chain to other kwargs function
    z = kwargs.pop('z', 2)
    result = z + f1(**kwargs)
    return result


def non_kwargs(x, y):
    return x+y
