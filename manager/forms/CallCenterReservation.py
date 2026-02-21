# forms.py
from datetime import date
from django import forms
from manager.model.patient import  AgentCompany, CheckUpPrice, City, Offers, Organizations, Patient, SufferedCases


class CCFormAddReservation(forms.ModelForm):
    fullname = forms.CharField(
        max_length=250,
        required=True,
        error_messages={'required': 'Full Name is required!'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'})
    )
    slotNumber = forms.ChoiceField(
    choices=[],
    required=False,
    widget=forms.Select(attrs={'class': 'form-select'})
)
    mobile=forms.CharField(required=True, error_messages={'required': 'Mobile is required!'},widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter Mobile'}))
    city = forms.ModelChoiceField(queryset=City.objects.active(), required=True, label="City", widget=forms.Select(attrs={'class': 'form-select'}))
    sufferedcase = forms.ModelChoiceField(queryset=SufferedCases.objects.active(), required=True, label="Suffered Case", widget=forms.Select(attrs={'class': 'form-select'}))    
    offerID = forms.ModelChoiceField(queryset=Offers.objects.active(), required=False, label="Offers", widget=forms.Select(attrs={'class': 'form-select'}))
    agentID = forms.ModelChoiceField(queryset=AgentCompany.objects.active(), required=False, label="Agent/Company", widget=forms.Select(attrs={'class': 'form-select'}))
    checkUpprice = forms.ModelChoiceField(queryset=CheckUpPrice.objects.active(), required=True, label="Check-Up price", widget=forms.Select(attrs={'class': 'form-select'}))
    # Exclude 'Center' choice
    filtered_choices = [choice for choice in Patient.leadSource_Choices if choice[0] != 'Center']
    leadSource = forms.ChoiceField(
    choices=[('', 'Select Lead Source')] + filtered_choices,
    required=True,
    error_messages={'required': 'Lead Source is required!'},
    widget=forms.Select(attrs={'class': 'form-select'})) 
    organizationID = forms.ModelChoiceField(
    queryset=Organizations.objects.active(),
    required=True,
    label="Organization",
    error_messages={'required': 'Organization is required!'},
    widget=forms.Select(attrs={'class': 'form-select'})
)

      

    class Meta:
        model = Patient
        fields = ['reservationCode', 'fullname', 'mobile', 'city', 'age', 'gender', 'sufferedcase', 'offerID', 'leadSource', 'remarks','expectedDate', 'callDirection', 'checkUpprice', 'agentID','organizationID' ,'slotNumber'
                 ]
        widgets = {
           
            'age': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 99}),
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
            'reservationCode': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control', 'style': 'background-color: yellow;font-weight:bold'}),
            'callDirection': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'organizationID': forms.Select(attrs={'class': 'form-select'}),
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'expectedDate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),   
        }

    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)      

        super().__init__(*args, **kwargs)
        self.fields['gender'].choices = [('M', 'Male'), ('F', 'Female')]
        self.fields['gender'].required = True
        # Explicitly enforce required validation and error messages
        self.fields['expectedDate'].initial = ''
        self.fields['expectedDate'].required = True
        # self.fields['fullname'].error_messages = {'required': 'Full Name is required!'}
        
        # Explicitly enforce required validation and error messages
        self.fields['mobile'].required = True
        self.fields['mobile'].error_messages = {'required': 'mobile  is required!'}
        
                # -----------------------------
        # Dynamic Slot Dropdown A-1 A-2 A-3
        # -----------------------------
        self.fields['slotNumber'].choices = [('', 'Select')]

        if self.request:
            extra = getattr(self.request.user, 'extra', None)

            if extra and extra.character and extra.tiny_number:

                char = extra.character.upper()
                max_num = extra.tiny_number

                self.fields['slotNumber'].choices += [
                    (f"{char}-{i}", f"{char}-{i}")
                    for i in range(1, max_num + 1)
                ]
        

       

    def clean_expectedDate(self):
        expected_date = self.cleaned_data.get('expectedDate')
        if expected_date is not None and expected_date < date.today():
            raise forms.ValidationError("Expected Date cannot be earlier than today.")
        return expected_date
    
    def clean_fullname(self):
        fullname = self.cleaned_data.get('fullname')
        if not fullname:
            raise forms.ValidationError("Full Name is required!")
        return fullname
    
    def clean_mobile(self):
        mobile = self.cleaned_data.get('mobile')
        if not mobile:
            raise forms.ValidationError("Mobile is required!")
        return mobile

    
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

    
    