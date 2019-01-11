from django.contrib.auth import login
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.views.generic import UpdateView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from .models import Signup
from .forms import SignUpForm


def signup(request):
    signup_methods = Signup()
    error_message = ''
    if request.method == 'POST':
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            if signup_methods.email_exist(user):
                error_message = f'A user with email {user.email} already exists'
                form = SignUpForm()

            else:
                user.save()
                login(request, user)
                signup_methods.send_welcome_email(user)
                return redirect('home')
    else:
        form = SignUpForm()

    return render(request, 'accounts/signup.html', {'form': form,
                                                    'error_message': error_message})

@method_decorator(login_required, name='dispatch')
class UserUpdateView(UpdateView):
    model = User
    fields = ('first_name', 'last_name', 'email', )
    template_name = 'accounts/my_account.html'
    success_url = reverse_lazy('home')

    def get_object(self):
        return self.request.user
