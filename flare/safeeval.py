"""Here we are trying to provide an secure and safe space for evaluate simple python expressions on some 'data'.

If you only need a oneshot evaluation, you call safeEval and enjoy the result. Otherwise call first compile to get the ast
representation and execute that compiled expression multiple times with different data.
A plain instance of SafeEval without allowedCallables argument will not accept any method/function like call on execution
"""

import ast
import typing
from typing import Any, Callable, Dict


def parseInt(value, ret=0):
    """
    Parses a value as int.
    This function works similar to its JavaScript-pendant, and performs
    checks to parse most of a string value as integer.
    :param value: The value that should be parsed as integer.
    :param ret: The default return value if no integer could be parsed.
    :return: Either the parse value as int, or ret if parsing not possible.
    """
    if value is None:
        return ret

    if not isinstance(value, str):
        value = str(value)

    conv = ""
    value = value.strip()

    for ch in value:
        if ch not in "+-0123456789":
            break

        conv += ch

    try:
        return int(conv)
    except ValueError:
        return ret


def parseFloat(value, ret=0.0):
    """
    Parses a value as float.
    This function works similar to its JavaScript-pendant, and performs
    checks to parse most of a string value as float.
    :param value: The value that should be parsed as float.
    :param ret: The default return value if no integer could be parsed.
    :return: Either the parse value as float, or ret if parsing not possible.
    """
    if value is None:
        return ret

    if not isinstance(value, str):
        value = str(value)

    conv = ""
    value = value.strip()
    dot = False

    for ch in value:
        if ch not in "+-0123456789.":
            break

        if ch == ".":
            if dot:
                break

            dot = True

        conv += ch

    try:
        return float(conv)
    except ValueError:
        return ret


def optimizeValue(val, allow=[int, bool, float, list, dict, str], default=str):
    """
    Evaluates the best matching value.
    """
    # Perform string conversion into float or int, whatever fits best.
    if isinstance(val, str):
        ival = parseInt(val, None) if int in allow else None
        fval = parseFloat(val, None) if float in allow else None

        if fval is not None and str(fval) == val:
            val = fval
        elif ival is not None and str(ival) == val:
            val = ival

    # When a float fits into an int, store it as int
    if isinstance(val, float) and float in allow and int in allow:
        ival = int(val)
        if float(ival) == val:
            val = ival

    if any([isinstance(val, t) for t in allow]):
        return val

    if callable(default):
        return default(val)

    return default


