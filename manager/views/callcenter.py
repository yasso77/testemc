from collections import Counter, defaultdict
from datetime import date, datetime, time, timedelta
from pyexpat.errors import messages
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
from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required,permission_required
from django.db.models import Count, Max, Subquery, OuterRef, Exists
from manager.model.patient import AgentCompany, CallTrack, City, Patient
from manager.model.visit import PatientVisits, PatientDiscussion
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from django.db.models import Q
from manager.forms.CallCenterReservation import CCFormAddReservation
from django.utils.timezone import make_aware, is_naive
from django.db import transaction
from django.core.cache import cache
from django.views.decorators.csrf import csrf_exempt
import uuid
from django.http import HttpResponse
from openpyxl import Workbook
import qrcode
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
from django.core.files import File
from django.conf import settings
from django.urls import reverse
import os
from django.contrib.staticfiles import finders
import json
from django.core.serializers.json import DjangoJSONEncoder


class CallCenterView(ListView):
    
    @staticmethod
    def _next_reservation_code(user):
        username_parts = user.username.split('_')
        username_prefix = ''.join([part[0].upper() for part in username_parts if part]) or 'X'
        current_month = str(datetime.now().month)

        latest_code = (
            Patient.objects
            .filter(createdBy_id=user.id, reservationCode__isnull=False)
            .order_by('-patientid')
            .values_list('reservationCode', flat=True)
            .first()
        )

        increment = 1
        if latest_code:
            parts = latest_code.split('-')
            if len(parts) >= 3 and parts[1] == current_month:
                try:
                    increment = int(parts[-1]) + 1
                except ValueError:
                    increment = 1

        while True:
            code = f"{username_prefix}-{current_month}-{increment:03d}"
            if not Patient.objects.filter(reservationCode=code, isDeleted=False).exists():
                return code
            increment += 1

    @staticmethod
    def _confirm_reservation_redirect(patient):
        return redirect(reverse("confirm_page_call", kwargs={
            "patientid": patient.patientid,
            "reservationCode": patient.reservationCode,
        }))

    @staticmethod
    def _reservation_nonce_key(user_id, nonce):
        return f'cc_res_nonce:{user_id}:{nonce}'

    @login_required
    def addNewPatient(request):
        reservationCode = CallCenterView._next_reservation_code(request.user)

        if request.method == 'POST':
            posted_code = (request.POST.get('reservationCode') or '').strip()
            posted_mobile = (request.POST.get('mobile') or '').strip()
            posted_name = (request.POST.get('fullname') or '').strip()
            form_nonce = (request.POST.get('form_nonce') or '').strip()
            callCenterform = CCFormAddReservation(request=request, data=request.POST)

            if callCenterform.is_valid():
                nonce_key = (
                    CallCenterView._reservation_nonce_key(request.user.id, form_nonce)
                    if form_nonce else None
                )
                with transaction.atomic():
                    get_user_model().objects.select_for_update().get(pk=request.user.pk)

                    # Same form submitted twice (double-click / retry / back+resubmit).
                    if nonce_key:
                        cached_pk = cache.get(nonce_key)
                        if cached_pk:
                            existing = Patient.objects.filter(
                                pk=cached_pk, isDeleted=False
                            ).first()
                            if existing:
                                return CallCenterView._confirm_reservation_redirect(existing)

                    if posted_mobile:
                        recent_duplicate = (
                            Patient.objects
                            .filter(
                                createdBy=request.user,
                                mobile=posted_mobile,
                                isDeleted=False,
                                createdDate__gte=now() - timedelta(seconds=120),
                            )
                            .order_by('-patientid')
                            .first()
                        )
                        if recent_duplicate:
                            recent_name = (recent_duplicate.fullname or '').strip().lower()
                            if not posted_name or recent_name == posted_name.lower():
                                if nonce_key:
                                    cache.set(nonce_key, recent_duplicate.patientid, 60 * 30)
                                return CallCenterView._confirm_reservation_redirect(recent_duplicate)

                    patient = callCenterform.save(commit=False)
                    if posted_code and not Patient.objects.filter(
                        reservationCode=posted_code, isDeleted=False
                    ).exists():
                        patient.reservationCode = posted_code
                    else:
                        patient.reservationCode = CallCenterView._next_reservation_code(request.user)

                    patient.reservedBy = request.user
                    patient.createdBy = request.user
                    if patient.createdDate is None:
                        patient.createdDate = now()
                    elif is_naive(patient.createdDate):
                        patient.createdDate = make_aware(patient.createdDate)
                    patient.save()

                    if nonce_key:
                        cache.set(nonce_key, patient.patientid, 60 * 30)

                return CallCenterView._confirm_reservation_redirect(patient)

            return render(
                request,
                'callcenter/newReservation.html',
                {
                    'form': callCenterform,
                    'code': reservationCode,
                    'form_nonce': form_nonce or uuid.uuid4().hex,
                },
            )

        callCenterform = CCFormAddReservation(
            request=request,
            initial={'reservationCode': reservationCode},
        )
        return render(
            request,
            'callcenter/newReservation.html',
            {
                'form': callCenterform,
                'code': reservationCode,
                'form_nonce': uuid.uuid4().hex,
            },
        )
    
    def confirm_page_call(request, patientid, reservationCode):
        patient = get_object_or_404(
            Patient,
            patientid=patientid,
            reservationCode=reservationCode
        )
        try:
            generate_reservation_image(patient)
            patient.save(update_fields=['reservation_image'])
        except Exception:
            pass
        return render(
            request,
            "callcenter/ConfirmMsgCallCenter.html",
            {
                "message": "The Reservation is Added Successfully.",
                "show_print": True,
                "patient": patient,
                "ticket_v": int(timezone.now().timestamp()),
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
                Q(mobile__icontains=txtSearch) |
                Q(fileserial__icontains=txtSearch)|Q(reservationCode__icontains=txtSearch)
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

    @login_required
    def performance_dashboard(request):
        """Personal call-center KPIs: reservations vs attendance vs operations."""
        today = date.today()
        default_from = today.replace(day=1)

        def parse_day(value, fallback):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except (TypeError, ValueError):
                return fallback

        from_date = parse_day(request.GET.get('from_date'), default_from)
        to_date = parse_day(request.GET.get('to_date'), today)
        if from_date > to_date:
            from_date, to_date = to_date, from_date

        period_days = (to_date - from_date).days + 1
        prev_to = from_date - timedelta(days=1)
        prev_from = prev_to - timedelta(days=period_days - 1)

        def period_bounds(start, end):
            # Avoid createdDate__date lookups: MySQL CONVERT_TZ is not loaded, so
            # Django's DATE(CONVERT_TZ(...)) returns NULL and every count becomes 0.
            start_dt = timezone.make_aware(datetime.combine(start, time.min))
            end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min))
            return start_dt, end_dt

        def local_day(dt):
            if not dt:
                return None
            if timezone.is_aware(dt):
                return timezone.localtime(dt).date()
            return dt.date()

        def agent_patients(start, end):
            start_dt, end_dt = period_bounds(start, end)
            return (
                Patient.objects
                .filter(
                    Q(reservedBy=request.user) | Q(createdBy=request.user),
                    isDeleted=False,
                    createdDate__gte=start_dt,
                    createdDate__lt=end_dt,
                )
                .exclude(leadSource='Center')
            )

        def summarize(start, end):
            qs = agent_patients(start, end)
            reserved = qs.count()
            attended = qs.filter(attendanceDate__isnull=False).count()
            patient_ids = list(qs.values_list('patientid', flat=True))

            surgery_ids = set(
                PatientVisits.objects.filter(
                    patientid_id__in=patient_ids,
                    evaluationeegree='Surgery',
                ).values_list('patientid_id', flat=True)
            )
            discussion_ids = set(
                PatientDiscussion.objects.filter(
                    patient_id__in=patient_ids,
                    discussionResult__name__iexact='DONE',
                ).values_list('patient_id', flat=True)
            )
            operations = len(surgery_ids | discussion_ids)

            attend_rate = round((attended / reserved) * 100, 1) if reserved else 0
            op_rate = round((operations / attended) * 100, 1) if attended else 0
            return {
                'reserved': reserved,
                'attended': attended,
                'operations': operations,
                'attend_rate': attend_rate,
                'op_rate': op_rate,
            }

        curr = summarize(from_date, to_date)
        prev = summarize(prev_from, prev_to)

        def delta_pct(current, previous):
            if previous == 0:
                return None if current == 0 else 100
            return round(((current - previous) / previous) * 100, 1)

        deltas = {
            'reserved': delta_pct(curr['reserved'], prev['reserved']),
            'attended': delta_pct(curr['attended'], prev['attended']),
            'operations': delta_pct(curr['operations'], prev['operations']),
        }

        patient_created = list(
            agent_patients(from_date, to_date).values_list(
                'patientid', 'createdDate', 'attendanceDate'
            )
        )
        daily_reserved = Counter()
        daily_attended = Counter()
        for pid, created, attendance in patient_created:
            day = local_day(created)
            if not day:
                continue
            daily_reserved[day] += 1
            if attendance:
                daily_attended[day] += 1

        patient_ids_all = [pid for pid, _, _ in patient_created]
        operated_ids = set(
            PatientVisits.objects.filter(
                patientid_id__in=patient_ids_all,
                evaluationeegree='Surgery',
            ).values_list('patientid_id', flat=True)
        ) | set(
            PatientDiscussion.objects.filter(
                patient_id__in=patient_ids_all,
                discussionResult__name__iexact='DONE',
            ).values_list('patient_id', flat=True)
        )
        op_by_day = Counter()
        for pid, created, _attendance in patient_created:
            if pid not in operated_ids:
                continue
            day = local_day(created)
            if day:
                op_by_day[day] += 1

        trend_labels = []
        trend_reserved = []
        trend_attended = []
        trend_operations = []
        cursor = from_date
        while cursor <= to_date:
            trend_labels.append(cursor.strftime('%d %b'))
            trend_reserved.append(daily_reserved.get(cursor, 0))
            trend_attended.append(daily_attended.get(cursor, 0))
            trend_operations.append(op_by_day.get(cursor, 0))
            cursor += timedelta(days=1)

        recent = (
            agent_patients(from_date, to_date)
            .annotate(
                has_surgery=Exists(
                    PatientVisits.objects.filter(
                        patientid_id=OuterRef('pk'),
                        evaluationeegree='Surgery',
                    )
                ),
                has_done_discussion=Exists(
                    PatientDiscussion.objects.filter(
                        patient_id=OuterRef('pk'),
                        discussionResult__name__iexact='DONE',
                    )
                ),
            )
            .order_by('-createdDate')[:15]
            .values(
                'patientid', 'fullname', 'reservationCode', 'mobile',
                'createdDate', 'attendanceDate', 'expectedDate',
                'has_surgery', 'has_done_discussion',
            )
        )

        return render(request, 'callcenter/performance_dashboard.html', {
            'agent_name': request.user.get_full_name() or request.user.username,
            'from_date': from_date,
            'to_date': to_date,
            'prev_from': prev_from,
            'prev_to': prev_to,
            'curr': curr,
            'prev': prev,
            'deltas': deltas,
            'recent': recent,
            'trend_labels_json': json.dumps(trend_labels, cls=DjangoJSONEncoder),
            'trend_reserved_json': json.dumps(trend_reserved, cls=DjangoJSONEncoder),
            'trend_attended_json': json.dumps(trend_attended, cls=DjangoJSONEncoder),
            'trend_operations_json': json.dumps(trend_operations, cls=DjangoJSONEncoder),
        })

    @staticmethod
    def _period_bounds(start, end):
        start_dt = timezone.make_aware(datetime.combine(start, time.min))
        end_dt = timezone.make_aware(datetime.combine(end + timedelta(days=1), time.min))
        return start_dt, end_dt

    @staticmethod
    def _summarize_agent(user, start, end):
        start_dt, end_dt = CallCenterView._period_bounds(start, end)
        qs = (
            Patient.objects
            .filter(
                Q(reservedBy=user) | Q(createdBy=user),
                isDeleted=False,
                createdDate__gte=start_dt,
                createdDate__lt=end_dt,
            )
            .exclude(leadSource='Center')
        )
        reserved = qs.count()
        attended = qs.filter(attendanceDate__isnull=False).count()
        patient_ids = list(qs.values_list('patientid', flat=True))
        surgery_ids = set(
            PatientVisits.objects.filter(
                patientid_id__in=patient_ids,
                evaluationeegree='Surgery',
            ).values_list('patientid_id', flat=True)
        )
        discussion_ids = set(
            PatientDiscussion.objects.filter(
                patient_id__in=patient_ids,
                discussionResult__name__iexact='DONE',
            ).values_list('patient_id', flat=True)
        )
        operations = len(surgery_ids | discussion_ids)
        attend_rate = round((attended / reserved) * 100, 1) if reserved else 0
        op_rate = round((operations / attended) * 100, 1) if attended else 0
        return {
            'user_id': user.id,
            'name': user.get_full_name() or user.username,
            'reserved': reserved,
            'attended': attended,
            'operations': operations,
            'attend_rate': attend_rate,
            'op_rate': op_rate,
        }

    @staticmethod
    def _compare_call_centers(agents, start, end):
        start_dt, end_dt = CallCenterView._period_bounds(start, end)
        agent_ids = [agent.id for agent in agents]
        agent_id_set = set(agent_ids)
        rows = (
            Patient.objects
            .filter(
                Q(reservedBy_id__in=agent_ids) | Q(createdBy_id__in=agent_ids),
                isDeleted=False,
                createdDate__gte=start_dt,
                createdDate__lt=end_dt,
            )
            .exclude(leadSource='Center')
            .values_list('patientid', 'reservedBy_id', 'createdBy_id', 'attendanceDate')
        )

        reserved_counts = Counter()
        attended_counts = Counter()
        patients_by_agent = defaultdict(list)
        seen = set()
        for pid, reserved_by, created_by, attendance in rows:
            agent_id = reserved_by if reserved_by in agent_id_set else created_by
            if agent_id not in agent_id_set:
                continue
            key = (agent_id, pid)
            if key in seen:
                continue
            seen.add(key)
            reserved_counts[agent_id] += 1
            patients_by_agent[agent_id].append(pid)
            if attendance:
                attended_counts[agent_id] += 1

        all_pids = [pid for pids in patients_by_agent.values() for pid in pids]
        operated_ids = set(
            PatientVisits.objects.filter(
                patientid_id__in=all_pids,
                evaluationeegree='Surgery',
            ).values_list('patientid_id', flat=True)
        ) | set(
            PatientDiscussion.objects.filter(
                patient_id__in=all_pids,
                discussionResult__name__iexact='DONE',
            ).values_list('patient_id', flat=True)
        )

        comparison = []
        for agent in agents:
            reserved = reserved_counts.get(agent.id, 0)
            attended = attended_counts.get(agent.id, 0)
            operations = sum(1 for pid in patients_by_agent.get(agent.id, []) if pid in operated_ids)
            comparison.append({
                'user_id': agent.id,
                'name': agent.get_full_name() or agent.username,
                'username': agent.username,
                'reserved': reserved,
                'attended': attended,
                'operations': operations,
                'attend_rate': round((attended / reserved) * 100, 1) if reserved else 0,
                'op_rate': round((operations / attended) * 100, 1) if attended else 0,
            })
        comparison.sort(key=lambda row: (-row['reserved'], -row['attended'], row['name'].lower()))
        for index, row in enumerate(comparison, start=1):
            row['rank'] = index
        return comparison

    @login_required
    def marketing_performance_report(request):
        if not (request.user.is_staff or request.user.is_superuser):
            return redirect('no_permission')

        today = date.today()
        default_from = today.replace(day=1)

        def parse_day(value, fallback):
            try:
                return datetime.strptime(value, '%Y-%m-%d').date()
            except (TypeError, ValueError):
                return fallback

        from_date = parse_day(request.GET.get('from_date'), default_from)
        to_date = parse_day(request.GET.get('to_date'), today)
        if from_date > to_date:
            from_date, to_date = to_date, from_date

        agents = list(
            get_user_model().objects.filter(
                groups__name__iexact='Call Center',
                is_active=True,
            ).order_by('first_name', 'username')
        )
        agent_map = {agent.id: agent for agent in agents}

        selected_id = request.GET.get('agent') or ''
        compare_id = request.GET.get('compare_agent') or ''
        selected_agent = agent_map.get(int(selected_id)) if selected_id.isdigit() else None
        compare_agent = agent_map.get(int(compare_id)) if compare_id.isdigit() else None
        if compare_agent and selected_agent and compare_agent.id == selected_agent.id:
            compare_agent = None

        selected_stats = (
            CallCenterView._summarize_agent(selected_agent, from_date, to_date)
            if selected_agent else None
        )
        compare_stats = (
            CallCenterView._summarize_agent(compare_agent, from_date, to_date)
            if compare_agent else None
        )
        comparison = CallCenterView._compare_call_centers(agents, from_date, to_date)

        highlight_ids = {row_id for row_id in (
            selected_agent.id if selected_agent else None,
            compare_agent.id if compare_agent else None,
        ) if row_id}

        return render(request, 'reports/callcenter_performance.html', {
            'from_date': from_date,
            'to_date': to_date,
            'agents': agents,
            'selected_id': selected_agent.id if selected_agent else '',
            'compare_id': compare_agent.id if compare_agent else '',
            'selected_stats': selected_stats,
            'compare_stats': compare_stats,
            'comparison': comparison,
            'highlight_ids': highlight_ids,
            'chart_labels_json': json.dumps([row['name'] for row in comparison], cls=DjangoJSONEncoder),
            'chart_reserved_json': json.dumps([row['reserved'] for row in comparison], cls=DjangoJSONEncoder),
            'chart_attended_json': json.dumps([row['attended'] for row in comparison], cls=DjangoJSONEncoder),
            'chart_operations_json': json.dumps([row['operations'] for row in comparison], cls=DjangoJSONEncoder),
        })

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
    
    def reservation_qr_view(request, token):
        patient = get_object_or_404(Patient, qr_token=token)

        return render(request, 'callcenter/qr_details.html', {
            'patient': patient
        })
        





