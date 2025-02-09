from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User



class Specialties(models.Model):
    specialtyID=models.AutoField(primary_key=True)
    specialtyName=models.CharField(max_length=255)

    def __str__(self) -> str:
        return self.SpecialtyNam

class Doctor(models.Model):
    doctorID=models.AutoField(primary_key=True,verbose_name='Dcotor ID')
    fullName=models.CharField(max_length=255,verbose_name='Doctor Name')
    mobile=models.CharField(max_length=155,null=True)
    specialtyID=models.ForeignKey(Specialties,on_delete=models.PROTECT,verbose_name='Speciality Name',default=1)
    active=models.BooleanField(default=True)
    image=models.ImageField(upload_to='doctors/photos/%y/%m/%d',null=True,default='photos/doctor.jpg')

    def __str__(self) -> str:
        return self.fullName