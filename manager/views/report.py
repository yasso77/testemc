from collections import defaultdict
from datetime import datetime
from django.http import JsonResponse
from django.shortcuts import render
from django.core.paginator import Paginator
from manager.decorators import permission_required_with_redirect
from django.contrib.auth.decorators import login_required
from openpyxl import Workbook
from manager.model.patient import AgentCompany, City, Patient
from manager.model.visit import PatientVisits
from manager.orm import ORMPatientsHandling
from django.views.generic.list import ListView
from django.utils import timezone
from django.http import HttpResponse
from django.utils.timezone import localtime
from openpyxl.utils import get_column_letter
from datetime import datetime, timedelta

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

    
    def patient_report_view(request):
        patients = Patient.objects.filter(isDeleted=False)

        # Get filters from request
        date_field = request.GET.get('date_field', 'createdDate')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        city_id = request.GET.get('city')
        agent_id = request.GET.get('agentID')
        lead_source = request.GET.get('leadSource')
        export = request.GET.get('export')

        # Date filtering with proper range logic
        if date_from and date_to:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')

                if date_field == 'createdDate':
                    # DateTimeField: include full day
                    start_datetime = date_from_obj
                    end_datetime = date_to_obj + timedelta(days=1)
                    patients = patients.filter(**{
                        f"{date_field}__range": [start_datetime, end_datetime]
                    })
                else:
                    # DateField
                    patients = patients.filter(**{
                        f"{date_field}__range": [date_from_obj.date(), date_to_obj.date()]
                    })
            except ValueError:
                pass  # Ignore invalid date formats

        # Additional filters
        if city_id:
            patients = patients.filter(city_id=city_id)
        if agent_id:
            patients = patients.filter(agentID_id=agent_id)
        if lead_source:
            patients = patients.filter(leadSource=lead_source)

        # Excel export
        if export == 'excel':
            wb = Workbook()
            ws = wb.active
            ws.title = "Patients Report"

            # English column headers
            headers = ['Code', 'Name', 'Mobile','Suffered Case' 'City', 'Agent', 'Lead Source', 'Created Date', 'Attendance Date']
            ws.append(headers)

            for p in patients:
                ws.append([
                    p.reservationCode,
                    p.fullname,
                    p.mobile,
                    p.sufferedcase,
                    p.city.cityName if p.city else '',
                    p.agentID.AgentCompany if p.agentID else '',
                    p.leadSource,
                    localtime(p.createdDate).strftime('%Y-%m-%d %H:%M') if p.createdDate else '',
                    p.attendanceDate.strftime('%Y-%m-%d') if p.attendanceDate else '',
                ])

            # Auto-fit column widths
            for col in ws.columns:
                max_length = max(len(str(cell.value)) if cell.value else 0 for cell in col)
                ws.column_dimensions[get_column_letter(col[0].column)].width = max_length + 2

            response = HttpResponse(
                content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            )
            response['Content-Disposition'] = 'attachment; filename=patients_report.xlsx'
            wb.save(response)
            return response

        # Pagination
        paginator = Paginator(patients.order_by('-createdDate'), 25)
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        leadSource_Choices=[('Facebook','Facebook'),('Whatsapp','Whatsapp'),('Youtube','Youtube'),('Newspaper','Newspaper'),('Friend','Friend'),('Call','Call'),('Instagram','Instagram'),('Center','Center')]

        context = {
            'page_obj': page_obj,
            'cities': City.objects.all(),
            'agents': AgentCompany.objects.all(),
            'date_field': date_field,
            'date_from': date_from,
            'date_to': date_to,
            'city_id': city_id,
            'agent_id': agent_id,
            'lead_source': lead_source,
            'lead_sources': dict(leadSource_Choices),  # This is important
        }

        return render(request, 'reports/export_patients_xl.html', context)


    
