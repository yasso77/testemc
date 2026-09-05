from django.db import models
from django.contrib.auth.models import User
from manager.model.patient import Patient

class ClassficationsOptions(models.Model):
    
    classifiedGroup=['OK','++','Surgery','6/6','Bad']
    
    classifiedID=models.AutoField(db_column='VisitID', primary_key=True)
    classifiedCategory=models.CharField(max_length=20, verbose_name='Classified Category',choices=[(item, item) for item in classifiedGroup])
    optionClassified=models.CharField(max_length=300,verbose_name='Options Classified')
    isActive=models.BooleanField(blank=True, null=True,verbose_name='Is Visiable')
    createdDate = models.DateField(verbose_name='Created Date', blank=True, null=True, auto_now_add=True)
    createdBy = models.ForeignKey(User, verbose_name='Created By', on_delete=models.DO_NOTHING, null=True, blank=True)


class PatientVisits(models.Model):
    
    visitid = models.AutoField(db_column='VisitID', primary_key=True)  # Field name made lowercase.
    patientid = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='PatientID', blank=True, null=True, related_name='patientvisits')  # Note the related_name db_column='PatientID', blank=True, null=True)
    visittype=models.CharField(max_length=2,blank=True,null=True)
    doctorid = models.ForeignKey(User,on_delete=models.DO_NOTHING,  db_column='DoctorID', blank=True, null=True)  # Field name made lowercase.
    visitdate = models.DateField(db_column='VisitDate', blank=True, null=True)  # Field name made lowercase.
    reasonforvisit = models.TextField(db_column='ReasonForVisit', blank=True, null=True)  # Field name made lowercase.
    diagnosis = models.TextField(db_column='Diagnosis', blank=True, null=True)  # Field name made lowercase.
    treatment = models.TextField(db_column='Treatment', blank=True, null=True)  # Field name made lowercase.
    followup = models.BooleanField( db_column='FollowUp', blank=True, null=True)  # Field name made lowercase.
    evaluationeegree = models.CharField(db_column='EvaluationDegree',max_length=20, blank=True, null=True)  # Field name made lowercase.
    classifiedID=models.ForeignKey(ClassficationsOptions,blank=True, null=True, verbose_name='Classified Option',on_delete=models.DO_NOTHING)
    createdate = models.DateField(db_column='CreateDate', blank=True, null=True)  # Field name made 
    updatedDate= models.DateField(db_column='updatedDate', blank=True, null=True)  # Field name made 
    operationType = models.ForeignKey(
        'OperationType',
        on_delete=models.DO_NOTHING,
        blank=True,
        null=True,
        db_constraint=False,
        related_name='patient_visits',
        verbose_name='نوع العملية',
    )
    discussionNotes = models.TextField(blank=True, null=True, verbose_name='ملاحظات للديسكشن')



class OperationType(models.Model):
    operationTypeID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name='Operation Type')
    isActive = models.BooleanField(default=True, verbose_name='Is Active')
    createdDate = models.DateField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Operation Type'
        verbose_name_plural = 'Operation Types'


class DiscussionResult(models.Model):
    discussionResultID = models.AutoField(primary_key=True)
    name = models.CharField(max_length=200, verbose_name='Discussion Result')
    isActive = models.BooleanField(default=True, verbose_name='Is Active')
    createdDate = models.DateField(auto_now_add=True, blank=True, null=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Discussion Result'
        verbose_name_plural = 'Discussion Results'


class PatientDiscussion(models.Model):
    discussionID = models.AutoField(primary_key=True)
    discussionSerial = models.CharField(
        max_length=150,
        unique=True,
        verbose_name='Discussion Serial',
    )
    patient = models.ForeignKey(
        Patient, on_delete=models.CASCADE, related_name='discussions', blank=True, null=True
    )
    doctor = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name='discussions', blank=True, null=True
    )
    doctorName = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name='اسم الطبيب',
    )
    operationType = models.ForeignKey(
        OperationType, on_delete=models.DO_NOTHING, blank=True, null=True, verbose_name='Operation Type'
    )
    EYE_CHOICES = [
        ('OS', 'OS'),
        ('OD', 'OD'),
        ('OU', 'OU'),
    ]
    eyeSelection = models.CharField(
        max_length=2,
        choices=EYE_CHOICES,
        blank=True,
        null=True,
        verbose_name='تحديد العين',
    )
    specifyDate = models.DateField(blank=True, null=True, verbose_name='Specify Date')
    discussionResult = models.ForeignKey(
        DiscussionResult, on_delete=models.DO_NOTHING, blank=True, null=True, verbose_name='Discussion Result'
    )
    note = models.TextField(blank=True, null=True, verbose_name='Note')
    totalAmount = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    deposit = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    remainder = models.DecimalField(max_digits=12, decimal_places=2, blank=True, null=True)
    createdDate = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    createdBy = models.ForeignKey(
        User, on_delete=models.DO_NOTHING, related_name='created_discussions', blank=True, null=True
    )
    receiptNo = models.PositiveIntegerField(blank=True, null=True, unique=True, verbose_name='Receipt No')

    def __str__(self):
        return self.discussionSerial or str(self.discussionID)

    class Meta:
        verbose_name = 'Patient Discussion'
        verbose_name_plural = 'Patient Discussions'

   