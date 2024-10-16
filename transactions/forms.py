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

class DepositeForm(TransectionForm):
    def clean_amount(self):
        min_deposite_amount = 500
        amount = self.cleaned_data.get('amount')
        if amount < min_deposite_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposite_amount} BDT'
            )
        return amount

class WithdrawForm(TransectionForm):
    def clean_amount(self):
        account = self.account
        min_withdraw_account = 500
        max_withdraw_account = 500000
        balance = account.balance
        amount = self.cleaned_data.get('amount')
        
        if amount < min_withdraw_account:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_account} BDT'
            )
        
        if amount > max_withdraw_account:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_account} BDT'
            )
        
        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance} BDT in you account'
                'You can not withdraw more than you account balance'
            )
        return amount

class LoanRequestForm(Transection):
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        return amount