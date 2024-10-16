from django import forms
from .models import Transection

class TransectionForm(forms.ModelForm):
    class Meta:
        model = Transection
        fields = ['amount', 'transaction_type']
    
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')
        super.__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True
        self.fields['transaction_type'].widget = forms.HiddenInput()

    def save(self, commit = True):
        self.instance.account = self.account
        self.instance.balance_after_transection = self.account.balance
        return super().save()