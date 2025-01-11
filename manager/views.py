from datetime import datetime
from django.db.models import Q
from django.contrib.auth import logout
from django.contrib.auth import login
from django.contrib.auth import authenticate
from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
import pandas as pd
import json
from django.core.serializers.json import DjangoJSONEncoder
from manager.decorators import permission_required_with_redirect
from manager.forms.UploadForm import ExcelUploadForm
from manager.forms.addpatient import MyModelForm
from manager.forms.forms import LoginForm
from manager.models import Doctor, Patient, PatientVisits,ClassficationsOptions
from django.contrib.auth.decorators import login_required,permission_required
from manager.orm import ORMPatientsHandling


ormObj=ORMPatientsHandling()

# Create your views here.
@login_required
def index(request):
    return render(request,'index.html',{'name':'index'})

def no_permission_view(request):
    return render(request, 'no_permission.html')

@login_required
@permission_required_with_redirect('manager.UploadPatientFile',login_url='/no-permission/')
def uploadpatientData(request):
    if request.method == 'POST':
            form = ExcelUploadForm(request.POST, request.FILES)      
            excel_file = request.FILES['my_file']
            df = pd.read_excel(excel_file)
            added_count = 0
            updated_count = 0

            
            for index, row in df.iterrows():
                # Check if the mobile number already exists in the database
                mobile_number = row['Mobile']
                existing_patient = Patient.objects.filter(mobile=mobile_number).first()

                if existing_patient:
                    # If a patient with the same mobile number exists, update the existing record
                    existing_patient.fullname = row['Name']
                    existing_patient.age = row['Age']
                    existing_patient.sufferedcase = row['Case']
                    existing_patient.city = row['City']
                    existing_patient.reservedBy = row['ReservedBy']
                    existing_patient.arrivedOn = row['ArrivedOn']
                    existing_patient.remarks = row['Remarks']
                    existing_patient.expectedDate = row['ArrivalDate']
                    existing_patient.save()
                    updated_count += 1
                else:
                    # If no patient with the same mobile number exists, create a new record
                    Patient.objects.create(
                        fullname=row['Name'],
                        mobile=row['Mobile'],
                        age=row['Age'],
                        sufferedcase=row['Case'],
                        city=row['City'],
                        reservedBy=row['ReservedBy'],
                        arrivedOn=row['ArrivedOn'],
                        remarks=row['Remarks'],
                        expectedDate=row['ArrivalDate']
                        # Map other columns accordingly
                    ) 
                    added_count += 1               
            message = f'Patient data uploaded successfully.<br>{added_count} patients were added.<br>{updated_count} patients were updated.'
            
            
            return render(request,"ConfirmMsg.html",{'message': message,'returnUrl':'upload','btnText':'Upload New File'}, status=200)
   
    return render(request, 'uploadPatientData.html', {'form': 'form'})


@login_required
@permission_required_with_redirect('manager.ShowPatientReport',login_url='/no-permission/')
def showPatientData(request):
    
        patientList=ormObj.getPatientsTodayWithNoVisitYet()
        patientcount=patientList.count()  
   
        return render(request, 'SearchOnPatients.html', {
        'patients': patientList,
        'Total': patientcount
        })

@permission_required_with_redirect('manager.UpdatePatinetData', login_url='/no-permission/')
def uploadedPatientDataList(request): 
    
      if request.method == 'POST':
        fromDate = request.POST.get('txtFromDate')
        toDate = request.POST.get('txtToDate')
        # Fetch patients with their related visits
        queryset = ormObj.get_all_Patients_Between_Period(fromDate, toDate)
        context = {
            'patients': queryset,
        }
      else:
        context = {}  # Define an empty context if request method is not POST

      return render(request, 'UploadedPatientsList.html', context)
   

@permission_required_with_redirect('manager.UpdatePatinetData', login_url='/no-permission/')
def showPatientDataAttendedToday(request): 
     
    
    patientList=ormObj.getPatientsTodayWithVisitStatus()
    patientcount=patientList.count()   

    return render(request, 'SearchOnPatientsPrintForm.html', {
            'patients': patientList,
            'Total': patientcount
        })
        
    



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

        patient = Patient.objects.get(pk=txtpatientid)
        doctor = Doctor.objects.get(pk=doctorid)
        visit_date = datetime.now().date()

        # Save the patient visit
        data = PatientVisits(
            patientid=patient,
            diagnosis=txtdiagnosis,
            evaluationeegree=EvaulDegree,
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


#This is a block of code
#This is a block of code
#This is a block of code


@permission_required_with_redirect('manager.LiveReport', login_url='/no-permission/')
def LiveDegreeReport(request):
    current_time = datetime.now().time()
    return render(request,'LiveDegreeReport.html',context={'current_time': current_time})

@permission_required_with_redirect('manager.LiveReport', login_url='/no-permission/')
def ajaxReportChartEvlDegree(request):
    if request.method == 'POST' and 'inputDate' in request.POST:
            visitdate = request.POST.get('inputDate', None)
            queryset = PatientVisits.objects.filter(visitdate__date=datetime.now().date()).values('evaluationeegree')  

        # Convert QuerySet to list of dictionaries
            data = list(queryset.values())

        # Return JsonResponse with the converted data
            return JsonResponse(data, safe=False)
            
    else:
            return JsonResponse({'success': False, 'error': 'Invalid request'})  


#This is a block of code
#This is a block of code
#This is a block of code


def ConfirmMsg(request):
     return render(request,'ConfirmMsg.html',{'Msg':request.POST.get('msg')})


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


def custom_logout_view(request):
    logout(request)
    return redirect('/custom-logout-page/')
    
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            # Process the form data (authentication logic here)
            # For example, authenticate user and log in
             username = form.cleaned_data['username']
             password = form.cleaned_data['password']
             user = authenticate(request, username=username, password=password)
             if user is not None:
                login(request, user)
                return redirect('some_view')
            
    else:
        form = LoginForm()
    
    return render(request, 'registration/login.html', {'form': form})

    

