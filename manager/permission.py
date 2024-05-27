from django.db import models

class PublichManagerPerm(models.Model):
    # Define fields here

    class Meta:
        permissions = (
            ("UploadPatientFile", "Can upload patient files"),
            ("LiveReport", "Can view live report"),
            ("ShowPatientReport","Show Patient Report")
        )

    def __str__(self):
        return "PublichManagerPerm"

   
class PublichDoctorsPerm(models.Model):
   
    # TODO: Define fields here

    class Meta:
        permissions = (("addNewVisitForPatient", "Record a Visit"),)

    def __str__(self):        
        return "PublichDoctorsPerm"
    
class PublicReceptionistPerm(models.Model):
   
    # TODO: Define fields here

    class Meta:
        permissions = (("AddNewPatient", "Add New Patient"),("UpdatePatinetData", "Update Patient Data"))

    def __str__(self):        
        pass