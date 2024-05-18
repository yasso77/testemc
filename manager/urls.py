from django.urls import path
from .import views

urlpatterns=[
    path('', views.index,name='index'), 
    path('upload', views.uploadpatientData,name='pushpatientData'),
    path('showPatientData', views.showPatientData,name='showPatientData'),
    path('searchPatient', views.get_patientData,name='index') ,     
    path('getattendedpatient', views.showPatientDataAttendedToday,name='getattendedpatient') , 
    
    path('UploadedList', views.uploadedPatientDataList,name='UploadedList') , 
    path('UpdatePatientData', views.UpdatePatientData, name='update_patient_data'),

    path('DoctorEvaluation', views.doctorPatientvisit,name='DoctorEvaluation'),   
    path('report',views.ajaxReportChartEvlDegree,name='LiveEvulationReport'),

    #path('AddVisit',views.addPatientVisit,name='SubmitVisit'),
    path('Message',views.ConfirmMsg,name='MessageAlert'),

    path('reportview',views.LiveDegreeReport,name='reportview'),   

    path('patientForm/<int:patientid>/',views.patientForm,name='patientForm'),    

    path('addnewpatient', views.my_model_form_view, name='addnewpatient'),

]