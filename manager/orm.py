from manager import models
from datetime import datetime
from django.db.models import Q,OuterRef,Subquery,F
from datetime import datetime, date
from manager.model.patient import Patient
from manager.model.visit import PatientVisits


class ORMPatientsHandling():    

    # TODO: Define fields here
    
    def getPatientsTodayWithNoVisitYet(self):
        # Get today's date
        today = datetime.now().date()

                # Step 1: Get patients who attended today
        patients_attended_today = Patient.objects.filter(expectedDate=today)

        # Step 2: Get patients who do not have a visit date today
        patients_no_visit_today = patients_attended_today.exclude(
            Q(patientvisits__visitdate=today)
        ) 
        
        return patients_no_visit_today
           
    
    def getPatientsAttendedToday(self):
        # Get today's date
                
        today = datetime.now().date()  # Get today's date
        FALLBACK_DATE = date(1900, 1, 1)  # Ensure using 'date' and not 'datetime.date'

        patients_attended_today = Patient.objects.filter(
           Q(expectedDate=today) |Q(attendanceDate=today)
        ).exclude(fileserial__isnull=True)

        # Step 2: Get patients who do not have a visit date today
        patients_no_visit_today = patients_attended_today.exclude(
            Q(patientvisits__visitdate=today)
        ) 
        
        return patients_no_visit_today   
    
    def getPatientsForDoctorExam(self):
        # Get today's date
                
        today = datetime.now().date()  # Get today's date
        FALLBACK_DATE = date(1900, 1, 1)  # Ensure using 'date' and not 'datetime.date'

        # Get Patients who have a visit today with visittype='D'
        patients_with_d_visit_today = Patient.objects.filter(
            patientvisits__visitdate=today,
            patientvisits__visittype='A'
        ).distinct()
        #print(patients_with_d_visit_today.query)
        return patients_with_d_visit_today         
    
    def getPatientsTodayWithVisitStatus(self):
        # Get today's date
        today = datetime.now().date()

        # Subquery to get evaluation degree for each patient if available
        evaluation_degree_subquery = PatientVisits.objects.filter(
            visitdate__date=today,
            patientid=OuterRef('pk')  # Correlate with the patient ID
        ).order_by('-visitdate').values('evaluationeegree')[:1]  # Fetch the latest evaluation degree

        # Query to get patients who attended today with evaluation degree if available
        patients_today_with_evaluation_degree = Patient.objects.filter(
            attendanceDate=today
        ).annotate(
            evaluation_degree=Subquery(evaluation_degree_subquery)
        )

        return patients_today_with_evaluation_degree

    def expectedPatientToday(self):
        
          today = datetime.now().date()    
          patients_today = Patient.objects.filter(expectedDate=today)          
          return patients_today  
      
    def get_all_Patients_Between_Period(self,fromdate,todate):         


        queryset = Patient.objects.filter(
            expectedDate__gte=fromdate,
            expectedDate__lte=todate
        ).prefetch_related('patientvisits').filter(
            Q(patientvisits__isnull=True) | Q(patientvisits__patientid=F('patientid'))
        ).distinct()

        return queryset
    


    def __str__(self):
       
        pass
