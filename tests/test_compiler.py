import pytest
import os
import tempfile
from pathlib import Path
from typer.testing import CliRunner

from drf_to_ninja.parsers.serializers import parse_serializers
from drf_to_ninja.parsers.views import parse_views
from drf_to_ninja.parsers.urls import parse_urls
from drf_to_ninja.parsers.permissions import parse_permissions
from drf_to_ninja.parsers.settings import parse_settings
from drf_to_ninja.generators.schemas import generate_schemas
from drf_to_ninja.generators.routers import generate_routers
from drf_to_ninja.generators.urls import generate_url_wiring
from drf_to_ninja.generators.auth import generate_auth, generate_settings_report
from drf_to_ninja.cli import app

runner = CliRunner()

BASE = "tests/example_drf"


# ============================================================
# Serializer Parser Tests
# ============================================================


class TestSerializerParser:
    def test_basic_model_serializer(self):
        serializers = parse_serializers(f"{BASE}/serializers.py")
        assert len(serializers) == 3

        item = next(s for s in serializers if s["name"] == "ItemSerializer")
        assert item["model"] == "Item"
        assert item["fields"] == ["id", "name", "description", "price"]
        assert not item["needs_review"]

    def test_all_fields(self):
        serializers = parse_serializers(f"{BASE}/serializers.py")
        user = next(s for s in serializers if s["name"] == "UserSerializer")
        assert user["fields"] == "__all__"

    def test_custom_fields_flagged(self):
        serializers = parse_serializers(f"{BASE}/ecommerce_serializers.py")
        order = next(s for s in serializers if s["name"] == "OrderSerializer")
        assert order["needs_review"] is True
        assert any("total" in cf for cf in order["custom_fields"])

    def test_simple_serializer_no_review(self):
        serializers = parse_serializers(f"{BASE}/ecommerce_serializers.py")
        product = next(s for s in serializers if s["name"] == "ProductSerializer")
        assert not product["needs_review"]

    def test_nested_serializer_detected(self):
        serializers = parse_serializers(f"{BASE}/advanced_serializers.py")
        product = next(s for s in serializers if s["name"] == "ProductSerializer")
        assert product["needs_review"] is True
        nested = product.get("nested_serializers", [])
        assert len(nested) == 2
        cat_nested = next(n for n in nested if n["field"] == "category")
        assert cat_nested["serializer"] == "CategorySerializer"
        assert cat_nested["many"] is False
        tags_nested = next(n for n in nested if n["field"] == "tags")
        assert tags_nested["serializer"] == "TagSerializer"
        assert tags_nested["many"] is True

    def test_depth_detected(self):
        serializers = parse_serializers(f"{BASE}/advanced_serializers.py")
        order = next(s for s in serializers if s["name"] == "OrderSerializer")
        assert order["depth"] == 2
        assert order["needs_review"] is True

    def test_simple_nested_no_depth(self):
        serializers = parse_serializers(f"{BASE}/advanced_serializers.py")
        category = next(s for s in serializers if s["name"] == "CategorySerializer")
        assert category["depth"] is None
        assert not category["needs_review"]


# ============================================================
# View Parser Tests
# ============================================================


