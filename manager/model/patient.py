from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User
from django.utils.timezone import now


class CityManager(models.Manager):
        def active(self):
            return self.filter(isVisible=True)

class AgentCompanyManager(models.Manager):
     def active(self):
            return self.filter(isVisible=True)
class OffersManager(models.Manager):
        def active(self):
            return self.filter(isVisible=True)
class CheckUpPriceManager(models.Manager):
    def active(self):
            return self.filter(isVisible=True)
class SufferedCasesManager(models.Manager):
        def active(self):
            return self.filter(isVisible=True)      

class CheckUpPrice(models.Model):
    checkupPriceID=models.AutoField(primary_key=True)
    checkupPriceName=models.CharField(max_length=350, blank=True, null=True,verbose_name='check-Up Price')
    isVisible=models.BooleanField(blank=True,null=True,verbose_name='Visible')    
    createdDate=models.DateField(auto_now_add=True,verbose_name='Created date')
    
    objects = CheckUpPriceManager()
    def __str__(self):
        return self.checkupPriceName
    class Meta:
        verbose_name='Check-Up Price'
        verbose_name_plural = "Check-Up Prices"
    

class City(models.Model):    
    cityID=models.AutoField(primary_key=True)
    cityName=models.CharField(max_length=100, blank=True, null=True,verbose_name='City Name')
    isVisible=models.BooleanField(blank=True,null=True,verbose_name='Visible')
    createdDate=models.DateField(auto_now_add=True,verbose_name='Created date')
    
    objects = CityManager()
    def __str__(self):
        return self.cityName
    class Meta:
        verbose_name='City'
        verbose_name_plural = "Cities"


class AgentCompany(models.Model):    
    agentID=models.AutoField(primary_key=True)
    AgentCompany=models.CharField(max_length=200, blank=True, null=True,verbose_name='Agent Company Name')
    isVisible=models.BooleanField(blank=True,null=True,verbose_name='Visible')
    createdDate=models.DateField(auto_now_add=True,verbose_name='Created date')
    
    objects = AgentCompanyManager()
    def __str__(self):
        return self.AgentCompany
    class Meta:
        verbose_name='Agent-Company'
        verbose_name_plural = "Agent-Company"    
         
class Offers(models.Model):    
    offerID=models.AutoField(primary_key=True)
    offerName=models.CharField(max_length=350, blank=True, null=True,verbose_name='Offer Name')
    isVisible=models.BooleanField(blank=True,null=True,verbose_name='Visible')
    validFromDate=models.DateField(verbose_name='Valid from',blank=True,null=True)
    validToDate=models.DateField(verbose_name='Valid To',blank=True,null=True)
    createdDate=models.DateField(auto_now_add=True,verbose_name='Created date')
    
    objects = OffersManager()
    def __str__(self):
        return self.offerName
    class Meta:
        verbose_name='Offer'
        verbose_name_plural = "Offers"
        
class SufferedCases(models.Model):    
    sufferedcaseID=models.AutoField(primary_key=True)
    caseName=models.CharField(max_length=350, blank=True, null=True,verbose_name='Case Name')
    isVisible=models.BooleanField(blank=True,null=True,verbose_name='Visible')
    createdDate=models.DateField(auto_now_add=True,verbose_name='Created date')
    
    objects = SufferedCasesManager()
    def __str__(self):
        return self.caseName
    class Meta:
        verbose_name='Suffered Case'
        verbose_name_plural = "Suffered Cases"


class PatientManager(models.Manager):
        def active(self):
            return self.filter(isDeleted=False)
