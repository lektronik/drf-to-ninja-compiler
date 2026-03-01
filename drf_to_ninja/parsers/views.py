import ast
from typing import List, Dict, Any


class ViewParser(ast.NodeVisitor):
    def __init__(self) -> None:
        self.views: List[Dict[str, Any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        is_view = False
        view_type = None
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id in ["APIView", "ModelViewSet", "ViewSet"]:
                is_view = True
                view_type = base.id
            elif isinstance(base, ast.Attribute) and base.attr in ["APIView", "ModelViewSet", "ViewSet"]:
                is_view = True
                view_type = base.attr

        if not is_view:
            self.generic_visit(node)
            return

        view_info: Dict[str, Any] = {
            "name": node.name,
            "type": view_type,
            "methods": [],  # To hold HTTP methods like get, post, put, delete
            "queryset": None,
            "serializer_class": None,
            "custom_methods": [],
            "needs_review": False,
        }

        # Look for the HTTP methods / attributes defined in this class
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "queryset":
                            # Super hacky AST to string for simple querysets `Model.objects.all()`
                            if isinstance(item.value, ast.Call) and isinstance(item.value.func, ast.Attribute):
                                if (
                                    isinstance(item.value.func.value, ast.Attribute)
                                    and item.value.func.value.attr == "objects"
                                ):
                                    if isinstance(item.value.func.value.value, ast.Name):
                                        view_info["queryset"] = (
                                            f"{item.value.func.value.value.id}.objects.{item.value.func.attr}()"
                                        )
                        elif target.id == "serializer_class":
                            if isinstance(item.value, ast.Name):
                                view_info["serializer_class"] = item.value.id

            elif isinstance(item, ast.FunctionDef):
                if view_type == "APIView" and item.name in ["get", "post", "put", "patch", "delete"]:
                    view_info["methods"].append(item.name)
                elif view_type in ["ModelViewSet", "ViewSet"] and item.name in [
                    "list",
                    "create",
                    "retrieve",
                    "update",
                    "partial_update",
                    "destroy",
                ]:
                    view_info["methods"].append(item.name)
                elif item.name not in ["__init__"]:
                    view_info["custom_methods"].append(item.name)
                    view_info["needs_review"] = True

        self.views.append(view_info)
        self.generic_visit(node)


def parse_views(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    parser = ViewParser()
    parser.visit(tree)
    return parser.views
