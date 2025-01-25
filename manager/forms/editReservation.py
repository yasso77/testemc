# forms.py
from datetime import date, datetime
from django import forms
import re
from django.core.exceptions import ValidationError
from django.db.models import Q
from manager.model.patient import City, Offers, Patient, SufferedCases


class editReservationForm(forms.ModelForm):   
    
    city = forms.ModelChoiceField(queryset=City.objects.active(), required=True, label="City", widget=forms.Select(attrs={'class': 'form-select'}))
    sufferedcase= forms.ModelChoiceField(queryset=SufferedCases.objects.active(), required=True, label="Suffered Case", widget=forms.Select(attrs={'class': 'form-select'}))
    offerID= forms.ModelChoiceField(queryset=Offers.objects.active(),required=False,  label="Offers", widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = Patient
        exclude = ['createdDate', 'createdby','fullName']  # Exclude non-editable fields
        fields = [ 'reservationCode','mobile', 'city','age','gender','sufferedcase','leadSource','remarks','confirmationDate','offerID','callDirection']
        
        widgets = {
            #'reservationCode': forms.HiddenInput(),  # Make this field hidden
            #'fullname': forms.TextInput(attrs={'class': 'form-control'}),           
            'mobile': forms.TextInput(attrs={'class': 'form-control' }),           
            'callDirection': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'age': forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,  # Minimum age
            'max': 99,  # Maximum age (restricts to two digits)
            
                }),
            
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
            'fileserial': forms.TextInput(attrs={'class': 'form-control'}),
           
            'leadSource': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'reservedBy': forms.TextInput(attrs={'class': 'form-control'}),
            'expectedDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),  # Correct type attribute
            'confirmationDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),  # Correct type attribute
             
    
        }
        error_messages = {
           
            'mobile': {
                'required': 'Mobile number is required.',
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
            'confirmationDate': {
                'required': 'Confirmation Date is required.',
            }           
            
          } 
        
    # def clean_mobile(self):
    #     mobileNum = self.cleaned_data.get('mobile')
    #     reservCode = self.cleaned_data.get('reservationCode')
    #     print(reservCode)       

    #     # Check for duplicate mobile with a different reservation code
    #     if Patient.objects.filter(mobile=mobileNum).exclude(reservationCode=reservCode).exists():
    #         raise forms.ValidationError('A patient with this Mobile Number already exists.')

    #     return mobileNum
    
    def clean_confirmationDate(self):
        confirmation_date = self.cleaned_data.get('confirmationDate')
        if confirmation_date and confirmation_date < date.today():
            raise forms.ValidationError("Confirmation Date Date cannot be earlier than today.")
        return confirmation_date

        
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if not (1 <= age <= 99):
            raise forms.ValidationError('Age must be a number between 1 and 99.')
        return age
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the empty choice for gender field
        self.fields['gender'].choices = [
            choice for choice in self.fields['gender'].choices if choice[0] != ''
        ]
