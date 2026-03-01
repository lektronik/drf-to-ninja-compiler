import ast
from typing import List, Dict, Any


class URLParser(ast.NodeVisitor):
    def __init__(self) -> None:
        self.url_patterns: List[Dict[str, Any]] = []

    def visit_Call(self, node: ast.Call) -> None:
        func_name = None
        if isinstance(node.func, ast.Name):
            func_name = node.func.id
        elif isinstance(node.func, ast.Attribute):
            func_name = node.func.attr

        if func_name == "path":
            self._parse_path(node)
        elif func_name == "include":
            self._parse_include(node)

        self.generic_visit(node)

    def _parse_path(self, node: ast.Call) -> None:
        pattern_info: Dict[str, Any] = {
            "route": None,
            "view": None,
            "name": None,
            "is_router": False,
        }

        if node.args:
            if isinstance(node.args[0], ast.Constant):
                pattern_info["route"] = node.args[0].value

        if len(node.args) > 1:
            view_arg = node.args[1]
            if isinstance(view_arg, ast.Call):
                if isinstance(view_arg.func, ast.Attribute) and view_arg.func.attr == "as_view":
                    if isinstance(view_arg.func.value, ast.Call):
                        if isinstance(view_arg.func.value.func, ast.Attribute):
                            pattern_info["view"] = view_arg.func.value.func.attr
                            pattern_info["is_router"] = True
                    elif isinstance(view_arg.func.value, ast.Name):
                        pattern_info["view"] = view_arg.func.value.id
                elif isinstance(view_arg.func, ast.Name):
                    pattern_info["view"] = view_arg.func.id
            elif isinstance(view_arg, ast.Attribute):
                pattern_info["view"] = view_arg.attr

        for kw in node.keywords:
            if kw.arg == "name" and isinstance(kw.value, ast.Constant):
                pattern_info["name"] = kw.value.value

        if pattern_info["route"] is not None:
            self.url_patterns.append(pattern_info)

    def _parse_include(self, node: ast.Call) -> None:
        if node.args and isinstance(node.args[0], ast.Constant):
            self.url_patterns.append(
                {
                    "route": None,
                    "view": None,
                    "name": None,
                    "is_router": False,
                    "include": node.args[0].value,
                }
            )


def parse_urls(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    parser = URLParser()
    parser.visit(tree)
    return parser.url_patterns
