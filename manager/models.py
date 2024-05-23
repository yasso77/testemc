from django.db import models
from django.core.validators import RegexValidator

# Create your models here.

# Create your models here.
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

class PatientVisits(models.Model):
    
    visitid = models.AutoField(db_column='VisitID', primary_key=True)  # Field name made lowercase.
    patientid = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='PatientID', blank=True, null=True)
    doctorid = models.ForeignKey(Doctor,on_delete=models.DO_NOTHING,  db_column='DoctorID', blank=True, null=True)  # Field name made lowercase.
    visitdate = models.DateTimeField(db_column='VisitDate', blank=True, null=True)  # Field name made lowercase.
    reasonforvisit = models.TextField(db_column='ReasonForVisit', blank=True, null=True)  # Field name made lowercase.
    diagnosis = models.TextField(db_column='Diagnosis', blank=True, null=True)  # Field name made lowercase.
    treatment = models.TextField(db_column='Treatment', blank=True, null=True)  # Field name made lowercase.
    followup = models.BooleanField( db_column='FollowUp', blank=True, null=True)  # Field name made lowercase.
    evaluationeegree = models.CharField(db_column='EvaluationDegree',max_length=1, blank=True, null=True)  # Field name made lowercase.
    createdate = models.DateField(db_column='CreateDate', blank=True, null=True)  # Field name made 