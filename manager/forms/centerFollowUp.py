# forms.py
from datetime import date
from django import forms
from manager.model.patient import CallTrack, City, Offers, Patient, SufferedCases
from django.contrib import messages




class centerTrackForm(forms.ModelForm):   
    
    # Explicitly define city field outside Meta
    
    class Meta:
        model = CallTrack
       
        fields = ['patientID', 'remarks','outcome','createdBy','createdDate']
        
        widgets = {
            'remarks': forms.TextInput(attrs={'class': 'form-control'}), 
            
            'outcome': forms.RadioSelect(attrs={'class': 'form-check-input'}), 
            
            'createdDate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                
            })
            
             
    
        }
        error_messages = {
            'remarks': {
                 'required': 'remarks is required.',
             },
            'outcome': {
                'required': 'Outcome is required.',
            },
           
          }
        
    def __init__(self, *args, **kwargs):
        # Extract 'request' before calling the parent constructor
        self.request = kwargs.pop('request', None)
        
        # Call the parent constructor
        super().__init__(*args, **kwargs)
        
        # Initialize field values
        self.fields['createdDate'].initial = '' 
        # Explicitly set choices for the gender field to avoid null values
        self.fields['outcome'].choices = [
            ('Re-examination','Re-examination'),
            ('Eye surgery','Eye surgery'),
        ]        
        
    
    
    
    
    
    
    
