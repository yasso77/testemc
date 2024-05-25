from django.urls import include, path
from .import views
from django.views.generic import TemplateView

urlpatterns=[
    path('', views.index,name='index'), 
    path('upload', views.uploadpatientData,name='pushpatientData'),
    path('showPatientData', views.showPatientData,name='showPatientData'),
    path('searchPatient', views.get_patientData,name='searchP') ,     
    path('getattendedpatient', views.showPatientDataAttendedToday,name='getattendedpatient') , 
    path('no-permission/', views.no_permission_view, name='no_permission'),
    path('PatientsList', views.uploadedPatientDataList,name='PatientsList') , 
    path('UpdatePatientData', views.UpdatePatientData, name='update_patient_data'),

    path('DoctorEvaluation', views.doctorPatientvisit,name='DoctorEvaluation'),   
    path('report',views.ajaxReportChartEvlDegree,name='LiveEvulationReport'),

    #path('AddVisit',views.addPatientVisit,name='SubmitVisit'),
    path('Message',views.ConfirmMsg,name='MessageAlert'),

    path('reportview',views.LiveDegreeReport,name='reportview'),   

    path('patientForm/<int:patientid>/',views.patientForm,name='patientForm'),    

    path('addnewpatient', views.addNewPatient, name='addnewpatient'),
    
    path('logout/', views.custom_logout_view, name='logoutx'),
    path('custom-logout-page/', TemplateView.as_view(template_name='logout.html'), name='custom-logout-page'),
    path('login/', views.login_view, name='loginView'),
    path('accounts/', include('django.contrib.auth.urls')),

]