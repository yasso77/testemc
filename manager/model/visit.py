from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

from manager.model.doctor import Doctor
from manager.model.patient import Patient
from manager.models import ClassficationsOptions





class PatientVisits(models.Model):
    
    visitid = models.AutoField(db_column='VisitID', primary_key=True)  # Field name made lowercase.
    patientid = models.ForeignKey(Patient, on_delete=models.CASCADE, db_column='PatientID', blank=True, null=True, related_name='patientvisits')  # Note the related_name db_column='PatientID', blank=True, null=True)
    visittype=models.CharField(max_length=2,blank=True,null=True)
    doctorid = models.ForeignKey(Doctor,on_delete=models.DO_NOTHING,  db_column='DoctorID', blank=True, null=True)  # Field name made lowercase.
    visitdate = models.DateTimeField(db_column='VisitDate', blank=True, null=True)  # Field name made lowercase.
    reasonforvisit = models.TextField(db_column='ReasonForVisit', blank=True, null=True)  # Field name made lowercase.
    diagnosis = models.TextField(db_column='Diagnosis', blank=True, null=True)  # Field name made lowercase.
    treatment = models.TextField(db_column='Treatment', blank=True, null=True)  # Field name made lowercase.
    followup = models.BooleanField( db_column='FollowUp', blank=True, null=True)  # Field name made lowercase.
    evaluationeegree = models.CharField(db_column='EvaluationDegree',max_length=1, blank=True, null=True)  # Field name made lowercase.
    classifiedID=models.ForeignKey(ClassficationsOptions,blank=True, null=True, verbose_name='Classified Option',on_delete=models.DO_NOTHING)
    createdate = models.DateField(db_column='CreateDate', blank=True, null=True)  # Field name made 
    


   