class Patient(models.Model):

   
    GENDER_CHOICES = [
        ('M', 'Male'),
        ('F', 'Female'),
    ]
    YesNo_CHOICES=[
        ('Y', 'Yes'),
        ('N', 'No'),
        
    ]    
    leadSource_Choices=[('Facebook','Facebook'),('Whatsapp','Whatsapp'),('Youtube','Youtube'),('Newspaper','Newspaper'),('Friend','Friend'),('Call','Call'),('Instagram','Instagram')]
    
    CallDirection_CHOICES=[
        ('IN','INCOMING- Patient Call'),
        ('OUT','OUTGOING - Call Center Call'),
        
    ]
    
    reservations_CHOICES=[
        ('FV','First Visit'),
        ('FX','Follow-up Re-examination'),
        ('FS','Follow-up Eye surgery'),
        
    ] 
    
    referral_CHOICES=[
        ('W','Walk-In'),
        ('R','Referred by someone'),
     ]       

    patientid = models.AutoField(primary_key=True)  # Field name made lowercase.
    reservationCode = models.CharField( max_length=150, blank=False, null=True,verbose_name='Confirmation Code',error_messages='Reservation code is requiered')
    fileserial = models.CharField( max_length=150, blank=False, null=True,verbose_name='File Number',error_messages='The Patient file number is requiered')  # Field name made lowercase.
    reservationType=models.CharField(max_length=150,choices=reservations_CHOICES,verbose_name='Reservation Type',default=reservations_CHOICES[1][0],null=True)
    referral=models.CharField(max_length=150,choices=referral_CHOICES,verbose_name='Referral',default=referral_CHOICES[1][0],null=True)
    leadSource=models.CharField(choices=leadSource_Choices,max_length=100, verbose_name='Lead Source',null=True, blank=True)
    fullname = models.CharField(max_length=250, blank=False, null=True,verbose_name='Patient Name')  # Field name made lowercase.
    
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES, null=True, blank=True)
    image=models.ImageField(upload_to='patients/photos/%y/%m/%d',null=True,default='photos/patient.png')
    mobile = models.CharField(max_length=15, validators=[RegexValidator(r'^\d{1,15}$', 'Enter a valid mobile number.')], null=False, blank=False,default=000)  # Field name made lowercase.
    otherMobile= models.CharField(max_length=15, validators=[RegexValidator(r'^\d{1,15}$', 'Enter a valid mobile number.')], null=True, blank=True) 
    address = models.CharField(max_length=1000, blank=True, null=True,verbose_name='Address')  # Field name made lowercase.
    city = models.ForeignKey(City,blank=True, null=True,on_delete=models.SET_NULL,verbose_name='City Name')  # Field name made lowercase.
    email = models.CharField(max_length=150, blank=True, null=True,verbose_name='Email')  # Field name made lowercase.  
    checkUpprice =models.ForeignKey(CheckUpPrice, null=True, on_delete=models.DO_NOTHING,related_name='Check_UpPrice')
    reservedBy = models.ForeignKey(User, on_delete=models.DO_NOTHING,related_name='reserved_patients')  # Field name made lowercase.
    offerID = models.ForeignKey(Offers,blank=True, null=True,on_delete=models.DO_NOTHING,related_name='offers_related')  
    agentID=models.ForeignKey(AgentCompany,blank=True, null=True,on_delete=models.DO_NOTHING,related_name='agent_related',verbose_name='Agent/Company')  
    sufferedcase = models.ForeignKey(
        SufferedCases,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Suffered Case'
    )
    sufferedcaseByPatient = models.ForeignKey(
        SufferedCases,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        verbose_name='Suffered Case by Patient',
        related_name='caseBypatient'
    )
    arrivedOn = models.CharField(max_length=150, blank=True, null=True,)  # Field name made lowercase.
    remarks = models.CharField(max_length=2055, blank=True, null=True,verbose_name='Remarks')
    
    age=models.IntegerField(validators=[RegexValidator(r'^\d{1,15}$', 'Enter a valid mobile number.')], null=True,  # Allows NULL values in the database
    blank=True,verbose_name='Age')  # Allows blank values in forms,verbose_name='Age')  # Field name made lowercase.
    birthdate = models.DateField( blank=True, null=True,verbose_name='Birth Date')
    callDirection=models.CharField(max_length=5,choices=CallDirection_CHOICES,verbose_name='Call Direction',default=CallDirection_CHOICES[1][0],null=True)
    expectedDate = models.DateField( blank=True, null=True,verbose_name='Expected Date')  # Field name made lowercase.
      # Field name made lowercase.
    attendanceDate = models.DateTimeField(blank=True, null=True,verbose_name='Actual Attendance  Date')  # Field name made lowercase.
    rideglass = models.CharField(max_length=1, choices=YesNo_CHOICES, null=True, blank=True,verbose_name='Ride Of Glass')
    wearingconduct = models.CharField(max_length=1, choices=YesNo_CHOICES, null=True, blank=True,verbose_name='WEaring Conduct')
    createdBy = models.ForeignKey(User,blank=True, null=True,on_delete=models.DO_NOTHING,related_name='created_patients')  # Field name made lowercase.
    createdDate = models.DateTimeField(auto_now_add=True)

    latestupdate = models.DateField( blank=True, null=True)  # Field name made lowercase.
    updatedby = models.IntegerField( blank=True, null=True)  # Field name made lowercase.
    isDeleted = models.BooleanField(default=False)
    formPrinted = models.BooleanField(default=False)
    
    objects = PatientManager()
    
    

    def __str__(self):
        return self.fullname
    class Meta:
        verbose_name='Patients'
        ordering=['-fullname']
        
        
