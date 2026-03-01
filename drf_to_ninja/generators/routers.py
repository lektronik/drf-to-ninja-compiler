from typing import List, Dict, Any


def generate_routers(views: List[Dict[str, Any]], style: str = "router") -> str:
    if style == "api":
        output = "from ninja import NinjaAPI\n\n"
        output += "api = NinjaAPI()\n\n"
        decorator = "api"
    else:
        output = "from ninja import Router\n\n"
        output += "router = Router()\n\n"
        decorator = "router"

    for view in views:
        name = view.get("name", "UnknownView")
        v_type = view.get("type")
        methods = view.get("methods", [])

        prefix = name.lower().replace("view", "").replace("viewset", "").replace("api", "")

        output += f"# --- Generated from {name} ({v_type}) ---\n"

        if view.get("needs_review"):
            output += "    # ⚠️ USER REVIEW REQUIRED:\n"
            output += "    # The compiler detected custom overrides in this ViewSet/APIView:\n"
            for cm in view.get("custom_methods", []):
                output += f"    #  - def {cm}(self, ...):\n"
            output += "    # You must manually port this custom logic into the Ninja route below.\n\n"

        qs = view.get("queryset", "Model.objects.all()")
        raw_serializer = view.get("serializer_class") or "dict"
        schema_out = raw_serializer.replace("Serializer", "Schema") if raw_serializer != "dict" else "dict"
        schema_in = schema_out.replace("Schema", "InSchema") if schema_out != "dict" else "dict"

        if v_type in ["ModelViewSet", "ViewSet"]:
            if "list" in methods:
                output += f"@{decorator}.get('/{prefix}/', response=list[{schema_out}])\n"
                output += f"def list_{prefix}(request):\n"
                output += f'    """Automatically generated list view for {name}."""\n'
                output += f"    return {qs}\n\n"

            if "create" in methods:
                output += f"@{decorator}.post('/{prefix}/', response={schema_out})\n"
                output += f"def create_{prefix}(request, payload: {schema_in}):\n"
                output += f'    """Automatically generated create view for {name}."""\n'
                output += f"    # TODO: Implement creation logic using payload.dict()\n"
                output += f"    pass\n\n"

            if "retrieve" in methods:
                output += f"@{decorator}.get('/{prefix}/{{id}}', response={schema_out})\n"
                output += f"def get_{prefix}(request, id: int):\n"
                output += f'    """Automatically generated retrieve view for {name}."""\n'
                output += f"    pass\n\n"

            if "update" in methods:
                output += f"@{decorator}.put('/{prefix}/{{id}}', response={schema_out})\n"
                output += f"def update_{prefix}(request, id: int, payload: {schema_in}):\n"
                output += f'    """Automatically generated update view for {name}."""\n'
                output += f"    pass\n\n"

            if "destroy" in methods:
                output += f"@{decorator}.delete('/{prefix}/{{id}}')\n"
                output += f"def delete_{prefix}(request, id: int):\n"
                output += f'    """Automatically generated delete view for {name}."""\n'
                output += f"    pass\n\n"

        elif v_type == "APIView":
            for method in methods:
                method_name = method.lower()
                output += f"@{decorator}.{method_name}('/{prefix}/')\n"
                output += f"def {method_name}_{prefix}(request):\n"
                output += f'    """Automatically generated {method_name} view for {name}."""\n'
                output += f"    pass\n\n"

    return output
