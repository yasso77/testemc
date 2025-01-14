# forms.py
from datetime import date, datetime
from django import forms

from manager.model.patient import Patient


class MyModelForm(forms.ModelForm):   
    
    
    class Meta:
        model = Patient
        fields = ['fileserial','fullname', 'mobile', 'city','age','gender','sufferedcase','reservedBy','remarks','expectedDate']
        
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.Select(attrs={'class': 'form-control'}),
            'age': forms.TextInput(attrs={'class': 'form-control'}),
            'sufferedcase': forms.TextInput(attrs={'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
            'fileserial': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'reservedBy': forms.TextInput(attrs={'class': 'form-control'}),
            'expectedDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),  # Correct type attribute
             
    
        }
        error_messages = {
            'fileserial': {
                'required': 'File serial is required.',
            },
            'fullname': {
                'required': 'Full name is required.',
            },
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
            }
          }
        
    def __init__(self, *args, **kwargs):
        super(MyModelForm, self).__init__(*args, **kwargs)
        self.fields['expectedDate'].initial = date.today()
        # Set choices for gender field explicitly to avoid null value
        self.fields['gender'].choices = [
            ('M', 'Male'),
            ('F', 'Female')
        ]
        
        
    def clean_fileserial(self):
        fileserial = self.cleaned_data.get('fileserial')
        if Patient.objects.filter(fileserial=fileserial).exists():
            raise forms.ValidationError('A patient with this file serial already exists.')
        return fileserial
    
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if Patient.objects.filter(mobile=mobile).exists():
            raise forms.ValidationError('A patient with this mobile number already exists.')
        return mobile