import ast
import json
import os
import pprint
import sys


class KwargHeuristic(ast.NodeVisitor):

    def __init__(self, kwarg_name, *args, **kwargs):
        self.kwarg_name = kwarg_name
        self.guesses = []
        super().__init__(*args, **kwargs)

    def iskwvar(self, node):
        return isinstance(node, ast.Name) and node.id == self.kwarg_name

    def visit_Call(self, node):
        # Check for chaining
        for k in node.keywords:
            if k.arg is None:
                # this is a f(..., **expr)
                if self.iskwvar(k.value):
                    # chained call
                    self.guesses.append("<chain>")
                # other kwarg passing will not enter the if statement above
        # check for interesting method calls
        if isinstance(node.func, ast.Attribute):
            # looks like a method call
            if self.iskwvar(node.func.value):
                guess = '<unknown>'
                if node.func.attr in ('get', 'pop'):
                    # we have a kwargs.get(...) call (or pop). Check first argument
                    try:
                        guess = ast.literal_eval(node.args[0])
                    except ValueError:
                        pass
                self.guesses.append(guess)

        self.generic_visit(node)

    def visit_Subscript(self, node):
        if self.iskwvar(node.value):
            # kwargs[...]
            slice = node.slice
            if isinstance(slice, ast.Index):
                try:
                    guess = ast.literal_eval(slice.value)
                except ValueError:
                    guess = '<unknown>'
            else:
                guess = '<unknown>'
            self.guesses.append(guess)
        self.generic_visit(node)

    def visit_Compare(self, node):
        for i, op in enumerate(node.ops):
            if isinstance(op, (ast.In, ast.NotIn)):
                rhs = node.comparators[i]
                if self.iskwvar(rhs):
                    # ... in kwargs
                    lhs = ([node.left] + node.comparators)[i]
                    try:
                        guess = ast.literal_eval(lhs)
                    except ValueError:
                        guess = '<unknown>'
                    self.guesses.append(guess)
        self.generic_visit(node)


def guess_kwargs(nodes, kwname):
    h = KwargHeuristic(kwname)
    result = set()
    for node in nodes:
        h.visit(node)
        result.update(h.guesses)
    return list(result)


def load_call_map(filename):
    result = {}
    with open(filename) as call_tree:
        for call in json.load(call_tree):
            caller = call["caller"]
            callees = call["callee"]
            result[tuple(caller)] = [tuple(callee) for callee in callees]
    return result


def resolve_chain_calls(reg, f):
    args = reg[f]
    if '<chain>' in args:
        args.remove('<chain>')
        chain_args = []
        for c in call_map[f]:
            resolve_chain_calls(reg, c)
            chain_args += reg[c]
        args += chain_args


class FunctionFinder(ast.NodeVisitor):

    def __init__(self, *args, **kwargs):
        self.function_registry = {}
        self.filename = None
        super().__init__(*args, **kwargs)

    def visit_FunctionDef(self, node):
        func_id = (self.filename, node.name, node.lineno)
        self.function_registry[func_id] = args = []

        # Add normal args:
        args += [a.arg for a in node.args.args]

        # Add keyword only args
        args += [a.arg for a in node.args.kwonlyargs]

        # Check for **kwargs
        kwarg = node.args.kwarg
        if kwarg is not None:
            args += guess_kwargs(node.body, kwarg.arg)

call_map = load_call_map("calls.json")

# Analyze files in command line
visitor = FunctionFinder()
for filename in sys.argv[1:]:
    filename = os.path.abspath(filename)
    source = open(filename).read()
    tree = ast.parse(source, filename)

    visitor.filename = filename
    visitor.visit(tree)

# Resolve chain calls
for f in visitor.function_registry:
    resolve_chain_calls(visitor.function_registry, f)

pprint.pprint(visitor.function_registry)
