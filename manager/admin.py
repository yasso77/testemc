from django.contrib import admin
from manager.model.doctor import Doctor, Specialties
from manager.model.patient import Patient,City
from manager.models import ClassficationsOptions

# Register your models here.

admin.site.site_header='EMC-Administration'
admin.site.site_title='EMC'
class DoctorAdmin(admin.ModelAdmin):
    list_display=['doctorID','fullName','mobile','specialtyID','active']
    list_display_links=['fullName']   
    search_fields=['fullName','mobile']
# Register your models here.

admin.site.register(Doctor,DoctorAdmin)
admin.site.register(Specialties)

class PatientAdmin(admin.ModelAdmin):
    list_display=['fileserial','fullname','birthdate','gender','mobile','city']
    list_display_links=['fullname']
    list_editable=['mobile']
    search_fields=['fileserial','fullname','mobile']
   # list_filter=['mobile']
    #list_per_page=2
    #fields=['fileserial','fullname','birthdate']
    exclude = ['createddate', 'createdby','latestupdate','updatedby']  # List the fields you want to exclude
   
# Register your models here.
admin.site.register(Patient,PatientAdmin)

class ClassficationsOptionsAdmin(admin.ModelAdmin):
    list_display=['classifiedID','classifiedCategory','optionClassified','isActive','createdDate','createdBy']
    list_display_links=['classifiedID']   
    search_fields=['classifiedCategory','optionClassified']
    exclude = ['createdDate']
    
    # Make 'createdBy' read-only, or you can omit this if you want it to be editable
    readonly_fields = ('createdBy',)

    # Override the save_model method to automatically set 'createdBy' field to the logged-in user
    def save_model(self, request, obj, form, change):
        if not obj.createdBy:  # Only set createdBy if it is not already set
            obj.createdBy = request.user  # Set the logged-in user as createdBy
        obj.save()   
    
admin.site.register(ClassficationsOptions,ClassficationsOptionsAdmin)
admin.site.register(City)
