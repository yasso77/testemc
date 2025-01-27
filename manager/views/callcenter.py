from datetime import date, datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from manager.decorators import permission_required_with_redirect
from django.contrib.auth.models import User

from manager.forms.addFollowUp import insertCallTrackForm
from manager.forms.editReservation import editReservationForm

from django.contrib.auth.decorators import login_required,permission_required

from manager.model.patient import CallTrack, Patient
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from django.db.models import Q


class CallCenterView(ListView):
    
    @login_required
   
    def reservationsList(request):
       # Get the current date
        today = date.today()
        
        # Calculate the date 10 days ago
        ten_days_ago = today - timedelta(days=30)
        
        # Filter the Patient records created within the previous 10 days by a specific user (createdby)
        # assuming `request.user` is the logged-in user
        is_admin = request.user.groups.filter(name='Admin').exists()
        #print(is_admin)
        recent_patients = (
        Patient.objects.active()
         .filter(
        Q(createdDate__gte=ten_days_ago) &
        (Q(reservedBy=request.user) | Q() if not is_admin else Q())
        )
        .select_related('sufferedcase')
        .values(
            'patientid', 'fullname', 'reservationCode', 'leadSource',
            'createdDate', 'city', 'mobile', 'age',
            'sufferedcase__caseName', 'expectedDate',
            'gender', 'attendanceDate'
        )
    )
        
        return render(request, 'callcenter/reservationsList.html', {'patients': recent_patients})
        
        
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
                .values(
                    'patientid', 'fullname', 'reservationCode', 'leadSource',
                    'createdDate', 'city', 'mobile', 'age',
                    'sufferedcase__caseName', 'expectedDate',
                    'gender', 'attendanceDate'
                )
            )
        elif viewScope=='missed':
                recent_patients = (
                Patient.objects.active()
                .filter(
                    createdDate__gte=thirty_days_ago,  # Patients created within the last 30 days
                    reservedBy=request.user,          # Filter by the currently logged-in user
                    attendanceDate__isnull=True,      # Patients who have not attended yet
                    isDeleted=False,                  # Exclude deleted patients
                   
                ).filter(
                    Q(expectedDate__lt=today) #| Q(confirmationDate__lt=today)  # Correct usage of Q object with OR logic
                )
                .select_related('sufferedcase')       # Optimize related model queries
                .values(
                    'patientid', 'fullname', 'reservationCode', 'leadSource',
                    'createdDate', 'city', 'mobile', 'age',
                    'sufferedcase__caseName', 'expectedDate',
                    'gender', 'attendanceDate'
                )
            )
                
        elif viewScope=='confirmed':
                recent_patients = (
                Patient.objects.active()
                .filter(
                    reservedBy=request.user,
                    #confirmationDate__gt=today,
                    createdDate__gte=thirty_days_ago,
                    attendanceDate__isnull=True,
                    isDeleted=False                # Exclude deleted patients
                   
                ).select_related('sufferedcase')       # Optimize related model queries
                .values(
                    'patientid', 'fullname', 'reservationCode', 'leadSource',
                    'createdDate', 'city', 'mobile', 'age',
                    'sufferedcase__caseName', 'expectedDate',
                    'gender', 'attendanceDate'
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
                .values(
                    'patientid', 'fullname', 'reservationCode', 'leadSource',
                    'createdDate', 'city', 'mobile', 'age',
                    'sufferedcase__caseName', 'expectedDate',
                    'gender', 'attendanceDate'
                )
            )
    
    
    def reservationsListviewMobile(request,strmobile):
            
            recent_patients = (
            Patient.objects.active()
            .filter(
                
                reservedBy=request.user,
                mobile=strmobile,
                #isDeleted=False
            )
            .select_related('sufferedcase')
            .values(
                'patientid', 'fullname', 'reservationCode', 'leadSource',
                'createdDate', 'city', 'mobile', 'age',
                'sufferedcase__caseName', 'expectedDate',
                'gender', 'attendanceDate'
            )
        )
        
        
        # Pass the data to the template      
        
            return render(request, 'callcenter/reservationsList.html', {'patients': recent_patients,'viewScope':strmobile})
       
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
    
    def edit_reservation(request, patientid):
        # Fetch the patient instance or return 404 if not found
        patient = get_object_or_404(Patient, patientid=patientid)
        
        if request.method == 'POST':
            # Bind form data to the existing patient instance
            form = editReservationForm(request.POST, instance=patient)
            if form.is_valid():
                form.save()  # Save the updated instance
                return redirect('reservationList')  # Redirect to the reservation list page
            else:
                print(form.errors)
        else:
            # Display the form pre-filled with patient data
            form = editReservationForm(instance=patient)
        
        # Render the edit page with the form and patient data
        return render(request, 'callcenter/editReservation.html', {'form': form, 'patient': patient})

    
    def delete_patient(request, patientid):
        patient = get_object_or_404(Patient, patientid=patientid)
        if request.method == 'POST':
            # Perform a soft delete by setting isDeleted to True
            patient.isDeleted = True
            patient.save()
            return redirect('reservationList')  # Redirect to the list view
        #return render(request, 'patients/confirm_delete.html', {'patient': patient})
    

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
                
                # Save the instance to the database
                calltrack.save()
                
               
               
                # Return confirmation message
                return render(
                    request,
                    "ConfirmMsg.html",
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
    
    def get_patient_statistics_past_30_days(user):
        today = date.today()
        thirty_days_ago = today - timedelta(days=30)

        # 1. Patients reserved by the user in the past 30 days
        reserved_by_user_count = Patient.objects.filter(
            reservedBy=user,
            createdDate__gte=thirty_days_ago,
            isDeleted=False
        ).count()

        # 2. Patients who confirmed their dates in the past 30 days & their confirmation date is greater than today
        confirmed_patients_count = Patient.objects.filter(
            reservedBy=user,
            #confirmationDate__gt=today,
            createdDate__gte=thirty_days_ago,
            attendanceDate__isnull=True,
            isDeleted=False
        ).count()

        # 3. Patients whose expected or confirmation date is today in the past 30 days
        expected_or_confirmed_today_count = Patient.objects.filter(
            reservedBy=user,
            createdDate__gte=thirty_days_ago,
            isDeleted=False
                ).filter(
                    Q(expectedDate=today) #| Q(confirmationDate=today)  # Either condition can be true
                ).count()

        # 4. Patients who missed their expected or confirmation date in the past 30 days
        missed_patients_count = Patient.objects.filter(
            reservedBy=user,            
            createdDate__gte=thirty_days_ago,
            attendanceDate__isnull=True,
            isDeleted=False
                ).filter(
                    Q(expectedDate__lt=today) #| Q(confirmationDate__lt=today)  # Either condition can be true
                ).count()
        
         # 5. Patients who atteneded in the past 30 days
        attended_patients_count= Patient.objects.filter(
            reservedBy=user,
            
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
        # Dates for the last 7 days
        today = datetime.today()
        last_30_days = [today - timedelta(days=i) for i in range(30)]
        last_30_days.reverse()  # Keep it in chronological order

        # Dates for the same period last month
        last_month = [date - timedelta(days=30) for date in last_30_days]

        # Fetch data for the last 7 days
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
            current_count = next((item['count'] for item in last_30_days_data if item['createdDate'] == date.date()), 0)
            last_month_count = next((item['count'] for item in last_month_data if item['createdDate'] == last_month[i].date()), 0)

            data.append({
                'date': date_str,
                'currentCount': current_count,
                'lastMonthCount': last_month_count,
            })

        return JsonResponse({'reservationsData': data})
    
    def validate_mobile(request):
        mobile = request.GET.get('mobile', None)
        if mobile:
            if Patient.objects.filter(mobile=mobile).exists():
                return JsonResponse({'exists': True, 'message': 'A patient with this Mobile Number already exists.'})
        return JsonResponse({'exists': False})