def generate_reservation_image(patient):
    import qrcode
    from PIL import Image, ImageDraw, ImageFont
    from io import BytesIO
    from django.core.files import File
    from django.conf import settings
    from django.urls import reverse
    from django.contrib.staticfiles import finders
    import os

    TEAL = "#0F4146"
    TAUPE = "#928469"
    CREAM = "#EAE4D7"
    MUTED = "#718096"
    CARD_LINE = "#e8e4dc"
    W = 900

    def existing_files(*paths):
        found = []
        for path in paths:
            if path and os.path.isfile(path):
                found.append(path)
        return found

    here = os.path.dirname(os.path.abspath(__file__))
    app_fonts = os.path.abspath(os.path.join(here, "..", "fonts"))
    static_fonts = os.path.join(str(settings.BASE_DIR), "static", "assets", "fonts")
    collected_fonts = os.path.join(str(getattr(settings, "STATIC_ROOT", "") or ""), "assets", "fonts")
    barcode_font = ""
    try:
        import barcode as barcode_mod
        barcode_font = os.path.join(os.path.dirname(barcode_mod.__file__), "fonts", "DejaVuSansMono.ttf")
    except Exception:
        pass

    regular_candidates = existing_files(
        os.path.join(app_fonts, "arial.ttf"),
        os.path.join(static_fonts, "arial.ttf"),
        os.path.join(collected_fonts, "arial.ttf"),
        finders.find("assets/fonts/arial.ttf"),
        os.path.join(str(settings.BASE_DIR), "arial.ttf"),
        r"C:\Windows\Fonts\arial.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
        "/usr/share/fonts/truetype/freefont/FreeSans.ttf",
        "/usr/share/fonts/truetype/noto/NotoSans-Regular.ttf",
        barcode_font,
    )
    bold_candidates = existing_files(
        os.path.join(app_fonts, "arialbd.ttf"),
        os.path.join(static_fonts, "arialbd.ttf"),
        os.path.join(collected_fonts, "arialbd.ttf"),
        finders.find("assets/fonts/arialbd.ttf"),
        r"C:\Windows\Fonts\arialbd.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/dejavu/DejaVuSans-Bold.ttf",
    ) + regular_candidates

    def make_font(size, bold=False):
        for path in (bold_candidates if bold else regular_candidates):
            try:
                return ImageFont.truetype(path, size)
            except Exception:
                continue
        try:
            return ImageFont.load_default(size=size)
        except TypeError:
            return ImageFont.load_default()

    title_font = make_font(36, bold=True)
    subtitle_font = make_font(22)
    label_font = make_font(16)
    value_font = make_font(28, bold=True)
    footer_title_font = make_font(24, bold=True)
    footer_font = make_font(22)
    caption_font = make_font(18)

    # Draw on a tall canvas, then crop to the real content height.
    image = Image.new("RGB", (W, 1800), "#ffffff")
    draw = ImageDraw.Draw(image)
    draw.chord([(-80, -160), (W + 80, 80)], start=0, end=360, fill=CREAM)

    def text_size(text, font):
        bbox = draw.textbbox((0, 0), str(text), font=font)
        return bbox[2] - bbox[0], bbox[3] - bbox[1]

    def center_text(text, y, font, color):
        tw, th = text_size(text, font)
        draw.text(((W - tw) / 2, y), str(text), fill=color, font=font)
        return th

    def fit_text(text, font, max_width):
        text = str(text or "")
        if text_size(text, font)[0] <= max_width:
            return text
        ellipsis = "..."
        while text and text_size(text + ellipsis, font)[0] > max_width:
            text = text[:-1]
        return text + ellipsis

    y = 18
    logo_path = finders.find("assets/img/logo4.png")
    if logo_path:
        logo = Image.open(logo_path).convert("RGBA")
        ratio = 220 / logo.width
        logo = logo.resize((int(logo.width * ratio), int(logo.height * ratio)))
        image.paste(logo, ((W - logo.width) // 2, y), logo)
        y += logo.height + 8

    y += 4
    y += center_text("RESERVATION CONFIRMATION", y, title_font, TEAL) + 10
    draw.ellipse([(W // 2 - 4, y), (W // 2 + 4, y + 8)], fill=TAUPE)
    draw.line([(W // 2 - 46, y + 4), (W // 2 - 12, y + 4)], fill=TAUPE, width=2)
    draw.line([(W // 2 + 12, y + 4), (W // 2 + 46, y + 4)], fill=TAUPE, width=2)
    y += 18
    y += center_text("Your reservation has been created successfully.", y, subtitle_font, MUTED) + 16

    date = patient.expectedDate
    date_str = date.strftime("%d %B %Y (%A)") if date else "Not Scheduled"
    card_x1, card_x2 = 56, W - 56
    value_max_w = card_x2 - card_x1 - 150
    rows = [
        ("user", "PATIENT NAME", fit_text(patient.fullname, value_font, value_max_w)),
        ("calendar", "RESERVATION DATE", date_str),
        ("hash", "RESERVATION CODE", f"#{patient.reservationCode}"),
    ]

    row_h = 64
    card_y1 = y
    card_y2 = card_y1 + 18 + (len(rows) * row_h)
    draw.rounded_rectangle([card_x1, card_y1, card_x2, card_y2], radius=18, fill="#ffffff", outline=CARD_LINE, width=2)
    draw.rounded_rectangle([card_x1, card_y1, card_x1 + 8, card_y2], radius=6, fill=TEAL)

    def load_icon(name):
        path = finders.find(f"assets/icons/{name}.png")
        if path:
            return Image.open(path).convert("RGBA").resize((36, 36))
        return None

    icon_x = card_x1 + 24
    text_x = icon_x + 58
    for i, (icon_name, label, value) in enumerate(rows):
        cy = card_y1 + 14 + (i * row_h)
        draw.ellipse([icon_x, cy + 6, icon_x + 42, cy + 48], fill=TEAL)
        icon = load_icon(icon_name)
        if icon:
            image.paste(icon, (icon_x + 3, cy + 9), icon)
        draw.line([(text_x, cy + 10), (text_x, cy + 44)], fill=CARD_LINE, width=2)
        draw.text((text_x + 14, cy + 4), label, fill=MUTED, font=label_font)
        draw.text((text_x + 14, cy + 24), value, fill=TEAL, font=value_font)

    y = card_y2 + 18

    path = reverse("reservation_qr", kwargs={"token": patient.qr_token})
    qr_data = f"{settings.BASE_URL.rstrip('/')}{path}"
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=2)
    qr.add_data(qr_data)
    qr.make(fit=True)
    qr_img = qr.make_image(fill_color=TEAL, back_color="white").convert("RGB")

    qr_size = 300
    qr_img = qr_img.resize((qr_size, qr_size))
    qr_x = (W - qr_size) // 2
    pad = 16
    draw.rounded_rectangle(
        [qr_x - pad, y, qr_x + qr_size + pad, y + qr_size + pad * 2],
        radius=16,
        outline=TAUPE,
        width=3,
        fill="white",
    )
    image.paste(qr_img, (qr_x, y + pad))
    y += qr_size + pad * 2 + 10
    y += center_text("Scan this code at the center", y, caption_font, MUTED) + 14
    y += center_text("Thank you for choosing us", y, footer_title_font, TEAL) + 6
    y += center_text("We look forward to serving you.", y, subtitle_font, MUTED) + 16

    bar_h = 56
    draw.rounded_rectangle([48, y, W - 48, y + bar_h], radius=16, fill=TAUPE)
    address = "بغداد - الكرادة - ساحة الواثق"
    tw, th = text_size(address, footer_font)
    draw.text(((W - tw) / 2, y + (bar_h - th) / 2), address, fill="#ffffff", font=footer_font)
    y += bar_h + 16

    image = image.crop((0, 0, W, y))

    buffer = BytesIO()
    image.save(buffer, format="PNG")
    buffer.seek(0)

    file_name = f"reservation_{patient.patientid}.png"
    if patient.reservation_image:
        patient.reservation_image.delete(save=False)
    patient.reservation_image.save(file_name, File(buffer), save=False)