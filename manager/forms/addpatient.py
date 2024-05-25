# forms.py
from django import forms
from manager.models import Patient

class MyModelForm(forms.ModelForm):   
    
    
    class Meta:
        model = Patient
        fields = ['fileserial','fullname', 'mobile', 'city','age','gender','sufferedcase','reservedBy','remarks']
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'city': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.TextInput(attrs={'class': 'form-control'}),
            'sufferedcase': forms.TextInput(attrs={'class': 'form-control'}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
            'fileserial': forms.TextInput(attrs={'class': 'form-control'}),
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'reservedBy': forms.TextInput(attrs={'class': 'form-control'}),
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
   