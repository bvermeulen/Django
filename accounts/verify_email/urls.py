from django.urls import path
from .views import verify_user_and_activate, confirm_email, request_new_link

urlpatterns = [
    path(
        f"user/verify-email/<useremail>/<usertoken>/",
        verify_user_and_activate,
        name="verify-email",
    ),
    path(
        f"user/confirm-email/<useremail>/<usertoken>/",
        confirm_email,
        name="confirm-email"
    ),
    path(
        f"user/verify-email/request-new-link/<useremail>/<usertoken>/",
        request_new_link,
        name="request-new-link-from-token",
    ),
    path(
        f"user/verify-email/request-new-link/",
        request_new_link,
        name="request-new-link-from-email",
    ),
]
