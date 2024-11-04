from django.shortcuts import get_object_or_404, redirect
from django.views.generic import CreateView, ListView, FormView
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import Transaction, Bank
from .forms import DepositForm, WithdrawForm, LoanRequestForm, TransferForm
from .constants import DEPOSIT, WITHDRAWAL, LOAN, LOAN_PAID, TRANSFER
from django.contrib import messages
from django.http import HttpResponse
from datetime import datetime
from django.db.models import Sum
from django.views import View
from django.urls import reverse_lazy
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_transaction_email(user, amount, subject, template):
    message = render_to_string(template, {
        'user' : user,
        'amount' : amount,
    })
    send_email = EmailMultiAlternatives(subject, message, to=[user.email])
    send_email.attach_alternative(message, "text/html")
    send_email.send()

class TransactionCreateMixin(LoginRequiredMixin, CreateView):
    template_name = 'transactions/transaction_form.html'
    model = Transaction
    title = ''
    success_url = reverse_lazy('transaction_report')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['account'] = self.request.user.account  # Pass the account to the form
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = self.title
        return context

class DepositMoneyView(TransactionCreateMixin):
    form_class = DepositForm
    title = 'Deposit'

    def get_initial(self):
        initial = {'transaction_type': DEPOSIT}
        return initial
    
    def form_valid(self, form):
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance += amount
        account.save(update_fields=['balance'])

        messages.success(self.request, f'{amount} BDT was deposited to your account successfully.')
        # mail_subject = 'Deposite Message'
        # message = render_to_string('transactions/deposite_email.html', {
        #     'user' : self.request.user,
        #     'amount' : amount,
        # })
        # to_email = self.request.user.email
        # send_email = EmailMultiAlternatives(mail_subject, message, to=[to_email])
        # send_email.attach_alternative(message, "text/html")
        # send_email.send()
        send_transaction_email(self.request.user, amount, "Deposite Message", "transactions/deposite_email.html")
        return super().form_valid(form)

class WithdrawMoneyView(TransactionCreateMixin):
    form_class = WithdrawForm
    title = 'Withdraw Money'

    def get_initial(self):
        initial = {'transaction_type': WITHDRAWAL}
        return initial
    
    def form_valid(self, form):
        bank = get_object_or_404(Bank)
        if bank.bankrupt:
            messages.error(self.request, 'The bank is bankrupt. No transfers or withdrawals allowed.')
            return self.form_invalid(form)
        amount = form.cleaned_data.get('amount')
        account = self.request.user.account
        account.balance -= amount
        account.save(update_fields=['balance'])

        messages.success(self.request, f'Successfully withdrawn {amount} BDT from your account.')
        send_transaction_email(self.request.user, amount, "Withdrawal Message", "transactions/withdrawal_email.html")
        return super().form_valid(form)
    
class LoanRequestView(TransactionCreateMixin):
    form_class = LoanRequestForm
    title = 'Request for loan'

    def get_initial(self):
        initial = {'transaction_type': LOAN}
        return initial
    
    def form_valid(self, form):
        bank = get_object_or_404(Bank, id=1)
        if bank.bankrupt:
            messages.error(self.request, 'The bank is bankrupt. No transfers or withdrawals allowed.')
            return self.form_invalid(form)
        amount = form.cleaned_data.get('amount')
        current_loan_count = Transaction.objects.filter(
            account=self.request.user.account,
            transaction_type=LOAN,
            loan_approve=True
        ).count()
        
        if current_loan_count >= 2:
            return HttpResponse("You have crossed your loan limit.")
        
        messages.success(self.request, f'Loan request for {amount} BDT has been successfully sent to admin.')
        send_transaction_email(self.request.user, amount, "Loan Message", "transactions/loan_email.html")
        return super().form_valid(form)

