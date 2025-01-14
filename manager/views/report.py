from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render

from manager.decorators import permission_required_with_redirect
from django.contrib.auth.decorators import login_required

from manager.model.visit import PatientVisits
from manager.orm import ORMPatientsHandling
from django.views.generic.list import ListView

ormObj=ORMPatientsHandling()

class ReportView(ListView):

    @permission_required_with_redirect('manager.UpdatePatinetData', login_url='/no-permission/')
    def showPatientDataAttendedToday(request):       
        
        patientList=ormObj.getPatientsTodayWithVisitStatus()
        patientcount=patientList.count()   

        return render(request, 'SearchOnPatientsPrintForm.html', {
                'patients': patientList,
                'Total': patientcount
            })
    

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



    
