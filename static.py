import ast
import pprint
import sys


def guess_kwargs(node, kwname):
    return ['lalala']


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
            args += guess_kwargs(node.body, kwarg)

filename = sys.argv[1]
source = open(filename).read()
tree = ast.parse(source, filename)

visitor = FunctionFinder()
visitor.filename = filename
visitor.visit(tree)

pprint.pprint(visitor.function_registry)