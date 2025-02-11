from datetime import date,  timedelta
import string
from django.shortcuts import render
from django.urls import reverse
from django.utils.timezone import now, make_aware, is_naive
from django.utils import timezone
from manager.forms.addreservation import MyModelForm

from django.utils.timezone import now
from django.contrib.auth.decorators import login_required,permission_required

from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404, redirect
from django.db.models import Count
from django.db.models import Q
from django.db.models import Count, Max, Subquery, OuterRef
from manager.model.patient import CallTrack, Patient

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
        """View function to add a new reservation."""
        latest_fileserial = CenterView.generateFileSerial()  # Get new reservation code       
        

        if request.method == 'POST':
            # Pass request to the form and specify required fields
            centerform = MyModelForm(
                request=request, data=request.POST, required_fields=['fullname', 'mobile','reservationType','sufferedcaseByPatient','checkUpprice']
            )

            if centerform.is_valid():
                patient = centerform.save(commit=False)
                patient.fileserial = latest_fileserial  # Assign generated file serial
                #patient.reservedBy = request.user  # Assign logged-in user
                patient.createdBy = request.user  # Assign logged-in user
                patient.callDirection=None              
               

                # Ensure createdDate has a value
                if patient.createdDate is None:
                    patient.createdDate = now()  # Assign a timezone-aware datetime
                elif is_naive(patient.createdDate):
                    patient.createdDate = make_aware(patient.createdDate)
                
                if patient.attendancedate is None:
                    patient.attendancedate = now()  # Assign a timezone-aware datetime
                elif is_naive(patient.attendancedate):
                    patient.attendancedate = make_aware(patient.attendancedate)

                patient.save()

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
            centerform = MyModelForm(request=request, initial={'fileserial': latest_fileserial})

        # Render the new reservation form
        
        return render(request, 'center/newReservation.html', {'form': centerform, 'fileserial': latest_fileserial})
    
    def centerReservationByMobile(request,strmobile):
            
            recent_patients = (
            Patient.objects.active()
            .filter(
                
                reservedBy=request.user,
                mobile=strmobile,
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
                'patientid', 'fullname', 'reservationCode', 'leadSource',
                'createdDate', 'city', 'mobile', 'age',
                'sufferedcase__caseName', 'expectedDate', 'gender', 'attendanceDate',
                'call_count', 'last_call_date', 'last_call_outcome'  # Add annotated fields
            )
        )
        
        
        # Pass the data to the template      
        
            return render(request, 'center/reservationsList.html', {'patients': recent_patients,'viewScope':strmobile})
