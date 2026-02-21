# forms.py
from datetime import date, datetime
from django import forms
import re
from django.core.exceptions import ValidationError
from django.db.models import Q
from manager.model.patient import AgentCompany, CheckUpPrice, City, Offers, Patient, SufferedCases


class CallCenterEditReservationForm(forms.ModelForm):   
    
    slotNumber = forms.ChoiceField(
    choices=[],
    required=False,
    widget=forms.Select(attrs={'class': 'form-select'})
)
    city = forms.ModelChoiceField(queryset=City.objects.active(), required=True, label="City", widget=forms.Select(attrs={'class': 'form-select'}))
    sufferedcase= forms.ModelChoiceField(queryset=SufferedCases.objects.active(), required=True, label="Suffered Case", widget=forms.Select(attrs={'class': 'form-select'}))
    offerID= forms.ModelChoiceField(queryset=Offers.objects.active(),required=False,  label="Offers", widget=forms.Select(attrs={'class': 'form-select'}))
    agentID= forms.ModelChoiceField(queryset=AgentCompany.objects.active(),required=False,  label="Agent/Company", widget=forms.Select(attrs={'class': 'form-select'}))
    checkUpprice= forms.ModelChoiceField(queryset=CheckUpPrice.objects.active(),required=False,  label="Check-Up price", widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = Patient
        exclude = ['createdDate', 'createdby']  # Exclude non-editable fields
        fields = [ 'reservationCode', 'city','age','gender','mobile','sufferedcase','leadSource','remarks','offerID','callDirection','fullname','checkUpprice','agentID','organizationID','expectedDate','slotNumber']
        
        widgets = {
            #'reservationCode': forms.HiddenInput(),  # Make this field hidden
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),          
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),      
            'callDirection': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'age': forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,  # Minimum age
            'max': 99,  # Maximum age (restricts to two digits)
            
                }),
            
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),          
            'organizationID': forms.Select(attrs={'class': 'form-select'}),
            'leadSource': forms.Select(attrs={'class': 'form-select'}),            
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'reservedBy': forms.TextInput(attrs={'class': 'form-control'}),
            'expectedDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),  # Correct type attribute
           
             
    
        }
        error_messages = {
            'fullname': {
                'required': 'Full name is required.',
            },
           
          
            'city': {
                'required': 'City is required.',
            },
            'age': {
                'required': 'Age is required.',
            },
            'gender': {
                'required': 'Gender is required.',
            },
            'sufferedcase': {
                'required': 'Suffered case is required.',
            },
                       
            
          } 
                
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if not (1 <= age <= 99):
            raise forms.ValidationError('Age must be a number between 1 and 99.')
        return age
    
          
        
    def __init__(self, *args, existing_serial=False, **kwargs):
        self.request = kwargs.pop('request', None)   # ⭐ ADD THIS
        super().__init__(*args, **kwargs)
        self.fields['gender'].choices = [
            choice for choice in self.fields['gender'].choices if choice[0] != ''
        ]

        if existing_serial:
            self.fields["organizationID"].disabled = True
            self.fields["organizationID"].widget.attrs["disabled"] = "disabled"
            
          # Dynamic Slot Dropdown A-1 A-2 A-3
        # -----------------------------
        self.fields['slotNumber'].choices = [('', 'Select')]

        if self.request:
            extra = getattr(self.request.user, 'extra', None)

            if extra and extra.character and extra.tiny_number:

                char = extra.character.upper()
                max_num = extra.tiny_number

                self.fields['slotNumber'].choices += [
                    (f"{char}-{i}", f"{char}-{i}")
                    for i in range(1, max_num + 1)
                ]
