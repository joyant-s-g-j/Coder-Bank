from django.urls import path
from .views import DepositMoneyView, WithdrawMoneyView, TransectionReportView, LoanRequestView, LoanListView, PayLoanView

urlpatterns = [
    path('deposit/', DepositMoneyView.as_view(), name="deposit_money"),
    path('report/', TransectionReportView.as_view(), name="transection_report"),
    path('withdraw/', WithdrawMoneyView.as_view(), name="Withdraw_money"),
    path('loan_request/', LoanRequestView.as_view(), name="loan_request"),
    path('loans/', LoanListView.as_view(), name="loan_list"),
    path('loan/<int:loan_id>/', PayLoanView.as_view(), name="deposit_money"),
]
