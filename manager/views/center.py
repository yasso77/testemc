from datetime import date,  timedelta
import string
from urllib import request
from django.shortcuts import render
from django.urls import reverse
from django.utils.timezone import now, make_aware, is_naive
from django.utils import timezone
from manager.forms.centerReservation import CEAddReservationForm

from django.utils.timezone import now
from django.contrib.auth.decorators import login_required,permission_required
from django.core.exceptions import ObjectDoesNotExist
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from django.db.models import Q
from django.db.models import Count, Max, Subquery, OuterRef
from manager.forms.centerFollowUp import centerTrackForm
from manager.model import patient
from manager.model.patient import CallTrack, MedicalCondition, Patient, PatientMedicalHistory

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
                patient.fileserial = latest_fileserial  # Assign generated file serial
                patient.createdBy = request.user  # Assign logged-in user
                patient.reservedBy = request.user  # Assign logged-in user
                patient.callDirection = None              

                # Ensure createdDate has a value
                if patient.createdDate is None:
                    patient.createdDate = now()  # Assign a timezone-aware datetime
                elif is_naive(patient.createdDate):
                    patient.createdDate = make_aware(patient.createdDate)

                if patient.attendanceDate is None:
                    patient.attendanceDate = now()  # Assign a timezone-aware datetime
                elif is_naive(patient.attendanceDate):
                    patient.attendanceDate = make_aware(patient.attendanceDate)

                patient.save()

                # Initialize an empty list to store the conditions and relations
                # Initialize an empty list to store the conditions and relations
                medical_conditions = []
                
                # Iterate through all items in the POST data (request.POST)
                for condition_name, relation in request.POST.items():
                    # Only process the keys that start with 'medical_conditions'
                    if condition_name.startswith('medical_conditions'):
                        condition_key = condition_name.split('[')[1].split(']')[0]  # Extract the disease name from the key
                        
                        # Check if the value is either 'self' or 'relative'
                        if relation in ['self', 'relative']:
                            try:
                                # Try to get the MedicalCondition object
                                condition_obj = MedicalCondition.objects.get(conditionName=condition_key)
                            except ObjectDoesNotExist:
                                # Handle the case where the condition doesn't exist in the database
                                print(f"Condition '{condition_key}' does not exist in the database.")
                                continue  # Skip to the next condition
                            
                            # Append the condition and relation as a tuple
                            medical_conditions.append((condition_obj, relation))

                # Now save the PatientMedicalHistory records
                for condition_obj, relation in medical_conditions:
                    PatientMedicalHistory.objects.create(
                        patient=patient,
                        condition=condition_obj,
                        relation=relation,
                        createdBy=request.user
                    )

                # Return confirmation message
                return render(
                    request,
                    "ConfirmMsg.html",
                    {
                        'message': 'The Reservation is Added Successfully.',
                        'returnUrl': 'newreservation',
                        'btnText': 'Add New Reservation',
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
        
    
    def centerReservationToday(request):
            
            recent_patients = (
            Patient.objects.active()
            .filter(  
                #mobile=strmobile,
                #isDeleted=False
            )
            .select_related('sufferedcase')
            .annotate(
                call_count=Count('call_patients', filter=Q(call_patients__trackType='CE')),  
                last_call_date=Max('call_patients__createdDate', filter=Q(call_patients__trackType='CE')),
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
                'createdDate', 'city', 'mobile', 'sufferedcase__caseName',
                'sufferedcaseByPatient__caseName', 'expectedDate', 'gender', 'attendanceDate','birthdate',
                'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
            )
        )
        
        
        # Pass the data to the template      
        
            return render(request, 'center/reservationsList.html', {'patients': recent_patients})
        
        
        
    def centerReservationByMobile(request,strmobile):
            
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
                'createdDate', 'city', 'mobile', 'age','sufferedcase__caseName',
                'sufferedcaseByPatient__caseName', 'expectedDate', 'gender', 'attendanceDate','birthdate',
                'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
            )
        )
        
        
        # Pass the data to the template      
        
            return render(request, 'center/reservationsList.html', {'patients': recent_patients,'viewScope':strmobile})
        
    def centerSearchOnPatient(request):
         
        strText = request.GET.get('strText', '')  
        print(strText) 
        recent_patients = (
            Patient.objects.active()
            .filter(
                Q(mobile__icontains=strText) |  # Search in mobile
                Q(fullname__icontains=strText) |  # Search in name
                Q(birthdate__icontains=strText) |  # Search in birthdate
                Q(attendanceDate__icontains=strText),  # Search in attendance date
                reservedBy=request.user  # Keep the reservedBy filter
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
                'patientid', 'fullname', 'reservationCode', 'leadSource',
                'createdDate', 'city', 'mobile', 'age', 'sufferedcase__caseName',
                'sufferedcaseByPatient__caseName', 'expectedDate', 'gender', 'attendanceDate', 'birthdate',
                'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
            )
        )
        
        
        # Pass the data to the template      
        
        return render(request, 'center/reservationsList.html', {'patients': recent_patients,'viewScope':strText})
    
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
