from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import CreateView, ListView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Transection
from .forms import DepositForm, WithdrawForm, LoanRequestForm
from .constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum
from django.views import View
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

class TransectionReportView(LoginRequiredMixin, ListView):
    template_name = ""
    model = Transection
    balance = 0

    def get_queryset(self):
        queryset =  super().get_queryset().filter(
            account = self.request.user.account
        )

        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            queryset = queryset.filter(timestamp_date_gte = start_date, timestamp_date_lte = end_date)
            self.balance = Transection.objects.filter(timestamp_date_gte = start_date, timestamp_date_lte = end_date).aggregate(Sum('amount'))['amount__sum']
        else:
            self.balance = self.request.user.account.balance

        return queryset.distinct()
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context.update({
            'account' : self.request.user.account
        })
        return context
    
class PayLoanView(LoginRequiredMixin, View):
    def get(self, request, loan_id):
        loan = get_object_or_404(Transection, id=loan_id)

        if loan.loan_approve:
            user_account = loan.account
            if loan.amount < user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transection = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
            else:
                messages.error(self.request, f"Loan amount is greater than available balance")
                return redirect()
        
class LoanListView(LoginRequiredMixin, ListView):
    model = Transection
    template_name = ""
    context_object_name = "loans"

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transection.objects.filter(account = user_account, transaction_type = LOAN)
        return queryset
