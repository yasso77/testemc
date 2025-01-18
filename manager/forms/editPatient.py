# forms.py
from datetime import date, datetime
from django import forms
import re
from django.core.exceptions import ValidationError

from manager.model.patient import Patient


class editPatientForm(forms.ModelForm):   
    
    
    class Meta:
        model = Patient
        exclude = ['reservationCode','confirmationDate', 'createdDate', 'createdby',]  # Exclude non-editable fields
        fields = [ 'fullname','wearingconduct','rideglass','fileserial', 'age','gender','sufferedcase','remarks','attendanceDate']
        
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'fileserial': forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'abc-12345'  # Guide user to input correct format
            }),
            
            'age': forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,  # Minimum age
            'max': 99,  # Maximum age (restricts to two digits)
            'placeholder': 'Enter age',
                }),
            'sufferedcase': forms.TextInput(attrs={'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}), 
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),  
            'wearingconduct': forms.RadioSelect(attrs={'class': 'form-check-input'}),    
            'rideglass':forms.RadioSelect(attrs={'class': 'form-check-input'}), 
            'attendanceDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),  # Correct type attribute
             
    
        }
        error_messages = {
            'fileserial': {
                'required': 'File number is required.',
            },
           
            'mobile': {
                'required': 'Mobile number is required.',
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
            'attendanceDate': {
                'required': 'Attendance Date is required.',
            }           
            
          }       
    
        
        
    # def clean_fileserial(self):
    #     fileserial = self.cleaned_data.get('fileserial')
    #     if Patient.objects.filter(fileserial=fileserial).exists():
    #         raise forms.ValidationError('A patient with this file serial already exists.')
    #     return fileserial
    
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
