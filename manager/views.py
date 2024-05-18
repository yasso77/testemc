from datetime import datetime

from django.http import HttpResponse, HttpResponseRedirect, JsonResponse
from django.shortcuts import redirect, render
from django.urls import reverse
import pandas as pd

from manager.forms.UploadForm import ExcelUploadForm
from manager.forms.addpatient import MyModelForm
from manager.models import Doctor, Patient, PatientVisits

# Create your views here.

def index(request):
    return render(request,'index.html',{'name':'Yasser'})

def uploadpatientData(request):
    if request.method == 'POST':
            form = ExcelUploadForm(request.POST, request.FILES)      
            excel_file = request.FILES['my_file']
            df = pd.read_excel(excel_file)

            
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
           
            return render(request,"ConfirmMsg.html",{'message': 'Patient data uploaded Successfully','returnUrl':'pushpatientData','btnText':'Upload New File'}, status=200)
   
    return render(request, 'uploadPatientData.html', {'form': 'form'})


def showPatientData(request):  
    return render(request,'SearchOnPatients.html',{'patients':Patient.objects.all(),'Total':Patient.objects.count()})

def uploadedPatientDataList(request):  
    return render(request,'UploadedPatientsList.html',{'patients':Patient.objects.all(),'Total':Patient.objects.count()})


def showPatientDataAttendedToday(request):  
    return render(request,'SearchOnPatientsPrintForm.html',{'patients':Patient.objects.filter(attendanceDate='2024-04-30'),'Total':Patient.objects.filter(attendanceDate='2024-04-30').count()})




def doctorPatientvisit(request):        

        if request.method=='POST':
            txtpatientid=request.POST.get('hdfpatientid')
            doctorid=1 #request.POST.get('doctorid')
            txtdiagnosis=request.POST.get('Diagnosis')
            EvaulDegree=request.POST.get('gridRadios')
            #chkFollowup=request.POST.get('chkFollow')
            EvaulDegree=request.POST.get('gridRadios')
            txtRemarks=request.POST.get('txtRemarks')
            # followup = True if chkFollowup == 'on' else False
            patient = Patient.objects.get(pk=txtpatientid)
            doctor = Doctor.objects.get(pk=doctorid)
            data=PatientVisits(patientid=patient,diagnosis=txtdiagnosis,evaluationeegree=EvaulDegree,visitdate=datetime.now(),doctorid=doctor,reasonforvisit=txtRemarks,createdate='2024-04-30')#datetime.now()
            data.save()
            return render(request,"ConfirmMsg.html",{'message': 'Patient`s Visit is added successfully','returnUrl':'DoctorEvaluation','btnText':'New Patient'}, status=200)
           

        return render(request,'PatientVisit.html',{'patients':Patient.objects.all(),'Total':Patient.objects.count()})

#This is a block of code
#This is a block of code
#This is a block of code

def addPatientVisit(request):
    txtpatientid=request.POST.get('hdfpatientid')
    doctorid=1 #request.POST.get('doctorid')
    txtdiagnosis=request.POST.get('Diagnosis')
    EvaulDegree=request.POST.get('gridRadios')
    #chkFollowup=request.POST.get('chkFollow')
    EvaulDegree=request.POST.get('gridRadios')
    txtRemarks=request.POST.get('txtRemarks')

    if request.method=='POST':
       # followup = True if chkFollowup == 'on' else False
        patient = Patient.objects.get(pk=txtpatientid)
        doctor = Doctor.objects.get(pk=doctorid)
        data=PatientVisits(patientid=patient,diagnosis=txtdiagnosis,evaluationeegree=EvaulDegree,visitdate=datetime.now(),doctorid=doctor,reasonforvisit=txtRemarks,createdate='2024-04-30')#datetime.now()
        data.save()
        return HttpResponseRedirect("Message")


def LiveDegreeReport(request):
    current_time = datetime.now().time()
    return render(request,'LiveDegreeReport.html',context={'current_time': current_time})


def ajaxReportChartEvlDegree(request):
    if request.method == 'POST' and 'inputDate' in request.POST:
            visitdate = request.POST.get('inputDate', None)
            queryset = PatientVisits.objects.filter(createdate='2024-04-30').values('evaluationeegree')  

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
    

def UpdatePatientData(request):
    if request.method == 'POST':
       
        patient_id = request.POST.get('hdfpatientid')     
        patientFileNum=request.POST.get('txtFileSerial')
        patientName=request.POST.get('txtName')
        patientMobile=request.POST.get('txtMobile')
        patientGender= request.POST.get('gridRadios')
        patientAge=request.POST.get('txtAge')
        patientCase=request.POST.get('txtCase')
        patientRemarks=request.POST.get('txtRemarks')       

         # Retrieve the patient object
        try:
            patient = Patient.objects.get(patientid=patient_id)
        except Patient.DoesNotExist:
            return JsonResponse({'error': 'Patient not found'}, status=404)

        # Update patient attributes
        patient.fileserial=patientFileNum
        patient.fullname=patientName
        patient.mobile=patientMobile
        patient.sufferedcase=patientCase
        patient.remarks=patientRemarks
        patient.gender=patientGender
        patient.age = patientAge
        patient.attendanceDate='2024-04-30'#datetime.now().date

        # Save the updated patient object
        patient.save()      
        # Construct the URL with the patient ID    
         # Construct the URL for the patient form with the patient ID
        try:
            patient_form_url = reverse('patientForm', kwargs={'patientid': patient_id})
        except Exception as e:
            print(f"Error in URL reversing: {e}")
            patient_form_url = "#"

        return render(request,"ConfirmMsg.html",{'message': 'Patient updated Successfully..','returnUrl':patient_form_url,'btnText':'Print Patient Form','target':'_blank'}, status=200)
    



def my_model_form_view(request):
    if request.method == 'POST':
        form = MyModelForm(request.POST)
        if form.is_valid():
            form.save()
            return render(request,"ConfirmMsg.html",{'message': 'Patient Added Successfully..','returnUrl':'addnewpatient','btnText':'Add New Patient'}, status=200)
    else:
        form = MyModelForm()    
    
    return render(request, 'addpatient.html', {'form': form})





    

