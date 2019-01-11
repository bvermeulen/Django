from django.db import models
from django.contrib.auth.models import User
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string

class Signup(models.Model):

    def send_welcome_email(self, user):
        context = {'first_name': user.first_name,
                   'username': user.username,
                  }
        email_title = render_to_string('accounts/email_welcome_subject.txt').strip('\n')
        email_body_text = render_to_string('accounts/email_welcome_body.html', context)

        email = EmailMessage(email_title,
                             email_body_text,
                             'admin@howdiweb.nl',
                             [user.email, 'admin@howdiweb.nl'],)

        email.content_subtype = 'html'
        email.send(fail_silently=True)

    def email_exist(self, user):
        for existing_user in User.objects.all():
            if user.email == existing_user.email:
                return True
        return False
