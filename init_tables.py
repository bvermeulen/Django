import os

def populate():
    news.add_news_site_to_model()
    news.add_news_sites_to_default_user()

if __name__ == "__main__":
    import django
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'howdimain.settings')
    django.setup()
    import newsfeed.module_news as news
    populate()
