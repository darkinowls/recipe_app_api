from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework.views import APIView


@api_view(["GET"])
def get_health_check_view(_):
    return Response(status=200)
