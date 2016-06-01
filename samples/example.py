def f_fixed(*, x, y):
    return x + y


def f_get(**kwargs):
    # Pick arguments with get('name')
    x = kwargs.get('x', 0)
    y = kwargs.get('y', 1)
    return x+y


def f_getitem(**kwargs):
    # Pick arguments with ['name'] (__getitem__('name'))
    return kwargs['x'] * 2


def f_in(**kwargs):
    # Check for arguments with "in name" (__contains__('name'))
    if 'x' in kwargs:
        return kwargs['y'] * 2


def f_var_getitem(**kwargs):
    # Pick arguments with [var] (__getitem__(var))
    d = {}
    for argname in ('arg', 'blargh', 'cuack', 'doofus'):
        d[argname] = kwargs.get(argname)
    return d


def f_items(**kwargs):
    # Parse with .items()
    d = {}
    for arg, value in kwargs.items():
        if arg in ('arg', 'blargh', 'cuack', 'doofus'):
            d[arg] = value
    return d


def f_pop(**kwargs):
    # remove items with pop()
    x = kwargs.pop('x')
    y = kwargs.pop('y')
    return x + y


def f_chain(**kwargs):
    # Use some argument, then chain to other kwargs function
    z = kwargs.pop('z', 2)
    result = z + f1(**kwargs)
    return result


class C():
    def f(self, **kwargs):
        # Use of kwargs within method
        self.x = kwargs.get('x', 0)
        self.y = kwargs.get('y', 1)


def f_dynamic(obj, **kwargs):
    # Dynamically bound delegation of kwargs
    # This is statically unsolvable unless we know more about "obj"
    # (for example: obj is an instance of C)
    z = kwargs.pop('z', 2)
    obj.f(**kwargs)
    return z


def non_kwargs(x, y):
    return x+y