class TestViewParser:
    def test_basic_apiview(self):
        views = parse_views(f"{BASE}/views.py")
        api_view = next(v for v in views if v["name"] == "CustomAPIView")
        assert api_view["type"] == "APIView"
        assert "get" in api_view["methods"]
        assert "post" in api_view["methods"]

    def test_model_viewset(self):
        views = parse_views(f"{BASE}/views.py")
        vs = next(v for v in views if v["name"] == "ItemViewSet")
        assert vs["type"] == "ModelViewSet"
        assert vs["queryset"] is not None
        assert vs["serializer_class"] == "ItemSerializer"

    def test_custom_method_flagged(self):
        views = parse_views(f"{BASE}/ecommerce_views.py")
        order = next(v for v in views if v["name"] == "OrderViewSet")
        assert order["needs_review"] is True
        assert "get_recent_orders" in order["custom_methods"]

    def test_apiview_multi_method(self):
        views = parse_views(f"{BASE}/ecommerce_views.py")
        dashboard = next(v for v in views if v["name"] == "DashboardView")
        assert sorted(dashboard["methods"]) == ["delete", "get", "post"]

    def test_action_decorator_detected(self):
        views = parse_views(f"{BASE}/advanced_views.py")
        product = next(v for v in views if v["name"] == "ProductViewSet")
        assert len(product["actions"]) == 2

        add_review = next(a for a in product["actions"] if a["name"] == "add_review")
        assert add_review["detail"] is True
        assert add_review["methods"] == ["post"]
        assert add_review["url_path"] == "add-review"

        featured = next(a for a in product["actions"] if a["name"] == "featured")
        assert featured["detail"] is False
        assert featured["methods"] == ["get"]

    def test_generic_list_create_view(self):
        views = parse_views(f"{BASE}/advanced_views.py")
        user_lc = next(v for v in views if v["name"] == "UserListCreateView")
        assert user_lc["type"] == "ListCreateAPIView"
        assert "list" in user_lc["methods"]
        assert "create" in user_lc["methods"]

    def test_generic_retrieve_update_destroy_view(self):
        views = parse_views(f"{BASE}/advanced_views.py")
        user_rud = next(v for v in views if v["name"] == "UserDetailView")
        assert user_rud["type"] == "RetrieveUpdateDestroyAPIView"
        assert sorted(user_rud["methods"]) == ["destroy", "retrieve", "update"]

    def test_plain_apiview_in_advanced(self):
        views = parse_views(f"{BASE}/advanced_views.py")
        stats = next(v for v in views if v["name"] == "StatsView")
        assert stats["type"] == "APIView"
        assert stats["methods"] == ["get"]


# ============================================================
# URL Parser Tests
# ============================================================


class TestURLParser:
    def test_extracts_patterns(self):
        patterns = parse_urls(f"{BASE}/ecommerce_urls.py")
        assert len(patterns) >= 2

    def test_dashboard_route(self):
        patterns = parse_urls(f"{BASE}/ecommerce_urls.py")
        dashboard = next((p for p in patterns if p.get("name") == "dashboard"), None)
        assert dashboard is not None
        assert dashboard["route"] == "dashboard/"

    def test_all_patterns_are_dicts(self):
        patterns = parse_urls(f"{BASE}/ecommerce_urls.py")
        assert all(isinstance(p, dict) for p in patterns)


# ============================================================
# Settings Parser Tests
# ============================================================


class TestSettingsParser:
    def test_pagination(self):
        settings = parse_settings(f"{BASE}/settings.py")
        assert settings["pagination"]["PAGE_SIZE"] == 25
        assert "PageNumberPagination" in settings["pagination"]["DEFAULT_PAGINATION_CLASS"]

    def test_authentication(self):
        settings = parse_settings(f"{BASE}/settings.py")
        auth = settings["authentication"]
        assert any("TokenAuthentication" in c for c in auth)
        assert any("SessionAuthentication" in c for c in auth)

    def test_throttling(self):
        settings = parse_settings(f"{BASE}/settings.py")
        rates = settings["throttling"].get("DEFAULT_THROTTLE_RATES", {})
        assert rates.get("anon") == "100/day"
        assert rates.get("user") == "1000/day"


# ============================================================
# Schema Generator Tests
# ============================================================


class TestSchemaGenerator:
    def test_warning_comment_on_review(self):
        data = [
            {
                "name": "OrderSerializer",
                "model": "Order",
                "fields": ["id", "status"],
                "custom_fields": ["total", "method:get_total"],
                "nested_serializers": [],
                "depth": None,
                "needs_review": True,
            }
        ]
        output = generate_schemas(data)
        assert "USER REVIEW REQUIRED" in output
        assert "OrderSchema" in output

    def test_no_warning_when_clean(self):
        data = [
            {
                "name": "ItemSerializer",
                "model": "Item",
                "fields": ["id", "name"],
                "custom_fields": [],
                "nested_serializers": [],
                "depth": None,
                "needs_review": False,
            }
        ]
        output = generate_schemas(data)
        assert "USER REVIEW" not in output
        assert "ItemSchema" in output

    def test_nested_serializer_in_review(self):
        data = [
            {
                "name": "ProductSerializer",
                "model": "Product",
                "fields": ["id", "name"],
                "custom_fields": [],
                "nested_serializers": [{"field": "tags", "serializer": "TagSerializer", "many": True}],
                "depth": None,
                "needs_review": True,
            }
        ]
        output = generate_schemas(data)
        assert "nested: tags" in output
        assert "many=True" in output

    def test_depth_in_review(self):
        data = [
            {
                "name": "OrderSerializer",
                "model": "Order",
                "fields": "__all__",
                "custom_fields": [],
                "nested_serializers": [],
                "depth": 2,
                "needs_review": True,
            }
        ]
        output = generate_schemas(data)
        assert "depth = 2" in output


