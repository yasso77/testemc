# serializers.py
from rest_framework import serializers

from manager.model.patient import Patient


class PatientReservationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ['fullname', 'mobile', 'gender']  # Add more if needed

    def create(self, validated_data):
        import random
        import string

        # توليد كود حجز عشوائي مثلاً 8 أرقام + أحرف
        reservation_code = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
        patient = Patient.objects.create(
            reservationCode=reservation_code,
            fileserial='AUTO',  # أو قم بتوليدها حسب نظامك
            reservationType='LASIK',  # أو احصل عليها من validated_data إذا أرسلت من العميل
            fullname=validated_data['fullname'],
            mobile=validated_data['mobile'],
            gender=validated_data.get('gender')
        )
        return patient
