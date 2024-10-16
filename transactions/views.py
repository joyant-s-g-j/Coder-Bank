from django.shortcuts import render
from django.views.generic import CreateView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Transection
from .forms import DepositForm, WithdrawForm, LoanRequestForm
from .constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID
from django.contrib import messages
from django.http import HttpResponse
# Create your views here.
class TransectionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = ''
    model = Transection
    title = ''
    success_url = ''

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.update({
            'account' : self.request.user.account,
        })
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'title' : self.title
        })

class DepositMoneyView(TransectionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type' : DEPOSIT}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance += amount
        account.save(
            update_fields = ['balance']
        )

        messages.success(self.request, f'{amount} BDT was deposited to you account successfully')
        return super().form_valid(form)

class WithdrawMoneyView(TransectionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type' : WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance -= amount
        account.save(
            update_fields = ['balance']
        )

        messages.success(self.request, f'Successfully withdrawn {amount} BDT from you account successfully')
        return super().form_valid(form)
    
class LoanMoneyView(TransectionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request for loan'

    def get_initial(self):
        initial = {'transaction_type' : LOAN}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transection.objects.filter(account = self.request.user.account, transaction_type = 3, loan_approve = True).count()
        if current_loan_count >= 2:
            return HttpResponse("You have crossed you loan limit")
        messages.success(self.request, f'loan request for {amount} BDT has been successfully sent to admin')
        return super().form_valid(form)
    