from datetime import date, datetime, timedelta, timezone
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from manager.decorators import permission_required_with_redirect
from django.contrib.auth.models import User

from django.utils.timezone import make_aware, is_naive
from django.contrib.auth.decorators import login_required,permission_required

from manager.forms.editPatient import editPatientForm
from manager.model.patient import CallTrack, Patient, PatientMedicalHistory
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404, redirect
from django.utils.timezone import now



class PatientView(ListView):
    
    


    def patient_form_view(request, patient_id):
        
        CONDITIONS_LIST = [
            ('DIABETES', 'HEART DISEASE', 'GLAUCOMA', 'EYE SURGERY'),
            ('HTN', 'ASTHMA ALLERGY', 'CATARACT', 'EYE INJURY'),
            ('THYROID', 'CANCER', 'RETINAL D.', None)
            ]
        patientData = get_object_or_404(Patient, id=patient_id)
        medical_history = PatientMedicalHistory.objects.filter(patient=patientData).first()

        # Debugging:
        print(f"Patient Data: {patientData}")  
        print(f"Medical History: {medical_history}")  
        return render(request, 'center/patientForm.html',  {
            #'patientData': patientData,
            'medical_history': medical_history,
            'conditions_list': CONDITIONS_LIST  # Pass list from view
        })
    
   

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
            if patient.attendanceDate is None:
                   patient.attendanceDate = now()  # Assign a timezone-aware datetime

            elif is_naive(patient.attendanceDate):  
                   patient.attendanceDate = make_aware(patient.attendanceDate)   
            
            
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
   

    
    
    @login_required
   
    def patientsList(request):
       # Get the current date
        today = date.today()
        
        # Calculate the date 10 days ago
        ten_days_ago = today - timedelta(days=20)
        
        # Filter the Patient records created within the previous 10 days by a specific user (createdby)
        # assuming `request.user` is the logged-in user
        recent_patients = Patient.objects.active().filter(
        createdDate__gte=ten_days_ago        
        ).values(
            'fileserial','patientid','fullname', 'reservationCode', 'createdDate','city','age','sufferedcase__caseName','expectedDate','gender','attendanceDate')  # Select only the required fields
        
        # Pass the data to the template      
        
        return render(request, 'center/patientsList.html', {'patients': recent_patients})
    
    
    def edit_patient(request, patientid):
        # Fetch the patient instance or return 404 if not found
        patient = get_object_or_404(Patient, patientid=patientid)
        calltrack=CallTrack.objects.filter(patientID=patientid)
        
        try:
             patient_form_url = reverse('patientForm', kwargs={'patientid': patientid})
        except Exception as e:
                print(f"Error in URL reversing: {e}")
                patient_form_url = "#"
        # Pre-fill attendanceDate with today's date only if it's NULL
        initial_data = {}
        if patient.attendanceDate is None:
            initial_data['attendanceDate'] = date.today()  # Set default for form only
        
        if request.method == 'POST':
            # Bind form data to the existing patient instance
            form = editPatientForm(request.POST, instance=patient)
            if form.is_valid():
                
                form.save()  # Save the updated instance
                #return redirect('patientForm', patientid=patient.patientid)  # Redirect to the reservation list page
                return render(request, "ConfirmMsg.html", {
                    'message': 'Patient updated successfully.',
                    'returnUrl': patient_form_url,
                    'btnText': 'Print Patient Form',
                    'target': '_blank'
                }, status=200)
            else:
                
                print(form.errors)  # Print the errors to the console
        else:
            # Display the form pre-filled with patient data
            # print('x')
            form = editPatientForm(instance=patient)
        
        # Render the edit page with the form and patient data
        return render(request, 'center/editPatient.html', {'form': form, 'patient': patient,'calltracks':calltrack})