from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from manager.decorators import permission_required_with_redirect

from manager.forms.addpatient import MyModelForm

from django.contrib.auth.decorators import login_required,permission_required

from manager.model.patient import Patient
from django.views.generic.list import ListView



class PatientView(ListView):
    
    def patientForm(request,patientid):
        return render(request,'PatientForm.html',{'patientData':Patient.objects.get(patientid=patientid)})

    def get_patientData(request):

        if request.method == 'POST' and 'myData' in request.POST:
            patientID = request.POST.get('myData', None)
            queryset = Patient.objects.filter(patientid=patientID)    

        # Convert QuerySet to list of dictionaries
            data = list(queryset.values())

        # Return JsonResponse with the converted data
            return JsonResponse(data, safe=False)
            
        else:
            return JsonResponse({'success': False, 'error': 'Invalid request'})  

    def check_fileserial(request):
        if request.method == 'GET':
            fileserial = request.GET.get('fileserial')
            patient_id = request.GET.get('patient_id')

            if fileserial:
                exists = Patient.objects.filter(fileserial=fileserial).exclude(patientid=patient_id).exists()
                if exists:
                    return JsonResponse({'exists': True, 'message': 'Another patient with this file serial already exists.'}, status=200)
                else:
                    return JsonResponse({'exists': False, 'message': 'File serial is available.'}, status=200)

        return JsonResponse({'error': 'Invalid request'}, status=400)
        
    @permission_required_with_redirect('manager.UpdatePatinetData', login_url='/no-permission/')
    def UpdatePatientData(request):
        if request.method == 'POST':
            patient_id = request.POST.get('hdfpatientid')
            patientFileNum = request.POST.get('txtFileSerial')
            patientName = request.POST.get('txtName')
            patientMobile = request.POST.get('txtMobile')
            patientGender = request.POST.get('gridRadios')
            patientAge = request.POST.get('txtAge')
            patientCase = request.POST.get('txtCase')
            RideGlass = request.POST.get('glassRadios')
            wearingConduct = request.POST.get('contuctRadios')
            patientRemarks = request.POST.get('txtRemarks')

            # Retrieve the patient object
            try:
                patient = Patient.objects.get(patientid=patient_id)
            except Patient.DoesNotExist:
                return JsonResponse({'error': 'Patient not found'}, status=404)

            # Check if the fileserial exists for another patient
            

            # Update patient attributes
            patient.fileserial = patientFileNum
            patient.fullname = patientName
            patient.mobile = patientMobile
            patient.sufferedcase = patientCase
            patient.remarks = patientRemarks
            patient.gender = patientGender
            patient.age = patientAge
            patient.rideglass = RideGlass
            patient.wearingconduct = wearingConduct
            patient.attendanceDate = datetime.now().date()
            patient.arrivedOn = datetime.now().time().isoformat()

            # Save the updated patient object
            patient.save()

            # Construct the URL for the patient form with the patient ID
            try:
                patient_form_url = reverse('patientForm', kwargs={'patientid': patient_id})
            except Exception as e:
                print(f"Error in URL reversing: {e}")
                patient_form_url = "#"

            return render(request, "ConfirmMsg.html", {
                'message': 'Patient updated successfully.',
                'returnUrl': patient_form_url,
                'btnText': 'Print Patient Form',
                'target': '_blank'
            }, status=200)
        
        # Handle non-POST requests or other logic if needed
        return render(request, 'update_patient_form.html')
        

    @login_required
    @permission_required_with_redirect('manager.AddNewPatient', login_url='/no-permission/')
    def addNewPatient(request):
        if request.method == 'POST':
            form = MyModelForm(request.POST)
            if form.is_valid():
                form.save()
                return render(request,"ConfirmMsg.html",{'message': 'Patient Added Successfully..','returnUrl':'addnewpatient','btnText':'Add New Patient'}, status=200)
        else:
            form = MyModelForm()    
        
        return render(request, 'addpatient.html', {'form': form})