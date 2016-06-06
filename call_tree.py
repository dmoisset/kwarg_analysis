from collections import defaultdict
import dis
import sys

HAS_KWARGS = 0x08
HAS_VARARGS = 0x04


def _fid_from_frame(frame):
    filename = frame.f_code.co_filename
    name = frame.f_code.co_name
    line = frame.f_code.co_firstlineno
    return filename, name, line


def _get_kwargs(frame):
    if frame.f_code.co_flags & HAS_KWARGS:
        # A kwargs function is being called in this frame
        # get the kwargs argument name
        skip_args = frame.f_code.co_argcount + frame.f_code.co_kwonlyargcount
        if frame.f_code.co_flags & HAS_VARARGS:
            skip_args += 1
        kwvar = frame.f_code.co_varnames[skip_args]
        kwargs = frame.f_locals[kwvar]
        return kwargs


class Tracer():

    def __init__(self):
        self.calls = defaultdict(list)

    def call_trace(self, frame, event, arg):
        # FIXME: Should we call the old trace function?
        if event == 'call':
            caller = frame.f_back
            if caller is not None and caller.f_code.co_flags & HAS_KWARGS:
                if _get_kwargs(caller) == _get_kwargs(frame):
                    if caller.f_code.co_code[caller.f_lasti] == dis.opmap['CALL_FUNCTION_KW']:
                        # At this point we know that
                        #  - the caller is a function with KWARGS
                        #  - the callee is a function with KWARGS (otherwise get_kwargs -> None)
                        #  - both kwarg dictionaries look the same (not object identity
                        #    because they never are identical the way Python handles calls)
                        #  - the call actually was done with a func(..., **something)
                        # So we can guess that we are looking at some chaining. Let's record this:
                        self.calls[_fid_from_frame(caller)].append(_fid_from_frame(frame))
            # Keep tracing
            return self.call_trace

    def __enter__(self):
        self._trace = sys.gettrace()
        sys.settrace(self.call_trace)
        return self.calls

    def __exit__(self, exc_type, exc_value, exc_trace):
        sys.settrace(self._trace)
        del self._trace

if __name__ == "__main__":
    with Tracer() as calls:
        import samples.example as x
        x.f_chain(x=3)
        x.f_non_chain()
        x.f_dynamic(x.C())

    import json
    with open("calls.json", "w") as f:
        json.dump([dict(caller=k, callee=v) for k, v in calls.items()], f)
