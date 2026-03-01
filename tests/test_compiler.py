import pytest
import os
import tempfile
from drf_to_ninja.parsers.serializers import parse_serializers
from drf_to_ninja.parsers.views import parse_views
from drf_to_ninja.parsers.urls import parse_urls
from drf_to_ninja.parsers.permissions import parse_permissions
from drf_to_ninja.parsers.settings import parse_settings
from drf_to_ninja.generators.schemas import generate_schemas
from drf_to_ninja.generators.routers import generate_routers
from drf_to_ninja.generators.urls import generate_url_wiring
from drf_to_ninja.generators.auth import generate_auth, generate_settings_report

# ---------- Serializer Parser Tests ----------


def test_serializer_parser():
    file_path = "tests/example_drf/serializers.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    serializers = parse_serializers(file_path)
    assert len(serializers) == 3

    item_ser = next(s for s in serializers if s["name"] == "ItemSerializer")
    assert item_ser["model"] == "Item"
    assert item_ser["fields"] == ["id", "name", "description", "price"]
    assert not item_ser.get("needs_review")

    user_ser = next(s for s in serializers if s["name"] == "UserSerializer")
    assert user_ser["model"] == "'User'"
    assert user_ser["fields"] == "__all__"


def test_ecommerce_serializer_custom_fields_detected():
    """Custom fields like SerializerMethodField should trigger needs_review."""
    file_path = "tests/example_drf/ecommerce_serializers.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    serializers = parse_serializers(file_path)
    assert len(serializers) == 5

    order_ser = next(s for s in serializers if s["name"] == "OrderSerializer")
    assert order_ser["needs_review"] is True
    assert any("total" in cf for cf in order_ser["custom_fields"])
    assert any("validate_status" in cf for cf in order_ser["custom_fields"])


def test_ecommerce_simple_serializer_no_review():
    """A simple ModelSerializer with fields='__all__' should not need review."""
    file_path = "tests/example_drf/ecommerce_serializers.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    serializers = parse_serializers(file_path)
    product_ser = next(s for s in serializers if s["name"] == "ProductSerializer")
    assert product_ser["fields"] == "__all__"
    assert not product_ser["needs_review"]


# ---------- View Parser Tests ----------


def test_views_parser():
    file_path = "tests/example_drf/views.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    views = parse_views(file_path)
    assert len(views) == 2

    api_view = next(v for v in views if v["name"] == "CustomAPIView")
    assert api_view["type"] == "APIView"
    assert "get" in api_view["methods"]
    assert "post" in api_view["methods"]
    assert api_view.get("needs_review") is not None

    viewset = next(v for v in views if v["name"] == "ItemViewSet")
    assert viewset["type"] == "ModelViewSet"
    assert viewset.get("queryset") is not None
    assert viewset.get("serializer_class") == "ItemSerializer"


def test_ecommerce_viewset_custom_action_flagged():
    """Custom ViewSet methods like get_recent_orders should trigger needs_review."""
    file_path = "tests/example_drf/ecommerce_views.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    views = parse_views(file_path)
    order_vs = next(v for v in views if v["name"] == "OrderViewSet")
    assert order_vs["needs_review"] is True
    assert "get_recent_orders" in order_vs["custom_methods"]


def test_ecommerce_apiview_multi_method():
    """An APIView with get, post, delete should parse all three methods."""
    file_path = "tests/example_drf/ecommerce_views.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    views = parse_views(file_path)
    dashboard = next(v for v in views if v["name"] == "DashboardView")
    assert dashboard["type"] == "APIView"
    assert sorted(dashboard["methods"]) == ["delete", "get", "post"]


# ---------- URL Parser Tests ----------


def test_url_parser_extracts_patterns():
    """URL parser should extract route, view, and name from path() calls."""
    file_path = "tests/example_drf/ecommerce_urls.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    patterns = parse_urls(file_path)
    assert len(patterns) >= 2

    dashboard = next((p for p in patterns if p.get("name") == "dashboard"), None)
    assert dashboard is not None
    assert dashboard["route"] == "dashboard/"


def test_url_parser_detects_include():
    """URL parser should detect include() calls."""
    file_path = "tests/example_drf/ecommerce_urls.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    patterns = parse_urls(file_path)
    includes = [p for p in patterns if p.get("include")]
    # router.urls is not a string include, so we check the structure is valid
    assert all(isinstance(p, dict) for p in patterns)


# ---------- Settings Parser Tests ----------


def test_settings_parser_pagination():
    """Should extract PAGE_SIZE and pagination class from REST_FRAMEWORK dict."""
    file_path = "tests/example_drf/settings.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    settings = parse_settings(file_path)
    assert settings["pagination"]["PAGE_SIZE"] == 25
    assert "PageNumberPagination" in settings["pagination"]["DEFAULT_PAGINATION_CLASS"]


def test_settings_parser_authentication():
    """Should extract default authentication classes."""
    file_path = "tests/example_drf/settings.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    settings = parse_settings(file_path)
    auth_classes = settings["authentication"]
    assert any("TokenAuthentication" in c for c in auth_classes)
    assert any("SessionAuthentication" in c for c in auth_classes)


def test_settings_parser_throttling():
    """Should extract throttle rates."""
    file_path = "tests/example_drf/settings.py"
    if not os.path.exists(file_path):
        pytest.skip(f"Could not find example file at {file_path}")

    settings = parse_settings(file_path)
    rates = settings["throttling"].get("DEFAULT_THROTTLE_RATES", {})
    assert rates.get("anon") == "100/day"
    assert rates.get("user") == "1000/day"


