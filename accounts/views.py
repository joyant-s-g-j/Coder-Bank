from django.shortcuts import render,redirect
from django.views.generic import FormView
from .forms import UserRegistrationForm, UserUpdateForm
from django.contrib.auth import login, logout
from django.urls import reverse_lazy
from django.contrib.auth.views import LoginView, LogoutView
from django.views import View
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import PasswordChangeForm
from django.contrib.auth import update_session_auth_hash
from django.contrib import messages
from django.core.mail import EmailMultiAlternatives
from django.template.loader import render_to_string

def send_passchange_email(user, subject, template):
    message = render_to_string(template, {
        'user' : user,
    })
    send_email = EmailMultiAlternatives(subject, message, to=[user.email])
    send_email.attach_alternative(message, 'text/html')
    send_email.send()

@login_required
def pass_change(request):
    form = PasswordChangeForm(user=request.user, data=request.POST)
    if request.user.is_authenticated:
        if request.method == "POST":
            if form.is_valid():
                form.save()
                update_session_auth_hash(request, form.user)
                messages.success(request, "Your password was updated successfully!")
                send_passchange_email(user=request.user, subject='Password Changed', template="accounts/passchange_email.html")
                return redirect('profile')
        else:
            messages.error(request, "Please correct the error below.")
    else:
        return redirect('login')
    
    return render(request, 'accounts/passchange.html', {'form': form})

class UserRegistrationView(FormView):
    template_name = 'accounts/user_registration.html'
    form_class = UserRegistrationForm
    success_url = reverse_lazy('register')

    def form_valid(self, form):
        user = form.save()
        login(self.request, user)
        return super().form_valid(form)

class UserLoginView(LoginView):
    template_name = 'accounts/user_login.html'
    def get_success_url(self):
        return reverse_lazy('home')
    
class UserLogoutView(LogoutView):
    def get_success_url(self):
        if self.request.user.is_authenticated:
            logout(self.request)
        return reverse_lazy('home')

class UserBankAccountUpdateView(View):
    template_name = 'accounts/profile.html'

    def get(self, request):
        form = UserUpdateForm(instance=request.user)
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = UserUpdateForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect('profile')  # Redirect to the user's profile page
        return render(request, self.template_name, {'form': form})

