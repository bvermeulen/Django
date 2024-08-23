
from django.apps import AppConfig
from howdimain.utils.plogger import Logger
logger = Logger.getlogger()


class VerifyEmailConfig(AppConfig):
    name = "accounts.verify_email"

    def ready(self):
        logger.debug("[Email Verification] : importing signals - OK.")
        import accounts.verify_email.signals
