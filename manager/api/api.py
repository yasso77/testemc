# views.py
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from .serializers import PatientReservationSerializer

class ReservePatientAPIView(APIView):
    def post(self, request):
        serializer = PatientReservationSerializer(data=request.data)
        if serializer.is_valid():
            patient = serializer.save()
            return Response({
                "success": True,
                "reservation_number": patient.reservationCode,
                "name": patient.fullname,
                "mobile": patient.mobile
            }, status=status.HTTP_201_CREATED)
        return Response({"success": False, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)
