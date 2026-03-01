from typing import List, Dict, Any


def generate_url_wiring(url_patterns: List[Dict[str, Any]], app_name: str = "api") -> str:
    output = "from ninja import NinjaAPI\n\n"
    output += f'{app_name} = NinjaAPI(title="Auto-generated API", version="1.0.0")\n\n'
    output += "# Wire routers extracted from DRF url patterns:\n"

    for pattern in url_patterns:
        route = pattern.get("route", "")
        view = pattern.get("view")
        include_path = pattern.get("include")

        if include_path:
            output += f"# TODO: Manually wire included app: {include_path}\n"
            continue

        if not view:
            continue

        router_name = view.lower().replace("viewset", "").replace("view", "").replace("api", "")
        if not router_name:
            router_name = "default"

        output += f"# Route: '{route}' -> {view}\n"
        output += f"# {app_name}.add_router('/{router_name}/', {router_name}_router)\n"

    output += "\n"
    output += "# Add this to your main urls.py:\n"
    output += f"# path('api/', {app_name}.urls),\n"

    return output
