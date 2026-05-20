import ast
import json
import math
from pathlib import Path
from typing import Any, Dict

from flask import current_app


def _instance_dir() -> Path:
    # use instance/plugin_yeast_bank for user-customizable calc JSONs in future
    p = Path(current_app.instance_path) / "plugin_yeast_bank" / "calc"
    p.mkdir(parents=True, exist_ok=True)
    return p


def _package_dir() -> Path:
    return Path(__file__).resolve().parent / "calc"


def load_calc_catalog() -> Dict[str, Any]:
    """Carrega o catálogo de cálculos.
    Primeiro tenta instance/, depois fallback para utils/calc.
    """
    inst = _instance_dir() / "cont_calc_Yeast.json"
    pkg = _package_dir() / "cont_calc_Yeast.json"
    path = inst if inst.exists() else pkg
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


_ALLOWED_FUNCS = {
    "avg": lambda xs: sum(xs) / len(xs) if xs else 0,
    "sum": sum,
    "min": min,
    "max": max,
    "abs": abs,
    "round": round,
    "exp": math.exp,
    "log": math.log,
    "sqrt": math.sqrt,
}


class SafeEval(ast.NodeVisitor):
    """Avaliador de expressões matemáticas simples, sem exec/eval perigosos."""

    allowed_nodes = (
        ast.Expression, ast.BinOp, ast.UnaryOp, ast.Num, ast.Constant,
        ast.Name, ast.Load, ast.Call, ast.List, ast.Tuple,
        ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Pow, ast.Mod,
        ast.USub, ast.UAdd, ast.Compare, ast.Gt, ast.GtE, ast.Lt, ast.LtE, ast.Eq, ast.NotEq,
        ast.IfExp,
    )

    def __init__(self, env: Dict[str, Any]):
        self.env = env

    def visit(self, node):
        if not isinstance(node, self.allowed_nodes):
            raise ValueError(f"Expressão contém nó não permitido: {type(node).__name__}")
        return super().visit(node)

    def visit_Expression(self, node: ast.Expression):
        return self.visit(node.body)

    def visit_Constant(self, node: ast.Constant):
        if isinstance(node.value, (int, float)):
            return node.value
        raise ValueError("Constante não numérica não permitida")

    def visit_Num(self, node: ast.Num):
        return node.n

    def visit_Name(self, node: ast.Name):
        if node.id in self.env:
            return self.env[node.id]
        raise ValueError(f"Variável desconhecida: {node.id}")

    def visit_List(self, node: ast.List):
        return [self.visit(elt) for elt in node.elts]

    def visit_Tuple(self, node: ast.Tuple):
        return tuple(self.visit(elt) for elt in node.elts)

    def visit_UnaryOp(self, node: ast.UnaryOp):
        v = self.visit(node.operand)
        if isinstance(node.op, ast.USub):
            return -v
        if isinstance(node.op, ast.UAdd):
            return +v
        raise ValueError("Operação unária não permitida")

    def visit_BinOp(self, node: ast.BinOp):
        a = self.visit(node.left)
        b = self.visit(node.right)
        op = node.op
        if isinstance(op, ast.Add): return a + b
        if isinstance(op, ast.Sub): return a - b
        if isinstance(op, ast.Mult): return a * b
        if isinstance(op, ast.Div): return a / b
        if isinstance(op, ast.Pow): return a ** b
        if isinstance(op, ast.Mod): return a % b
        raise ValueError("Operação binária não permitida")

    def visit_IfExp(self, node: ast.IfExp):
        test = self.visit(node.test)
        return self.visit(node.body if test else node.orelse)

    def visit_Compare(self, node: ast.Compare):
        left = self.visit(node.left)
        for op, comp in zip(node.ops, node.comparators):
            right = self.visit(comp)
            if isinstance(op, ast.Gt) and not (left > right): return False
            if isinstance(op, ast.GtE) and not (left >= right): return False
            if isinstance(op, ast.Lt) and not (left < right): return False
            if isinstance(op, ast.LtE) and not (left <= right): return False
            if isinstance(op, ast.Eq) and not (left == right): return False
            if isinstance(op, ast.NotEq) and not (left != right): return False
            left = right
        return True

    def visit_Call(self, node: ast.Call):
        if not isinstance(node.func, ast.Name):
            raise ValueError("Somente chamadas a funções simples são permitidas")
        fn_name = node.func.id
        if fn_name not in _ALLOWED_FUNCS:
            raise ValueError(f"Função não permitida: {fn_name}")
        fn = _ALLOWED_FUNCS[fn_name]
        args = [self.visit(a) for a in node.args]
        return fn(*args)


def eval_formula(formula: str, env: Dict[str, Any]) -> float:
    tree = ast.parse(formula, mode="eval")
    return float(SafeEval(env).visit(tree))


def run_method(method: Dict[str, Any], inputs: Dict[str, Any]) -> Dict[str, Any]:
    constants = method.get("constants") or {}
    env = {}
    env.update(constants)

    # normalize inputs
    for k, v in inputs.items():
        env[k] = v

    value = eval_formula(method.get("formula") or "0", env)

    # mapping: first output key gets the result
    outs = method.get("outputs") or []
    out_key = outs[0]["key"] if outs else "result"
    return {out_key: value}
