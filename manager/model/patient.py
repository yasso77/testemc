from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
class Patient(models.Model):

    ComingSource=[('Facebook','Facebook'),('Newspaper','Newspaper'),('Friend','Friend')]
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    YesNo_CHOICES=[
        ('Y', 'Yes'),
        ('N', 'No'),
        
    ]

    patientid = models.AutoField(db_column='PatientID', primary_key=True)  # Field name made lowercase.
    fileserial = models.CharField(db_column='FileSerial', max_length=150, blank=False, null=True,verbose_name='File Number',error_messages='The Patient file number is requiered')  # Field name made lowercase.
    fullname = models.CharField(db_column='FullName', max_length=150, blank=False, null=True,verbose_name='Patient Name')  # Field name made lowercase.
    birthdate = models.DateField(db_column='BirthDate', blank=False, null=True,verbose_name='Birth Date')  # Field name made lowercase.
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    image=models.ImageField(upload_to='patients/photos/%y/%m/%d',null=True,default='photos/patient.png')
    mobile = models.CharField(max_length=15, validators=[RegexValidator(r'^\d{1,15}$', 'Enter a valid mobile number.')], null=False, blank=False,default=000)  # Field name made lowercase.
    address = models.CharField(db_column='Address', max_length=1000, blank=True, null=True)  # Field name made lowercase.
    city = models.CharField(db_column='City',max_length=150, blank=True, null=True)  # Field name made lowercase.
    email = models.CharField(db_column='Email', max_length=150, blank=True, null=True)  # Field name made lowercase.
    comingsource=models.CharField(max_length=100,blank=True,null=True,choices=ComingSource)
    reservedBy = models.CharField(db_column='ReservedBy', max_length=150, blank=True, null=True)  # Field name made lowercase.
    arrivedOn = models.CharField(db_column='ArrivedOn', max_length=150, blank=True, null=True)  # Field name made lowercase.
    remarks = models.CharField(db_column='Remarks', max_length=2055, blank=True, null=True)
    sufferedcase = models.CharField(db_column='SufferedCase', max_length=255, blank=True, null=True)   # Field name made lowercase.
    age=models.IntegerField(db_column='Age', validators=[RegexValidator(r'^\d{1,15}$', 'Enter a valid mobile number.')], null=False, blank=False,default=0)  # Field name made lowercase.
    expectedDate = models.DateField(db_column='ExpectedDate', blank=True, null=True)  # Field name made lowercase.
    attendanceDate = models.DateField(db_column='AttendanceDate', blank=True, null=True)  # Field name made lowercase.
    rideglass = models.CharField(db_column='RideGlass',max_length=1, choices=YesNo_CHOICES, null=True, blank=True)
    wearingconduct = models.CharField(db_column='WearingConduct',max_length=1, choices=YesNo_CHOICES, null=True, blank=True)
    createdby = models.CharField(db_column='CreatedBy',max_length=100, blank=True, null=True)  # Field name made lowercase.
    latestupdate = models.DateField(db_column='LatestUpdate', blank=True, null=True)  # Field name made lowercase.
    updatedby = models.IntegerField(db_column='UpdatedBy', blank=True, null=True)  # Field name made lowercase.

    def __str__(self):
        return self.fullname
    class Meta:
        verbose_name='Patients'
        ordering=['-fullname']