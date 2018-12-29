# Howdiweb
>Website application with topic board and personal news feed if user is logged in

The website is available at:  
https://howdiweb.nl  
https://www.howdiweb.nl  

*note to enter https as http does not forward (yet)*

![](howdiweb_screenshot.png)

## Settings
- Web application in Django 2.1
- Python 3.6
- Instance is running on AWS Elastic Beanstalk
- Database PostgreSQL on AWS RDS
- Requirements are listed in requirements.txt:

The environment file .env is not provided. Following settings must be given:  
SECRET_KEY = 'some_secret_key'  
DEBUG = True [or False]  
ALLOWED_HOSTS = mywebserver.com  
AWS_ACCESS_KEY_ID = 'myawsaccesskey'  
AWS_SECRET_ACCESS_KEY = 'myawssecretkey'  
DATABASE_PASSWORD = 'mydatabasepassword'  


## Author
Name: Bruno Vermeulen  
Email: bruno.vermeulen@hotmail.com  
Date: 17 November 2018  
