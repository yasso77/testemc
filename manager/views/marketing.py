from django.shortcuts import render
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.views.generic.list import ListView
from manager.model.patient import CheckUpPrice, City, Patient, SufferedCases
from django.utils.timezone import now
from django.contrib.auth.models import User

class MarketingView(ListView):

    def marketing_dashboard(request):
        # Get data for the last 30 days
        thirty_days_ago = timezone.now() - timedelta(days=30)
        patients = Patient.objects.filter(createdDate__gte=thirty_days_ago, isDeleted=False)
        
        # 1️⃣ Lead Source Distribution
        lead_sources = patients.values('leadSource').annotate(count=Count('patientid'))
        lead_source_labels = [entry['leadSource'] or 'Unknown' for entry in lead_sources]
        lead_source_counts = [entry['count'] for entry in lead_sources]
        
        

        # 2️⃣ Suffered Cases Distribution
        suffered_casesx = patients.values('sufferedcase_id').annotate(count=Count('patientid'))
       
        suffered_case = SufferedCases.objects.values('sufferedcaseID', 'caseName')
        
        suffered_case_labels = [str(entry['caseName']) for entry in suffered_case] 
        suffered_case_counts = [entry['count'] for entry in suffered_casesx]

        # 3️⃣ Check-Up Price Distribution
        checkup_pricesx = patients.values('checkUpprice_id').annotate(count=Count('patientid'))
        checkup_prices = CheckUpPrice.objects.values('checkupPriceID', 'checkupPriceName')
        checkup_price_labels = [str(entry['checkupPriceName']) for entry in checkup_prices]
        checkup_price_counts = [entry['count'] for entry in checkup_pricesx]

        # 4️⃣ Age & Gender Distribution
        male_counts = [entry['count'] for entry in patients.filter(gender='M').values('age').annotate(count=Count('patientid'))]
        female_counts = [entry['count'] for entry in patients.filter(gender='F').values('age').annotate(count=Count('patientid'))]
        age_labels = [str(entry['age']) for entry in patients.values('age').annotate(count=Count('patientid'))]

        # 5️⃣ New reservations added by call center agent
        # Aggregate count of patients grouped by reservedBy_id
        # Count patients grouped by reservedBy_id
        reservedBy_counts = patients.values('reservedBy_id').annotate(count=Count('patientid'))

        # Extract reservedBy_id values
        reserved_by_ids = [entry['reservedBy_id'] for entry in reservedBy_counts]

        # Debugging: Print reservedBy_id values
        #print("Reserved By IDs:", reserved_by_ids)

        # Fetch call center user data
        callcenter = User.objects.filter(id__in=reserved_by_ids).values('id', 'username')

        # Debugging: Print retrieved user data
        #print("Call Center Users:", list(callcenter))

        # Create a mapping of user IDs to usernames
        user_mapping = {entry['id']: entry['username'] for entry in callcenter}

        # Debugging: Print user mapping
        print("User Mapping:", user_mapping)

        # Prepare labels and counts
        callcenter_labels = [user_mapping.get(int(entry['reservedBy_id']), "Unknown") for entry in reservedBy_counts]
        reservations_counts = [entry['count'] for entry in reservedBy_counts]

        # Debugging: Print final output
        #print("Final Labels:", callcenter_labels)
        #print("Final Counts:", reservations_counts)

        context = {
            'lead_source_labels': lead_source_labels,
            'lead_source_counts': lead_source_counts,
            'suffered_case_labels': suffered_case_labels,
            'suffered_case_counts': suffered_case_counts,
            'checkup_price_labels': checkup_price_labels,
            'checkup_price_counts': checkup_price_counts,
            'age_labels': age_labels,
            'male_counts': male_counts,
            'female_counts': female_counts,
            'callcenter_labels': callcenter_labels,
            'reservations_counts': reservations_counts,
        }

        return context
    
    
    def get_patient_statistics_past_30_days():
        
        thirty_days_ago = timezone.now() - timedelta(days=30)

        # 1. Patients reserved by the user in the past 30 days
        reserved_by_user_count = Patient.objects.filter(          
            createdDate__gte=thirty_days_ago,
            isDeleted=False
        ).count()

        # 2. Patients who confirmed their dates in the past 30 days & their confirmation date is greater than today
        
        today = now().date()

        confirmed_patients_count = Patient.objects.filter(
            
            createdDate__gte=thirty_days_ago,
            attendanceDate__isnull=True,
            isDeleted=False,
            call_patients__outcome="Confirmed",  # Outcome is "Confirmed"
            call_patients__confirmationDate__gt=today          # Add condition: confirmationDate > today
            #call_patients__createdBy=user
        ).distinct().count()

        # 3. Patients whose expected or confirmation date is today in the past 30 days
        expected_or_confirmed_today_count = Patient.objects.filter(
           
            createdDate__gte=thirty_days_ago,
            isDeleted=False,
            expectedDate=today            
               ).count()

        # 4. Patients who missed their expected or confirmation date in the past 30 days
        missed_patients_count = Patient.objects.filter(                  
            createdDate__gte=thirty_days_ago,
            attendanceDate__isnull=True,
            fileserial__isnull=True,
            isDeleted=False,
            expectedDate__lt=today).count()
        
         # 5. Patients who atteneded in the past 30 days
        attended_patients_count= Patient.objects.filter(            
            fileserial__isnull=False,            
            createdDate__gte=thirty_days_ago,
            attendanceDate__isnull=False,
            isDeleted=False
        ).count()

        # Returning the statistics
        states= {
            "reserved_count": reserved_by_user_count,
            "confirmed_patients_count": confirmed_patients_count,
            "expected_today_count": expected_or_confirmed_today_count,
            "missed_patients_count": missed_patients_count,
            "attended_patients_count": attended_patients_count,
            'date_range': {
            'start': thirty_days_ago,
            'end': today,
        }
        }
        
        return states
        
