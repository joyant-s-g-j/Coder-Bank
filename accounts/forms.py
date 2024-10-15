from django.contrib.auth.forms import UserCreationForm
from django import forms
from . constants import GENDER_TYPE, ACCOUNT_TYPE
from django.contrib.auth.models import User
from .models import UserBankAccount, UserAddress

class UserRegistrationForm(UserCreationForm):
    birth_day = forms.DateField(widget=forms.DateInput(attrs={'type':'date'}))
    gender = forms.ChoiceField(choices=GENDER_TYPE)
    account_type = forms.ChoiceField(choices=ACCOUNT_TYPE)
    street_address = forms.CharField(max_length=100)
    city = forms.CharField(max_length=100)
    postal_code = forms.IntegerField()
    country = forms.CharField(max_length=100)
    class Meta:
        model = User
        fields = ['username', 'password1', 'password2', 'first_name', 'last_name', 'email', 'account_type', 'birth_day', 'gender', 'postal_code', 'street_address', 'city', 'country']

    def save(self, commit=True):
        our_user = super().save(commit=False)
        if commit == True:
            our_user.save()
            account_type = self.cleaned_data.get('account_type')
            gender = self.cleaned_data.get('gender')
            postal_code = self.cleaned_data.get('postal_code')
            country = self.cleaned_data.get('country')
            birth_day = self.cleaned_data.get('birth_day')
            city = self.cleaned_data.get('city')
            street_address = self.cleaned_data.get('street_address')
            

            UserAddress.objects.create(
                user = our_user,
                postal_code = postal_code,
                country = country,
                city = city,
                street_address = street_address
            )
            UserBankAccount.objects.create(
                user = our_user,
                account_type = account_type,
                gender = gender, 
                birth_day = birth_day,
                account_no = 1000000 + our_user.id
            )
        return our_user