class CallTrack(models.Model):    
    
    outcomeStatus= [
            ('Canceled', 'Canceled'),
            ('Rescheduled', 'Rescheduled'),
            ('Confirmed','Confirmed'),
            ('Re-examination','Re-examination'),
            ('Eye surgery','Eye surgery'),
            ('After surgery','After surgery')
            ]
    
    trackTypes=[('CC','Call Center'),('CE','Center'),('MK','Marketing')]
    
    
    callTrackID=models.AutoField(primary_key=True)
    trackType=models.CharField(max_length=100, blank=True, null=True,verbose_name='Track Type',choices=trackTypes)
    patientID=models.ForeignKey(Patient,blank=True, null=True,on_delete=models.DO_NOTHING,related_name='call_patients')
    remarks=models.CharField(max_length=500, blank=True, null=True,verbose_name='Call Remarks')
    nextFollow=models.DateField(verbose_name='Next Follow-Up Date', blank=True, null=True) 
    confirmationDate = models.DateField(verbose_name='Confirmation Date', blank=True, null=True) 
    outcome=models.CharField(max_length=100, blank=True, null=True,verbose_name='Outcome of Follow-Up',choices=outcomeStatus)
    agentID=models.ForeignKey(User,blank=True, null=True,on_delete=models.DO_NOTHING,related_name='agent_agent')
    createdBy=models.ForeignKey(User,blank=True, null=True,on_delete=models.DO_NOTHING,related_name='call_agent')
    createdDate=models.DateField(auto_now_add=True,verbose_name='Created date')
    
  
    def __str__(self):
        return self.remarks
    class Meta:
        verbose_name='Call Track'
        verbose_name_plural = "Call Tracks"
        
class MedicalCondition(models.Model):
    
    conditionName = models.CharField(max_length=100, primary_key=True)

    def __str__(self):
        return self.conditionName
    
class PatientMedicalHistory(models.Model):
    RELATION_CHOICES = [
        ('SELF', 'Self'),
        ('REL', 'Relative'),
    ]

    patient = models.ForeignKey(Patient, on_delete=models.CASCADE)
    condition = models.ForeignKey(MedicalCondition, on_delete=models.CASCADE)
    relation = models.CharField(max_length=10, choices=RELATION_CHOICES)
    createdBy=models.ForeignKey(User,blank=True, null=True,on_delete=models.DO_NOTHING,related_name='creator')
    createdDate=models.DateField(auto_now_add=True,verbose_name='Created date')

           

    def __str__(self):
        return f"{self.patient} - {self.condition} ({self.relation})"
        
    
        
        
