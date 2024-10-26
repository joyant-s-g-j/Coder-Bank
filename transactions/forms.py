from django import forms
from .models import Transaction, UserBankAccount

class TransactionForm(forms.ModelForm):
    class Meta:
        model = Transaction
        fields = ['amount', 'transaction_type']
    
    def __init__(self, *args, **kwargs):
        self.account = kwargs.pop('account')  # Retrieve the account from kwargs
        super().__init__(*args, **kwargs)
        self.fields['transaction_type'].disabled = True  # Disable transaction_type field
        self.fields['transaction_type'].widget = forms.HiddenInput()  # Hide the field

    def save(self, commit=True):
        self.instance.account = self.account  # Set the account instance
        self.instance.balance_after_transaction = self.account.balance  # Set balance
        return super().save(commit)  # Call the parent save method

class DepositForm(TransactionForm):
    def clean_amount(self):
        min_deposit_amount = 500
        amount = self.cleaned_data.get('amount')
        if amount < min_deposit_amount:
            raise forms.ValidationError(
                f'You need to deposit at least {min_deposit_amount} BDT.'
            )
        return amount

class WithdrawForm(TransactionForm):
    def clean_amount(self):
        account = self.account  # Get the account from the mixin
        min_withdraw_amount = 500
        max_withdraw_amount = 500000
        balance = account.balance
        amount = self.cleaned_data.get('amount')

        if amount < min_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at least {min_withdraw_amount} BDT.'
            )
        
        if amount > max_withdraw_amount:
            raise forms.ValidationError(
                f'You can withdraw at most {max_withdraw_amount} BDT.'
            )
        
        if amount > balance:
            raise forms.ValidationError(
                f'You have {balance} BDT in your account. '
                'You cannot withdraw more than your account balance.'
            )
        return amount

class LoanRequestForm(TransactionForm):  # Inherit from TransactionForm
    def clean_amount(self):
        amount = self.cleaned_data.get('amount')
        if amount <= 0:  # Ensure amount is positive
            raise forms.ValidationError('Loan amount must be positive.')
        return amount

class TransferForm(forms.Form):
    account_number = forms.CharField(label='Account Number')
    amount = forms.DecimalField(label='Amount')

    def __init__(self, *args, **kwargs):
        self.sender_account = kwargs.pop('sender_account', None)

        super().__init__(*args, **kwargs)

        for field in self.fields:
            self.fields[field].widget.attrs.update({
                'class' : (
                    'appearance-none block w-full bg-gray-200 '
                    'text-gray-700 border border-gray-200 rounded '
                    'py-3 px-4 leading-tight focus:outline-none '
                    'focus:bg-white focus:border-gray-500'
                )
            })

    def clean(self):
        cleaned_data = super().clean()
        recipient_account_number = cleaned_data.get('account_number')
        amount = cleaned_data.get('amount')
        recipient_account = UserBankAccount.objects.filter(account_no=recipient_account_number).first()
        if recipient_account is None:
            raise forms.ValidationError("Recipient account not found!")
        
        # sender_balance = self.sender_account.balance
        if amount <= 0:
            raise forms.ValidationError("The transfer amount must be positive")
        
        sender_balance = self.sender_account.balance
        if amount > sender_balance:
            raise forms.ValidationError(
                f"Insufficient balance! You have {sender_balance} BDT in your account"
            )
        
        cleaned_data['recipient_account'] = recipient_account
        return cleaned_data
   