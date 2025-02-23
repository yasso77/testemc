from django.urls import include, path
from manager.views.center import CenterView
from manager.views.doctor import DoctorView
from manager.views.patient import PatientView
from manager.views.main import MainView
from manager.views.report import ReportView
from manager.views.callcenter import CallCenterView
from django.views.generic import TemplateView
from django.contrib.auth.views import PasswordResetView, PasswordResetDoneView, PasswordResetConfirmView, PasswordResetCompleteView

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
   
    path('UpdatePatientData', PatientView.UpdatePatientData, name='update_patient_data'),
    
    path('edit_patient/<int:patientid>/', PatientView.edit_patient, name='edit_patient'),
   
    path('check_fileserial/', PatientView.check_fileserial, name='check_fileserial'),
    
    
    #Center
    path('centerNewreservation', CenterView.addNewReservation, name='centerNewreservation'),
    path('centerReservationByMobile/<str:strmobile>/', CenterView.centerReservationByMobile, name='centerReservationByMobile'),
    path('centerPatients/<str:ScopeView>/', CenterView.centerReservations, name='centerPatients'),
    path('centerSearchOnPatinet/',CenterView.centerSearchOnPatient,name='centerSearchOnPatinet'),
    path('followup/<int:patientid>/', CenterView.follow_reservation, name='followup'),
    path('patientForm/<int:patientid>/', CenterView.patientForm, name='patientForm'),
    path('centeredit_reservation/<int:patientid>/', CenterView.edit_reservation, name='centeredit_reservation'),
    

    # CallCenterView
    path('newreservation', CallCenterView.addNewPatient, name='newreservation'),
    path('reservationList', CallCenterView.reservationsList, name='reservationList'),
    path('reservationListScope/<str:viewScope>/', CallCenterView.reservationsListviewScope, name='reservationListScope'),
    path('reservationListMobile/<str:strmobile>/', CallCenterView.reservationsListviewMobile, name='reservationListMobile'),
    path('edit_reservation/<int:patientid>/', CallCenterView.edit_reservation, name='edit_reservation'),
    path('follow_reservation/<int:patientid>/', CallCenterView.follow_reservation, name='follow_reservation'),
    path('delete_patient/<int:patientid>/', CallCenterView.delete_patient, name='delete_patient'),
    path('check_reservationCode/', CallCenterView.check_reservationCode, name='check_reservationCode'),
    path('reservation-data/', CallCenterView.get_reservation_data, name='reservation_data'),
    path('validate-mobile/', CallCenterView.validate_mobile, name='validate_mobile'),
    path('callCentersearchOnPatinet/',CenterView.centerSearchOnPatient,name='callCentersearchOnPatinet'),
    

    # DoctorView
    path('DoctorEvaluation', DoctorView.doctorPatientvisit, name='DoctorEvaluation'),
    path('AuditEvaluation', DoctorView.auditPatientvisit, name='AuditEvaluation'),

    # Authentication
    path('accounts/', include('django.contrib.auth.urls')),
    # Password reset views
    path('password-reset/', PasswordResetView.as_view(template_name='registration/changepassword.html'), name='password_reset'),
    path('password-reset/done/', PasswordResetDoneView.as_view(template_name='registration/password_reset_done.html'), name='password_reset_done'),
    path('reset/<uidb64>/<token>/', PasswordResetConfirmView.as_view(template_name='registration/password_reset_confirm.html'), name='password_reset_confirm'),
    path('reset/done/', PasswordResetCompleteView.as_view(template_name='registration/password_reset_complete.html'), name='password_reset_complete'),
]
