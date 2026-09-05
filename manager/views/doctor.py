import datetime  # Use fully qualified import for datetime
from django.shortcuts import  redirect, render
import json
from django.core.serializers.json import DjangoJSONEncoder
from django.http import JsonResponse
from django.urls import reverse
  # Import from the package, not the specific file
from manager.decorators import permission_required_with_redirect
from manager.model.doctor import Doctor
from manager.model.patient import Patient
from manager.model.visit import ClassficationsOptions, PatientVisits, OperationType, DiscussionResult, PatientDiscussion
from django.shortcuts import get_object_or_404
from manager.orm import ORMPatientsHandling
from django.views.generic import ListView
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from datetime import date, timedelta
from django.utils import timezone
from django.db import transaction
from django.db.models import Count, Case, When, IntegerField, Q, Sum, Max
from django.db.models.functions import TruncDate
from django.db.utils import OperationalError, IntegrityError
from django.core.paginator import Paginator
from django.contrib import messages

ormObj=ORMPatientsHandling()


def amount_to_arabic_words(amount):
    try:
        number = int(round(float(amount)))
    except (TypeError, ValueError):
        return ''

    if number == 0:
        return 'صفر دينار عراقي فقط لا غير'

    ones = ['', 'واحد', 'اثنان', 'ثلاثة', 'أربعة', 'خمسة', 'ستة', 'سبعة', 'ثمانية', 'تسعة']
    teens = ['عشرة', 'أحد عشر', 'اثنا عشر', 'ثلاثة عشر', 'أربعة عشر', 'خمسة عشر', 'ستة عشر', 'سبعة عشر', 'ثمانية عشر', 'تسعة عشر']
    tens = ['', 'عشرة', 'عشرون', 'ثلاثون', 'أربعون', 'خمسون', 'ستون', 'سبعون', 'ثمانون', 'تسعون']
    hundreds = ['', 'مائة', 'مائتان', 'ثلاثمائة', 'أربعمائة', 'خمسمائة', 'ستمائة', 'سبعمائة', 'ثمانمائة', 'تسعمائة']

    def join_ar(*parts):
        return ' و '.join([p for p in parts if p])

    def three_digits(n):
        h, rest = divmod(n, 100)
        t, o = divmod(rest, 10)
        parts = []
        if h:
            parts.append(hundreds[h])
        if rest == 0:
            return join_ar(*parts)
        if rest < 10:
            parts.append(ones[rest])
        elif rest < 20:
            parts.append(teens[rest - 10])
        else:
            if o:
                parts.append(ones[o])
            parts.append(tens[t])
        return join_ar(*parts)

    millions, rem = divmod(number, 1000000)
    thousands, rem = divmod(rem, 1000)
    parts = []
    if millions:
        if millions == 1:
            parts.append('مليون')
        elif millions == 2:
            parts.append('مليونان')
        elif millions < 11:
            parts.append(f'{three_digits(millions)} ملايين')
        else:
            parts.append(f'{three_digits(millions)} مليون')
    if thousands:
        if thousands == 1:
            parts.append('ألف')
        elif thousands == 2:
            parts.append('ألفان')
        elif thousands < 11:
            parts.append(f'{three_digits(thousands)} آلاف')
        else:
            parts.append(f'{three_digits(thousands)} ألف')
    if rem:
        parts.append(three_digits(rem))

    return f"{join_ar(*parts)} دينار عراقي فقط لا غير"


def ensure_receipt_no(discussion):
    try:
        if discussion.receiptNo:
            return discussion.receiptNo
        with transaction.atomic():
            discussion = PatientDiscussion.objects.select_for_update().get(pk=discussion.pk)
            if discussion.receiptNo:
                return discussion.receiptNo
            last = (
                PatientDiscussion.objects
                .exclude(receiptNo__isnull=True)
                .order_by('-receiptNo')
                .values_list('receiptNo', flat=True)
                .first()
            ) or 0
            discussion.receiptNo = last + 1
            discussion.save(update_fields=['receiptNo'])
            return discussion.receiptNo
    except OperationalError:
        return discussion.discussionID


def discussion_serial_for_today(fileserial, on_date=None):
    """رقم الديسكشن = رقم الملف + تاريخ اليوم (ديسكشن واحد للمريض في اليوم)."""
    day = on_date or timezone.now().date()
    return f"{fileserial}-{day.strftime('%Y-%m-%d')}"


def get_patient_discussion_for_day(patient, on_date=None):
    day = on_date or timezone.now().date()
    serial = discussion_serial_for_today(patient.fileserial, day)
    by_serial = PatientDiscussion.objects.filter(patient=patient, discussionSerial=serial).first()
    if by_serial:
        return by_serial
    return (
        PatientDiscussion.objects
        .filter(patient=patient, createdDate__date=day)
        .order_by('-discussionID')
        .first()
    )


def get_discussion_doctors():
    return (
        User.objects.filter(groups__name='Doctors', is_active=True)
        .order_by('first_name', 'last_name', 'username')
    )


def user_display_name(user):
    if not user:
        return ''
    return user.get_full_name() or user.username


