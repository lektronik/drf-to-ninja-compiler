import ast
from typing import List, Dict, Any, Union

GENERIC_VIEW_MAP = {
    "ListAPIView": ["list"],
    "CreateAPIView": ["create"],
    "RetrieveAPIView": ["retrieve"],
    "UpdateAPIView": ["update"],
    "DestroyAPIView": ["destroy"],
    "ListCreateAPIView": ["list", "create"],
    "RetrieveUpdateAPIView": ["retrieve", "update"],
    "RetrieveDestroyAPIView": ["retrieve", "destroy"],
    "RetrieveUpdateDestroyAPIView": ["retrieve", "update", "destroy"],
}

ALL_VIEW_BASES = [
    "APIView",
    "ModelViewSet",
    "ViewSet",
    *GENERIC_VIEW_MAP.keys(),
]

STANDARD_VIEWSET_METHODS = {
    "list",
    "create",
    "retrieve",
    "update",
    "partial_update",
    "destroy",
    "__init__",
}


class ViewParser(ast.NodeVisitor):
    def __init__(self) -> None:
        self.views: List[Dict[str, Any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        is_view = False
        view_type = None
        for base in node.bases:
            name = None
            if isinstance(base, ast.Name):
                name = base.id
            elif isinstance(base, ast.Attribute):
                name = base.attr

            if name in ALL_VIEW_BASES:
                is_view = True
                if name in GENERIC_VIEW_MAP:
                    view_type = name
                elif name in ("ModelViewSet", "ViewSet"):
                    view_type = name
                else:
                    view_type = "APIView"

        if not is_view:
            self.generic_visit(node)
            return

        view_info: Dict[str, Any] = {
            "name": node.name,
            "type": view_type,
            "methods": [],
            "queryset": None,
            "serializer_class": None,
            "custom_methods": [],
            "actions": [],
            "needs_review": False,
        }

        if view_type in GENERIC_VIEW_MAP:
            view_info["methods"] = list(GENERIC_VIEW_MAP[view_type])

        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "queryset":
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
                        elif target.id == "permission_classes":
                            pass
                        elif target.id == "authentication_classes":
                            pass

            elif isinstance(item, ast.FunctionDef):
                is_action = False
                action_detail = False
                action_methods = ["get"]
                action_url_path = None

                for decorator in item.decorator_list:
                    if isinstance(decorator, ast.Call):
                        func = decorator.func
                        deco_name = None
                        if isinstance(func, ast.Name):
                            deco_name = func.id
                        elif isinstance(func, ast.Attribute):
                            deco_name = func.attr

                        if deco_name == "action":
                            is_action = True
                            for kw in decorator.keywords:
                                if kw.arg == "detail" and isinstance(kw.value, ast.Constant):
                                    action_detail = kw.value.value
                                elif kw.arg == "methods" and isinstance(kw.value, (ast.List, ast.Tuple)):
                                    action_methods = [
                                        elt.value for elt in kw.value.elts if isinstance(elt, ast.Constant)
                                    ]
                                elif kw.arg == "url_path" and isinstance(kw.value, ast.Constant):
                                    action_url_path = kw.value.value
                    elif isinstance(decorator, ast.Name) and decorator.id == "action":
                        is_action = True

                if is_action:
                    view_info["actions"].append(
                        {
                            "name": item.name,
                            "detail": action_detail,
                            "methods": action_methods,
                            "url_path": action_url_path or item.name,
                        }
                    )
                elif view_type == "APIView" and item.name in [
                    "get",
                    "post",
                    "put",
                    "patch",
                    "delete",
                ]:
                    view_info["methods"].append(item.name)
                elif view_type in ("ModelViewSet", "ViewSet") and item.name in (
                    STANDARD_VIEWSET_METHODS - {"__init__"}
                ):
                    view_info["methods"].append(item.name)
                elif item.name not in ("__init__",):
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
