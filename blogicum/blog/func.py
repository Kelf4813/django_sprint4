def filter_posts(posts):
    return posts.select_related('location', 'category', 'author').filter(
        is_published=True,
        category__is_published=True).order_by('id')