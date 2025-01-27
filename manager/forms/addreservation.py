# forms.py
from datetime import date
from django import forms
from manager.model.patient import  City, Offers, Patient, SufferedCases


class MyModelForm(forms.ModelForm):   
    
    # Explicitly define city field outside Meta
    city = forms.ModelChoiceField(queryset=City.objects.active(), required=True, label="City", widget=forms.Select(attrs={'class': 'form-select'}))
    sufferedcase= forms.ModelChoiceField(queryset=SufferedCases.objects.active(), required=True, label="Suffered Case", widget=forms.Select(attrs={'class': 'form-select'}))
    offerID= forms.ModelChoiceField(queryset=Offers.objects.active(),required=False,  label="Offers", widget=forms.Select(attrs={'class': 'form-select'}))
    class Meta:
        model = Patient
       
        fields = ['reservationCode','fullname', 'mobile', 'city','age','gender','sufferedcase','offerID','leadSource','remarks','expectedDate','callDirection']
        
        widgets = {
            'fullname': forms.TextInput(attrs={'class': 'form-control'}),
            # 'mobile': forms.TextInput(attrs={
            # 'class': 'form-control',
            # #'placeholder': '7xx1234567'  # Guide user to input correct format
            # }),           
            
            'age': forms.NumberInput(attrs={
            'class': 'form-control',
            'min': 1,  # Minimum age
            'max': 99,  # Maximum age (restricts to two digits)
               }),
            
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),            
            'reservationCode': forms.TextInput(attrs={
            'readonly': 'readonly',
            'class': 'form-control',
            'style': 'background-color: yellow;font-weight:bold'}),
            
            
            'callDirection': forms.RadioSelect(attrs={'class': 'form-check-input'}),

            'leadSource': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            
            'expectedDate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control',
                'required': True,  # Add required attribute here
            }),
            
             
    
        }
        error_messages = {
            'callDirection': {
                 'required': 'Call Direction is required.',
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
            },
            'leadSource': {
                'required': 'Coming Source is required.',
            },
            
             'expectedDate': {
                'required': 'Expected Date is required.',
            }
          }
        
    def __init__(self, *args, **kwargs):
        # Extract 'request' before calling the parent constructor
        self.request = kwargs.pop('request', None)
        
        # Call the parent constructor
        super().__init__(*args, **kwargs)
        
        # Initialize field values
        self.fields['expectedDate'].initial = ''
        self.fields['mobile'].initial = ''
        self.fields['age'].initial = ''
        
        # Explicitly set choices for the gender field to avoid null values
        self.fields['gender'].choices = [
            ('M', 'Male'),
            ('F', 'Female'),
        ]
        
        # Ensure RadioSelect fields are marked as required
        self.fields['gender'].widget.attrs.update({'required': True})
        self.fields['leadSource'].widget.attrs.update({'required': True})

        
    # def clean_mobile(self): 
    #     mobileNum = self.cleaned_data.get('mobile') 
    #     if Patient.objects.filter(mobile=mobileNum).exists(): 
    #         print(mobileNum)
    #         if self.request:  # Ensure request is available
    #             print('hello request')
    #             messages.warning(self.request, 'A patient with this Mobile Number already exists.')
    #     return mobileNum
        
    # def clean_fileserial(self):
    #     fileserial = self.cleaned_data.get('fileserial')
    #     if Patient.objects.filter(fileserial=fileserial).exists():
    #         raise forms.ValidationError('A patient with this file serial already exists.')
    #     return fileserial
    
    # def clean_mobile(self):
    #     mobileNum = self.cleaned_data.get('mobile')
    #     if Patient.objects.filter(mobile=mobileNum).exists():
    #         raise forms.ValidationError('A patient with this Mobile Number already exists.')
    #     return mobileNum
    
    def clean_expectedDate(self):
        expected_date = self.cleaned_data.get('expectedDate')
        if expected_date and expected_date < date.today():
            raise forms.ValidationError("Expected Date cannot be earlier than today.")
        return expected_date
    
    # def clean_mobile(self):
    #     mobile = self.cleaned_data.get('mobile')        
    #     # Regex pattern to match 7xx1234567
    #     pattern = r'^7\d{2}\d{3}\d{4}$'
    #     if not re.match(pattern, mobile):
    #         raise ValidationError('Mobile number must be in the format 7xx1234567.')
        
    #     return mobile
    
    def clean_age(self):
        age = self.cleaned_data.get('age')
        if not (1 <= age <= 99):
            raise forms.ValidationError('Age must be a number between 1 and 99.')
        return age
    
    