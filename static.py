import ast
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


class FunctionFinder(ast.NodeVisitor):

    def __init__(self, *args, **kwargs):
        self.function_registry = {}
        self.filename = None
        super().__init__(*args, **kwargs)

    def visit_FunctionDef(self, node):
        func_id = (self.filename, node.name, node.lineno, node.col_offset)
        self.function_registry[func_id] = args = []

        # Add normal args:
        args += [a.arg for a in node.args.args]

        # Add keyword only args
        args += [a.arg for a in node.args.kwonlyargs]

        # Check for **kwargs
        kwarg = node.args.kwarg
        if kwarg is not None:
            args += guess_kwargs(node.body, kwarg.arg)

filename = sys.argv[1]
source = open(filename).read()
tree = ast.parse(source, filename)

visitor = FunctionFinder()
visitor.filename = filename
visitor.visit(tree)

pprint.pprint(visitor.function_registry)