class DoctorView(ListView):
    
    #@permission_required_with_redirect('manager.addNewVisitForPatient',login_url='/no-permission/')
    @login_required   
    def doctorPatientvisit(request): 
        classifiedOptions = ClassficationsOptions.objects.filter(isActive=True).values(
            'classifiedID', 'classifiedCategory', 'optionClassified', 'isActive'
        )
        
        classifiedOptionsJSON = json.dumps(list(classifiedOptions), cls=DjangoJSONEncoder)

        if request.method == 'POST':
            txtpatientid = request.POST.get('hdfpatientid')
            userID = request.user   # Static doctor ID for now; replace with actual data.
            txtdiagnosis = request.POST.get('Diagnosis')
            EvaulDegree = request.POST.get('gridRadios')
            txtRemarks = request.POST.get('txtRemarks')
            hdfclassifiedID = request.POST.get('selectedOption')
        

            patient = Patient.objects.get(pk=txtpatientid)
            doctor = userID
            visit_date = timezone.now().date()  # Use fully qualified datetime
            objclassifiedID = get_object_or_404(ClassficationsOptions, pk=hdfclassifiedID)
            

            # Save the patient visit
            data = PatientVisits(
                patientid=patient,
                visittype='D',
                diagnosis=txtdiagnosis,
                evaluationeegree=EvaulDegree,
                classifiedID=objclassifiedID,
                visitdate=visit_date,
                doctorid=doctor,
                reasonforvisit=txtRemarks,
                createdate=timezone.now().date(),
            )
            data.save()

            
            return redirect(reverse("confirm_page_doctor", kwargs={                   
                    "fileserial": patient.fileserial
                   
                }))

        
        patientList = ormObj.getPatientsForDoctorExam()
        patientcount = patientList.count()

        return render(
            request,
            'center/doctorPatientVisit.html',
            {
                'patients': patientList,
                'Total': patientcount,
                'classifiedOptionsJSON': classifiedOptionsJSON,
            }
        )

    
    def confirm_page_doctor(request, fileserial):
        # use fileserial safely
        # print(fileserial)
      

        return render(request, "doctor/ConfirmMsgDoctor.html", {
            "fileserial": fileserial,
            #"patientName": patientName,
            ##"show_print": True,
            
            
            
        })
        
    def confirm_page_audit(request, fileserial):
        # use fileserial safely
       

        return render(request, "doctor/ConfirmMsgAudit.html", {
            "fileserial": fileserial,
            #"patientName": patientName,
            
            
            
            
        })



   # @permission_required_with_redirect('manager.addNewVisitForPatient',login_url='/no-permission/')
    @login_required   
    def auditPatientvisit(request): 
        classifiedOptions = ClassficationsOptions.objects.filter(isActive=True).values(
            'classifiedID', 'classifiedCategory', 'optionClassified', 'isActive'
        )
        
        classifiedOptionsJSON = json.dumps(list(classifiedOptions), cls=DjangoJSONEncoder)

        if request.method == 'POST':
            txtpatientid = request.POST.get('hdfpatientid')
            userID = request.user  # Static doctor ID for now; replace with actual data.
            #txtdiagnosis = request.POST.get('Diagnosis')
            EvaulDegree = request.POST.get('gridRadios')
            #txtRemarks = request.POST.get('txtRemarks')
            hdfclassifiedID = request.POST.get('selectedOption')       

            patient = Patient.objects.get(pk=txtpatientid)
            
            visit_date = datetime.datetime.now().date()  # Use fully qualified datetime
            objclassifiedID = get_object_or_404(ClassficationsOptions, pk=hdfclassifiedID)
            

            # Save the patient visit
            data = PatientVisits(
                patientid=patient,
                visittype='A',
                #diagnosis=txtdiagnosis,
                evaluationeegree=EvaulDegree,
                classifiedID=objclassifiedID,
                visitdate=visit_date,
                doctorid=userID,
                #reasonforvisit=txtRemarks,
                createdate=visit_date,
            )
            data.save()

            return redirect(reverse("confirm_page_audit", kwargs={                   
                    "fileserial": patient.fileserial
                    #"patientName": patient.fullname
                   
                }))
        
        patientList = ormObj.getPatientsAttendedToday()
        patientcount = patientList.count()

        return render(
            request,
            'doctor/auditPatientVisit_SEC.html',
            {
                'patients': patientList,
                'Total': patientcount,
                'classifiedOptionsJSON': classifiedOptionsJSON,
            }
        )

    #visit list
    def getPatientVisits(request,visittype,scopeview=None):
        if scopeview == 'None':    
            scopeview = None
            
        today_date = date.today()
        past_10_days_date = today_date - timedelta(days=10)
        doctorUser = request.user.id  # Get the logged-in doctor's ID  

        # Create the base filter dictionary
        filter_criteria = {
            #"createdate__gte": past_10_days_date,
            "patientid__fileserial__isnull": False,
            "visittype": visittype,
            "doctorid": doctorUser,
        }

        # Conditionally add 'evaluationdegree' filter if scopeview is not None
        if scopeview is not None:
            filter_criteria["evaluationeegree"] = scopeview

        # Apply the filters to the queryset
        #patientList = PatientVisits.objects.filter(**filter_criteria).select_related('patientid', 'classifiedID')
        patientList = (
            PatientVisits.objects
            .filter(**filter_criteria)
            .select_related('patientid', 'classifiedID')
            .order_by('-createdate')[:50]
)
        
        
                # Example categories you want to exclude
        excluded_categories = ["OK", "6/6", "++"]
        classfications_options = []
        
        

        if visittype == "D":
            classfications_options = (
                ClassficationsOptions.objects
                .exclude(classifiedCategory__in=excluded_categories)
                .values("classifiedCategory")
                .distinct()
            )
        else:
            classfications_options = (
                ClassficationsOptions.objects
                .values("classifiedCategory")
                .distinct()
            )        
             
              

        return render(
            request,
            'doctor/auditPatientsList.html',
            {
                'patients': patientList,
                'classfications_options': classfications_options,
            }
        )
        
    def get_classified_options(request):
        category = request.GET.get('category', None)  # Get selected category from request
        if category:
            options = ClassficationsOptions.objects.filter(classifiedCategory=category, isActive=True).values_list('optionClassified', flat=True)
            return JsonResponse({'options': list(options)})
        return JsonResponse({'options': []})
    
    def update_patient_visit(request):
        if request.method == "POST":
            try:
                visit_id = request.POST.get("visit_id")
                evaluation_degree = request.POST.get("evaluation_degree")
                classified_id = request.POST.get("classified_id")

                # Ensure visit_id exists
                if not visit_id:
                    return JsonResponse({"success": False, "error": "Missing visit_id"}, status=400)

                visit = get_object_or_404(PatientVisits, visitid=visit_id)

                # Set values
                visit.evaluationeegree = evaluation_degree if evaluation_degree else None

                # Ensure classified_id is valid
                if classified_id:
                    classified_option = get_object_or_404(ClassficationsOptions, optionClassified=classified_id,classifiedCategory=visit.evaluationeegree)
                    visit.classifiedID = classified_option
                else:
                    visit.classifiedID = None  # Allow unsetting

                visit.updatedDate = date.today()
                visit.save()

                return JsonResponse({"success": True})

            except Exception as e:
                return JsonResponse({"success": False, "error": str(e)}, status=500)

        return JsonResponse({"success": False, "error": "Invalid request method"}, status=400)
    
    def get_evaluation_degree_count(doctor_id):
        last_30_days = timezone.now() - timedelta(days=30)
        
        return (
            PatientVisits.objects.filter(doctorid=doctor_id, visitdate__gte=last_30_days)
            .aggregate(
                ok_count=Count(Case(When(evaluationeegree="OK", then=1), output_field=IntegerField())),
                plus_plus_count=Count(Case(When(evaluationeegree="++", then=1), output_field=IntegerField())),
                bad_count=Count(Case(When(evaluationeegree="Bad", then=1), output_field=IntegerField())),
                surgery_count=Count(Case(When(evaluationeegree="Surgery", then=1), output_field=IntegerField())),
                six_six_count=Count(Case(When(evaluationeegree="6/6", then=1), output_field=IntegerField()))
            )
        )
        
        
    def doctorOperation(request):
        
        ratio, percent = DoctorView.get_doctor_stats(doctor_id= request.user)
        operation_types = OperationType.objects.filter(isActive=True).order_by('name')
        context = {
            'ratio': ratio,
            'precent': percent,
            'operation_types': operation_types,
        }
        
        return render(
            request,
            'doctor/operation.html', context          
        )

    @login_required
    def doctorDiscussion(request):
        doctor_name = request.user.get_full_name() or request.user.username
        today = timezone.now().date()
        DiscussionResult.objects.get_or_create(name='DONE', defaults={'isActive': True})
        operation_types = list(
            OperationType.objects.filter(isActive=True).values('operationTypeID', 'name')
        )
        discussion_results = list(
            DiscussionResult.objects.filter(isActive=True).values('discussionResultID', 'name')
        )
        doctors = list(get_discussion_doctors())
        if not any(d.pk == request.user.pk for d in doctors):
            doctors.append(request.user)
        return render(
            request,
            'doctor/discussion.html',
            {
                'doctor_name': doctor_name,
                'today': today.strftime('%Y-%m-%d'),
                'operation_types': operation_types,
                'discussion_results': discussion_results,
                'doctors': doctors,
                'operation_types_json': json.dumps(operation_types, cls=DjangoJSONEncoder),
                'discussion_results_json': json.dumps(discussion_results, cls=DjangoJSONEncoder),
            },
        )

    @staticmethod
    def _discussion_calendar_day_counts(start_week, end_week, calendar_type='operation'):
        """Count discussions grouped by day for operation or discussion calendars."""
        if calendar_type == 'discussion':
            qs = (
                PatientDiscussion.objects.filter(createdDate__isnull=False)
                .annotate(day=TruncDate('createdDate'))
                .filter(day__gte=start_week, day__lte=end_week)
            )
            day_field = 'day'
        else:
            qs = PatientDiscussion.objects.filter(
                specifyDate__gte=start_week,
                specifyDate__lte=end_week,
            )
            day_field = 'specifyDate'

        rows = (
            qs.values(day_field)
            .annotate(
                total=Count('discussionID'),
                done=Count('discussionID', filter=Q(discussionResult__name__iexact='DONE')),
                pending=Count('discussionID', filter=~Q(discussionResult__name__iexact='DONE')),
            )
        )
        counts = {}
        for row in rows:
            day = row.get(day_field)
            if day:
                counts[day] = row
        return counts

    @staticmethod
    @login_required
    def discussion_week_counts(request):
        """Return per-day counts for the inline week picker on the discussion form."""
        week_start_str = request.GET.get('week_start')
        calendar_type = (request.GET.get('calendar_type') or 'operation').strip().lower()
        if calendar_type not in ('discussion', 'operation'):
            calendar_type = 'operation'

        try:
            week_start = datetime.datetime.strptime(week_start_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            today = timezone.now().date()
            week_start = today - datetime.timedelta(days=today.weekday())

        week_end = week_start + datetime.timedelta(days=6)
        counts = DoctorView._discussion_calendar_day_counts(
            week_start, week_end, calendar_type=calendar_type
        )

        days = []
        for i in range(7):
            day = week_start + datetime.timedelta(days=i)
            row = counts.get(day) or {}
            days.append({
                'date': day.strftime('%Y-%m-%d'),
                'label': day.strftime('%a'),
                'day_num': day.day,
                'count': row.get('total', 0) or 0,
            })

        return JsonResponse({
            'calendar_type': calendar_type,
            'week_start': week_start.strftime('%Y-%m-%d'),
            'week_end': week_end.strftime('%Y-%m-%d'),
            'days': days,
        })

    @staticmethod
    @login_required
    def save_discussion(request):
        if request.method != 'POST':
            return JsonResponse({'error': 'POST required'}, status=405)

        try:
            payload = json.loads(request.body.decode('utf-8'))
        except (json.JSONDecodeError, UnicodeDecodeError):
            return JsonResponse({'error': 'Invalid JSON'}, status=400)

        patient_id = payload.get('patient_id')
        doctor_id = payload.get('doctor_id') or request.user.id
        operation_type_id = payload.get('operation_type_id')
        eye_selection = (payload.get('eye_selection') or '').strip().upper()
        discussion_result_id = payload.get('discussion_result_id')
        specify_date = payload.get('specify_date')
        note = payload.get('note') or ''
        total_amount = payload.get('total_amount') or 0
        deposit = payload.get('deposit') or 0

        patient = get_object_or_404(Patient, pk=patient_id)
        doctor = get_object_or_404(User, pk=doctor_id, is_active=True)
        operation_type = get_object_or_404(OperationType, pk=operation_type_id)
        discussion_result = get_object_or_404(DiscussionResult, pk=discussion_result_id)

        if eye_selection not in ('OS', 'OD', 'OU'):
            return JsonResponse({'error': 'الرجاء اختيار تحديد العين (OS / OD / OU)'}, status=400)

        try:
            specify_date_obj = datetime.datetime.strptime(specify_date, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid specify date'}, status=400)

        if specify_date_obj < timezone.now().date():
            return JsonResponse({'error': 'لا يمكن اختيار تاريخ سابق'}, status=400)

        try:
            total_amount = float(total_amount)
            deposit = float(deposit)
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid amounts'}, status=400)

        remainder = total_amount - deposit
        today = timezone.now().date()
        discussion_serial = discussion_serial_for_today(patient.fileserial, today)

        # Block true double-submit: same patient/date/op/eye/amounts by same user within 90s
        recent_duplicate = (
            PatientDiscussion.objects
            .filter(
                patient=patient,
                specifyDate=specify_date_obj,
                createdBy=request.user,
                operationType=operation_type,
                eyeSelection=eye_selection,
                totalAmount=total_amount,
                deposit=deposit,
                createdDate__gte=timezone.now() - datetime.timedelta(seconds=90),
            )
            .order_by('-discussionID')
            .first()
        )
        if recent_duplicate:
            is_done = (
                recent_duplicate.discussionResult
                and (recent_duplicate.discussionResult.name or '').strip().upper() == 'DONE'
            )
            if is_done:
                ensure_receipt_no(recent_duplicate)
            return JsonResponse({
                'ok': True,
                'discussion_id': recent_duplicate.discussionID,
                'discussion_serial': recent_duplicate.discussionSerial,
                'print_receipt': bool(is_done),
                'receipt_url': reverse('discussion_receipt', args=[recent_duplicate.discussionID]) if is_done else None,
                'authorization_url': reverse('discussion_authorization', args=[recent_duplicate.discussionID]) if is_done else None,
                'result_name': recent_duplicate.discussionResult.name if recent_duplicate.discussionResult else '',
                'duplicate_prevented': True,
            })

        existing_today = get_patient_discussion_for_day(patient, today)
        if existing_today:
            return JsonResponse({
                'error': 'المريض لديه ديسكشن لهذا اليوم',
                'discussion_serial': existing_today.discussionSerial,
                'discussion_id': existing_today.discussionID,
            }, status=400)

        with transaction.atomic():
            try:
                discussion = PatientDiscussion.objects.create(
                    discussionSerial=discussion_serial,
                    patient=patient,
                    doctor=doctor,
                    doctorName=user_display_name(doctor),
                    operationType=operation_type,
                    eyeSelection=eye_selection,
                    specifyDate=specify_date_obj,
                    discussionResult=discussion_result,
                    note=note,
                    totalAmount=total_amount,
                    deposit=deposit,
                    remainder=remainder,
                    createdBy=request.user,
                )
            except IntegrityError:
                existing_today = get_patient_discussion_for_day(patient, today)
                if existing_today:
                    return JsonResponse({
                        'error': 'المريض لديه ديسكشن لهذا اليوم',
                        'discussion_serial': existing_today.discussionSerial,
                        'discussion_id': existing_today.discussionID,
                    }, status=400)
                raise

        is_done = (discussion_result.name or '').strip().upper() == 'DONE'
        if is_done:
            ensure_receipt_no(discussion)
        receipt_url = reverse('discussion_receipt', args=[discussion.discussionID]) if is_done else None
        authorization_url = reverse('discussion_authorization', args=[discussion.discussionID]) if is_done else None

        return JsonResponse({
            'ok': True,
            'discussion_id': discussion.discussionID,
            'discussion_serial': discussion.discussionSerial,
            'print_receipt': is_done,
            'receipt_url': receipt_url,
            'authorization_url': authorization_url,
            'result_name': discussion_result.name,
        })

    @login_required
    def discussion_receipt(request, discussion_id):
        discussion = get_object_or_404(
            PatientDiscussion.objects.select_related(
                'patient', 'doctor', 'operationType', 'discussionResult', 'createdBy'
            ),
            pk=discussion_id,
        )
        result_name = (discussion.discussionResult.name if discussion.discussionResult else '') or ''
        if result_name.strip().upper() != 'DONE':
            return render(request, 'Duplicated.html', {
                'message': 'يتم طباعة سند القبض فقط عندما تكون نتيجة الديسكشن DONE.',
                'returnUrl': '/Discussion',
                'btnText': 'رجوع',
            }, status=200)

        deposit = discussion.deposit or 0
        remainder = discussion.remainder or 0
        total = discussion.totalAmount or 0
        payment_type = 'completion' if float(remainder) <= 0 else 'advance'
        today = timezone.now().date()
        patient_name = discussion.patient.fullname if discussion.patient else ''
        operation_name = discussion.operationType.name if discussion.operationType else ''
        eye = discussion.eyeSelection or ''
        reason_parts = []
        if operation_name:
            reason_parts.append(f"عملية {operation_name}")
        if eye:
            reason_parts.append(f"العين {eye}")
        reason = " — ".join(reason_parts) if reason_parts else 'عملية'
        receipt_no = ensure_receipt_no(discussion)

        return render(request, 'doctor/discussion_receipt.html', {
            'discussion': discussion,
            'receipt_no': f"{receipt_no:04d}",
            'receipt_date': today,
            'patient_name': patient_name,
            'file_serial': discussion.patient.fileserial if discussion.patient else '',
            'deposit': deposit,
            'remainder': remainder,
            'total': total,
            'payment_type': payment_type,
            'amount_words': amount_to_arabic_words(deposit),
            'reason': reason,
            'cashier': (request.user.get_full_name() or request.user.username),
        })

    @login_required
    def discussion_authorization(request, discussion_id):
        discussion = get_object_or_404(
            PatientDiscussion.objects.select_related(
                'patient', 'doctor', 'operationType', 'discussionResult'
            ),
            pk=discussion_id,
        )
        patient_name = discussion.patient.fullname if discussion.patient else ''
        file_serial = discussion.patient.fileserial if discussion.patient else ''
        operation_name = discussion.operationType.name if discussion.operationType else ''
        eye = discussion.eyeSelection or ''
        operation_text = operation_name or ''
        if eye:
            operation_text = f"{operation_text} ({eye})".strip()

        return render(request, 'doctor/discussion_authorization.html', {
            'discussion': discussion,
            'patient_name': patient_name,
            'file_serial': file_serial,
            'auth_date': timezone.now().date(),
            'operation_text': operation_text,
            'doctor_name': (
                discussion.doctor.get_full_name() or discussion.doctor.username
            ) if discussion.doctor else '',
        })

    @login_required
    def discussion_dashboard(request):
        qs = PatientDiscussion.objects.select_related(
            'patient', 'doctor', 'operationType', 'discussionResult'
        ).order_by('-specifyDate', '-createdDate')

        q = (request.GET.get('q') or '').strip()
        date_from = (request.GET.get('date_from') or '').strip()
        date_to = (request.GET.get('date_to') or '').strip()
        operation_type_id = (request.GET.get('operation_type') or '').strip()
        result_id = (request.GET.get('result') or '').strip()
        doctor_id = (request.GET.get('doctor') or '').strip()
        doctor_name = (request.GET.get('doctor_name') or '').strip()

        if q:
            qs = qs.filter(
                Q(discussionSerial__icontains=q) |
                Q(patient__fileserial__icontains=q) |
                Q(patient__fullname__icontains=q) |
                Q(note__icontains=q)
            )
        if date_from:
            qs = qs.filter(specifyDate__gte=date_from)
        if date_to:
            qs = qs.filter(specifyDate__lte=date_to)
        if operation_type_id:
            qs = qs.filter(operationType_id=operation_type_id)
        if result_id:
            qs = qs.filter(discussionResult_id=result_id)
        if doctor_name:
            qs = qs.filter(doctorName=doctor_name)
        elif doctor_id:
            qs = qs.filter(doctor_id=doctor_id)

        today = timezone.now().date()
        week_start = today - datetime.timedelta(days=today.weekday())
        all_qs = PatientDiscussion.objects.all()
        stats = {
            'total': all_qs.count(),
            'today': all_qs.filter(specifyDate=today).count(),
            'done': all_qs.filter(discussionResult__name__iexact='DONE').count(),
            'week': all_qs.filter(specifyDate__gte=week_start, specifyDate__lte=today).count(),
            'filtered': qs.count(),
        }

        paginator = Paginator(qs, 20)
        page_obj = paginator.get_page(request.GET.get('page'))

        doctor_names = (
            PatientDiscussion.objects.exclude(doctorName__isnull=True)
            .exclude(doctorName='')
            .values_list('doctorName', flat=True)
            .distinct()
            .order_by('doctorName')
        )

        return render(request, 'doctor/discussion_dashboard.html', {
            'page_obj': page_obj,
            'stats': stats,
            'q': q,
            'date_from': date_from,
            'date_to': date_to,
            'operation_type_id': operation_type_id,
            'result_id': result_id,
            'doctor_id': doctor_id,
            'doctor_name': doctor_name,
            'operation_types': OperationType.objects.filter(isActive=True),
            'discussion_results': DiscussionResult.objects.filter(isActive=True),
            'doctor_names': doctor_names,
        })

    @staticmethod
    def _render_discussion_calendar_page(request, calendar_type='discussion'):
        today = timezone.now().date()
        week_offset = int(request.GET.get('week', 0) or 0)
        start_week = today - datetime.timedelta(days=(today.weekday() + 2) % 7)
        start_week = start_week + datetime.timedelta(weeks=week_offset * 2)
        end_week = start_week + datetime.timedelta(days=13)

        counts = DoctorView._discussion_calendar_day_counts(
            start_week, end_week, calendar_type=calendar_type
        )

        week_days = []
        period_total = period_done = period_pending = 0
        is_discussion = calendar_type == 'discussion'
        for i in range(14):
            day = start_week + datetime.timedelta(days=i)
            row = counts.get(day) or {}
            total = row.get('total', 0) or 0
            done = row.get('done', 0) or 0
            pending = row.get('pending', 0) or 0
            period_total += total
            period_done += done
            period_pending += pending
            week_days.append({
                'date': day,
                'date_str': day.strftime('%Y-%m-%d'),
                'day_name': day.strftime('%A'),
                'total': total,
                'done': done,
                'pending': pending,
                'display_count': total if is_discussion else done,
                'is_today': day == today,
            })

        return render(request, 'doctor/discussion_weekly_calendar.html', {
            'calendar_type': calendar_type,
            'page_title': 'تقرير تواريخ الديسكشن' if is_discussion else 'تقرير مواعيد العمليات',
            'page_subtitle': 'Discussion Dates Report' if is_discussion else 'Operation Dates Report',
            'count_label': 'الديسكشن' if is_discussion else 'العمليات',
            'date_basis': 'تاريخ إجراء الديسكشن (تاريخ الإنشاء)' if is_discussion else 'تاريخ العملية — عمليات بحالة DONE فقط',
            'other_report_url': reverse('OperationCalendar') if is_discussion else reverse('DiscussionCalendar'),
            'other_report_label': 'تقرير مواعيد العمليات' if is_discussion else 'تقرير تواريخ الديسكشن',
            'show_pending': False,
            'show_done': is_discussion,
            'modal_status': 'all' if is_discussion else 'done',
            'period_stats': {
                'total': period_total if is_discussion else period_done,
                'done': period_done,
                'pending': period_pending,
            },
            'week_days': week_days,
            'week1_days': week_days[:7],
            'week2_days': week_days[7:],
            'start_week': start_week,
            'end_week': end_week,
            'week1_end': start_week + datetime.timedelta(days=6),
            'week2_start': start_week + datetime.timedelta(days=7),
            'week_offset': week_offset,
        })

    @login_required
    def discussion_weekly_calendar(request):
        return DoctorView._render_discussion_calendar_page(request, calendar_type='discussion')

    @login_required
    def discussion_operation_calendar(request):
        return DoctorView._render_discussion_calendar_page(request, calendar_type='operation')

    @staticmethod
    @login_required
    def discussion_day_list(request):
        date_str = request.GET.get('date')
        status = (request.GET.get('status') or 'all').strip().lower()
        calendar_type = (request.GET.get('mode') or request.GET.get('calendar_type') or 'discussion').strip().lower()
        if calendar_type not in ('discussion', 'operation'):
            calendar_type = 'discussion'
        try:
            day = datetime.datetime.strptime(date_str, '%Y-%m-%d').date()
        except (TypeError, ValueError):
            return JsonResponse({'error': 'Invalid date'}, status=400)

        if calendar_type == 'operation':
            qs = PatientDiscussion.objects.filter(specifyDate=day)
        else:
            qs = PatientDiscussion.objects.filter(createdDate__date=day)

        qs = (
            qs.select_related('patient', 'doctor', 'operationType', 'discussionResult')
            .order_by('-createdDate')
        )
        if status == 'done':
            qs = qs.filter(discussionResult__name__iexact='DONE')
        elif status == 'pending':
            qs = qs.exclude(discussionResult__name__iexact='DONE')

        items = []
        for d in qs:
            doctor_name = d.doctorName or ''
            if not doctor_name and d.doctor:
                doctor_name = d.doctor.get_full_name() or d.doctor.username
            result_name = d.discussionResult.name if d.discussionResult else ''
            items.append({
                'id': d.discussionID,
                'serial': d.discussionSerial,
                'file_serial': d.patient.fileserial if d.patient else '',
                'patient_name': d.patient.fullname if d.patient else '',
                'doctor': doctor_name,
                'discussion_date': d.createdDate.strftime('%Y-%m-%d') if d.createdDate else '',
                'operation_date': d.specifyDate.strftime('%Y-%m-%d') if d.specifyDate else '',
                'operation_type': d.operationType.name if d.operationType else '',
                'eye_selection': d.eyeSelection or '',
                'result': result_name,
                'total_amount': str(d.totalAmount) if d.totalAmount is not None else '',
                'deposit': str(d.deposit) if d.deposit is not None else '',
                'remainder': str(d.remainder) if d.remainder is not None else '',
                'note': d.note or '',
                'view_url': reverse('discussion_detail', args=[d.discussionID]),
                'edit_url': reverse('discussion_edit', args=[d.discussionID]),
                'receipt_url': reverse('discussion_receipt', args=[d.discussionID]) if (result_name or '').upper() == 'DONE' else '',
            })

        if status == 'done':
            title = 'DONE'
        elif status == 'pending':
            title = 'غير DONE'
        else:
            title = 'الكل'
        return JsonResponse({
            'date': date_str,
            'status': status,
            'calendar_type': calendar_type,
            'title': title,
            'count': len(items),
            'items': items,
        })

    @staticmethod
    def _pct(part, whole):
        return round((float(part) / float(whole)) * 100, 1) if whole else 0

    @staticmethod
    def _delta(curr, prev):
        if prev:
            return round(((float(curr) - float(prev)) / float(prev)) * 100, 1)
        return None

    @staticmethod
    def _management_range_stats(from_date, to_date):
        patients_added = Patient.objects.filter(
            isDeleted=False,
            createdDate__date__gte=from_date,
            createdDate__date__lte=to_date,
        ).count()
        patients_attended = Patient.objects.filter(
            isDeleted=False,
            attendanceDate__gte=from_date,
            attendanceDate__lte=to_date,
        ).count()
        doctor_visits = PatientVisits.objects.filter(
            visittype='D',
            visitdate__gte=from_date,
            visitdate__lte=to_date,
        )
        doctor_visit_count = doctor_visits.count()
        doctor_visit_patients = doctor_visits.values('patientid').distinct().count()

        discussions = PatientDiscussion.objects.filter(
            createdDate__date__gte=from_date,
            createdDate__date__lte=to_date,
        )
        discussed_count = discussions.count()
        discussed_patients = discussions.values('patient').distinct().count()
        done_qs = discussions.filter(discussionResult__name__iexact='DONE')
        done_count = done_qs.count()
        done_patients = done_qs.values('patient').distinct().count()
        money = done_qs.aggregate(
            total=Sum('totalAmount'),
            collected=Sum('deposit'),
            remaining=Sum('remainder'),
        )
        return {
            'added': patients_added,
            'attended': patients_attended,
            'doctor_visits': doctor_visit_count,
            'doctor_patients': doctor_visit_patients,
            'discussed': discussed_count,
            'discussed_patients': discussed_patients,
            'done': done_count,
            'done_patients': done_patients,
            'total_amount': float(money['total'] or 0),
            'collected': float(money['collected'] or 0),
            'remaining': float(money['remaining'] or 0),
        }

    @login_required
    def discussion_management_report(request):
        today = timezone.now().date()
        from_str = request.GET.get('from_date')
        to_str = request.GET.get('to_date')
        try:
            from_date = datetime.datetime.strptime(from_str, '%Y-%m-%d').date() if from_str else today.replace(day=1)
        except ValueError:
            from_date = today.replace(day=1)
        try:
            to_date = datetime.datetime.strptime(to_str, '%Y-%m-%d').date() if to_str else today
        except ValueError:
            to_date = today
        if from_date > to_date:
            from_date, to_date = to_date, from_date

        curr = DoctorView._management_range_stats(from_date, to_date)
        period_days = (to_date - from_date).days + 1
        prev_to = from_date - datetime.timedelta(days=1)
        prev_from = prev_to - datetime.timedelta(days=period_days - 1)
        prev = DoctorView._management_range_stats(prev_from, prev_to)

        funnel = [
            {'label': 'Patients added', 'value': curr['added']},
            {'label': 'Attended', 'value': curr['attended']},
            {'label': 'Visited doctor', 'value': curr['doctor_patients']},
            {'label': 'Discussed', 'value': curr['discussed_patients']},
            {'label': 'Paid / DONE', 'value': curr['done_patients']},
        ]
        funnel_max = max([s['value'] for s in funnel] + [1])
        for step in funnel:
            step['width'] = DoctorView._pct(step['value'], funnel_max)

        conversions = {
            'attend_rate': DoctorView._pct(curr['attended'], curr['added']),
            'visit_rate': DoctorView._pct(curr['doctor_patients'], curr['attended']),
            'discuss_rate': DoctorView._pct(curr['discussed_patients'], curr['doctor_patients']),
            'close_rate': DoctorView._pct(curr['done_patients'], curr['discussed_patients']),
            'paid_vs_visit': DoctorView._pct(curr['done_patients'], curr['doctor_patients']),
        }

        deltas = {
            'added': DoctorView._delta(curr['added'], prev['added']),
            'attended': DoctorView._delta(curr['attended'], prev['attended']),
            'doctor_patients': DoctorView._delta(curr['doctor_patients'], prev['doctor_patients']),
            'discussed_patients': DoctorView._delta(curr['discussed_patients'], prev['discussed_patients']),
            'done_patients': DoctorView._delta(curr['done_patients'], prev['done_patients']),
            'collected': DoctorView._delta(curr['collected'], prev['collected']),
        }

        trend_days = []
        cursor = from_date
        while cursor <= to_date:
            trend_days.append(cursor)
            cursor += datetime.timedelta(days=1)

        visits_by_day = {
            r['visitdate']: r['c']
            for r in PatientVisits.objects.filter(
                visittype='D', visitdate__gte=from_date, visitdate__lte=to_date
            ).values('visitdate').annotate(c=Count('visitid'))
            if r['visitdate']
        }
        discussed_by_day = {
            r['day']: r['c']
            for r in PatientDiscussion.objects.filter(
                createdDate__date__gte=from_date, createdDate__date__lte=to_date
            ).annotate(day=TruncDate('createdDate')).values('day').annotate(c=Count('discussionID'))
            if r['day']
        }
        done_by_day = {
            r['day']: r['c']
            for r in PatientDiscussion.objects.filter(
                createdDate__date__gte=from_date,
                createdDate__date__lte=to_date,
                discussionResult__name__iexact='DONE',
            ).annotate(day=TruncDate('createdDate')).values('day').annotate(c=Count('discussionID'))
            if r['day']
        }
        trend = {
            'labels': [d.strftime('%d-%b') for d in trend_days],
            'visits': [visits_by_day.get(d, 0) for d in trend_days],
            'discussed': [discussed_by_day.get(d, 0) for d in trend_days],
            'done': [done_by_day.get(d, 0) for d in trend_days],
        }

        result_rows = list(
            PatientDiscussion.objects.filter(
                createdDate__date__gte=from_date,
                createdDate__date__lte=to_date,
            ).values('discussionResult__name').annotate(c=Count('discussionID')).order_by('-c')
        )
        result_breakdown = [
            {'name': r['discussionResult__name'] or 'Not set', 'count': r['c']}
            for r in result_rows
        ]

        visit_stats = {
            r['doctorid']: r['c']
            for r in PatientVisits.objects.filter(
                visittype='D', visitdate__gte=from_date, visitdate__lte=to_date
            ).values('doctorid').annotate(c=Count('visitid'))
        }
        disc_stats = {
            r['doctor_id']: r
            for r in PatientDiscussion.objects.filter(
                createdDate__date__gte=from_date,
                createdDate__date__lte=to_date,
            ).values('doctor_id', 'doctor__first_name', 'doctor__last_name', 'doctor__username').annotate(
                discussed=Count('discussionID'),
                done=Count('discussionID', filter=Q(discussionResult__name__iexact='DONE')),
                collected=Sum('deposit', filter=Q(discussionResult__name__iexact='DONE')),
            )
        }
        doctor_ids = set(visit_stats.keys()) | set(disc_stats.keys())
        doctor_rows = []
        for did in doctor_ids:
            info = disc_stats.get(did) or {}
            name = ' '.join(p for p in [info.get('doctor__first_name'), info.get('doctor__last_name')] if p).strip()
            if not name:
                name = info.get('doctor__username') or f'Doctor #{did or "-"}'
            visits = visit_stats.get(did, 0)
            done = info.get('done', 0) or 0
            doctor_rows.append({
                'name': name,
                'visits': visits,
                'discussed': info.get('discussed', 0) or 0,
                'done': done,
                'collected': float(info.get('collected') or 0),
                'paid_vs_visit': DoctorView._pct(done, visits),
            })
        doctor_rows.sort(key=lambda r: r['collected'], reverse=True)

        insights = []
        if conversions['paid_vs_visit'] < 20 and curr['doctor_patients']:
            insights.append('Paid/DONE conversion vs doctor visits is below 20%. Review discussion quality and follow-up on visited patients who did not close.')
        if conversions['attend_rate'] < 50 and curr['added']:
            insights.append('Less than half of added patients attended. Call-center confirmation and reminder timing should be reviewed.')
        if conversions['discuss_rate'] < 50 and curr['doctor_patients']:
            insights.append('Many doctor visits are not reaching discussion. Check handoff from examination to discussion desk.')
        if curr['remaining'] > curr['collected'] and curr['done']:
            insights.append('Outstanding remainder is higher than collected deposits. Collection follow-up on DONE cases can lift cash received.')
        if curr['done_patients'] and curr['collected']:
            avg_ticket = curr['collected'] / curr['done_patients']
            insights.append(f'Average collected per paid patient is {avg_ticket:,.0f}. Track this weekly as a management KPI.')
        if not insights:
            insights.append('Funnel looks stable in this period. Keep watching paid vs doctor-visit conversion as the primary management KPI.')

        return render(request, 'doctor/discussion_management_report.html', {
            'from_date': from_date,
            'to_date': to_date,
            'prev_from': prev_from,
            'prev_to': prev_to,
            'curr': curr,
            'prev': prev,
            'funnel': funnel,
            'conversions': conversions,
            'deltas': deltas,
            'trend_json': json.dumps(trend, cls=DjangoJSONEncoder),
            'result_breakdown': result_breakdown,
            'result_json': json.dumps(result_breakdown, cls=DjangoJSONEncoder),
            'doctor_rows': doctor_rows,
            'insights': insights,
        })

    @login_required
    def discussion_detail(request, discussion_id):
        discussion = get_object_or_404(
            PatientDiscussion.objects.select_related(
                'patient', 'doctor', 'operationType', 'discussionResult', 'createdBy'
            ),
            pk=discussion_id,
        )
        result_name = (discussion.discussionResult.name if discussion.discussionResult else '') or ''
        return render(request, 'doctor/discussion_detail.html', {
            'discussion': discussion,
            'can_print': result_name.strip().upper() == 'DONE',
        })

    @login_required
    def discussion_edit(request, discussion_id):
        discussion = get_object_or_404(
            PatientDiscussion.objects.select_related(
                'patient', 'doctor', 'operationType', 'discussionResult'
            ),
            pk=discussion_id,
        )
        operation_types = OperationType.objects.filter(isActive=True)
        discussion_results = DiscussionResult.objects.filter(isActive=True)

        if request.method == 'POST':
            operation_type_id = request.POST.get('operation_type')
            eye_selection = (request.POST.get('eye_selection') or '').strip().upper()
            discussion_result_id = request.POST.get('discussion_result')
            specify_date = request.POST.get('specify_date')
            note = request.POST.get('note') or ''
            total_amount = request.POST.get('total_amount') or 0
            deposit = request.POST.get('deposit') or 0

            try:
                specify_date_obj = datetime.datetime.strptime(specify_date, '%Y-%m-%d').date()
            except (TypeError, ValueError):
                messages.error(request, 'تاريخ غير صالح')
                return redirect('discussion_edit', discussion_id=discussion.discussionID)

            try:
                total_amount = float(total_amount)
                deposit = float(deposit)
            except (TypeError, ValueError):
                messages.error(request, 'المبالغ غير صالحة')
                return redirect('discussion_edit', discussion_id=discussion.discussionID)

            if eye_selection not in ('OS', 'OD', 'OU'):
                messages.error(request, 'الرجاء اختيار تحديد العين')
                return redirect('discussion_edit', discussion_id=discussion.discussionID)

            discussion.operationType = get_object_or_404(OperationType, pk=operation_type_id)
            discussion.eyeSelection = eye_selection
            discussion.discussionResult = get_object_or_404(DiscussionResult, pk=discussion_result_id)
            discussion.specifyDate = specify_date_obj
            discussion.note = note
            discussion.totalAmount = total_amount
            discussion.deposit = deposit
            discussion.remainder = total_amount - deposit
            doctor_id = request.POST.get('doctor_id')
            if doctor_id:
                discussion.doctor = get_object_or_404(User, pk=doctor_id, is_active=True)
                discussion.doctorName = user_display_name(discussion.doctor)
            discussion.save()

            messages.success(request, 'تم حفظ تعديلات الديسكشن')
            result_name = (discussion.discussionResult.name or '').strip().upper()
            if result_name == 'DONE':
                ensure_receipt_no(discussion)
                return redirect('discussion_receipt', discussion_id=discussion.discussionID)
            return redirect('discussion_detail', discussion_id=discussion.discussionID)

        doctors = list(get_discussion_doctors())
        if discussion.doctor and not any(d.pk == discussion.doctor_id for d in doctors):
            doctors.append(discussion.doctor)
        return render(request, 'doctor/discussion_edit.html', {
            'discussion': discussion,
            'operation_types': operation_types,
            'discussion_results': discussion_results,
            'doctors': doctors,
            'specify_date': discussion.specifyDate.strftime('%Y-%m-%d') if discussion.specifyDate else '',
        })

        
    @staticmethod
    def get_patient_info(request, file_number):
        # Try to fetch patient by file serial
        visits = []
        patient = Patient.objects.filter(fileserial=file_number).first()
        if not patient:
            return JsonResponse({"error": "Patient not found"}, status=404)

        # Convert visits queryset to list of dicts.
        # Defer the new DoctorOp fields so search still works if those
        # columns have not been added on the database yet.
        visits_qs = (
            PatientVisits.objects
            .filter(patientid=patient)
            .defer('operationType', 'discussionNotes')
            .order_by("-visitdate")
        )
        visits = [
            {
                "visit_id": v.visitid,
                "visit_type": v.visittype,
                "doctor": v.doctorid.get_full_name() if v.doctorid else None,
                "visit_date": v.visitdate.strftime("%Y-%m-%d") if v.visitdate else None,
                "evaluation_degree": v.evaluationeegree,
                "evaluation_classified": v.classifiedID.optionClassified if v.classifiedID else None,
            }
            for v in visits_qs
        ]

        discussions = []
        try:
            discussions_qs = (
                PatientDiscussion.objects.filter(patient=patient)
                .select_related('doctor', 'operationType', 'discussionResult')
                .order_by('-specifyDate', '-createdDate')
            )
            discussions = [
                {
                    "discussion_id": d.discussionID,
                    "discussion_serial": d.discussionSerial,
                    "doctor": (d.doctor.get_full_name() or d.doctor.username) if d.doctor else None,
                    "specify_date": d.specifyDate.strftime("%Y-%m-%d") if d.specifyDate else None,
                    "operation_type": d.operationType.name if d.operationType else None,
                    "eye_selection": d.eyeSelection or None,
                    "discussion_result": d.discussionResult.name if d.discussionResult else None,
                    "total_amount": str(d.totalAmount) if d.totalAmount is not None else None,
                    "deposit": str(d.deposit) if d.deposit is not None else None,
                    "remainder": str(d.remainder) if d.remainder is not None else None,
                    "note": d.note or "",
                    "created_date": d.createdDate.strftime("%Y-%m-%d") if d.createdDate else None,
                }
                for d in discussions_qs
            ]
        except OperationalError:
            discussions = []

        today = timezone.now().date()
        today_discussion = None
        try:
            today_discussion = get_patient_discussion_for_day(patient, today)
        except OperationalError:
            today_discussion = None

        doctor_operation_type_id = None
        doctor_discussion_notes = ""
        try:
            latest_operation = (
                PatientVisits.objects
                .filter(patientid=patient, evaluationeegree='Surgery')
                .select_related('operationType')
                .order_by('-visitdate', '-visitid')
                .first()
            )
            if latest_operation:
                doctor_operation_type_id = latest_operation.operationType_id
                doctor_discussion_notes = latest_operation.discussionNotes or ""
        except OperationalError:
            pass

        data = {
            "name": patient.fullname,
            "fileserial": patient.fileserial,
            "visits": visits,
            "discussions": discussions,
            "age": patient.age,
            "patientID": patient.patientid,
            "remarks": patient.remarks or "",
            "discussion_call_notes": getattr(patient, "discussionCallNotes", None) or "",
            "doctor_operation_type_id": doctor_operation_type_id,
            "doctor_discussion_notes": doctor_discussion_notes,
            "has_today_discussion": bool(today_discussion),
            "today_discussion_serial": today_discussion.discussionSerial if today_discussion else None,
            "today_discussion_id": today_discussion.discussionID if today_discussion else None,
        }

        return JsonResponse(data)

    
       
    @staticmethod
    def get_doctor_stats(doctor_id):
        today = datetime.datetime.now().date()  # current date with timezone support

        # Total patients for this doctor today
        total_patients = PatientVisits.objects.filter(
            doctorid=doctor_id,
            visitdate=today
        ).count()

        # Patients with evaluationDegree today
        with_evaluation = PatientVisits.objects.filter(
            doctorid=doctor_id,
            visitdate=today
        ).exclude(evaluationeegree__isnull=True).exclude(evaluationeegree="Bad").count()

        ratio = f"{with_evaluation}/{total_patients}" if total_patients else "0/0"
        percent = int(round((with_evaluation / total_patients) * 100, 0)) if total_patients else 0

        return ratio, percent
    
    
    
    # function of operation or losing the patient
    def doctorPatientvisit(request): 
        classifiedOptions = ClassficationsOptions.objects.filter(isActive=True).values(
            'classifiedID', 'classifiedCategory', 'optionClassified', 'isActive'
        )
        
        classifiedOptionsJSON = json.dumps(list(classifiedOptions), cls=DjangoJSONEncoder)

        if request.method == 'POST':
            txtpatientid = request.POST.get('hdfpatientid')
            userID = request.user  # Static doctor ID for now; replace with actual data.
            #txtdiagnosis = request.POST.get('Diagnosis')
            #check which button is pressed to specify the doctor chocen
            if 'btnOperation' in request.POST:
                EvaulDegree = 'Surgery'
            else:
                EvaulDegree = 'Bad'

            operation_type_id = (request.POST.get('operationType') or '').strip()
            discussion_notes = (request.POST.get('discussionNotes') or '').strip()

            # Kept for later when DoctorOp asks for operation type again:
            # if EvaulDegree == 'Surgery' and not operation_type_id:
            #     return render(
            #         request,
            #         "Duplicated.html",
            #         {
            #             'message': "الرجاء اختيار نوع العملية.",
            #             'returnUrl': 'DoctorOp',
            #             'btnText': 'رجوع'
            #         },
            #         status=200,
            #     )
            
            #txtRemarks = request.POST.get('txtRemarks')
            #hdfclassifiedID = request.POST.get('selectedOption')       

            patient = Patient.objects.get(pk=txtpatientid)
            
            visit_date = datetime.datetime.now().date()  # Use fully qualified datetime
            #objclassifiedID = get_object_or_404(ClassficationsOptions, pk=hdfclassifiedID)
            already_exists  = PatientVisits.objects.filter(
                patientid=patient,
                doctorid=userID,
                visitdate=visit_date
            ).exists()
            
            if already_exists:
                return render(
                request,
                "Duplicated.html",
                {
                    'message': "This patient already has a visit added by you today.",
                    'returnUrl': 'DoctorOp',
                    'btnText': 'Back'
                },
                status=200,
            )

            # Save the patient visit
            data = PatientVisits(
                patientid=patient,
                visittype='D',
                #diagnosis=txtdiagnosis,
                evaluationeegree=EvaulDegree,
                #classifiedID=objclassifiedID,
                visitdate=visit_date,
                doctorid=userID,
                #reasonforvisit=txtRemarks,
                createdate=visit_date,
                discussionNotes=discussion_notes or None,
            )
            if operation_type_id:
                data.operationType_id = operation_type_id
            data.save()

            return redirect(reverse("confirm_page_doctor", kwargs={                   
                    "fileserial": patient.fileserial,
                    #"patientName": patient.fullname
                }))
        
        patientList = ormObj.getPatientsAttendedToday()
        patientcount = patientList.count()

        return render(
            request,
            'doctor/auditPatientVisit.html',
            {
                'patients': patientList,
                'Total': patientcount,
                'classifiedOptionsJSON': classifiedOptionsJSON,
            }
        )