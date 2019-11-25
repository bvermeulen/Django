from django import template

register = template.Library()

@register.simple_tag
def get_last_n_posts(topic, n):
    return topic.posts.order_by('-created_at')[:n]
