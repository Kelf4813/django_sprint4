from django.contrib.auth import get_user_model
from django.shortcuts import render, get_object_or_404, redirect
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count

from .forms import ProfileEdit, NewPost, AddComment
from .models import Post, Category, Comment

User = get_user_model()


def filter_posts(posts):
    return posts.select_related('location', 'category', 'author').filter(
        is_published=True,
        category__is_published=True).order_by('id')


def index(request):
    now = timezone.now()
    posts = Post.objects.filter(pub_date__lte=now, is_published=True,
                                category__is_published=True).annotate(
        comment_count=Count('comment'))
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj}
    return render(
        request,
        template_name='blog/index.html',
        context=context)


def post_detail(request, post_id):
    post = get_object_or_404(filter_posts(Post.objects), id=post_id)
    comments = Comment.objects.all().filter(post_id=post_id).order_by(
        'created_at')
    form = AddComment(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        instance = form.save(commit=False)
        instance.post_id = post_id
        instance.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(
        request,
        template_name='blog/detail.html',
        context={'post': post, 'form': form, 'comments': comments})


def category_posts(request, category_slug):
    now = timezone.now()
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    post_list = filter_posts(Post.objects).filter(category=category,
                                                  is_published=True,
                                                  pub_date__lte=now).annotate(
        comment_count=Count('comment'))
    paginator = Paginator(post_list, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'category': category, 'page_obj': page_obj}
    return render(request, template_name='blog/category.html', context=context)


def profile(request, username):
    now = timezone.now()
    user = request.user
    profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=profile.id).annotate(
        comment_count=Count('comment'))
    if username != user.username:
        posts = posts.filter(pub_date__lte=now, is_published=True)
    paginator = Paginator(posts, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    context = {'page_obj': page_obj, 'profile': profile}
    return render(request, template_name='blog/profile.html', context=context)


@login_required
def edit_profile(request):
    user = request.user
    form = ProfileEdit(instance=user)
    if request.method == 'POST':
        form = ProfileEdit(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect('blog:profile', username=user.username)

    return render(request, 'blog/user.html', context={'form': form})


@login_required
def create_post(request, post_id=None):
    if post_id is not None:
        instance = get_object_or_404(Post, id=post_id)
    else:
        instance = None
    form = NewPost(request.POST or None, instance=instance)
    user = request.user
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = request.user
        instance.save()
        return redirect('blog:profile', username=user.username)
    return render(request, 'blog/create.html', context={'form': form})


@login_required
def add_comment(request, post_id, comment_id=None):
    user = request.user
    if comment_id is not None:
        instance = get_object_or_404(Comment, id=comment_id, author=user.id)
    else:
        instance = None
    form = AddComment(request.POST or None, instance=instance)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = request.user
        instance.post_id = post_id
        instance.save()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context={'form': form,
                                                         'comment': instance})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(filter_posts(Post.objects), id=post_id)
    instance = get_object_or_404(Post, pk=post_id)
    form = NewPost(instance=instance)
    context = {'form': form, 'post': post}
    if request.method == 'POST':
        user = request.user
        instance.delete()
        return redirect('blog:profile', username=user.username)
    return render(request, 'blog/create.html', context)


@login_required
def delete_comment(request, post_id, comment_id):
    user = request.user
    instance = get_object_or_404(Comment, pk=comment_id, author=user.id)
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context={'comment': instance})
