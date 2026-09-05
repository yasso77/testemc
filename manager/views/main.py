from django.db.models import Q
from django.contrib.auth import logout, authenticate, login, update_session_auth_hash
from django.contrib.auth.views import LoginView
from django.shortcuts import redirect, render
from django.urls import reverse
from manager.forms.forms import LoginForm, EmcAuthenticationForm, ForcedPasswordChangeForm
from manager.model.userExtra import UserExtra

import pandas as pd

from django.core.serializers.json import DjangoJSONEncoder
from manager.decorators import permission_required_with_redirect
from manager.forms.UploadForm import ExcelUploadForm

from django.contrib.auth.decorators import login_required,permission_required
from manager.model.patient import CallTrack, Patient
from manager.orm import ORMPatientsHandling
from django.shortcuts import get_object_or_404
from django.views.generic.list import ListView
from manager.views.callcenter import CallCenterView
from manager.views.center import CenterView
from manager.views.doctor import DoctorView
from manager.views.marketing import MarketingView
from django.db.models import Count
from django.db.models import Q
from django.db.models import Count, Max, Subquery, OuterRef

# Create your views here.

class MainView(ListView):
    
    @login_required
    def dashboard(request):
        
        # if request.user.groups.filter(name="admin").exists():
            
        #      return render(request, 'centerx/dashboard.html', {'context': 'cc'})
        
        if request.user.groups.filter(name="Reception").exists():
            
            
            #  missedCount=CenterView.countMissedLeads()
            #  followupCount=CenterView.countFollowUp()
            #  attendToday=CenterView.countAttendToday()
             
             return render(request, 'center/SearchOnReservation.html')
           
        
        elif request.user.groups.filter(name="Marketing").exists():
             context = MarketingView.marketing_dashboard(request)  # ✅ Pass request, not request.user
             stats=MarketingView.get_patient_statistics_past_30_days()
             return render(request, 'dashboards/center.html', {'context': context,'stats':stats})

        elif request.user.groups.filter(name="Call center").exists():
            stats = CallCenterView.get_patient_statistics_past_30_days(request)  # ✅ Pass request, not request.user
            return render(request, 'dashboards/callCenter.html', {'stats': stats})       
        
       
        elif request.user.groups.filter(name="Doctors").exists() or request.user.groups.filter(name="DoctorAudit").exists():

            stats = DoctorView.get_evaluation_degree_count(request.user.id)  # ✅ Pass request, not request.user
            return render(request, 'dashboards/doctor.html', {'stats': stats})

        elif request.user.groups.filter(name="Discussion Group").exists():
            return redirect('DiscussionDashboard')
        else:
            return render(request,'index.html',{'name':'index'})
        
        
 
    def no_permission_view(request):
        return render(request, 'no_permission.html')


   

    @login_required
    
    def uploadpatientData(request):
        if request.method == 'POST':
                form = ExcelUploadForm(request.POST, request.FILES)      
                excel_file = request.FILES['my_file']
                df = pd.read_excel(excel_file)
                added_count = 0
                updated_count = 0

                
                for index, row in df.iterrows():
                    # Check if the mobile number already exists in the database
                    mobile_number = row['Mobile']
                    existing_patient = Patient.objects.filter(mobile=mobile_number).first()

                    if existing_patient:
                        # If a patient with the same mobile number exists, update the existing record
                        existing_patient.fullname = row['Name']
                        existing_patient.age = row['Age']
                        existing_patient.sufferedcase = row['Case']
                        existing_patient.city = row['City']
                        existing_patient.reservedBy = row['ReservedBy']
                        existing_patient.arrivedOn = row['ArrivedOn']
                        existing_patient.remarks = row['Remarks']
                        existing_patient.expectedDate = row['ArrivalDate']
                        existing_patient.save()
                        updated_count += 1
                    else:
                        # If no patient with the same mobile number exists, create a new record
                        Patient.objects.create(
                            fullname=row['Name'],
                            mobile=row['Mobile'],
                            age=row['Age'],
                            sufferedcase=row['Case'],
                            city=row['City'],
                            reservedBy=row['ReservedBy'],
                            arrivedOn=row['ArrivedOn'],
                            remarks=row['Remarks'],
                            expectedDate=row['ArrivalDate']
                            # Map other columns accordingly
                        ) 
                        added_count += 1               
                message = f'Patient data uploaded successfully.<br>{added_count} patients were added.<br>{updated_count} patients were updated.'
                
                
                return render(request,"ConfirmMsg.html",{'message': message,'returnUrl':'upload','btnText':'Upload New File'}, status=200)
    
        return render(request, 'uploadPatientData.html', {'form': 'form'})
    
    def ConfirmMsg(request):
     return render(request,'ConfirmMsg.html',{'Msg':request.POST.get('msg')})
 
    def custom_logout_view(request):
        logout(request)
        return redirect('/custom-logout-page/')

    @login_required
    def forced_password_change(request):
        extra, _ = UserExtra.objects.get_or_create(
            user=request.user,
            defaults={'must_change_password': True},
        )
        if not extra.must_change_password or not request.session.get('password_change_pending'):
            return redirect('index')

        if request.method == 'POST':
            form = ForcedPasswordChangeForm(user=request.user, data=request.POST)
            if form.is_valid():
                form.save()
                extra.must_change_password = False
                extra.save(update_fields=['must_change_password'])
                request.session.pop('password_change_pending', None)
                update_session_auth_hash(request, request.user)
                return redirect('index')
        else:
            form = ForcedPasswordChangeForm(user=request.user)

        return render(request, 'registration/force_password_change.html', {
            'form': form,
        })


class EmcLoginView(LoginView):
    template_name = 'registration/login.html'
    authentication_form = EmcAuthenticationForm
    redirect_authenticated_user = False

    def form_valid(self, form):
        remember_me = form.cleaned_data.get('remember_me')
        response = super().form_valid(form)
        if remember_me:
            self.request.session.set_expiry(60 * 60 * 24 * 14)
        else:
            self.request.session.set_expiry(0)
        extra, _ = UserExtra.objects.get_or_create(
            user=self.request.user,
            defaults={'must_change_password': True},
        )
        if extra.must_change_password:
            self.request.session['password_change_pending'] = True
            return redirect('password_change_forced')
        self.request.session.pop('password_change_pending', None)
        return response
