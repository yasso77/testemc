from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

class City(models.Model):
    
    cityID=models.AutoField(primary_key=True)
    cityName=models.CharField(max_length=100, blank=True, null=True,verbose_name='City Name')
    isVisible=models.BooleanField(blank=True,null=True)
    createdDate=models.DateField(blank=True,null=True)
    
    def __str__(self):
        return self.cityName
    class Meta:
        verbose_name='Cities'
        
class Patient(models.Model):

   
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    YesNo_CHOICES=[
        ('Y', 'Yes'),
        ('N', 'No'),
        
    ]    
    leadSource_Choices=[('Facebook','Facebook'),('Whatsapp','Whatsapp'),('Youtube','Youtube'),('Newspaper','Newspaper'),('Friend','Friend')]

    patientid = models.AutoField(primary_key=True)  # Field name made lowercase.
    reservationCode = models.CharField( max_length=150, blank=False, null=True,verbose_name='Confirmation Code',error_messages='Reservation code is requiered')
    fileserial = models.CharField( max_length=150, blank=False, null=True,verbose_name='File Number',error_messages='The Patient file number is requiered')  # Field name made lowercase.
    leadSource=models.CharField(choices=leadSource_Choices,max_length=100, verbose_name='Lead Source',null=True, blank=True)
    fullname = models.CharField(max_length=250, blank=False, null=True,verbose_name='Patient Name')  # Field name made lowercase.
    birthdate = models.DateField( blank=False, null=True,verbose_name='Birth Date')  # Field name made lowercase.
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    image=models.ImageField(upload_to='patients/photos/%y/%m/%d',null=True,default='photos/patient.png')
    mobile = models.CharField(max_length=15, validators=[RegexValidator(r'^\d{1,15}$', 'Enter a valid mobile number.')], null=False, blank=False,default=000)  # Field name made lowercase.
    address = models.CharField(max_length=1000, blank=True, null=True,verbose_name='Address')  # Field name made lowercase.
    city = models.ForeignKey(City,blank=True, null=True,on_delete=models.SET_NULL,verbose_name='City Name')  # Field name made lowercase.
    email = models.CharField(max_length=150, blank=True, null=True,verbose_name='Email')  # Field name made lowercase.   
    reservedBy = models.ForeignKey(User, on_delete=models.DO_NOTHING)  # Field name made lowercase.
    arrivedOn = models.CharField(max_length=150, blank=True, null=True)  # Field name made lowercase.
    remarks = models.CharField(max_length=2055, blank=True, null=True,verbose_name='Remarks')
    sufferedcase = models.CharField(max_length=255, blank=True, null=True,verbose_name='Case')   # Field name made lowercase.
    age=models.IntegerField(validators=[RegexValidator(r'^\d{1,15}$', 'Enter a valid mobile number.')], null=False, blank=False,default=0,verbose_name='Age')  # Field name made lowercase.
    expectedDate = models.DateField( blank=True, null=True,verbose_name='Expected Date')  # Field name made lowercase.
    confirmationDate = models.DateField(verbose_name='Confirmation Date', blank=True, null=True)  # Field name made lowercase.
    attendanceDate = models.DateField(blank=True, null=True,verbose_name='Actual Attendance  Date')  # Field name made lowercase.
    rideglass = models.CharField(max_length=1, choices=YesNo_CHOICES, null=True, blank=True,verbose_name='Ride Of Glass')
    wearingconduct = models.CharField(max_length=1, choices=YesNo_CHOICES, null=True, blank=True,verbose_name='WEaring Conduct')
    createdby = models.CharField(max_length=100, blank=True, null=True)  # Field name made lowercase.
    latestupdate = models.DateField( blank=True, null=True)  # Field name made lowercase.
    updatedby = models.IntegerField( blank=True, null=True)  # Field name made lowercase.

    def __str__(self):
        return self.fullname
    class Meta:
        verbose_name='Patients'
        ordering=['-fullname']
        
        
