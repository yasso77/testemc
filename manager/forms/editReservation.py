# forms.py
from datetime import date, datetime
from django import forms
import re
from django.core.exceptions import ValidationError

from manager.model.patient import Patient


class editReservationForm(forms.ModelForm):   
    
    
    class Meta:
        model = Patient
        exclude = ['reservationCode', 'createdDate', 'createdby','fullName']  # Exclude non-editable fields
        fields = [ 'mobile', 'city','age','gender','sufferedcase','leadSource','remarks','confirmationDate']
        
        widgets = {
            #'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.NumberInput(attrs={
            'class': 'form-control',
            'placeholder': '7xx1234567'  # Guide user to input correct format
            }),
            'city': forms.Select(attrs={
            'class': 'form-select',
            'placeholder': 'Select a city'  # Guide user to input correct format
            }),
            
            'age': forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,  # Minimum age
            'max': 99,  # Maximum age (restricts to two digits)
            'placeholder': 'Enter age',
                }),
            'sufferedcase': forms.TextInput(attrs={'class': 'form-control'}),
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
    
        
        
    def clean_fileserial(self):
        fileserial = self.cleaned_data.get('fileserial')
        if Patient.objects.filter(fileserial=fileserial).exists():
            raise forms.ValidationError('A patient with this file serial already exists.')
        return fileserial
    
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')        
        # Regex pattern to match 7xx1234567
        pattern = r'^7\d{2}\d{3}\d{4}$'
        if not re.match(pattern, mobile):
            raise ValidationError('Mobile number must be in the format 7xx1234567.')
        
        return mobile
    
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
