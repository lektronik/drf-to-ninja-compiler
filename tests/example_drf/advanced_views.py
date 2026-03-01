from rest_framework import viewsets, serializers
from rest_framework.decorators import action
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView
from rest_framework.response import Response
from rest_framework.views import APIView


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer

    @action(detail=True, methods=["post"], url_path="add-review")
    def add_review(self, request, pk=None):
        product = self.get_object()
        return Response({"status": "review added"})

    @action(detail=False, methods=["get"])
    def featured(self, request):
        featured = Product.objects.filter(featured=True)
        serializer = self.get_serializer(featured, many=True)
        return Response(serializer.data)


class UserListCreateView(ListCreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class UserDetailView(RetrieveUpdateDestroyAPIView):
    queryset = User.objects.all()
    serializer_class = UserSerializer


class StatsView(APIView):
    def get(self, request):
        return Response({"total_users": 42})
