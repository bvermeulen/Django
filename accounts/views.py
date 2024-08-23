from django.contrib.auth import logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.contrib.auth.signals import (
    user_logged_in,
    user_logged_out,
    user_login_failed,
)
from django.dispatch import receiver
from django.shortcuts import render, redirect
from django.views.generic import UpdateView
from django.utils.decorators import method_decorator
from django.urls import reverse_lazy
from accounts.verify_email.email_handler import send_verification_email
from howdimain.utils.plogger import Logger
from howdimain.utils.get_ip import get_client_ip
from .models import Signup, Home
from .forms import SignUpForm, UserUpdateForm

logger = Logger.getlogger()


def home_page(request):
    welcome_text = Home.objects.last().welcome_text
    welcome_image = Home.objects.last().welcome_image
    member_text = Home.objects.last().member_text
    member_image = Home.objects.last().member_image

    context = {
        "welcome_image": welcome_image,
        "welcome_text": welcome_text,
        "member_image": member_image,
        "member_text": member_text,
    }

    return render(request, "accounts/home.html", context)


def signup(request):
    signup_methods = Signup()
    error_message = ""
    if request.method == "POST":
        form = SignUpForm(request.POST)
        if form.is_valid():
            user = form.save(commit=False)
            ip_address = get_client_ip(request)
            if signup_methods.email_exist(user):
                error_message = f"A user with email {user.email} already exists"
                logger.info(
                    f"user {user.username} (ip: {ip_address}) tries to use "
                    f"existing email: {user.email}"
                )
                form = SignUpForm()

            else:
                inactive_user = send_verification_email(request, form)
                signup_methods.send_welcome_email(inactive_user)
                logger.info(
                    f"user {inactive_user.username} (ip: {ip_address}) "
                    f"has succesfully signed up, email sent to {user.email}"
                )
                return redirect("home")

    else:
        form = SignUpForm()

    return render(
        request, "accounts/signup.html", {"form": form, "error_message": error_message}
    )


@method_decorator(login_required, name="dispatch")
class UserUpdateView(UpdateView):
    model = User
    form_class = UserUpdateForm
    template_name = "accounts/my_account.html"
    success_url = reverse_lazy("home")

    def get_object(self):  # pylint: disable=arguments-differ
        logger.info(
            f"user: {self.request.user.username} (ip: {get_client_ip(self.request)}) "
            f"is updating account"
        )
        return self.request.user


def logout_view(request):
    logout(request)
    return redirect("home")


@receiver(user_logged_in)
def user_logged_in_callback(sender, request, user, **kwargs):
    # in tests there is no attribute user
    try:
        logger.info(
            f"user: {request.user.username} (ip: {get_client_ip(request)}) has logged in"
        )

    except AttributeError:
        pass


@receiver(user_logged_out)
def user_logged_out_callback(sender, request, user, **kwargs):
    # in tests there is no attribute user
    try:
        logger.info(
            f"user: {request.user.username} (ip: {get_client_ip(request)}) has logged out"
        )

    except AttributeError:
        pass


@receiver(user_login_failed)
def user_login_failed_callback(sender, request, credentials, **kwargs):
    try:
        username = credentials["username"]

    except KeyError:
        username = ""

    logger.info(f"login failed for user: {username} (ip: {get_client_ip(request)})")
