from django.urls import include, path
from manager.views.doctor import DoctorView
from manager.views.paitent import PatientView
from manager.views.main import MainView
from manager.views.report import ReportView
from django.views.generic import TemplateView

urlpatterns=[
    path('', MainView.index,name='index'), 
    path('upload', MainView.uploadpatientData,name='pushpatientData'),
    path('showPatientData', ReportView.showPatientData,name='showPatientData'),
    path('searchPatient', PatientView.get_patientData,name='searchP') ,     
    path('getattendedpatient', ReportView.showPatientDataAttendedToday,name='getattendedpatient') , 
    path('no-permission/', MainView.no_permission_view, name='no_permission'),
    path('PatientsList', ReportView.uploadedPatientDataList,name='PatientsList') , 
    path('UpdatePatientData', PatientView.UpdatePatientData, name='update_patient_data'),

    path('DoctorEvaluation', DoctorView.doctorPatientvisit,name='DoctorEvaluation'),   
    path('report',ReportView.ajaxReportChartEvlDegree,name='LiveEvulationReport'),

    #path('AddVisit',views.addPatientVisit,name='SubmitVisit'),
    path('Message',MainView.ConfirmMsg,name='MessageAlert'),

    path('reportview',ReportView.LiveDegreeReport,name='reportview'),   

    path('patientForm/<int:patientid>/',PatientView.patientForm,name='patientForm'),    

    path('addnewpatient', PatientView.addNewPatient, name='addnewpatient'),
    
    path('logout/', MainView.custom_logout_view, name='logoutx'),
    path('custom-logout-page/', TemplateView.as_view(template_name='logout.html'), name='custom-logout-page'),
    path('login/', MainView.login_view, name='loginView'),
    path('accounts/', include('django.contrib.auth.urls')),
    path('check_fileserial/', PatientView.check_fileserial, name='check_fileserial'),

]