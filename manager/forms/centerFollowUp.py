# forms.py
from datetime import date,timedelta
from django import forms
from manager.model.patient import CallTrack, City, Offers, Patient, SufferedCases
from django.contrib import messages




class centerTrackForm(forms.ModelForm):   
    
    # Explicitly define city field outside Meta
    
    class Meta:
        model = CallTrack
       
        fields = ['patientID', 'remarks','outcome','createdBy','nextFollow']
        
        widgets = {
            'remarks': forms.TextInput(attrs={'class': 'form-control'}), 
            
            'outcome': forms.RadioSelect(attrs={'class': 'form-check-input'}), 
            
            'nextFollow': forms.DateInput(attrs={
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
        self.fields['nextFollow'].initial = '' 
        # Explicitly set choices for the gender field to avoid null values
        self.fields['outcome'].choices = [
            ('Re-examination','Re-examination'),
            ('Eye surgery','Eye surgery'),
            ('After surgery','After surgery'),
        ] 
        
    def clean_nextFollow(self):
        nextFollow_date = self.cleaned_data.get('nextFollow')
        if nextFollow_date and nextFollow_date < date.today() - timedelta(days=1):
            raise forms.ValidationError("Next Follow_date Date cannot be earlier than today.")
        return nextFollow_date       
        
    
    
    
    
    
    
    