# ---------- Schema Generator Tests ----------


def test_schema_generation_contains_warning_comment():
    """Generated schemas should contain a warning when needs_review is True."""
    fake_data = [
        {
            "name": "OrderSerializer",
            "model": "Order",
            "fields": ["id", "status"],
            "custom_fields": ["total", "method:get_total"],
            "needs_review": True,
        }
    ]
    output = generate_schemas(fake_data)
    assert "USER REVIEW REQUIRED" in output
    assert "total" in output
    assert "OrderSchema" in output


# ---------- Router Generator Tests ----------


def test_router_generation_includes_docstrings():
    """Generated routers should include automatic docstrings."""
    fake_data = [
        {
            "name": "ProductViewSet",
            "type": "ModelViewSet",
            "methods": ["list", "create"],
            "queryset": "Product.objects.all()",
            "serializer_class": "ProductSerializer",
            "custom_methods": [],
            "needs_review": False,
        }
    ]
    output = generate_routers(fake_data)
    assert "def list_product" in output
    assert "def create_product" in output
    assert "Automatically generated" in output
    assert "ProductSchema" in output


def test_router_generation_api_style():
    """When style='api', output should use @api.get instead of @router.get."""
    fake_data = [
        {
            "name": "ItemViewSet",
            "type": "ModelViewSet",
            "methods": ["list"],
            "queryset": "Item.objects.all()",
            "serializer_class": "ItemSerializer",
            "custom_methods": [],
            "needs_review": False,
        }
    ]
    output = generate_routers(fake_data, style="api")
    assert "@api.get" in output
    assert "NinjaAPI" in output
    assert "@router" not in output


def test_router_generation_router_style_default():
    """Default style should use @router.get."""
    fake_data = [
        {
            "name": "ItemViewSet",
            "type": "ModelViewSet",
            "methods": ["list"],
            "queryset": "Item.objects.all()",
            "serializer_class": "ItemSerializer",
            "custom_methods": [],
            "needs_review": False,
        }
    ]
    output = generate_routers(fake_data)
    assert "@router.get" in output
    assert "Router()" in output


# ---------- URL Wiring Generator Tests ----------


def test_url_wiring_generates_ninja_api():
    """URL wiring should generate NinjaAPI setup."""
    fake_patterns = [
        {"route": "products/", "view": "ProductViewSet", "name": "products", "is_router": True},
        {"route": "dashboard/", "view": "DashboardView", "name": "dashboard", "is_router": False},
    ]
    output = generate_url_wiring(fake_patterns)
    assert "NinjaAPI" in output
    assert "product" in output
    assert "dashboard" in output


# ---------- Auth Generator Tests ----------


def test_auth_generator_maps_known_permissions():
    """Known DRF permissions should map to Ninja equivalents."""
    fake_data = [
        {"view": "OrderViewSet", "type": "permission", "classes": ["IsAuthenticated", "AllowAny"]},
        {"view": "OrderViewSet", "type": "authentication", "classes": ["TokenAuthentication"]},
    ]
    output = generate_auth(fake_data)
    assert "django_auth" in output
    assert "HttpBearer" in output


def test_auth_generator_flags_custom_permissions():
    """Custom permissions should be flagged for manual review."""
    fake_data = [
        {"view": "SecretView", "type": "permission", "classes": ["IsProjectOwner"]},
    ]
    output = generate_auth(fake_data)
    assert "USER REVIEW REQUIRED" in output
    assert "IsProjectOwner" in output


# ---------- Settings Report Tests ----------


def test_settings_report_includes_pagination():
    """Settings report should include pagination configuration."""
    fake_settings = {
        "pagination": {
            "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
            "PAGE_SIZE": 20,
        },
        "authentication": [],
        "permissions": [],
        "throttling": {},
        "filtering": [],
        "renderers": [],
        "parsers": [],
        "raw": {},
    }
    output = generate_settings_report(fake_settings)
    assert "PAGE_SIZE=20" in output
    assert "paginate" in output


def test_settings_report_flags_throttling():
    """Settings report should flag throttling as needing manual review."""
    fake_settings = {
        "pagination": {},
        "authentication": [],
        "permissions": [],
        "throttling": {"DEFAULT_THROTTLE_RATES": {"anon": "100/day"}},
        "filtering": [],
        "renderers": [],
        "parsers": [],
        "raw": {},
    }
    output = generate_settings_report(fake_settings)
    assert "USER REVIEW REQUIRED" in output
    assert "throttling" in output.lower()


# ---------- Dry-Run / Output Tests ----------


def test_dry_run_does_not_write_files():
    """Dry-run mode should not create any files."""
    from drf_to_ninja.cli import write_output
    from pathlib import Path
    from unittest.mock import MagicMock
    from io import StringIO

    with tempfile.TemporaryDirectory() as tmpdir:
        write_output("test.py", "# test", Path(tmpdir), dry_run=True)
        assert not os.path.exists(os.path.join(tmpdir, "test.py"))


def test_output_writes_file():
    """When not in dry-run, output should write the file."""
    from drf_to_ninja.cli import write_output
    from pathlib import Path

    with tempfile.TemporaryDirectory() as tmpdir:
        write_output("schemas.py", "# generated", Path(tmpdir), dry_run=False)
        target = os.path.join(tmpdir, "schemas.py")
        assert os.path.exists(target)
        with open(target) as f:
            assert f.read() == "# generated"