# ============================================================
# Router Generator Tests
# ============================================================


class TestRouterGenerator:
    def test_list_and_create(self):
        data = [
            {
                "name": "ProductViewSet",
                "type": "ModelViewSet",
                "methods": ["list", "create"],
                "queryset": "Product.objects.all()",
                "serializer_class": "ProductSerializer",
                "custom_methods": [],
                "actions": [],
                "needs_review": False,
            }
        ]
        output = generate_routers(data)
        assert "def list_product" in output
        assert "def create_product" in output
        assert "ProductSchema" in output

    def test_api_style(self):
        data = [
            {
                "name": "ItemViewSet",
                "type": "ModelViewSet",
                "methods": ["list"],
                "queryset": "Item.objects.all()",
                "serializer_class": "ItemSerializer",
                "custom_methods": [],
                "actions": [],
                "needs_review": False,
            }
        ]
        output = generate_routers(data, style="api")
        assert "@api.get" in output
        assert "NinjaAPI" in output

    def test_router_style_default(self):
        data = [
            {
                "name": "ItemViewSet",
                "type": "ModelViewSet",
                "methods": ["list"],
                "queryset": "Item.objects.all()",
                "serializer_class": "ItemSerializer",
                "custom_methods": [],
                "actions": [],
                "needs_review": False,
            }
        ]
        output = generate_routers(data)
        assert "@router.get" in output

    def test_action_routes_generated(self):
        data = [
            {
                "name": "ProductViewSet",
                "type": "ModelViewSet",
                "methods": ["list"],
                "queryset": "Product.objects.all()",
                "serializer_class": "ProductSerializer",
                "custom_methods": [],
                "actions": [
                    {
                        "name": "add_review",
                        "detail": True,
                        "methods": ["post"],
                        "url_path": "add-review",
                    },
                    {
                        "name": "featured",
                        "detail": False,
                        "methods": ["get"],
                        "url_path": "featured",
                    },
                ],
                "needs_review": False,
            }
        ]
        output = generate_routers(data)
        assert "add-review" in output
        assert "@router.post" in output
        assert "featured" in output
        assert "Custom action" in output

    def test_generic_view_routes(self):
        data = [
            {
                "name": "UserListCreateView",
                "type": "ListCreateAPIView",
                "methods": ["list", "create"],
                "queryset": "User.objects.all()",
                "serializer_class": "UserSerializer",
                "custom_methods": [],
                "actions": [],
                "needs_review": False,
            }
        ]
        output = generate_routers(data)
        assert "def list_userlistcreate" in output
        assert "def create_userlistcreate" in output

    def test_patch_route(self):
        data = [
            {
                "name": "ItemViewSet",
                "type": "ModelViewSet",
                "methods": ["partial_update"],
                "queryset": "Item.objects.all()",
                "serializer_class": "ItemSerializer",
                "custom_methods": [],
                "actions": [],
                "needs_review": False,
            }
        ]
        output = generate_routers(data)
        assert "@router.patch" in output
        assert "def patch_item" in output


# ============================================================
# URL Wiring Generator Tests
# ============================================================


class TestURLWiringGenerator:
    def test_generates_ninja_api(self):
        patterns = [
            {"route": "products/", "view": "ProductViewSet", "name": "products", "is_router": True},
            {"route": "dashboard/", "view": "DashboardView", "name": "dashboard", "is_router": False},
        ]
        output = generate_url_wiring(patterns)
        assert "NinjaAPI" in output
        assert "product" in output


# ============================================================
# Auth Generator Tests
# ============================================================


class TestAuthGenerator:
    def test_maps_known_permissions(self):
        data = [
            {"view": "OrderViewSet", "type": "permission", "classes": ["IsAuthenticated"]},
            {"view": "OrderViewSet", "type": "authentication", "classes": ["TokenAuthentication"]},
        ]
        output = generate_auth(data)
        assert "django_auth" in output
        assert "HttpBearer" in output

    def test_flags_custom_permissions(self):
        data = [
            {"view": "SecretView", "type": "permission", "classes": ["IsProjectOwner"]},
        ]
        output = generate_auth(data)
        assert "USER REVIEW REQUIRED" in output
        assert "IsProjectOwner" in output


