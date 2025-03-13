# forms.py
import datetime
from django.utils.timezone import localtime
from django.utils.timezone import now, is_naive, make_aware
from django import forms

from django.db.models import Q
from manager.model.patient import AgentCompany, CheckUpPrice, City, MedicalConditionData, Offers, Patient, SufferedCases


class CenterEditReservationForm(forms.ModelForm):   
    
    fullname = forms.CharField(
        max_length=250,
        required=True,
        error_messages={'required': 'Full Name is required!'},
        widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter full name'})
    )
    mobile = forms.CharField(
    required=True,
    error_messages={'required': 'Mobile is required!'},
    widget=forms.TextInput(attrs={'id': 'id_mobile', 'class': 'form-control'})
)
    
    otherMobile = forms.CharField( 
                                  required=False,   
    widget=forms.TextInput(attrs={'class': 'form-control'})
    )
    
    referral=forms.CharField( required=False,widget=forms.Select(attrs={'class': 'form-control'}))
    city = forms.ModelChoiceField(queryset=City.objects.active(), required=True, label="City",
                                  widget=forms.Select(attrs={'class': 'form-select'}))    
    sufferedcaseByPatient = forms.ModelChoiceField(queryset=SufferedCases.objects.active(), required=True, label="Suffered Case-By patient",widget=forms.Select(attrs={'class': 'form-select'}))
    offerID = forms.ModelChoiceField(queryset=Offers.objects.active(), required=False, label="Offers",
                                     widget=forms.Select(attrs={'class': 'form-select'}))
    agentID = forms.ModelChoiceField(queryset=AgentCompany.objects.active(), required=False, label="Agent/Company",widget=forms.Select(attrs={'class': 'form-select'}))
    checkUpprice = forms.ModelChoiceField(queryset=CheckUpPrice.objects.active(), required=True, label="Check-Up price",widget=forms.Select(attrs={'class': 'form-select'}))

    # Medical history fields
    medical_conditions = forms.ModelMultipleChoiceField(
        queryset=MedicalConditionData.objects.all(),
        required=False,
        label="Medical Conditions",
        widget=forms.CheckboxSelectMultiple()
    )

    relation_choices = [
        ('SELF', 'Self'),
        ('REL', 'Relative'),
    ]
    
    condition_relation = forms.ChoiceField(
        choices=relation_choices,
        required=False,
        label="Relation",
        widget=forms.RadioSelect(attrs={'class': 'form-check-input'})
    )
    class Meta:
        model = Patient
        exclude = ['createdDate', 'createdby']  # Exclude non-editable fields
        fields = ['fullname', 'mobile', 'city', 'gender', 'offerID', 'remarks','checkUpprice', 'fileserial', 'birthdate', 'reservationType', 'referral', 'otherMobile','sufferedcaseByPatient', 'wearingconduct', 'rideglass','attendanceTime','attendanceDate','address']
        
        widgets = {            
            'mobile': forms.TextInput(attrs={'class': 'form-control'}),
            'otherMobile': forms.TextInput(attrs={'class': 'form-control'}),            
            'remarks': forms.TextInput(attrs={'class': 'form-control'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
            'reservationCode': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control', 
                                                      'style': 'background-color: yellow;font-weight:bold'}),
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'fileserial': forms.TextInput(attrs={'readonly': 'readonly', 'class': 'form-control'}),
           
            'reservationType': forms.Select(attrs={'class': 'form-select'}),
            'referral': forms.Select(attrs={'class': 'form-select'}),
            'birthdate': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'wearingconduct': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'rideglass': forms.RadioSelect(attrs={'class': 'form-check-input'}),
        }
    
    def __init__(self, *args, **kwargs):
        self.request = kwargs.pop('request', None)
        super().__init__(*args, **kwargs)
        
    def clean_attendanceTime(self):
        data = self.cleaned_data.get("attendanceTime")
        if not data:
            data = localtime().time()  # Uses timezone-aware local time
        return data
    

    def clean_attendanceDate(self):
        data = self.cleaned_data.get("attendanceDate")

        if data is None:
            return now().date()  # Return only the date part

        if isinstance(data, datetime):  # Ensure it's a datetime object
            if is_naive(data):
                return make_aware(data)  # Convert to timezone-aware
            return data
        else:
            # Convert `date` to `datetime` before making it timezone-aware
            naive_datetime = datetime.combine(data, datetime.min.time())
            return make_aware(naive_datetime)
        
    # def clean_mobile(self):
    #     mobileNum = self.cleaned_data.get('mobile')
    #     reservCode = self.cleaned_data.get('reservationCode')
    #     print(reservCode)       

    #     # Check for duplicate mobile with a different reservation code
    #     if Patient.objects.filter(mobile=mobileNum).exclude(reservationCode=reservCode).exists():
    #         raise forms.ValidationError('A patient with this Mobile Number already exists.')

    #     return mobileNum
    
    # def clean_confirmationDate(self):
    #     confirmation_date = self.cleaned_data.get('confirmationDate')
    #     if confirmation_date and confirmation_date < date.today():
    #         raise forms.ValidationError("Confirmation Date Date cannot be earlier than today.")
    #     return confirmation_date

        
    
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Remove the empty choice for gender field
        self.fields['gender'].choices = [
            choice for choice in self.fields['gender'].choices if choice[0] != ''
        ]
