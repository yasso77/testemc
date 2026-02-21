from datetime import date, datetime,  timedelta
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from manager.decorators import permission_required_with_redirect
from django.template.loader import render_to_string
from django.core.paginator import Paginator
from django.utils import timezone
from manager.forms.addFollowUp import insertCallTrackForm
from manager.forms.callCenterEditReservation import CallCenterEditReservationForm
from manager.forms.editReservation import editReservationForm
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required,permission_required
from django.db.models import Count, Max, Subquery, OuterRef
from manager.model.patient import AgentCompany, CallTrack, City, Patient
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from django.db.models import Q
from manager.forms.CallCenterReservation import CCFormAddReservation
from django.utils.timezone import make_aware, is_naive
from django.db.models import F
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse
from openpyxl import Workbook

class CallCenterView(ListView):
    
    @login_required
    def addNewPatient(request):        
      
        username_parts = request.user.username.split('_')
        username_prefix = ''.join([part[0].upper() for part in username_parts if part])

        
               
        latest_code = Patient.objects.filter(
            createdBy__id=request.user.id,
            reservationCode__isnull=False  # Exclude NULL values
        ).order_by('patientid').last()
        
        

        # Get the current month as a number
        current_month = str(datetime.now().month)  # "2" for February, "3" for March, etc.

        # Determine incrementing part
        if latest_code and latest_code.reservationCode:
            latest_code_parts = latest_code.reservationCode.split('-')
            
            if len(latest_code_parts) >= 3 and latest_code_parts[1] == current_month:
                latest_increment = int(latest_code_parts[-1])  # Get the last part and convert to int
                increment = latest_increment + 1
            else:
                increment = 1  # Reset increment if month is different
        else:
            increment = 1

        # Format increment with leading zeros
        increment_part = f"{increment:03d}"
        reservationCode = f"{username_prefix}-{current_month}-{increment_part}"
        
        if request.method == 'POST':
            # Pass request to the form for message handling
            
            callCenterform = CCFormAddReservation(request=request, data=request.POST)
           
            if callCenterform.is_valid():
                patient = callCenterform.save(commit=False)
                patient.reservationCode = reservationCode
                patient.reservedBy = request.user  # Assign the logged-in user
                patient.createdBy = request.user  # Assign the logged-in user
                # Ensure createdDate has a value
                if patient.createdDate is None:
                   patient.createdDate = now()  
                elif is_naive(patient.createdDate):  
                   patient.createdDate = make_aware(patient.createdDate)   
                patient.save()           
                
               
                
                return redirect(reverse("confirm_page_call", kwargs={
                    "patientid": patient.patientid,
                    "reservationCode": patient.reservationCode,
                    #"patientName": patient.fullname
                }))
        else:
            # Initialize the form with the generated reservation code
            callCenterform = CCFormAddReservation(request=request, initial={'reservationCode': reservationCode})
            # Initial GET request
           
          
        # Render the new reservation form
        return render(request, 'callcenter/newReservation.html', {'form': callCenterform, 'code': reservationCode})
    
    def confirm_page_call(request, patientid, reservationCode):
        return render(
            request,
            "callcenter/ConfirmMsgCallCenter.html",
            {
                "message": "The Reservation is Added Successfully.",
                "patientid": patientid,
                "reservationCode": reservationCode,
                #"patientName": patientName,
                "show_print": True,
            },
        )
    
    
    @login_required  
    def reservationsList(request):
        today = date.today()

        # =========================
        # Filters
        # =========================
        date_field = request.GET.get('date_field', 'createdDate')
        export = request.GET.get('export')
        date_from = request.GET.get('date_from')
        date_to = request.GET.get('date_to')
        city_id = request.GET.get('city')
        agent_id = request.GET.get('agentID')
        lead_source = request.GET.get('leadSource') 
        txtSearch = request.GET.get('txtSearch')      
        search = request.GET.get('search', '').strip()

        # =========================
        # Permissions
        # =========================
        is_admin_or_marketing = request.user.groups.filter(
            name__in=['Admin', 'Marketing']
        ).exists()

        # =========================
        # Base queryset
        # =========================
        patients_qs = (
            Patient.objects.active()
            .exclude(leadSource='Center')
            .filter(
                (Q(reservedBy=request.user) if not is_admin_or_marketing else Q())
            )
        )

        # =========================
        # Date filtering
        # =========================
        if date_from and date_to:
            try:
                date_from_obj = datetime.strptime(date_from, '%Y-%m-%d')
                date_to_obj = datetime.strptime(date_to, '%Y-%m-%d')

                patients_qs = patients_qs.filter(
                        createdDate__range=(
                            date_from_obj,
                            date_to_obj + timedelta(days=1)
                        )
                    )
              
            except ValueError:
                pass

        # =========================
        # Other filters
        # =========================
        if txtSearch:
            patients_qs = patients_qs.filter(
                Q(fullname__icontains=txtSearch) |
                Q(mobile__icontains=txtSearch)
            )
        if city_id:
            patients_qs = patients_qs.filter(city_id=city_id)

        if agent_id:
            patients_qs = patients_qs.filter(agentID_id=agent_id)

        if lead_source:
            patients_qs = patients_qs.filter(leadSource=lead_source)       

        if search:
            patients_qs = patients_qs.filter(
                Q(fullname__icontains=search) |
                Q(phone__icontains=search)
            )

        # =========================
        # Annotations & optimization
        # =========================
        patients_qs = patients_qs.select_related(
            'sufferedcase', 'createdBy', 'city', 'agentID'
        ).annotate(
            call_count=Count(
                'call_patients',
                filter=Q(call_patients__trackType='CC')
            ),
            last_call_date=Max(
                'call_patients__createdDate',
                filter=Q(call_patients__trackType='CC')
            ),
            last_call_outcome=Subquery(
                CallTrack.objects.filter(
                    patientID=OuterRef('pk'),
                    trackType='CC'
                )
                .order_by('-createdDate')
                .values('outcome')[:1]
            )
        ).order_by('-createdDate')

        # =========================
        # Pagination
        # =========================
        paginator = Paginator(patients_qs, 20)
        page_number = request.GET.get('page', 1)
        page_obj = paginator.get_page(page_number)

        # =========================
        # AJAX response
        # =========================
        if request.headers.get('x-requested-with') == 'XMLHttpRequest':
            html = render_to_string(
                'callcenter/patient_rows.html',
                {'patients': page_obj}
            )
            return JsonResponse({
                'html': html,
                'has_next': page_obj.has_next(),
                'total_count': paginator.count
            })

        # =========================
        # Normal render
         # =========================
        leadSource_Choices = [
            ('Facebook', 'Facebook'),
            ('Whatsapp', 'Whatsapp'),
            ('Youtube', 'Youtube'),
            ('Newspaper', 'Newspaper'),
            ('Friend', 'Friend'),
            ('Call', 'Call'),
            ('Instagram', 'Instagram'),
            ('Center', 'Center'),
        ]

        # =========================
        
        # EXPORT TO EXCEL
        if export == 'excel':
            return CallCenterView.export_patients_excel(patients_qs)

        context = {
            'patients': page_obj,
            'total_count': paginator.count,
            

            'cities': City.objects.all(),
            'agents': AgentCompany.objects.all(),    
            'date_field': date_field,
            'date_from': date_from,
            'date_to': date_to,
            'city_id': str(city_id) if city_id else '',
            'agent_id': str(agent_id) if agent_id else '',           
            'lead_source': lead_source or '',
            'lead_sources': dict(leadSource_Choices),
            
        }
        return render(request, 'callcenter/reservationsList.html', context)

        
    def export_patients_excel(queryset):
        wb = Workbook()
        ws = wb.active
        ws.title = "Patients"

        # Header
        headers = [          
            'Reservation Code',
            'File Serial',
            'Patient Name',
            'Gender',
            'Mobile',
            'City',
            'Agent',
            'Check Price',
            'Organization',
            'Suffered Case',
            'Lead Source',
            'Created Date',
            'Attendance Date',
        ]
        ws.append(headers)

        # Rows
        for p in queryset:
            ws.append([              
                p.reservationCode,
                p.fileserial,
                p.fullname,
                p.gender,
                p.mobile,
                p.city.cityName if p.city else '',
                p.agentID.AgentCompany if p.agentID else '',
                str(p.checkUpprice) if p.checkUpprice else '',
               
                p.organizationID.orgName,
                str(p.sufferedcase) if p.sufferedcase else '',
               
                p.leadSource,
                p.createdDate.strftime('%Y-%m-%d') if p.createdDate else '',
                p.attendanceDate.strftime('%Y-%m-%d') if p.attendanceDate else '',
            ])

        response = HttpResponse(
            content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
        )
        response['Content-Disposition'] = 'attachment; filename=patients.xlsx'
        wb.save(response)
        return response
    
    @login_required
   
    def reservationsListviewScope(request,viewScope):
       # Get the current date
        today = date.today()
        
        # Calculate the date 10 days ago
        thirty_days_ago = today - timedelta(days=30)
        
        # Filter the Patient records created within the previous 10 days by a specific user (createdby)
        # assuming `request.user` is the logged-in user
        if viewScope=='attended':
                recent_patients = (
                Patient.objects.active()
                .filter(
                    createdDate__gte=thirty_days_ago,
                    reservedBy=request.user,
                    attendanceDate__isnull=False,
                    isDeleted=False
                )
                .select_related('sufferedcase')
                .annotate(
                call_count=Count('call_patients'),  # Count number of call tracks for each patient
                last_call_date=Max('call_patients__createdDate'),  # Get the latest call date
                last_call_outcome=Subquery(
                    CallTrack.objects.filter(
                        patientID=OuterRef('pk')  # Reference the current patient
                    )
                    .order_by('-createdDate')
                    .values('outcome')[:1]  # Get the outcome of the latest call
                )
            )
            .values(
                'patientid', 'fullname', 'createdBy__username','reservationCode', 'leadSource',
                'createdDate', 'city', 'mobile', 'age',
                'sufferedcase__caseName', 'expectedDate', 'gender', 'attendanceDate',
                'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
            )
            )
        elif viewScope=='missed':
                recent_patients = (
                Patient.objects.active()
                .filter( 
                        reservedBy=request.user,            
                        createdDate__gte=thirty_days_ago,
                        attendanceDate__isnull=True,
                        fileserial__isnull=True,
                        isDeleted=False,
                        expectedDate__lt=today
                ).select_related('sufferedcase').annotate(
                    call_count=Count('call_patients'),  # Count number of call tracks for each patient
                    last_call_date=Max('call_patients__createdDate'),  # Get the latest call date
                    last_call_outcome=Subquery(
                        CallTrack.objects.filter(
                            patientID=OuterRef('pk')  # Reference the current patient
                        )
                        .order_by('-createdDate')
                        .values('outcome')[:1]  # Get the outcome of the latest call
                    )
                ).values(
                    'patientid', 'fullname', 'reservationCode','createdBy__username', 'leadSource',
                    'createdDate', 'city', 'mobile', 'age',
                    'sufferedcase__caseName', 'expectedDate', 'gender', 'attendanceDate',
                    'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
                ) 
                )          
                
        elif viewScope=='confirmed':
                recent_patients = (
                Patient.objects.active()
                .filter(
                    reservedBy=request.user,
                    createdDate__gte=thirty_days_ago,
                    attendanceDate__isnull=True,
                    isDeleted=False
                )
                .annotate(
                    call_count=Count('call_patients', filter=Q(call_patients__outcome="Confirmed", call_patients__confirmationDate__gt=today)),  # Count only relevant calls
                    last_call_date=Max('call_patients__createdDate'),  # Get the latest call date
                    last_call_outcome=Subquery(
                        CallTrack.objects.filter(
                            patientID=OuterRef('pk'),
                            outcome="Confirmed",
                            confirmationDate__gt=today,
                            createdBy=request.user
                        )
                        .order_by('-createdDate')
                        .values('outcome')[:1]  # Get the outcome of the latest call
                    )
                )
                .filter(call_count__gt=0)  # Ensure patients have at least one confirmed call
                .values(
                    'patientid', 'fullname','createdBy__username', 'reservationCode', 'leadSource',
                    'createdDate', 'city', 'mobile', 'age',
                    'sufferedcase__caseName', 'expectedDate', 'gender', 'attendanceDate',
                    'call_count', 'last_call_date', 'last_call_outcome'
                )
            )
                
        elif viewScope=='willattend':
                recent_patients = (
                Patient.objects.active()
                .filter(
                   reservedBy=request.user,
                   createdDate__gte=thirty_days_ago,
                   isDeleted=False
                ).filter(
                    Q(expectedDate=today) #| Q(confirmationDate=today)  # Either condition can be true
                ).select_related('sufferedcase')       # Optimize related model queries
                    .annotate(
                    call_count=Count('call_patients'),  # Count number of call tracks for each patient
                    last_call_date=Max('call_patients__createdDate'),  # Get the latest call date
                    last_call_outcome=Subquery(
                        CallTrack.objects.filter(
                            patientID=OuterRef('pk')  # Reference the current patient
                        )
                        .order_by('-createdDate')
                        .values('outcome')[:1]  # Get the outcome of the latest call
                    )
                )
                .values(
                    'patientid', 'fullname','createdBy__username', 'reservationCode', 'leadSource',
                    'createdDate', 'city', 'mobile', 'age',
                    'sufferedcase__caseName', 'expectedDate', 'gender', 'attendanceDate',
                    'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
                )
            )
        return render(request, 'callcenter/reservationsList.html', {'patients': recent_patients,'viewScope':viewScope})
    
    @login_required
    def reservationsListviewMobile(request,strmobile):
            
            recent_patients = (
            Patient.objects.active()
            .filter(
                
                reservedBy=request.user,
                mobile=strmobile
                
            )
            .select_related('sufferedcase')
            .annotate(
                call_count=Count('call_patients'),  # Count number of call tracks for each patient
                last_call_date=Max('call_patients__createdDate'),  # Get the latest call date
                last_call_outcome=Subquery(
                    CallTrack.objects.filter(
                        patientID=OuterRef('pk')  # Reference the current patient
                    )
                    .order_by('-createdDate')
                    .values('outcome')[:1]  # Get the outcome of the latest call
                )
            )
            .values(
                'patientid', 'fullname', 'createdBy__username','reservationCode', 'leadSource',
                'createdDate', 'city', 'mobile', 'age',
                'sufferedcase__caseName', 'expectedDate', 'gender', 'attendanceDate',
                'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
            )
        )
        
        
        # Pass the data to the template      
        
            return render(request, 'callcenter/reservationsList.html', {'patients': recent_patients,'viewScope':strmobile})
        
        
    @login_required
    def reservationsListviewName(request,strname):
            
            recent_patients = (
            Patient.objects.active()
            .filter(
                
                reservedBy=request.user,
                fullname=strname,
                #isDeleted=False
            )
            .select_related('sufferedcase')
            .annotate(
                call_count=Count('call_patients'),  # Count number of call tracks for each patient
                last_call_date=Max('call_patients__createdDate'),  # Get the latest call date
                last_call_outcome=Subquery(
                    CallTrack.objects.filter(
                        patientID=OuterRef('pk')  # Reference the current patient
                    )
                    .order_by('-createdDate')
                    .values('outcome')[:1]  # Get the outcome of the latest call
                )
            )
            .values(
                'patientid', 'fullname', 'createdBy__username','reservationCode', 'leadSource',
                'createdDate', 'city', 'mobile', 'age',
                'sufferedcase__caseName', 'expectedDate', 'gender', 'attendanceDate',
                'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
            )
        )
        
        
        # Pass the data to the template      
        
            return render(request, 'callcenter/reservationsList.html', {'patients': recent_patients,'viewScope':strname})
           
    def check_reservationCode(request):
        if request.method == 'GET':
            reservation_Code = request.GET.get('reservation_Code')
            #patient_id = request.GET.get('patient_id')

            if reservation_Code:
                exists = Patient.objects.filter(reservationCode=reservation_Code).exists()
                if exists:
                    return JsonResponse({'exists': True, 'message': 'Another Reservation with this file serial already exists.'}, status=200)
                else:
                    return JsonResponse({'exists': False, 'message': 'Reservation code is available.'}, status=200)

        return JsonResponse({'error': 'Invalid request'}, status=400)
    
    @login_required
    def edit_reservation(request, patientid):
        # Fetch the patient instance or return 404 if not found
        patient = get_object_or_404(Patient, patientid=patientid)
        
        if request.method == 'POST':
            # Bind form data to the existing patient instance
            
        # ⭐ ADD request=request
            form = CallCenterEditReservationForm(
                request.POST,
                instance=patient,
                request=request
            )
            if form.is_valid():
                form.save()  # Save the updated instance
                return redirect(reverse("confirm_page_call", kwargs={
                    "patientid": patient.patientid,
                    "reservationCode": patient.reservationCode,
                    #"patientName": patient.fullname
                }))
              
            else:
                print(form.errors)
        else:
            # Display the form pre-filled with patient data
            form = CallCenterEditReservationForm(instance=patient, request=request)
        
        # Render the edit page with the form and patient data
        return render(request, 'callcenter/editReservation.html', {'form': form, 'patient': patient})

    
   
    
    @login_required
    def follow_reservation(request, patientid):
        # Fetch the patient instance or return 404 if not found
        patient = get_object_or_404(Patient, patientid=patientid)
        calltracks=CallTrack.objects.filter(patientID=patientid).order_by('-createdDate')
        if request.method == 'POST':
            # Bind form data to the existing patient instance
            form = insertCallTrackForm(request.POST)
            if form.is_valid():
                # Save form but do not commit to the database yet
                calltrack = form.save(commit=False)
                
                # Assign additional fields
                calltrack.patientID = patient
                calltrack.createdBy = request.user
                calltrack.agentID = request.user
                calltrack.trackType='CC'
                
                # Save the instance to the database
                calltrack.save()
                
               
                
                # Return confirmation message
                return render(
                    request,
                    "callcenter/ConfirmMsgCallCenter.html",
                    {
                        'message': 'Follow-UP is added successfully.',
                        'returnUrl': reverse('reservationList'),
                        'btnText': 'Return to Reservations List',
                    },
                    status=200,
                )
            else:
                print(form.errors)
        else:
            # Display the form pre-filled with patient data
            form = insertCallTrackForm(instance=patient)
        
        # Render the edit page with the form and patient data
        return render(request, 'callcenter/followReservation.html', {'form': form, 'patient': patient,'calltracks':calltracks})
    
    def get_patient_statistics_past_30_days(request):
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # 1. Patients reserved by the user in the past 30 days
        reserved_by_user_count = Patient.objects.filter(
            reservedBy=request.user,
            createdDate__gte=thirty_days_ago,
            isDeleted=False
        ).count()

        # 2. Patients who confirmed their dates in the past 30 days & their confirmation date is greater than today
        
        today = now().date()

        confirmed_patients_count = Patient.objects.filter(
            reservedBy=request.user,
            createdDate__gte=thirty_days_ago,
            attendanceDate__isnull=True,
            isDeleted=False,
            call_patients__outcome="Confirmed",  # Outcome is "Confirmed"
            call_patients__confirmationDate__gt=today,            # Add condition: confirmationDate > today
            call_patients__createdBy=request.user
        ).distinct().count()

        # 3. Patients whose expected or confirmation date is today in the past 30 days
        expected_or_confirmed_today_count = Patient.objects.filter(
            reservedBy=request.user,
            createdDate__gte=thirty_days_ago,
            isDeleted=False
                ).filter(
                    Q(expectedDate=today) #| Q(confirmationDate=today)  # Either condition can be true
                ).count()

        # 4. Patients who missed their expected or confirmation date in the past 30 days
        missed_patients_count = Patient.objects.filter(
            reservedBy=request.user,            
            createdDate__gte=thirty_days_ago,
            attendanceDate__isnull=True,
            fileserial__isnull=True,
            isDeleted=False,
            expectedDate__lt=today).count()
        
         # 5. Patients who atteneded in the past 30 days
        attended_patients_count= Patient.objects.filter(
            reservedBy=request.user,
            fileserial__isnull=False,            
            createdDate__gte=thirty_days_ago,
            attendanceDate__isnull=False,
            isDeleted=False
        ).count()

        # Returning the statistics
        return {
            "reserved_by_user_count": reserved_by_user_count,
            "confirmed_patients_count": confirmed_patients_count,
            "expected_today_count": expected_or_confirmed_today_count,
            "missed_patients_count": missed_patients_count,
            "attended_patients_count": attended_patients_count,
            'date_range': {
            'start': thirty_days_ago,
            'end': today,
        }
        }
        


    def get_reservation_data(request):
        # Get today's date and convert it to an aware datetime object
        today = timezone.now()

        # Generate the last 30 days, ensuring they are aware datetime objects
        last_30_days = [today - timedelta(days=i) for i in range(30)]

        # Convert naive datetimes to aware datetimes (if they are naive)
        last_30_days = [timezone.make_aware(date) if timezone.is_naive(date) else date for date in last_30_days]

        last_30_days.reverse()  # Keep it in chronological order

        # Dates for the same period last month (shift all dates by 30 days)
        last_month = [date - timedelta(days=30) for date in last_30_days]

        # Fetch data for the last 30 days, using aware datetimes for filtering
        last_30_days_data = (
            Patient.objects.filter(createdDate__range=(last_30_days[0], last_30_days[-1]))
            .values('createdDate')
            .annotate(count=Count('patientid'))
        )

        # Fetch data for the same period last month
        last_month_data = (
            Patient.objects.filter(createdDate__range=(last_month[0], last_month[-1]))
            .values('createdDate')
            .annotate(count=Count('patientid'))
        )

        # Format data for the frontend
        data = []
        for i, date in enumerate(last_30_days):
            date_str = date.strftime('%b %d')  # e.g., "Jan 24"
            current_count = next((item['count'] for item in last_30_days_data if item['createdDate'].date() == date.date()), 0)
            last_month_count = next((item['count'] for item in last_month_data if item['createdDate'].date() == last_month[i].date()), 0)

            data.append({
                'date': date_str,
                'currentCount': current_count,
                'lastMonthCount': last_month_count,
            })

        return JsonResponse({'reservationsData': data})

    @csrf_exempt
    def validate_mobile(request):
        mobile = request.GET.get('mobile', None)
        if mobile:
            if Patient.objects.filter(mobile=mobile, isDeleted=False).exists():
                return JsonResponse({'exists': True, 'message': 'A patient with this Mobile Number already exists.'})
        return JsonResponse({'exists': False})
    
    @csrf_exempt
    def validate_fullname(request):
        name = request.GET.get('fullname', None)
        if name:
            if Patient.objects.filter(fullname=name, isDeleted=False).exists():
                return JsonResponse({'exists': True, 'message': 'A patient with this Name Number already exists.'})
        return JsonResponse({'exists': False})

