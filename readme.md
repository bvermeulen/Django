# Howdiweb
>Website application with topic board and personal news feed if user is logged in

The website is available at:  
https://www.howdiweb.nl  

![](howdiweb_screenshot.png)

## Framworks used
- Python 3.6
- Web application in Django 2.2.3
- Database PostgreSQL
- Email Imgur
- Markdown editor Martor
- RSS feed through Feedparser
- Instance is running on Digital Ocean at ip 174.138.5.244
- Requirements are listed in requirements.txt:

## Environment variables
Environment variables are give in the file .env and for obvious readons is not provided.   
Following settings must be given:  
'''
SECRET_KEY =
LOG_FILE =
DEBUG =
ALLOWED_HOSTS =
 
# postgresql database on localhost
DB_NAME =
DB_USER =
DB_PASSWORD =

# imgur client_id and key
IMGUR_CLIENT_ID =
IMGUR_SECRET_KEY =
 
# email mailgun
EMAIL_BACKEND = django.core.mail.backends.smtp.EmailBackend
EMAIL_HOST = smtp.mailgun.org
EMAIL_HOST_USER =
EMAIL_HOST_PASSWORD =
'''

## Author
Name: Bruno Vermeulen  
Email: bruno.vermeulen@hotmail.com  
Date: 7 July 2019  
