from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import ProductViewSet, OrderViewSet, DashboardView

router = DefaultRouter()
router.register(r"products", ProductViewSet, basename="product")
router.register(r"orders", OrderViewSet, basename="order")

urlpatterns = [
    path("", include(router.urls)),
    path("dashboard/", DashboardView.as_view(), name="dashboard"),
    path("health/", lambda r: None, name="health-check"),
]
