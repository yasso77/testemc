from django.contrib import admin
from manager.model.doctor import Doctor, Specialties
from manager.model.patient import AgentCompany, CheckUpPrice, MedicalConditionData, Offers, Patient,City, SufferedCases
from manager.models import ClassficationsOptions

# Register your models here.

admin.site.site_header='EMC-Administration'
admin.site.site_title='EMC'
class DoctorAdmin(admin.ModelAdmin):
    list_display=['doctorID','fullName','mobile','active']
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
    exclude = ['createddate', 'createdBy','latestupdate','updatedby']  # List the fields you want to exclude
    def save_model(self, request, obj, form, change):
        if not obj.createdBy:  # Only set createdBy if it is not already set
            obj.createdBy = request.user  # Set the logged-in user as createdBy
        obj.save()  
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

class CityAdmin(admin.ModelAdmin):
    list_display=['cityID','cityName','isVisible','createdDate']
    list_display_links=['cityName']   
    search_fields=['cityName','isVisible']
   # list_filter=['mobile']
    #list_per_page=2
    #fields=['fileserial','fullname','birthdate']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'isVisible':
            # Replace the BooleanField widget with a RadioSelect showing Yes/No
            kwargs['widget'] = admin.widgets.AdminRadioSelect(
                choices=[(True, 'Yes'), (False, 'No')]
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)
# Register your models here.

admin.site.register(City,CityAdmin)


class SufferedCasesAdmin(admin.ModelAdmin):
    list_display=['sufferedcaseID','caseName','isVisible','createdDate']
    list_display_links=['caseName']   
    search_fields=['caseName','isVisible']
   # list_filter=['mobile']
    #list_per_page=2
    #fields=['fileserial','fullname','birthdate']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'isVisible':
            # Replace the BooleanField widget with a RadioSelect showing Yes/No
            kwargs['widget'] = admin.widgets.AdminRadioSelect(
                choices=[(True, 'Yes'), (False, 'No')]
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)
# Register your models here.

admin.site.register(SufferedCases,SufferedCasesAdmin)

class OffersAdmin(admin.ModelAdmin):
    list_display=['offerID','offerName','isVisible','validFromDate','validToDate','createdDate']
    list_display_links=['offerName']   
    search_fields=['offerName','isVisible']
   # list_filter=['mobile']
    #list_per_page=2
    #fields=['fileserial','fullname','birthdate']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'isVisible':
            # Replace the BooleanField widget with a RadioSelect showing Yes/No
            kwargs['widget'] = admin.widgets.AdminRadioSelect(
                choices=[(True, 'Yes'), (False, 'No')]
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)
# Register your models here.

admin.site.register(Offers,OffersAdmin)


class CheckUpPriceAdmin(admin.ModelAdmin):
    list_display=['checkupPriceID','checkupPriceName','isVisible','createdDate']
    list_display_links=['checkupPriceName']   
    search_fields=['checkupPriceName','isVisible']
   # list_filter=['mobile']
    #list_per_page=2
    #fields=['fileserial','fullname','birthdate']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'isVisible':
            # Replace the BooleanField widget with a RadioSelect showing Yes/No
            kwargs['widget'] = admin.widgets.AdminRadioSelect(
                choices=[(True, 'Yes'), (False, 'No')]
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)
# Register your models here.

admin.site.register(CheckUpPrice,CheckUpPriceAdmin)

class AgentCompanyAdmin(admin.ModelAdmin):
    
    list_display=['agentID','AgentCompany','isVisible','createdDate']
    list_display_links=['AgentCompany']   
    search_fields=['AgentCompany','isVisible']
   # list_filter=['mobile']
    #list_per_page=2
    #fields=['fileserial','fullname','birthdate']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'isVisible':
            # Replace the BooleanField widget with a RadioSelect showing Yes/No
            kwargs['widget'] = admin.widgets.AdminRadioSelect(
                choices=[(True, 'Yes'), (False, 'No')]
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)
# Register your models here.
admin.site.register(AgentCompany,AgentCompanyAdmin)

class MedicalConditionDataAdmin(admin.ModelAdmin):
    
    list_display=['conditionID','conditionName','isVisible','createdDate']
    list_display_links=['conditionName']   
    search_fields=['conditionName','isVisible']
   # list_filter=['mobile']
    #list_per_page=2
    #fields=['fileserial','fullname','birthdate']

    def formfield_for_dbfield(self, db_field, request, **kwargs):
        if db_field.name == 'isVisible':
            # Replace the BooleanField widget with a RadioSelect showing Yes/No
            kwargs['widget'] = admin.widgets.AdminRadioSelect(
                choices=[(True, 'Yes'), (False, 'No')]
            )
        return super().formfield_for_dbfield(db_field, request, **kwargs)
# Register your models here.
admin.site.register(MedicalConditionData,MedicalConditionDataAdmin)
    


