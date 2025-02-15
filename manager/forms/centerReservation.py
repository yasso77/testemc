# forms.py
from datetime import date
from django import forms
from manager.model.patient import  AgentCompany, CheckUpPrice, City, Offers, Patient, SufferedCases


class CEAddReservationForm(forms.ModelForm):
    fullname = forms.CharField(
        max_length=250,
        required=True,
        error_messages={'required': 'Full Name is required!'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'})
    )
    mobile=forms.CharField(required=True, error_messages={'required': 'Mobile is required!'})
    city = forms.ModelChoiceField(queryset=City.objects.active(), required=True, label="City", widget=forms.Select(attrs={'class': 'form-select'}))
    
    sufferedcaseByPatient = forms.ModelChoiceField(queryset=SufferedCases.objects.active(), required=True, label="Suffered Case-By patient", widget=forms.Select(attrs={'class': 'form-select'}))
    offerID = forms.ModelChoiceField(queryset=Offers.objects.active(), required=False, label="Offers", widget=forms.Select(attrs={'class': 'form-select'}))
    agentID = forms.ModelChoiceField(queryset=AgentCompany.objects.active(), required=False, label="Agent/Company", widget=forms.Select(attrs={'class': 'form-select'}))
    checkUpprice = forms.ModelChoiceField(queryset=CheckUpPrice.objects.active(), required=True, label="Check-Up price", widget=forms.Select(attrs={'class': 'form-select'}))

    class Meta:
        model = Patient
        fields = [ 'fullname', 'mobile', 'city', 'gender',  'offerID', 'leadSource', 'remarks','checkUpprice', 'fileserial', 'birthdate', 'reservationType', 'referral', 'otherMobile','sufferedcaseByPatient', 'wearingconduct', 'rideglass']
        widgets = {
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 99}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
            'reservationCode': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control', 'style': 'background-color: yellow;font-weight:bold'}),           
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'fileserial': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control', 'style': 'background-color: yellow;font-weight:bold'}),
            'otherMobile': forms.TextInput(attrs={'class': 'form-control'}),
            'reservationType': forms.Select(attrs={'class': 'form-select'}),
            'referral': forms.Select(attrs={'class': 'form-select'}),
            'birthdate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'wearingconduct': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'rideglass': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)       

        super().__init__(*args, **kwargs)
        self.fields['gender'].choices = [('M', 'Male'), ('F', 'Female')]
        self.fields['gender'].required = True
        self.fields['wearingconduct'].required = True
        self.fields['rideglass'].required = True
        self.fields['fullname'].error_messages = {'required': 'Full Name is required!'}
        self.fields['mobile'].error_messages = {'required': 'Mobile is required!'}
        self.fields['referral'].required= False

            
    # def clean_mobile(self):
    #     mobile = self.cleaned_data.get('mobile')        
    #     # Regex pattern to match 7xx1234567
    #     pattern = r'^7\d{2}\d{3}\d{4}$'
    #     if not re.match(pattern, mobile):
    #         raise ValidationError('Mobile number must be in the format 7xx1234567.')
        
    #     return mobile
    
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

    
    