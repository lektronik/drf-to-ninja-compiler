import ast
from typing import List, Dict, Any

DRF_TO_NINJA_PERMISSIONS = {
    "AllowAny": "lambda request: True",
    "IsAuthenticated": "django_auth",
    "IsAdminUser": "lambda request: request.user.is_staff",
    "IsAuthenticatedOrReadOnly": "lambda request: request.method in SAFE_METHODS or request.user.is_authenticated",
}

DRF_TO_NINJA_AUTH = {
    "TokenAuthentication": "HttpBearer",
    "SessionAuthentication": "django_auth",
    "BasicAuthentication": "HttpBasicAuth",
    "JWTAuthentication": "HttpBearer",
}


class PermissionParser(ast.NodeVisitor):
    def __init__(self) -> None:
        self.permissions: List[Dict[str, Any]] = []

    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        for item in node.body:
            if isinstance(item, ast.Assign):
                for target in item.targets:
                    if isinstance(target, ast.Name):
                        if target.id == "permission_classes":
                            self._parse_permission_list(node.name, item.value)
                        elif target.id == "authentication_classes":
                            self._parse_auth_list(node.name, item.value)

        self.generic_visit(node)

    def _parse_permission_list(self, view_name: str, value: ast.expr) -> None:
        perms = []
        if isinstance(value, (ast.List, ast.Tuple)):
            for elt in value.elts:
                if isinstance(elt, ast.Name):
                    perms.append(elt.id)
                elif isinstance(elt, ast.Attribute):
                    perms.append(elt.attr)

        self.permissions.append(
            {
                "view": view_name,
                "type": "permission",
                "classes": perms,
            }
        )

    def _parse_auth_list(self, view_name: str, value: ast.expr) -> None:
        auths = []
        if isinstance(value, (ast.List, ast.Tuple)):
            for elt in value.elts:
                if isinstance(elt, ast.Name):
                    auths.append(elt.id)
                elif isinstance(elt, ast.Attribute):
                    auths.append(elt.attr)

        self.permissions.append(
            {
                "view": view_name,
                "type": "authentication",
                "classes": auths,
            }
        )


def parse_permissions(file_path: str) -> List[Dict[str, Any]]:
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    parser = PermissionParser()
    parser.visit(tree)
    return parser.permissions
