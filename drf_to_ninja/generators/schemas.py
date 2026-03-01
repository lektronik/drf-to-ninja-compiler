from typing import List, Dict, Any


def generate_schemas(serializers: List[Dict[str, Any]]) -> str:
    output = "from ninja import ModelSchema, Schema\n\n"

    for serializer in serializers:
        name = serializer.get("name", "UnknownSerializer").replace("Serializer", "Schema")
        model = serializer.get("model")
        fields = serializer.get("fields", [])
        depth = serializer.get("depth")
        nested = serializer.get("nested_serializers", [])

        if model:
            output += f"class {name}(ModelSchema):\n"

            if serializer.get("needs_review"):
                output += "    # ⚠️ USER REVIEW REQUIRED:\n"
                output += "    # The compiler detected custom fields or methods in the DRF Serializer:\n"
                for cf in serializer.get("custom_fields", []):
                    output += f"    #  - {cf}\n"
                for ns in nested:
                    many_label = " (many=True)" if ns["many"] else ""
                    output += f"    #  - nested: {ns['field']} = {ns['serializer']}{many_label}\n"
                if depth is not None:
                    output += f"    #  - Meta.depth = {depth} (flatten nested relations manually)\n"
                output += "    # You will need to manually map these to standard Pydantic types or Resolve() blocks.\n"

            output += f"    class Meta:\n"
            output += f"        model = {model}\n"
            if fields == "__all__":
                output += f"        fields = '__all__'\n"
            else:
                formatted_fields = ", ".join([f"'{f}'" for f in fields])
                output += f"        fields = [{formatted_fields}]\n"
        else:
            output += f"class {name}(Schema):\n"
            output += f"    # TODO: Define fields for standard Schema\n"
            output += f"    pass\n"

        output += "\n"

    return output
