from django.urls import path, re_path
from django.contrib import admin
from django.contrib.auth import views as auth_views
from accounts import views

urlpatterns = [
    path('', views.home_page, name='home'),
    path('signup/', views.signup, name='signup'),
    path('settings/account/', views.UserUpdateView.as_view(),
         name='my_account'),

    path('admin/', admin.site.urls),

    path('login/', auth_views.LoginView.as_view(template_name='accounts/login.html'),
         name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('reset/', auth_views.PasswordResetView.as_view(
        template_name='accounts/password_reset.html',
        email_template_name='accounts/email_password_reset_body.html',
        subject_template_name='accounts/email_password_reset_subject.txt'),
         name='password_reset'),
    path('reset/done/', auth_views.PasswordResetDoneView.as_view(
        template_name='accounts/password_reset_done.html'),
         name='password_reset_done'),
    re_path(r'^reset/(?P<uidb64>[0-9A-Za-z_\-]+)/(?P<token>[0-9A-Za-z]{1,13}-[0-9A-Za-z]{1,20})/$',  #pylint: disable=line-too-long
            auth_views.PasswordResetConfirmView.as_view(
                template_name='accounts/password_reset_confirm.html'),
            name='password_reset_confirm'),
    path('reset/complete/', auth_views.PasswordResetCompleteView.as_view(
        template_name='accounts/password_reset_complete.html'),
         name='password_reset_complete'),
    path('settings/password/', auth_views.PasswordChangeView.as_view(
        template_name='accounts/password_change.html'),
         name='password_change'),
    path('settings/password/done/', auth_views.PasswordChangeDoneView.as_view(
        template_name='accounts/password_change_done.html'),
         name='password_change_done'),]
