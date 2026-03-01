import ast
from typing import List, Dict, Any, Union


class SerializerParser(ast.NodeVisitor):
    def __init__(self) -> None:
        self.serializers: List[Dict[str, Any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        # Check if the class inherits from ModelSerializer or Serializer
        is_serializer = False
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ["ModelSerializer", "Serializer"]:
                is_serializer = True
            elif isinstance(base, ast.Attribute) and base.attr in ["ModelSerializer", "Serializer"]:
                is_serializer = True

        if not is_serializer:
            self.generic_visit(node)
            return

        serializer_info: Dict[str, Any] = {
            "name": node.name,
            "model": None,
            "fields": [],
            "custom_fields": [],
            "needs_review": False,
        }

        # Look for the internal Meta class
        for item in node.body:
            if isinstance(item, ast.ClassDef) and item.name == "Meta":
                for stmt in item.body:
                    if isinstance(stmt, ast.Assign):
                        for target in stmt.targets:
                            if isinstance(target, ast.Name):
                                if target.id == "model":
                                    if isinstance(stmt.value, ast.Name):
                                        serializer_info["model"] = stmt.value.id
                                    elif isinstance(stmt.value, ast.Constant):
                                        serializer_info["model"] = f"'{stmt.value.value}'"
                                elif target.id == "fields":
                                    if isinstance(stmt.value, ast.List):
                                        serializer_info["fields"] = [elt.value for elt in stmt.value.elts if isinstance(elt, ast.Constant)]  # type: ignore
                                    elif isinstance(stmt.value, ast.Constant) and stmt.value.value == "__all__":
                                        serializer_info["fields"] = "__all__"
            elif isinstance(item, ast.Assign):
                # We found a custom field defined outside of Meta (e.g., SerializerMethodField)
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        serializer_info["custom_fields"].append(target.id)
                        serializer_info["needs_review"] = True
            elif isinstance(item, ast.FunctionDef):
                # We found a custom method (e.g. get_..., validate_...)
                serializer_info["custom_fields"].append(f"method:{item.name}")
                serializer_info["needs_review"] = True

        self.serializers.append(serializer_info)
        self.generic_visit(node)


def parse_serializers(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    parser = SerializerParser()
    parser.visit(tree)
    return parser.serializers
