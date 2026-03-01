from rest_framework import viewsets
from rest_framework.views import APIView
from rest_framework.response import Response


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer


class CustomAPIView(APIView):
    def get(self, request):
        return Response({"message": "Hello"})

    def post(self, request):
        return Response({"message": "Created"})
