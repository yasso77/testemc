from django.db import models
from django.core.validators import RegexValidator
from django.contrib.auth.models import User

# Create your models here.

# Create your models here.
   
class ClassficationsOptions(models.Model):
    
    classifiedGroup=['A','B','C','D','E']
    
    classifiedID=models.AutoField(db_column='VisitID', primary_key=True)
    classifiedCategory=models.CharField(max_length=2, verbose_name='Classified Category',choices=[(item, item) for item in classifiedGroup])
    optionClassified=models.CharField(max_length=300,verbose_name='Options Classified')
    isActive=models.BooleanField(blank=True, null=True,verbose_name='Is Visiable')
    createdDate = models.DateField(verbose_name='Created Date', blank=True, null=True, auto_now_add=True)
    createdBy = models.ForeignKey(User, verbose_name='Created By', on_delete=models.DO_NOTHING, null=True, blank=True)




    