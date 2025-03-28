import datetime  # Use fully qualified import for datetime
from django.shortcuts import  render
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
  # Import from the package, not the specific file
from manager.decorators import permission_required_with_redirect
from manager.model.doctor import Doctor
from manager.model.patient import Patient
from manager.model.visit import ClassficationsOptions, PatientVisits
from django.shortcuts import get_object_or_404
from manager.orm import ORMPatientsHandling
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from datetime import date, timedelta
from django.utils import timezone
ormObj=ORMPatientsHandling()


class DoctorView(ListView):
    
    #@permission_required_with_redirect('manager.addNewVisitForPatient',login_url='/no-permission/')
    @login_required   
    def doctorPatientvisit(request): 
        classifiedOptions = ClassficationsOptions.objects.filter(isActive=True).values(
            'classifiedID', 'classifiedCategory', 'optionClassified', 'isActive'
        )
        
        classifiedOptionsJSON = json.dumps(list(classifiedOptions), cls=DjangoJSONEncoder)

        if request.method == 'POST':
            txtpatientid = request.POST.get('hdfpatientid')
            doctorid = request.user  # Static doctor ID for now; replace with actual data.
            txtdiagnosis = request.POST.get('Diagnosis')
            EvaulDegree = request.POST.get('gridRadios')
            txtRemarks = request.POST.get('txtRemarks')
            hdfclassifiedID = request.POST.get('selectedOption')
        

            patient = Patient.objects.get(pk=txtpatientid)
            doctor = Doctor.objects.get(pk=doctorid)
            visit_date = timezone.now().date()  # Use fully qualified datetime
            objclassifiedID = get_object_or_404(ClassficationsOptions, pk=hdfclassifiedID)
            

            # Save the patient visit
            data = PatientVisits(
                patientid=patient,
                visittype='D',
                diagnosis=txtdiagnosis,
                evaluationeegree=EvaulDegree,
                classifiedID=objclassifiedID,
                visitdate=visit_date,
                doctorid=doctor,
                reasonforvisit=txtRemarks,
                createdate=timezone.now().date(),
            )
            data.save()

            return render(
                request,
                "ConfirmMsg.html",
                {
                    'message': "Patient's Visit is added successfully",
                    'returnUrl': 'DoctorEvaluation',
                    'btnText': 'New Patient'
                },
                status=200,
            )

        
        patientList = ormObj.getPatientsAttendedToday()
        patientcount = patientList.count()

        return render(
            request,
            'center/PatientVisit.html',
            {
                'patients': patientList,
                'Total': patientcount,
                'classifiedOptionsJSON': classifiedOptionsJSON,
            }
        )
        


   # @permission_required_with_redirect('manager.addNewVisitForPatient',login_url='/no-permission/')
    @login_required   
    def auditPatientvisit(request): 
        classifiedOptions = ClassficationsOptions.objects.filter(isActive=True).values(
            'classifiedID', 'classifiedCategory', 'optionClassified', 'isActive'
        )
        
        classifiedOptionsJSON = json.dumps(list(classifiedOptions), cls=DjangoJSONEncoder)

        if request.method == 'POST':
            txtpatientid = request.POST.get('hdfpatientid')
            userID = request.user  # Static doctor ID for now; replace with actual data.
            txtdiagnosis = request.POST.get('Diagnosis')
            EvaulDegree = request.POST.get('gridRadios')
            txtRemarks = request.POST.get('txtRemarks')
            hdfclassifiedID = request.POST.get('selectedOption')       

            patient = Patient.objects.get(pk=txtpatientid)
            
            visit_date = datetime.datetime.now().date()  # Use fully qualified datetime
            objclassifiedID = get_object_or_404(ClassficationsOptions, pk=hdfclassifiedID)
            

            # Save the patient visit
            data = PatientVisits(
                patientid=patient,
                visittype='A',
                diagnosis=txtdiagnosis,
                evaluationeegree=EvaulDegree,
                classifiedID=objclassifiedID,
                visitdate=visit_date,
                doctorid=userID,
                reasonforvisit=txtRemarks,
                createdate=visit_date,
            )
            data.save()

            return render(
                request,
                "ConfirmMsg.html",
                {
                    'message': "Patient's Visit is added successfully",
                    'returnUrl': 'AuditEvaluation',
                    'btnText': 'Take New Patient'
                },
                status=200,
            )

        
        patientList = ormObj.getPatientsAttendedToday()
        patientcount = patientList.count()

        return render(
            request,
            'center/auditPatientVisit.html',
            {
                'patients': patientList,
                'Total': patientcount,
                'classifiedOptionsJSON': classifiedOptionsJSON,
            }
        )

    def getPatientVisits(request):
        today_date = date.today()  # Get today's date
        past_10_days_date = today_date - timedelta(days=10)  
        
        patientList = PatientVisits.objects.filter(
    createdate__gte=past_10_days_date, 
    patientid__fileserial__isnull=False  # Only include records where fileserial is NOT NULL
).select_related('patientid', 'classifiedID')
        
        classfications_options = ClassficationsOptions.objects.values('classifiedCategory').distinct()


        
              

        return render(
            request,
            'center/auditPatientsList.html',
            {
                'patients': patientList,
                'classfications_options': classfications_options,
            }
        )
        
    def get_classified_options(request):
        category = request.GET.get('category', None)  # Get selected category from request
        if category:
            options = ClassficationsOptions.objects.filter(classifiedCategory=category, isActive=True).values_list('optionClassified', flat=True)
            return JsonResponse({'options': list(options)})
        return JsonResponse({'options': []})
    
    def update_patient_visit(request):
        if request.method == "POST":
            try:
                visit_id = request.POST.get("visit_id")
                evaluation_degree = request.POST.get("evaluation_degree")
                classified_id = request.POST.get("classified_id")

                # Ensure visit_id exists
                if not visit_id:
                    return JsonResponse({"success": False, "error": "Missing visit_id"}, status=400)

                visit = get_object_or_404(PatientVisits, visitid=visit_id)

                # Set values
                visit.evaluationeegree = evaluation_degree if evaluation_degree else None

                # Ensure classified_id is valid
                if classified_id:
                    classified_option = get_object_or_404(ClassficationsOptions, optionClassified=classified_id,classifiedCategory=visit.evaluationeegree)
                    visit.classifiedID = classified_option
                else:
                    visit.classifiedID = None  # Allow unsetting

                visit.updatedDate = date.today()
                visit.save()

                return JsonResponse({"success": True})

            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)}, status=500)

        return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)