class SafeEval:
    """Safely evaluate an expression from an untrusted party."""

    def __init__(
            self, allowedCallables: typing.Union[None, typing.Dict[str, typing.Any]] = None
    ):
        """Ctor for an SafeEval instance with optional mapping of function names to callables.

        :param allowedCallables: A mapping if function name to callable
        """
        self.allowedCallables = {
            "str": str,
            "float": float,
            "int": int
        }

        if allowedCallables:
            self.allowedCallables.update(allowedCallables)

        self.nodes: Dict[ast.AST, Callable[[ast.AST, Dict[str, Any]], Any]] = {
            ast.Call: self.callNode,
            ast.Compare: self.compareNode,
            ast.Name: lambda node, names: names.get(node.id),
            ast.Constant: lambda node, _: node.n,
            ast.NameConstant: lambda node, _: node.value,
            ast.Num: lambda node, _: node.n,
            ast.Str: lambda node, _: node.s,
            ast.JoinedStr: lambda node, names: [self.execute(x, names) for x in node.values],
            ast.Subscript: lambda node, names: (self.execute(node.value, names) or {}).get(
                self.execute(node.slice, names)),
            ast.Attribute: lambda node, names: (self.execute(node.value, names) or {}).get(node.attr),
            ast.Index: lambda node, names: self.execute(node.value, names),
            ast.BoolOp: self._BoolOp,
            ast.UnaryOp: lambda node, names: self.unaryOpMap[type(node.op)](self.execute(node.operand, names)),
            ast.BinOp: lambda node, names: self.dualOpMap[type(node.op)](self.execute(node.left, names),
                                                                         self.execute(node.right, names)),
            ast.IfExp: lambda node, names: self.execute(node.body, names) if self.execute(node.test,
                                                                                          names) else self.execute(
                node.orelse, names),
        }

        self.unaryOpMap: Dict[ast.AST, Callable[[Any], Any]] = {
            ast.Not: lambda x: not x,
            ast.USub: lambda x: -x,
            ast.UAdd: lambda x: +x,
        }

        self.dualOpMap: Dict[ast.AST, Callable[[Any, Any], Any]] = {
            ast.Eq: lambda x, y: x == y,
            ast.NotEq: lambda x, y: x != y,
            ast.Gt: lambda x, y: x > y,
            ast.GtE: lambda x, y: x >= y,
            ast.Lt: lambda x, y: x < y,
            ast.LtE: lambda x, y: x <= y,
            ast.In: lambda x, y: x in y,
            ast.NotIn: lambda x, y: x not in y,
            ast.Sub: lambda x, y: x - y,
            ast.Add: lambda x, y: x + y,
            ast.Mult: lambda x, y: x * y,
            ast.Div: lambda x, y: x / y,
        }

    def _BoolOp(self, node, names):
        """Handling ast.BoolOp in a Pythonic style."""
        for child in node.values:
            ret = self.execute(child, names)
            if isinstance(node.op, ast.Or) and ret:
                return ret
            elif isinstance(node.op, ast.And) and not ret:
                return ret

        return None

    def callNode(self, node: ast.Call, names: Dict[str, Any]) -> Any:
        """Evaluates the call if present in allowed callables.

        :param node: The call node to evaluate
        :param names: a mapping of local objects which is used as 'locals' namespace

        :return: If allowed to evaluate the node, its result will be returned
        """
        if node.func.id not in self.allowedCallables:
            raise NameError(f"function '{node.func.id}' not found in allowed callables - aborting")
        args = [self.execute(arg, names) for arg in node.args]
        return self.allowedCallables[node.func.id](*args)

    def compareNode(self, node: ast.Compare, names: Dict[str, Any]) -> bool:
        """Evaluates an 'if' expression.

        These are a bit tricky as they can have more than two operands (eg. "if 1 < 2 < 3")

        :param node: The compare node to evaluate
        :param names: a mapping of local objects which is used as 'locals' namespace
        """
        left = self.execute(node.left, names)
        for operation, rightNode in zip(node.ops, node.comparators):
            right = self.execute(rightNode, names)
            if not self.dualOpMap[type(operation)](left, right):
                return False
            left = right
        return True

    def execute(self, node: [str, ast.AST], names: Dict[str, Any]) -> Any:
        """Evaluates the current node with optional data.

        :param node: The compare node to evaluate
        :param names: a mapping of local objects which is used as 'locals' namespace

        :return: whatever the expression wants to return
        """
        if isinstance(node, str):
            node = self.compile(node)

        return self.nodes[type(node)](node, names)

    def compile(self, expr: str) -> ast.AST:
        """Compiles a python expression string to an ast.

        Afterwards you can use execute to run the compiled ast with optional data.
        If you only want to run a 'oneshot' expression feel free to use our safeEval method.

        :param expr: the expression to compile
        :return: the ready to use ast node
        """
        expr = expr.strip()
        assert (
                len(expr) < 500 and len([x for x in expr if x in {"(", "[", "{"}]) < 60
        ), "Recursion depth or len exceeded"
        return ast.parse(expr).body[0].value

    def safeEval(self, expr: str, names: Dict[str, Any]) -> Any:
        """Safely evaluate an expression.

        If you want to evaluate the expression multiple times with different variables use compile to generate
        the AST once and call execute for each set of variables.

        :param expr: the string to compile and evaluate
        :param names: a mapping of local objects which is used as 'locals' namespace

        :return: the result of evaluation of the expression with env provided by names
        """
        return self.execute(self.compile(expr), names)


__all__ = ["SafeEval"]