# ============================================================
# Settings Report Tests
# ============================================================


class TestSettingsReport:
    def test_includes_pagination(self):
        settings = {
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
        output = generate_settings_report(settings)
        assert "PAGE_SIZE=20" in output

    def test_flags_throttling(self):
        settings = {
            "pagination": {},
            "authentication": [],
            "permissions": [],
            "throttling": {"DEFAULT_THROTTLE_RATES": {"anon": "100/day"}},
            "filtering": [],
            "renderers": [],
            "parsers": [],
            "raw": {},
        }
        output = generate_settings_report(settings)
        assert "USER REVIEW REQUIRED" in output


# ============================================================
# Dry-Run / Output Tests
# ============================================================


class TestOutputModes:
    def test_dry_run_no_files(self):
        from drf_to_ninja.cli import write_output

        with tempfile.TemporaryDirectory() as tmpdir:
            write_output("test.py", "# test", Path(tmpdir), dry_run=True)
            assert not os.path.exists(os.path.join(tmpdir, "test.py"))

    def test_output_writes_file(self):
        from drf_to_ninja.cli import write_output

        with tempfile.TemporaryDirectory() as tmpdir:
            write_output("schemas.py", "# generated", Path(tmpdir), dry_run=False)
            target = os.path.join(tmpdir, "schemas.py")
            assert os.path.exists(target)
            with open(target) as f:
                assert f.read() == "# generated"


# ============================================================
# CLI Integration Tests (CliRunner)
# ============================================================


class TestCLIIntegration:
    def test_no_args_shows_help(self):
        result = runner.invoke(app, [])
        assert result.exit_code == 1
        assert "Oops" in result.output or "provide" in result.output.lower()

    def test_serializers_flag(self):
        result = runner.invoke(app, ["-s", f"{BASE}/serializers.py"])
        assert result.exit_code == 0
        assert "Schema" in result.output

    def test_views_flag(self):
        result = runner.invoke(app, ["-v", f"{BASE}/ecommerce_views.py"])
        assert result.exit_code == 0
        assert "Router" in result.output or "router" in result.output

    def test_dry_run_flag(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                ["-s", f"{BASE}/serializers.py", "-o", tmpdir, "--dry-run"],
            )
            assert result.exit_code == 0
            assert not os.path.exists(os.path.join(tmpdir, "schemas.py"))

    def test_output_flag_writes_files(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                ["-s", f"{BASE}/serializers.py", "-v", f"{BASE}/views.py", "-o", tmpdir],
            )
            assert result.exit_code == 0
            assert os.path.exists(os.path.join(tmpdir, "schemas.py"))
            assert os.path.exists(os.path.join(tmpdir, "api.py"))

    def test_project_flag_scans_directory(self):
        result = runner.invoke(app, ["--project", f"{BASE}"])
        assert result.exit_code == 0
        assert "Scanning" in result.output

    def test_style_api(self):
        result = runner.invoke(
            app,
            ["-v", f"{BASE}/views.py", "--style", "api"],
        )
        assert result.exit_code == 0
        assert "api" in result.output.lower()

    def test_full_compilation(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            result = runner.invoke(
                app,
                [
                    "-s",
                    f"{BASE}/ecommerce_serializers.py",
                    "-v",
                    f"{BASE}/ecommerce_views.py",
                    "-u",
                    f"{BASE}/ecommerce_urls.py",
                    "--settings",
                    f"{BASE}/settings.py",
                    "-o",
                    tmpdir,
                ],
            )
            assert result.exit_code == 0
            assert os.path.exists(os.path.join(tmpdir, "schemas.py"))
            assert os.path.exists(os.path.join(tmpdir, "api.py"))
            assert os.path.exists(os.path.join(tmpdir, "urls.py"))

    def test_advanced_views_compilation(self):
        result = runner.invoke(
            app,
            ["-v", f"{BASE}/advanced_views.py"],
        )
        assert result.exit_code == 0
        assert "add-review" in result.output or "featured" in result.output or "Router" in result.output
