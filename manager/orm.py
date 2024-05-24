

from multiprocessing import Value

from django.forms import CharField, IntegerField

from manager import models
from datetime import datetime
from django.db.models import Q, F,Case, When, Value, BooleanField,Exists, OuterRef,Subquery


class ORMPatientsHandling():
    

    # TODO: Define fields here
    
    def getPatientsTodayWithNoVisitYet(self):
        # Get today's date
        today = datetime.now().date()

                # Step 1: Get patients who attended today
        patients_attended_today = models.Patient.objects.filter(attendanceDate=today)

        # Step 2: Get patients who do not have a visit date today
        patients_no_visit_today = patients_attended_today.exclude(
            Q(patientvisits__visitdate=today)
        ) 
        
        return patients_no_visit_today
           
           
    
    def getPatientsTodayWithVisitStatus(self):
        # Get today's date
        today = datetime.now().date()

       # Query to get patients who attended today
        patients_today = models.Patient.objects.filter(attendanceDate=today)
        patient_visit=models.PatientVisits.objects.filter(visitdate__date=today,patientid=4)
        for it in patient_visit:
            print (it.evaluationeegree)

        from django.db.models import Subquery, OuterRef

        # Subquery to get evaluation degree for each patient if available
        evaluation_degree_subquery = models.PatientVisits.objects.filter(
            visitdate__date=today,
            patientid=OuterRef('pk')  # Correlate with the patient ID
        ).order_by('-visitdate').values('evaluationeegree')[:1]  # Fetch the latest evaluation degree

        # Query to get patients who attended today with evaluation degree if available
        patients_today_with_evaluation_degree = models.Patient.objects.filter(
            attendanceDate=today
        ).annotate(
            evaluation_degree=Subquery(evaluation_degree_subquery)
        )

        return patients_today_with_evaluation_degree


        











    def __str__(self):
       
        pass
