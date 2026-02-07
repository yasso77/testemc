from django import forms
from django.utils.timezone import localtime, now
from manager.model.patient import (
    AgentCompany, CheckUpPrice, City,
    MedicalConditionData, Offers,
    Patient, SufferedCases
)


class CenterEditReservationForm(forms.ModelForm):

    fullname = forms.CharField(
        max_length=250,
        required=True,
        error_messages={'required': 'Full Name is required!'},
        widget=forms.TextInput(attrs={
            'class': 'form-control',
            'placeholder': 'Enter full name'
        })
    )

    otherMobile = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    remarks = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={'class': 'form-control'})
    )

    city = forms.ModelChoiceField(
        queryset=City.objects.active(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    sufferedcaseByPatient = forms.ModelChoiceField(
        queryset=SufferedCases.objects.active(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    offerID = forms.ModelChoiceField(
        queryset=Offers.objects.active(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    agentID = forms.ModelChoiceField(
        queryset=AgentCompany.objects.active(),
        required=False,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    checkUpprice = forms.ModelChoiceField(
        queryset=CheckUpPrice.objects.active(),
        required=True,
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    medical_conditions = forms.ModelMultipleChoiceField(
        queryset=MedicalConditionData.objects.all(),
        required=False,
        widget=forms.CheckboxSelectMultiple()
    )

    class Meta:
        model = Patient

        # ✅ Explicit list of editable fields
        fields = [
            'fullname',
            'city',
            'gender',
            'offerID',
            'remarks',
            'checkUpprice',
            'fileserial',
            'birthdate',
            # 'reservationType',
            # 'referral',
            'otherMobile',
            'sufferedcaseByPatient',
            'wearingconduct',
            'rideglass',
            'attendanceTime',
            'attendanceDate',
            'address',
            'organizationID',
        ]

        widgets = {
            'gender': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'fileserial': forms.TextInput(attrs={
                'readonly': 'readonly',
                'class': 'form-control'
            }),
            'organizationID': forms.Select(attrs={'class': 'form-select'}),
            # 'reservationType': forms.Select(attrs={'class': 'form-select'}),
            # 'referral': forms.Select(attrs={'class': 'form-select'}),
            'birthdate': forms.DateInput(attrs={
                'type': 'date',
                'class': 'form-control'
            }),
            'wearingconduct': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'rideglass': forms.RadioSelect(attrs={'class': 'form-check-input'}),
            'address': forms.TextInput(attrs={'class': 'form-control'}),
        }

    # =========================
    # CLEANERS
    # =========================

    def clean_attendanceTime(self):
        value = self.cleaned_data.get("attendanceTime")
        return value or localtime().time()

    def clean_attendanceDate(self):
        value = self.cleaned_data.get("attendanceDate")
        return value or now().date()

    # =========================
    # INIT
    # =========================

    def __init__(self, *args, request=None, **kwargs):
        self.request = request
        super().__init__(*args, **kwargs)

        # Remove empty gender option
        self.fields['gender'].choices = [
            c for c in self.fields['gender'].choices if c[0]
        ]
