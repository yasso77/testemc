# forms.py
from datetime import date
from django import forms
from manager.model.patient import CallTrack, City, Offers, Patient, SufferedCases
from django.contrib import messages

class insertCallTrackForm(forms.ModelForm):   
    
    # Explicitly define city field outside Meta
    
    class Meta:
        model = CallTrack
        exclude = ['createdDate']
       
        fields = ['patientID', 'remarks', 'confirmationDate','nextFollow','outcome','agentID','createdBy']
        
        widgets = {
            'remarks': forms.TextInput(attrs={'class': 'form-control'}), 
            
            'outcome': forms.RadioSelect(attrs={'class': 'form-check-input'}),

            #'agentID': forms.Select(attrs={'class': 'form-select'}),            
            
            'nextFollow': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',               
            }),
            
            'confirmationDate': forms.DateInput(attrs={
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
        self.fields['confirmationDate'].initial = ''
        self.fields['nextFollow'].initial = ''
        
        
        # Explicitly set choices for the gender field to avoid null values
        self.fields['outcome'].choices = [
            ('Canceled', 'Canceled'),
            ('Rescheduled', 'Rescheduled'),
            ('Confirmed','Confirmed')
        ]
        
        
    def clean_confirmationDate(self):
        confirmed_date = self.cleaned_data.get('confirmationDate')
        if confirmed_date and confirmed_date < date.today():
            raise forms.ValidationError("Confirmation Date cannot be earlier than today.")
        return confirmed_date
    
    def clean_nextFollow(self):
        nextFollow_date = self.cleaned_data.get('nextFollow')
        if nextFollow_date and nextFollow_date < date.today():
            raise forms.ValidationError("Next Follow_date Date cannot be earlier than today.")
        return nextFollow_date
    
    
    
    
