from django.urls import include, path
from manager.views.doctor import DoctorView
from manager.views.patient import PatientView
from manager.views.main import MainView
from manager.views.report import ReportView
from manager.views.callcenter import CallCenterView
from django.views.generic import TemplateView

urlpatterns = [
    # MainView
    path('', MainView.dashboard, name='index'),
    path('upload', MainView.uploadpatientData, name='pushpatientData'),
    path('no-permission/', MainView.no_permission_view, name='no_permission'),
    path('Message', MainView.ConfirmMsg, name='MessageAlert'),
    path('logout/', MainView.custom_logout_view, name='logoutx'),
    path('custom-logout-page/', TemplateView.as_view(template_name='logout.html'), name='custom-logout-page'),
    path('login/', MainView.login_view, name='loginView'),
    
    # ReportView
    path('showPatientData', ReportView.showPatientData, name='showPatientData'),
    path('getattendedpatient', ReportView.showPatientDataAttendedToday, name='getattendedpatient'),
    path('PatientsList', ReportView.uploadedPatientDataList, name='PatientsList'),
    path('reportview', ReportView.LiveDegreeReport, name='reportview'),
    path('report', ReportView.ajaxReportChartEvlDegree, name='LiveEvulationReport'),

    # PatientView
    path('searchPatient', PatientView.get_patientData, name='searchP'),
    path('centerPatients', PatientView.patientsList, name='centerPatients'),
    path('UpdatePatientData', PatientView.UpdatePatientData, name='update_patient_data'),
    path('patientForm/<int:patientid>/', PatientView.patientForm, name='patientForm'),
    path('edit_patient/<int:patientid>/', PatientView.edit_patient, name='edit_patient'),
    path('newreservation', PatientView.addNewPatient, name='newreservation'),
    path('check_fileserial/', PatientView.check_fileserial, name='check_fileserial'),

    # CallCenterView
    path('reservationList', CallCenterView.reservationsList, name='reservationList'),
    path('edit_reservation/<int:patientid>/', CallCenterView.edit_reservation, name='edit_reservation'),
    path('delete_patient/<int:patientid>/', CallCenterView.delete_patient, name='delete_patient'),
    path('check_reservationCode/', CallCenterView.check_reservationCode, name='check_reservationCode'),

    # DoctorView
    path('DoctorEvaluation', DoctorView.doctorPatientvisit, name='DoctorEvaluation'),

    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
]
