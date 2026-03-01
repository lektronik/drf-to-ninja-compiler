"""
Real-world DRF views fixture — based on a production e-commerce API.
Tests complex patterns: ModelViewSet with queryset/serializer_class,
APIView with multiple HTTP methods, and custom action overrides.
"""

from rest_framework import viewsets, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all()
    serializer_class = OrderSerializer

    def list(self, request):
        return super().list(request)

    def create(self, request):
        return super().create(request)

    def retrieve(self, request, pk=None):
        return super().retrieve(request, pk)

    def update(self, request, pk=None):
        return super().update(request, pk)

    def destroy(self, request, pk=None):
        return super().destroy(request, pk)

    def get_recent_orders(self, request):
        """Custom action — should be flagged for manual review."""
        qs = self.queryset.order_by("-created_at")[:10]
        serializer = self.serializer_class(qs, many=True)
        return Response(serializer.data)


class DashboardView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({"message": "Dashboard data"})

    def post(self, request):
        return Response({"message": "Action performed"}, status=status.HTTP_201_CREATED)

    def delete(self, request):
        return Response(status=status.HTTP_204_NO_CONTENT)
