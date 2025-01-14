from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User



class Specialties(models.Model):
    SpecialtyID=models.AutoField(primary_key=True)
    SpecialtyNam=models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.SpecialtyNam

class Doctor(models.Model):
    DoctorID=models.AutoField(primary_key=True,verbose_name='Dcotor ID')
    FullName=models.CharField(max_length=255,verbose_name='Doctor Name')
    Mobile=models.CharField(max_length=155,null=True)
    SpecialtyID=models.ForeignKey(Specialties,on_delete=models.PROTECT,verbose_name='Speciality Name')
    active=models.BooleanField(default=True)
    image=models.ImageField(upload_to='doctors/photos/%y/%m/%d',null=True,default='photos/doctor.jpg')

    def __str__(self) -> str:
        return self.FullName