class TransactionReportView(LoginRequiredMixin, ListView):
    template_name = "transactions/transaction_report.html"
    model = Transaction
    context_object_name = 'transactions'

    def get_queryset(self):
        queryset = super().get_queryset().filter(account=self.request.user.account)

        start_date_str = self.request.GET.get('start_date')
        end_date_str = self.request.GET.get('end_date')

        if start_date_str and end_date_str:
            start_date = datetime.strptime(start_date_str, "%Y-%m-%d").date()
            end_date = datetime.strptime(end_date_str, "%Y-%m-%d").date()

            queryset = queryset.filter(
                timestamp__date__gte=start_date,
                timestamp__date__lte=end_date
            )

        return queryset.distinct()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['account'] = self.request.user.account
        context['balance'] = self.request.user.account.balance
        return context
    
class PayLoanView(LoginRequiredMixin, View):
    title = 'Loan List'
    def get(self, request, loan_id):
        loan = get_object_or_404(Transaction, id=loan_id)

        if loan.loan_approve:
            user_account = loan.account
            if loan.amount <= user_account.balance:
                user_account.balance -= loan.amount
                loan.balance_after_transaction = user_account.balance
                user_account.save()
                loan.transaction_type = LOAN_PAID
                loan.save()
                send_transaction_email(self.request.user, loan.amount, "Loan Paid Message", "transactions/loan_paid_email.html")
                return redirect('loan_list')
                # messages.success(request, f'Loan of {loan.amount} BDT has been successfully paid off.')

            else:
                messages.error(self.request, "Loan amount exceeds the available balance.")
                return redirect('loan_list')
        
        return redirect('loan_list')

class LoanListView(LoginRequiredMixin, ListView):
    model = Transaction
    template_name = "transactions/loan_request.html"
    context_object_name = "loans"

    def get_queryset(self):
        user_account = self.request.user.account
        queryset = Transaction.objects.filter(
            account=user_account,
            transaction_type=3
        )
        return queryset

class MoneyTransferView(FormView):
    template_name = 'transactions/transfer.html'
    form_class = TransferForm
    title = 'Money Transfer'
    success_url = reverse_lazy('transaction_report')

    def get_initial(self):
        initial = {'transaction_type': TRANSFER}
        return initial
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs.pop('instance', None)
        kwargs.pop('account', None)
        kwargs['sender_account'] = self.request.user.account
        return kwargs
    
    def create_transaction(self, sender_account, recipient_account, amount):
        sender_account.balance -= amount
        recipient_account.balance += amount
        sender_account.save()
        recipient_account.save()
        
        Transaction.objects.create(
            account=sender_account,
            amount=-amount,  
            balance_after_transaction=sender_account.balance,
            transaction_type=TRANSFER
        )
        
        Transaction.objects.create(
            account=recipient_account,
            amount=amount,  
            balance_after_transaction=recipient_account.balance,
            transaction_type=TRANSFER
        )
    
    def form_valid(self, form):
        bank, created = Bank.objects.get_or_create(id=1)

        if bank.bankrupt:
            messages.error(self.request, 'The bank is bankrupt. No transfers or withdrawals allowed.')
            return self.form_invalid(form)

        account_number = form.cleaned_data['account_number']
        sender_account = self.request.user.account
        amount = form.cleaned_data['amount']
        recipient_account = form.cleaned_data['recipient_account']

        if sender_account == recipient_account:
            messages.error(self.request, "Same account money transfer cannot be possible.")
            return self.form_invalid(form)

        if amount <= 0 or sender_account.balance < amount: 
            messages.error(self.request, "Insufficient balance or invalid transfer amount.")
            return self.form_invalid(form)

        self.create_transaction(
            sender_account=sender_account,
            recipient_account=recipient_account,
            amount=amount
        )

        messages.success(self.request, f'Successfully transferred {amount} BDT.')
        send_transaction_email(self.request.user, amount, "Balance Transfer Message", "transactions/balance_transfer_sender.html")
        send_transaction_email(recipient_account.user, amount, "Balance Added Message", "transactions/balance_transfer_receiver.html")
        return super().form_valid(form)
        
    def form_invalid(self, form):
        return super().form_invalid(form)
