import ast
import operator

# --- JSON Schema (sent to the model) ---
SCHEMA = {
    "type" : "function",
    "function":{
        "name": "calculator",
        "description":(
            "evalutest a safe mathematical expression"
            "use this for any arithmetic, percentages, or calculations"
        ),
        "parameters":{
            "type": "object",
            "properties":{
                "expression":{
                    "type":"string",
                    "description": "A valid math expression, e.g. '480 * 0.25' or '(100 + 50) / 3' "
                }
            },
            "required": ["expression"],
        }
    }
}

#--- implementation (run by your code, Not the model)---
_SAFE_OPS = {
    ast.Add : operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.USub: operator.neg,
}

def _safe_eval(node):
    if isinstance(node, ast.Constant):
        return node.value
    elif isinstance(node, ast.BinOp):
        return _SAFE_OPS[type(node.op)](
            _safe_eval(node.left), _safe_eval(node.right)
        )
    elif isinstance(node, ast.UnaryOp):
        return _SAFE_OPS[type(node.op)](_safe_eval(node.operand))
    raise ValueError(f"Unsafe expression: {ast.dump(node)}")

def run(expression: str) -> str:
    """Execute the calculator tool safely."""
    try:
        tree = ast.parse(expression, mode="eval")
        result = _safe_eval(tree.body)
        return str(round(result, 6))
    except Exception as e:
        return f"Error: {e}"