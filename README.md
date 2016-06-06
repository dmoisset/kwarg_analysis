# A kwarg analyzer

This is a Python code analysis tool to get actual argument names for functions defined with
open keyword arguments. It was inspired by a talk by James Powell at PyData Berlin 2016: https://youtu.be/MQMbnhSthZQ

Disclaimer: This program is a proof of concept and probably requires a lot of clean-up before
being used for real

## How to try it out

The code requires Python 3, and probably is CPython only (it uses some low level bytecode
disassembly tricks) but doesn't require any external libraries.

You can start playing with the `samples/example.py` demo, which is a piece of code that uses
a lot of kwargs in different ways.

The analysis works in two passes. The first one is dynamic, so you need something that exercises
and runs the functions you want to analyze. A test suite with good coverage should be fine. The
`call_tree.py` module provides a context manager, and you have to run those tests/example code
inside the manager and save the results. For the sample code just calling

```
python call_tree.py
```

is enough. Below in this document there's a more complicated example.

Calling the command above generates a file called `calls.json` with some metadata about your
function dependencies. Once you have that file, it can be used by the analysis tool:

```
python get_args.py samples/example.py
```

Which will give you an output similar to:

```
{('.../kwargs/samples/example.py', 'f_chain', 47): ['z',
                                                    'y',
                                                    'x'],
 ('.../kwargs/samples/example.py', 'f_dynamic', 69): ['obj',
                                                      'z',
                                                      'y',
                                                      'self',
                                                      'x'],
 ('.../kwargs/samples/example.py', 'f_fixed', 1): ['x',
                                                   'y'],
 ('.../kwargs/samples/example.py', 'f_get', 5): ['y',
                                                 'x'],
 ('.../kwargs/samples/example.py', 'f_getitem', 12): ['x'],
 ('.../kwargs/samples/example.py', 'f_in', 17): ['y',
                                                 'x'],
 ('.../kwargs/samples/example.py', 'f_items', 31): ['<unknown>'],
 ('.../kwargs/samples/example.py', 'f_non_chain', 54): ['z'],
 ('.../kwargs/samples/example.py', 'f_pop', 40): ['y',
                                                  'x'],
 ('.../kwargs/samples/example.py', 'f_var_getitem', 23): ['<unknown>'],
 ('.../kwargs/samples/example.py', 'method', 63): ['self',
                                                   'y',
                                                   'x'],
 ('.../kwargs/samples/example.py', 'non_kwargs', 78): ['x',
                                                       'y']}
```

Each block of the result can be read as "the function at file `'.../kwargs/samples/example.py'`
called `'f_chain'` in line `47` can be called with keyword arguments arguments `'z', 'y', 'x'`".
Note that it will show the name for both positional and keyword arguments, and even functions
without kwargs (it has to analyze the full thing anyway). You will see some `<unknown>` labels which
are cases where the analyzer knows that there are some other possible valid kwargs, but wasn't smart
enough to figure out which.

## Using it in a more complicated example

I have tested this on a large library (matplotlib) and seems to work reasonably ok (I haven't
done a lot of fine verification on its results, just a quick inspection). To try it, I downloaded
the source distribution of matplotlib (si I have the tests.py test runner), and modified the
`nose.main(...)` call to the following:

```
    import call_tree
    import json

    with call_tree.Tracer() as call_graph:
        nose.run(addplugins=[x() for x in plugins],
                 defaultTest=default_test_modules,
                 argv=sys.argv + extra_args,
                 env=env)
    with open("calls.json", "w") as f:
        json.dump([dict(caller=k, callee=v) for k, v in call_graph.items()], f)
```

Note that I am using `nose.run()` instead of `nose.main()` to avoid the tests exiting prematurely.
The wrapping code around the call is for capturing calls, and to save the results into the json
file.

Once I've added this, just running the matplotlib tests with `python tests.py` runs the tests but
also dumps a (large, ~100MB) JSON file with the call information that can be used with the analyzer

Then you can run the analyzer over one or many of the source files, for example

```
python get_args.py matplotlibsrc/lib/matplotlib/*.py
```

Note that you have to indicate the source paths. Also, if you do not cover all the files, you'll
get less accurate results (but if you cover more it can take more time+memory).

## How does it work

The call analyzer uses a dynamic approach using the `sys.settrace` runtime (the same kind of
things used by the python standard debugger and profiler). It essentially generates a filtered
call tree by looking for calls made with the `CALL_FUNCTION_KW` opcode (which is the one used when
you call a function with `f(x, y **args)` ). In those cases it also checks that the kwargs has
been passed down from the caller to the callee.

The argument analyzer is static (it doesn't run your code, it only parses it and creates an AST).
It loads the files and lookups for function definitions and records its arguments. If the function
definition has variable keyword arguments (ie, it is defined as `def f(x, y, **kwargs)`) it is
tagged as such, and the use of the kwargs argument are analyzed for common patterns. It also
detects cases when those kwargs are passed down to other function. After parsing all the functions
in all source files, it does another pass on functions that chain their keyword arguments, and
using the call tree information from the dynamic analyzer it propagates the arguments from the
called functions recursively.

## Things to improve

* Both passes should probably be integrated as one
* The static analyzer is confused with some real cases (where access to the kwargs is done through
a variable, like in the `f_items` example or some similar situations in real libraries like
matplotlib)
* I should also cover the `CALL_FUNCTION_VAR_KW` opcode. Just noticed :)
