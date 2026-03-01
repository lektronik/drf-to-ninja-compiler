import ast
from typing import Dict, Any, Optional

KNOWN_SETTINGS = {
    "DEFAULT_PAGINATION_CLASS": "pagination",
    "PAGE_SIZE": "pagination",
    "DEFAULT_AUTHENTICATION_CLASSES": "authentication",
    "DEFAULT_PERMISSION_CLASSES": "permissions",
    "DEFAULT_RENDERER_CLASSES": "renderers",
    "DEFAULT_PARSER_CLASSES": "parsers",
    "DEFAULT_THROTTLE_CLASSES": "throttling",
    "DEFAULT_THROTTLE_RATES": "throttling",
    "DEFAULT_FILTER_BACKENDS": "filtering",
}


def parse_settings(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r") as f:
        tree = ast.parse(f.read())

    result: Dict[str, Any] = {
        "pagination": {},
        "authentication": [],
        "permissions": [],
        "throttling": {},
        "filtering": [],
        "renderers": [],
        "parsers": [],
        "raw": {},
    }

    for node in ast.walk(tree):
        if not isinstance(node, ast.Assign):
            continue

        for target in node.targets:
            if not isinstance(target, ast.Name) or target.id != "REST_FRAMEWORK":
                continue

            if not isinstance(node.value, ast.Dict):
                continue

            for key, val in zip(node.value.keys, node.value.values):
                if not isinstance(key, ast.Constant):
                    continue

                setting_name = key.value
                category = KNOWN_SETTINGS.get(setting_name, "raw")

                if isinstance(val, ast.Constant):
                    parsed_val = val.value
                elif isinstance(val, (ast.List, ast.Tuple)):
                    parsed_val = []
                    for elt in val.elts:
                        if isinstance(elt, ast.Constant):
                            parsed_val.append(elt.value)
                elif isinstance(val, ast.Dict):
                    parsed_val = {}
                    for k, v in zip(val.keys, val.values):
                        if isinstance(k, ast.Constant) and isinstance(v, ast.Constant):
                            parsed_val[k.value] = v.value
                else:
                    parsed_val = f"<unparseable: {ast.dump(val)}>"

                if category == "raw":
                    result["raw"][setting_name] = parsed_val
                elif category == "pagination":
                    result["pagination"][setting_name] = parsed_val
                elif category == "throttling":
                    result["throttling"][setting_name] = parsed_val
                elif isinstance(parsed_val, list):
                    result[category].extend(parsed_val)
                else:
                    result[category] = parsed_val

    return result
