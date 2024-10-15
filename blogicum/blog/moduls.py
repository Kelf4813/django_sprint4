from django.db.models import Count
from django.utils import timezone


def filter_posts(posts):
    return posts.select_related('location', 'category', 'author').filter(
        is_published=True,
        category__is_published=True).order_by('id')


def filter_posts_time(posts):
    return posts.select_related('location', 'category', 'author').filter(
        pub_date__lte=timezone.now(), is_published=True,
        category__is_published=True)


def annotate_comments(posts):
    return posts.annotate(comment_count=Count('comment'))
