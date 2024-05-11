from django.contrib import admin

from manager.models import Doctor, Patient, Specialties

# Register your models here.
class DoctorAdmin(admin.ModelAdmin):
    list_display=['DoctorID','FullName','Mobile','SpecialtyID','active']
    list_display_links=['FullName']   
    search_fields=['FullName','Mobile']
# Register your models here.

admin.site.register(Doctor,DoctorAdmin)
admin.site.register(Specialties)

class PatientAdmin(admin.ModelAdmin):
    list_display=['fileserial','fullname','birthdate','gender','mobile','city']
    list_display_links=['fileserial']
    list_editable=['mobile']
    search_fields=['fileserial','fullname','mobile']
   # list_filter=['mobile']
    #list_per_page=2
    #fields=['fileserial','fullname','birthdate']
    exclude = ['createddate', 'createdby','latestupdate','updatedby']  # List the fields you want to exclude
    


# Register your models here.
admin.site.register(Patient,PatientAdmin)
admin.site.site_header='EMC-Administration'
admin.site.site_title='EMC'