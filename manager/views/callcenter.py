from datetime import date, datetime, timedelta
from django.http import JsonResponse
from django.shortcuts import render
from django.urls import reverse
from manager.decorators import permission_required_with_redirect
from django.contrib.auth.models import User
from manager.forms.editReservation import editReservationForm

from django.contrib.auth.decorators import login_required,permission_required

from manager.model.patient import Patient
from django.views.generic.list import ListView
from django.shortcuts import get_object_or_404, redirect


class CallCenterView(ListView):
    
    @login_required
    @permission_required_with_redirect('manager.AddNewPatient', login_url='/no-permission/')
    def reservationsList(request):
       # Get the current date
        today = date.today()
        
        # Calculate the date 10 days ago
        ten_days_ago = today - timedelta(days=20)
        
        # Filter the Patient records created within the previous 10 days by a specific user (createdby)
        # assuming `request.user` is the logged-in user
        recent_patients = Patient.objects.active().filter(
        createdDate__gte=ten_days_ago,
        reservedBy=request.user
        ).values(
            'patientid','fullname', 'reservationCode', 'leadSource','createdDate','city','mobile','age','sufferedcase','expectedDate','gender','attendanceDate')  # Select only the required fields
        
        # Pass the data to the template      
        
        return render(request, 'callcenter/reservationsList.html', {'patients': recent_patients})
       
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