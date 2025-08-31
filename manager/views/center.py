from datetime import  date, datetime, time,  timedelta
import datetime
from io import BytesIO
import string

from urllib import request
from django.shortcuts import render
from django.urls import reverse
from django.utils.timezone import now, make_aware, is_naive,localtime
from django.utils import timezone
from django.http import Http404
from manager.forms.CenterEditReservation import CenterEditReservationForm
from manager.forms.centerReservation import CEAddReservationForm
from django.db.models.functions import Coalesce,TruncDate

from django.utils.timezone import now
from django.contrib.auth.decorators import login_required,permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count,Exists, Q
from django.db.models import IntegerField,Max, Subquery, OuterRef,  Case, Value, When, Exists, DateField
from manager.forms.centerFollowUp import centerTrackForm
from manager.model import patient
from manager.model.patient import CallTrack,MedicalConditionData, Patient, PatientMedicalHistory
from django.db import models

from manager.views import barcode

import barcode
from barcode.writer import ImageWriter
from io import BytesIO
import base64
from django.shortcuts import render



class CenterView(ListView):
    
    def generateFileSerial():
        """Generate an incremented file serial in the format 'X-00001'."""
        # Generate a list of uppercase letters (A to Z)
        alphabet = list(string.ascii_uppercase)

        latest_fileserial = (
            Patient.objects.filter(fileserial__isnull=False)
            .order_by('-patientid')
            .first()
        )
        
        

        # Determine incrementing part
        if latest_fileserial and latest_fileserial.fileserial:
            latest_code_parts = latest_fileserial.fileserial.split('-')

            if len(latest_code_parts) == 2:  # Ensure it follows the "X-00001" format
                latest_prefix = latest_code_parts[0]  # Get current letter
                latest_increment = int(latest_code_parts[1])  # Get numeric part

                if latest_increment >= 99999:
                    # Find the next letter in the alphabet
                    if latest_prefix in alphabet:
                        current_index = alphabet.index(latest_prefix)
                        new_prefix = (
                            alphabet[current_index + 1] if current_index < len(alphabet) - 1 else 'A'
                        )
                    else:
                        new_prefix = 'A'  # Default to 'A' if invalid

                    increment = 1  # Reset the numeric part
                else:
                    new_prefix = latest_prefix  # Keep the same prefix
                    increment = latest_increment + 1
            else:
                new_prefix = 'A'  # Default prefix
                increment = 1
        else:
            new_prefix = 'A'  # Start with 'A' if no records exist
            increment = 1

        # Format increment with leading zeros (5 digits)
        increment_part = f"{increment:05d}"
        fileCode = f"{new_prefix}-{increment_part}"

        return fileCode


    @login_required
    def addNewReservation(request):       
                
        latest_fileserial = CenterView.generateFileSerial()  # Get new reservation code       

        if request.method == 'POST':
            # Pass request to the form and specify required fields
            centerform = CEAddReservationForm(request=request, data=request.POST)
            
           
            if centerform.is_valid():
                patient = centerform.save(commit=False)
                # Extract birthdate from form data
                birthdate = centerform.cleaned_data.get('birthdate')

                if birthdate:
                    today = date.today()
                    patient.age = today.year - birthdate.year - (
                        (today.month, today.day) < (birthdate.month, birthdate.day)
                    )
                patient.fileserial = latest_fileserial  # Assign generated file serial
                patient.createdBy = request.user  # Assign logged-in user
                patient.reservedBy = request.user  # Assign logged-in user
                patient.callDirection = None
                patient.leadSource='Center'               
                patient.save()

                # Initialize an empty list to store the conditions and relations
                # Initialize an empty list to store the conditions and relations
                medical_conditions = []

                # Iterate through all items in the POST data (request.POST)
                for condition_name, relation in request.POST.items():
                    if condition_name.startswith('medical_conditions[') and condition_name.endswith(']'):
                        condition_key = condition_name.split('[')[1].split(']')[0]  # Extract condition name

                        if relation in ['self', 'relative']:
                           #print(f"Searching for condition: {condition_key}")

                            # Ensure we fetch a single instance, not a QuerySet
                            condition_obj = MedicalConditionData.objects.filter(conditionName=condition_key).first()

                            if condition_obj:
                               # print(f"Found condition: {condition_obj} (ID: {condition_obj.conditionID})")
                                medical_conditions.append((condition_obj, relation))
                           

                # Ensure we are passing an **instance**, not a string
                for condition_obj, relation in medical_conditions:
                    if isinstance(condition_obj, MedicalConditionData):  # Ensure it's a model instance
                        PatientMedicalHistory.objects.create(
                            patient=patient,
                            condition=condition_obj,  # Must be an instance, NOT a string
                            relation=relation,
                            createdBy=request.user
                        )
                    # else:
                    #     print(f"Skipping invalid condition: {condition_obj}")


                return render(
                    request,
                    "ConfirmMsg.html",
                    {
                        'message': 'The Reservation is Added Successfully.',
                        'returnUrl': 'centerNewreservation',
                        'btnText': 'Add New Reservation',
                        'patientid':patient.patientid
                    },
                    status=200,
                )
            else:
                print(centerform.errors)

        else:
            # Initialize the form with the generated reservation code
            centerform = CEAddReservationForm(request=request, initial={'fileserial': latest_fileserial})

        # Render the new reservation form
        return render(request, 'center/newReservation.html', {'form': centerform, 'fileserial': latest_fileserial})
        
    def dashSearchOnPatient(request):
        return render(request, 'center/SearchOnReservation.html') 
    
    @login_required
    def centerReservations(request, ScopeView):
        
        today_date = datetime.date.today() # Ensures it matches expectedDate format
        #start_of_day = datetime.combine(today_date, datetime.min.time())  # 2025-02-21 00:00:00
        #end_of_day = datetime.combine(today_date, time(23, 59, 59))  # 2025-02-21 23:59:59
        FALLBACK_DATE = datetime.date(1900, 1, 1)

        # Get today's date
        
        # Get the date 90 days ago (starting from yesterday)
        past_90_days_date = today_date - timedelta(days=20)
        # Get the date 3 days from today
        next_3_days = today_date + timedelta(days=3)
            # Determine filtering condition based on scopeView
            # get all patients who should attend today (attendance today - expected date - confirmation date is =today and printform=false)
        if ScopeView == 'Attendance-Today':  
            # ✅ Ensure today_date is a proper date object
            today_date = datetime.date.today() # Ensures it matches expectedDate format
            
            # Get a fallback old date
            FALLBACK_DATE = datetime.date(1900, 1, 1)
            
            # Subquery to check if a patient's confirmation date in CallTrack is today
            confirmed_today = CallTrack.objects.filter(
                patientID=OuterRef('pk'),  # OuterRef links to the Patient model
                confirmationDate=today_date
            ).values('patientID')[:1]  # Ensures the query returns at most one match per patient
            #print(confirmed_today)
            
             # Subquery to fetch the latest confirmationDate for each patient
            reschadule_date = CallTrack.objects.filter(
                patientID=OuterRef('pk'),
                nextFollow=today_date
            ).order_by('-nextFollow').values('nextFollow')[:1]

            recent_patients = Patient.objects.annotate(
                        is_confirmed_today=Case(
                            When(Exists(confirmed_today), then=Value(1)),
                            default=Value(0),
                            output_field=IntegerField()
                        ),
                        reschadule_data=Subquery(reschadule_date, output_field=models.DateField()),
                        has_medical_history=Exists(
                            PatientMedicalHistory.objects.filter(patient=OuterRef('pk'))
                        ),
                        # ✅ Ensure consistent date format for filtering
                        safe_expectedDate=Coalesce("expectedDate", Value(FALLBACK_DATE, output_field=DateField())),  
                        safe_attendanceDate=Coalesce("attendanceDate", Value(FALLBACK_DATE, output_field=DateField()))  
                    ).filter(
                        # ✅ Ensures at least one date is present (excludes records where both are NULL)
                        ~Q(safe_expectedDate=FALLBACK_DATE) | ~Q(safe_attendanceDate=FALLBACK_DATE),

                        # ✅ Include cases where attendanceDate is today even if expectedDate is NULL
                        Q(safe_attendanceDate=today_date) | Q(safe_expectedDate=today_date),
                        isDeleted=False
                    ).distinct()
            
           

        elif ScopeView == 'All-List':
             # ✅ Ensure today_date is a proper date object
                       
            past_90_days_dateXX = today_date - timedelta(days=90)    
          

            recent_patients = Patient.objects.annotate(
                is_confirmed_today=Value('--'),
                reschadule_data=Value('oo'),
                # Ensure consistent date format for filtering
                safe_expectedDate=Coalesce("expectedDate", Value(FALLBACK_DATE, output_field=DateField())),  
                safe_attendanceDate=Coalesce("attendanceDate", Value(FALLBACK_DATE, output_field=DateField()))  
            ).filter(
                createdDate__gte=past_90_days_dateXX,
                isDeleted=False
            ).distinct()
              
            # get all patients who should who their follow update is today or 3 days in future
        elif ScopeView=='Follow-Up':
            # expected-confirmation-followup will comeafter 3 days from now
            # Query CallTrack for non-canceled outcomes with next follow-up date today or in the next 3 days
           # Get latest confirmation date for each patient
            latest_confirmation_date = CallTrack.objects.filter(
                patientID=OuterRef('pk'),
                confirmationDate__range=[today_date, next_3_days]
            ).order_by('-confirmationDate').values('confirmationDate')[:1]
            
            # Subquery to fetch the latest confirmationDate for each patient
            reschadule_date = CallTrack.objects.filter(
                patientID=OuterRef('pk'),
                nextFollow=today_date
            ).order_by('-nextFollow').values('nextFollow')[:1]

            # Check if a patient has an upcoming follow-up (excluding 'Canceled' outcomes)
            # Subquery to check if a patient has a valid upcoming follow-up within the range
                       
          # Subquery to check if a patient has a valid upcoming follow-up within the range
                        
            # Subquery to check if a patient has a valid upcoming follow-up within the range
            valid_upcoming_followups = CallTrack.objects.filter(
                patientID=OuterRef('pk'),  
                  # Exclude 'Canceled' outcomes
                nextFollow__range=[today_date, next_3_days]  
            )

            # Correct usage of Exists() inside a filter query
            patients_in_calltrack = Patient.objects.filter(
                Exists(valid_upcoming_followups)  # ✅ Pass only the QuerySet inside Exists()
            )

            # Query to fetch recent patients
            # Query to fetch recent patients
            recent_patientsx = Patient.objects.filter(
                Q(expectedDate__range=[today_date, next_3_days]),
                isDeleted=False,
                formPrinted=False
            ).distinct()
            
            # Merge both queries using OR condition
            # Merge both queries
            recent_patients = Patient.objects.filter(
                Q(pk__in=patients_in_calltrack.values('pk')) |  
                Q(pk__in=recent_patientsx.values('pk'))  
            ).annotate(
                reschadule_data=Subquery(reschadule_date, output_field=models.DateField()),
                        has_medical_history=Exists(
                            PatientMedicalHistory.objects.filter(patient=OuterRef('pk'))
                        ),
                latestConfirmation=Subquery(latest_confirmation_date, output_field=DateField())  # ✅ Apply annotation after merging
            )
            

            
            
            
        elif ScopeView=='Missed-Reservations':
            missed_past_90_days = CallTrack.objects.filter(
            patientID=OuterRef('pk'),  # OuterRef links to the Patient model
            confirmationDate__gte=past_90_days_date
        ).values('patientID')[:1]  # Ensures the query returns at most one match per patient
            
            # Subquery to fetch the latest confirmationDate for each patient
            latest_confirmation_date = CallTrack.objects.filter(
                patientID=OuterRef('pk'),
                confirmationDate__gte=past_90_days_date
            ).order_by('-confirmationDate').values('confirmationDate')[:1]
            
            # Subquery to fetch the latest confirmationDate for each patient
            reschadule_date = CallTrack.objects.filter(
                patientID=OuterRef('pk'),
                nextFollow=today_date
            ).order_by('-nextFollow').values('nextFollow')[:1]

            # Main query to get patients expected in the past 90 days or confirmed in the same range
            recent_patients = Patient.objects.annotate(
                reschadule_data=Subquery(reschadule_date, output_field=models.DateField()),
                        has_medical_history=Exists(
                            PatientMedicalHistory.objects.filter(patient=OuterRef('pk'))
                        ),
                latestConfirmation=Subquery(latest_confirmation_date, output_field=models.DateField())
            ).filter(
                Q(expectedDate__gte=past_90_days_date) | Q(Exists(missed_past_90_days)),
                isDeleted=False,
                formPrinted=False
            ).distinct()
            
            
                
        recent_patients = (                
        recent_patients.select_related('sufferedcase')
        .annotate(
            call_count=Count('call_patients', filter=Q(call_patients__trackType='CE')),  
            nxtFollow_date=Max('call_patients__nextFollow', filter=Q(call_patients__trackType='CE')),
            last_call_date=Max('call_patients__createdDate', filter=Q(call_patients__trackType='CE')),
            last_call_outcome=Subquery(
                CallTrack.objects.filter(
                    patientID=OuterRef('pk'),  # Reference the current patient
                    trackType='CE'
                )
                .order_by('-createdDate')
                .values('outcome')[:1]  # Get the outcome of the latest call
            ),
            has_medical_history=Exists(
            PatientMedicalHistory.objects.filter(patient=OuterRef('pk'))
        ))
        .order_by('-createdDate')
        .values(
            'patientid','fileserial', 'fullname', 'reservationCode', 'leadSource',
            'createdDate', 'city', 'mobile', 'sufferedcase__caseName',
            'sufferedcaseByPatient__caseName', 'expectedDate', 'gender', 'attendanceDate','birthdate','checkUpprice__checkupPriceName',
            'call_count', 'last_call_date', 'last_call_outcome','has_medical_history','reschadule_data'  # Add annotated fields
        )
    )
        
            
            # Pass the data to the template      
       
        return render(request, 'center/reservationsList.html', {'patients': recent_patients,'viewScope':ScopeView})
       
    def generate_barcode(code):
        # Get the barcode class (Code128 is a widely used barcode format)
        barcode_format = barcode.get_barcode_class('code128')
        
        # Generate barcode
        barcode_instance = barcode_format(code, writer=ImageWriter())

        # Save the barcode image to an in-memory buffer
        buffer = BytesIO()
        barcode_instance.write(buffer)

        # Convert the image buffer to a base64 string
        barcode_data = base64.b64encode(buffer.getvalue()).decode()

        # Pass barcode data to the template
        return  barcode_data
     
    @login_required       
    def patientForm(request, patientid):
        CONDITIONS_LIST = MedicalConditionData.objects.active()
        patientData = get_object_or_404(Patient, patientid=patientid)
        medical_history = PatientMedicalHistory.objects.filter(patient=patientData)
        patientData.formPrinted = True
        patientData.save()
        
        # Convert queryset to dictionary with condition names as keys
        history_dict = {entry.condition.conditionName: entry.relation for entry in medical_history}

        # Debugging:
        #print(f"Medical History: {history_dict}")  
         # Generate barcode based on patient's file serial number
        barcode_data = CenterView.generate_barcode(patientData.fileserial)

        return render(request, 'center/patientForm.html',  {
            'patientData': patientData,
            'medical_history': history_dict,  # Dictionary now uses condition names as keys
            'conditions_list': CONDITIONS_LIST,  # Pass list from view
            'barcode_data': barcode_data  # Pass barcode data to template
        })


    @login_required
    def centerReservationByMobile(request,strmobile):
        
            today_date = datetime.date.today()
        
            past_90_days_date = today_date - timedelta(days=90)
            
            # Subquery to fetch the latest confirmationDate for each patient
            latest_confirmation_date = CallTrack.objects.filter(
                patientID=OuterRef('pk'),
                confirmationDate__gte=past_90_days_date
            ).order_by('-confirmationDate').values('confirmationDate')[:1]
            
            recent_patients = (
            Patient.objects.active()
            .filter(
                
                #reservedBy=request.user,
                mobile=strmobile,
                #isDeleted=False
            )
            .select_related('sufferedcase')
            .annotate(
                call_count=Count('call_patients', filter=Q(call_patients__trackType='CE')),  
                last_call_date=Max('call_patients__createdDate', filter=Q(call_patients__trackType='CE')),
                latestConfirmation=Subquery(latest_confirmation_date, output_field=models.DateField()),
                last_call_outcome=Subquery(
                    CallTrack.objects.filter(
                        patientID=OuterRef('pk'),  # Reference the current patient
                        trackType='CE'
                    )
                    .order_by('-createdDate')
                    .values('outcome')[:1]  # Get the outcome of the latest call
                )
            )
            .order_by('-createdDate')
            .values(
                'patientid','fileserial', 'fullname', 'reservationCode', 'leadSource',
                'createdDate', 'city', 'mobile', 'age','sufferedcase__caseName','latestConfirmation',
                'sufferedcaseByPatient__caseName', 'expectedDate', 'gender', 'attendanceDate','birthdate',
                'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
            )
        )
        
        
        # Pass the data to the template      
        
            return render(request, 'center/reservationsList.html', {'patients': recent_patients,'viewScope':strmobile})
    
    @login_required   
    def centerSearchOnPatient(request):
         
        strText = request.GET.get('strText', '')  
        
        today_date = datetime.date.today()        
        past_90_days_date = today_date - timedelta(days=90)
        
        # Subquery to fetch the latest confirmationDate for each patient
        latest_confirmation_date = CallTrack.objects.filter(
            patientID=OuterRef('pk'),
            confirmationDate__gte=past_90_days_date
        ).order_by('-confirmationDate').values('confirmationDate')[:1]
    #print(strText) 
        recent_patients = (
            Patient.objects.active()
            .filter(
                Q(reservationCode__icontains=strText) |
                Q(mobile__icontains=strText) |  # Search in mobile
                Q(fileserial__icontains=strText) |  # Search in file serial
                Q(fullname__icontains=strText) |  # Search in name
                Q(birthdate__icontains=strText) |  # Search in birthdate
                Q(attendanceDate__icontains=strText),  # Search in attendance date
                reservedBy=request.user  # Keep the reservedBy filter
            )
            .select_related('sufferedcase')
            .annotate(
                latestConfirmation=Subquery(latest_confirmation_date, output_field=models.DateField()),
                call_count=Count('call_patients'),  # Count number of call tracks for each patient
                last_call_date=Max('call_patients__createdDate'),  # Get the latest call date
                last_call_outcome=Subquery(
                    CallTrack.objects.filter(
                        patientID=OuterRef('pk')  # Reference the current patient
                    )
                    .order_by('-createdDate')
                    .values('outcome')[:1]  # Get the outcome of the latest call
                ),
                 has_medical_history=Exists(
                 PatientMedicalHistory.objects.filter(patient=OuterRef('pk'))
            )  # ✅ Check if patient has a medical history
            )
            .values(
                'patientid', 'fullname', 'reservationCode', 'leadSource',
                'createdDate', 'city', 'mobile', 'age', 'sufferedcase__caseName',
                'sufferedcaseByPatient__caseName', 'expectedDate', 'gender', 'attendanceDate', 'birthdate',
                'call_count', 'last_call_date', 'last_call_outcome','has_medical_history','latestConfirmation'  # Add annotated fields
            )
        )  
        
        return render(request, 'center/reservationsList.html', {'patients': recent_patients,'viewScope':strText})
    
    @login_required
    def follow_reservation(request, patientid):
        # Fetch the patient instance or return 404 if not found
        patient = get_object_or_404(Patient, patientid=patientid)
        calltracks=CallTrack.objects.filter(patientID=patientid).order_by('-createdDate')
        if request.method == 'POST':
            # Bind form data to the existing patient instance
            form = centerTrackForm(request.POST)
            if form.is_valid():
                # Save form but do not commit to the database yet
                calltrack = form.save(commit=False)
                
                # Assign additional fields
                calltrack.patientID = patient
                calltrack.createdBy = request.user
                calltrack.agentID = request.user
                calltrack.trackType='CE'
                
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
            form = centerTrackForm(instance=patient)
        
        # Render the edit page with the form and patient data
        return render(request, 'center/followup.html', {'form': form, 'patient': patient,'calltracks':calltracks})
    
    @login_required
    def edit_reservation(request, patientid,scope):
               
        patient = get_object_or_404(Patient, patientid=patientid)  
          
        latest_fileserial = None  # Initialize variable
        if patient.fileserial is None or patient.fileserial == "":
                       
           latest_fileserial = CenterView.generateFileSerial()
        else:
            latest_fileserial=patient.fileserial  
                   

        if request.method == 'POST':
            form = CenterEditReservationForm(request.POST, instance=patient)
            # Extract birthdate from form data
            
            if form.is_valid():
                birthdate = form.cleaned_data.get('birthdate')
                if birthdate:
                    today = date.today()
                    patient.age = today.year - birthdate.year - (
                        (today.month, today.day) < (birthdate.month, birthdate.day)
                    )
                patient.fileserial=latest_fileserial
                patient = form.save()
            else:
                print(form.errors)

                # Clear existing medical history before saving new ones
            PatientMedicalHistory.objects.filter(patient=patient).delete()

            # Loop through medical conditions and save the new selections
            for condition in MedicalConditionData.objects.active():
                choice = request.POST.get(f"medical_conditions_{condition}")  # ✅ Works!

                
                if choice:  # If a selection is made (Self/Relative)
                    PatientMedicalHistory.objects.create(
                        patient=patient,
                        condition=condition,
                        relation=choice,
                        createdBy=request.user  # Assuming user is logged in
                    )

            #return redirect(reverse('centerPatients', args=[scope]))
            returnUrl = reverse('centerPatients', args=['Attendance-Today'])  # Generate URL dynamically
            return render(
                    request,
                    "ConfirmMsg.html",
                    {
                        'message': 'The Reservation is updated Successfully.',
                        'returnUrl': returnUrl,
                        'btnText': 'Return to List',
                        'patientid':patient.patientid
                    },
                    status=200,
                )

        else:
            form = CenterEditReservationForm(instance=patient)

        # Fetch existing medical history for this patient
         # Fetch existing medical history for this patient
        history_dict = CenterView.getPatientMedicalCases(patient)
        CONDITIONS_LIST=MedicalConditionData.objects.active()
        
        if not history_dict:
            history_dict = {"": ""}   

        return render(request, 'center/editReservation.html', {
            'form': form,
            'patient': patient,
            'fileserial': latest_fileserial,            
            'medical_history': history_dict,  # Pass history_dict to template
            'conditions_list': CONDITIONS_LIST  # Pass CONDITIONS_LIST to template
        })
   
      
    def getPatientMedicalCases(PatientObj):        
                
        medical_history = PatientMedicalHistory.objects.filter(patient=PatientObj)      
        
        # Convert to dictionary for easy lookup
        history_dict = {entry.condition: entry.relation for entry in medical_history}
        
        return history_dict
    
   
    def countMissedLeads():
        today_date = datetime.date.today()
       
        past_90_days_date = today_date - timedelta(days=90)
        
        missed_past_90_days = CallTrack.objects.filter(
            patientID=OuterRef('pk'),  # OuterRef links to the Patient model
            confirmationDate__gte=past_90_days_date
        ).values('patientID')[:1]  # Ensures the query returns at most one match per patient
            
            # Subquery to fetch the latest confirmationDate for each patient
        latest_confirmation_date = CallTrack.objects.filter(
                patientID=OuterRef('pk'),
                confirmationDate__gte=past_90_days_date
            ).order_by('-confirmationDate').values('confirmationDate')[:1]

            # Main query to get patients expected in the past 90 days or confirmed in the same range
        recent_patients = Patient.objects.annotate(
                latestConfirmation=Subquery(latest_confirmation_date, output_field=models.DateField())
            ).filter(
                Q(expectedDate__gte=past_90_days_date) | Q(Exists(missed_past_90_days)),
                isDeleted=False,
                formPrinted=False
            ).distinct()
            
        return recent_patients.count()
    
    
    def countFollowUp():
        
        today_date = datetime.date.today()
        next_3_days = today_date + timedelta(days=3)
        latest_confirmation_date = CallTrack.objects.filter(
            patientID=OuterRef('pk'),
            confirmationDate__range=[today_date, next_3_days]
        ).order_by('-confirmationDate').values('confirmationDate')[:1]

        
        valid_upcoming_followups = CallTrack.objects.filter(
            patientID=OuterRef('pk'),  
                # Exclude 'Canceled' outcomes
            nextFollow__range=[today_date, next_3_days]  
        )

        # Correct usage of Exists() inside a filter query
        patients_in_calltrack = Patient.objects.filter(
            Exists(valid_upcoming_followups)  # ✅ Pass only the QuerySet inside Exists()
        )

        
        recent_patientsx = Patient.objects.filter(
            Q(expectedDate__range=[today_date, next_3_days]),
            isDeleted=False,
            formPrinted=False
        ).distinct()
        
        
        recent_patients = Patient.objects.filter(
            Q(pk__in=patients_in_calltrack.values('pk')) |  
            Q(pk__in=recent_patientsx.values('pk'))  
        ).annotate(
            latestConfirmation=Subquery(latest_confirmation_date, output_field=DateField())  # ✅ Apply annotation after merging
        )
        
        return recent_patients.count()
     
       
    def countAttendToday():
            
        today_date = datetime.date.today() # Ensures it matches expectedDate format
        
        # Get a fallback old date
        FALLBACK_DATE = datetime.date(1900, 1, 1)
        
        # Subquery to check if a patient's confirmation date in CallTrack is today
        confirmed_today = CallTrack.objects.filter(
            patientID=OuterRef('pk'),  # OuterRef links to the Patient model
            confirmationDate=today_date
        ).values('patientID')[:1]  # Ensures the query returns at most one match per patient
        #print(confirmed_today)
        
            # Subquery to fetch the latest confirmationDate for each patient
        latest_confirmation_date = CallTrack.objects.filter(
            patientID=OuterRef('pk'),
            confirmationDate=today_date
        ).order_by('-confirmationDate').values('confirmationDate')[:1]

        recent_patients = Patient.objects.annotate(
                    is_confirmed_today=Case(
                        When(Exists(confirmed_today), then=Value(1)),
                        default=Value(0),
                        output_field=IntegerField()
                    ),
                    latestConfirmation=Subquery(latest_confirmation_date, output_field=models.DateField()),
                    has_medical_history=Exists(
                        PatientMedicalHistory.objects.filter(patient=OuterRef('pk'))
                    ),
                    # ✅ Ensure consistent date format for filtering
                    safe_expectedDate=Coalesce("expectedDate", Value(FALLBACK_DATE, output_field=DateField())),  
                    safe_attendanceDate=Coalesce("attendanceDate", Value(FALLBACK_DATE, output_field=DateField()))  
                ).filter(
                    # ✅ Ensures at least one date is present (excludes records where both are NULL)
                    ~Q(safe_expectedDate=FALLBACK_DATE) | ~Q(safe_attendanceDate=FALLBACK_DATE),

                    # ✅ Include cases where attendanceDate is today even if expectedDate is NULL
                    Q(safe_attendanceDate=today_date) | Q(safe_expectedDate=today_date),
                    isDeleted=False
                ).distinct()
                
        return recent_patients.count()
    
    @login_required       
    def getPatinetTrackData(request):
        
        strText = request.GET.get('strText', '')  
        recent_patients = (
            Patient.objects.active()
            .filter(
                Q(reservationCode__icontains=strText) |
                Q(mobile__icontains=strText) |  # Search in mobile
                Q(fullname__icontains=strText) |  # Search in name
                Q(birthdate__icontains=strText) |  # Search in birthdate
                Q(attendanceDate__icontains=strText),  # Search in attendance date
                reservedBy=request.user  # Keep the reservedBy filter
            )            
            .annotate(               
                call_count=Count('call_patients'),  # Count number of call tracks for each patient
                last_call_date=Max('call_patients__createdDate'),  # Get the latest call date
                last_call_outcome=Subquery(
                    CallTrack.objects.filter(
                        patientID=OuterRef('pk')  # Reference the current patient
                    )
                    .order_by('-createdDate')
                    .values('outcome')[:1]  # Get the outcome of the latest call
                ),
                 has_medical_history=Exists(
                 PatientMedicalHistory.objects.filter(patient=OuterRef('pk'))
            )  # ✅ Check if patient has a medical history
            )
            .values(
                'patientid', 'fullname', 'reservationCode', 'leadSource',
                'createdDate', 'city', 'mobile', 'age', 'sufferedcase__caseName',
                'sufferedcaseByPatient__caseName', 'expectedDate', 'gender', 'attendanceDate', 'birthdate',
                'call_count', 'last_call_date', 'last_call_outcome','has_medical_history','latestConfirmation'  # Add annotated fields
            )
        )  
        
        return render(request, 'center/reservationsList.html', {'patients': recent_patients,'viewScope':strText})
        
      
