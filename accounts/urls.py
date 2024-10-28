from django.urls import path
from .views import UserRegistrationView, UserLoginView, UserLogoutView, UserBankAccountUpdateView, pass_change
urlpatterns = [
    path('register/', UserRegistrationView.as_view(), name='register'),
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', UserBankAccountUpdateView.as_view(), name='profile'),
    path('pass_change/', pass_change, name='passchange'),
]