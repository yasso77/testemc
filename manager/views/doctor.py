from django.shortcuts import  render
import json
from django.core.serializers.json import DjangoJSONEncoder
from datetime import datetime
  # Import from the package, not the specific file
from manager.decorators import permission_required_with_redirect
from manager.model.patient import Patient
from manager.model.visit import PatientVisits
from manager.models import ClassficationsOptions
from django.shortcuts import get_object_or_404
from manager.orm import ORMPatientsHandling
from django.views.generic import ListView


ormObj=ORMPatientsHandling()


class DoctorView(ListView):
    
    @permission_required_with_redirect('manager.addNewVisitForPatient',login_url='/no-permission/')
    def doctorPatientvisit(request): 
        classifiedOptions = ClassficationsOptions.objects.filter(isActive=True).values(
            'classifiedID', 'classifiedCategory', 'optionClassified', 'isActive'
        )
        
        classifiedOptionsJSON = json.dumps(list(classifiedOptions), cls=DjangoJSONEncoder)

        if request.method == 'POST':
            txtpatientid = request.POST.get('hdfpatientid')
            doctorid = 1  # Static doctor ID for now; replace with actual data.
            txtdiagnosis = request.POST.get('Diagnosis')
            EvaulDegree = request.POST.get('gridRadios')
            txtRemarks = request.POST.get('txtRemarks')
            hdfclassifiedID = request.POST.get('selectedOption')
        

            patient = Patient.objects.get(pk=txtpatientid)
            doctor = Doctor.objects.get(pk=doctorid)
            visit_date = datetime.now().date()
            objclassifiedID = get_object_or_404(ClassficationsOptions, pk=hdfclassifiedID)
            

            # Save the patient visit
            data = PatientVisits(
                patientid=patient,
                diagnosis=txtdiagnosis,
                evaluationeegree=EvaulDegree,
                classifiedID=objclassifiedID,
                visitdate=visit_date,
                doctorid=doctor,
                reasonforvisit=txtRemarks,
                createdate=visit_date,
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
            'PatientVisit.html',
            {
                'patients': patientList,
                'Total': patientcount,
                'classifiedOptionsJSON': classifiedOptionsJSON,
            }
        )
