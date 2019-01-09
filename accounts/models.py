from django.db import models
from django.core.mail import EmailMessage, send_mail
from django.template.loader import render_to_string

class Signup(models.Model):

    def send_welcome_email(self, user):
        context = {'first_name': user.first_name,
                   'username': user.username,
                  }
        email_title = render_to_string(f'email_welcome_subject.txt').strip('\n')
        email_body_text = render_to_string('email_welcome_body.html', context)

        email = EmailMessage(email_title,
                             email_body_text,
                             'admin@howdiweb.nl',
                             [user.email, 'admin@howdiweb.nl'],)

        email.content_subtype = 'html'
        email.send(fail_silently=True)
