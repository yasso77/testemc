from collections import defaultdict
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render

from manager.decorators import permission_required_with_redirect
from django.contrib.auth.decorators import login_required

from manager.model.visit import PatientVisits
from manager.orm import ORMPatientsHandling
from django.views.generic.list import ListView
from django.utils import timezone
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
                

                today = timezone.now().date() 
                
                visitdate = request.POST.get('inputDate', None)
                queryset = PatientVisits.objects.filter(visitdate=today).values('evaluationeegree')  

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
    
    

    def compare_visits(request):
        # Fetch all relevant visits and include patient info
        visits = PatientVisits.objects.select_related('patientid', 'classifiedID').filter(
            visittype__in=['A', 'D']
        )

        # Organize visits by patient and visit type
        patient_data = {}
        for visit in visits:
            pid = visit.patientid
            if pid not in patient_data:
                patient_data[pid] = {
                    'name': visit.patientid.fullname,
                    'fileserial': visit.patientid.fileserial,
                    'A': None,
                    'D': None,
                }
            patient_data[pid][visit.visittype] = {
                'evaluation': visit.evaluationeegree,
                'classification': visit.classifiedID.classifiedCategory if visit.classifiedID else 'N/A'
            }

        # Build comparison list
        comparison_data = []
        for pid, data in patient_data.items():
            if data['A'] and data['D']:
                comparison_data.append({
                    'patient_id': pid,
                    'patient_name': data['name'],
                    'fileserial': data['fileserial'],
                    'a_evaluation': data['A']['evaluation'],
                    'd_evaluation': data['D']['evaluation'],
                    'a_classification': data['A']['classification'],
                    'd_classification': data['D']['classification'],
                    'match': '✅ Match' if data['A']['evaluation'] == data['D']['evaluation'] and
                                            data['A']['classification'] == data['D']['classification']
                            else '❌ No Match'
                })

        return render(request, 'reports/compare_visits.html', {'comparison_data': comparison_data})




    
