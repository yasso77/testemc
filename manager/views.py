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
from django.shortcuts import get_object_or_404




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

    

