from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from .forms import AddComment, NewPost, ProfileEdit
from .models import Category, Comment, Post
from .func import filter_posts

User = get_user_model()

POSTS_LIMIT = 10


def index(request):
    posts = Post.objects.filter(pub_date__lte=timezone.now(),
                                is_published=True,
                                category__is_published=True).annotate(
        comment_count=Count('comment')).order_by('-pub_date')
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        template_name='blog/index.html',
        context={'page_obj': page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.filter((Q(is_published=True) & Q(
        category__is_published=True)) | Q(author=request.user.id)), id=post_id)
    comments = post.comment.all()
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
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    post_list = filter_posts(Post.objects).filter(
        category=category, is_published=True,
        ub_date__lte=timezone.now()).annotate(
        comment_count=Count('comment')).order_by('-pub_date')
    paginator = Paginator(post_list, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, template_name='blog/category.html',
                  context={'category': category, 'page_obj': page_obj})


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    posts = Post.objects.filter(author=profile.id).annotate(
        comment_count=Count('comment')).order_by('-pub_date')
    if username != request.user.username:
        posts = (
            posts.filter(pub_date__lte=timezone.now(),
                         is_published=True).order_by(
                '-pub_date'))
    paginator = Paginator(posts, POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, template_name='blog/profile.html',
                  context={'page_obj': page_obj, 'profile': profile})


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
    user = request.user
    if post_id is not None:
        instance = get_object_or_404(Post, id=post_id)
        if instance.author.username != user.username:
            return redirect('blog:post_detail', post_id=post_id)
    else:
        instance = None
    form = NewPost(request.POST or None,
                   files=request.FILES or None,
                   instance=instance)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = request.user
        instance.save()
        return redirect('blog:profile', username=user.username)
    return render(request, 'blog/create.html', context={'form': form})


@login_required
def add_comment(request, post_id, comment_id=None):
    post = get_object_or_404(Post, id=post_id)
    if post:
        if comment_id is not None:
            instance = get_object_or_404(Comment, id=comment_id,
                                         author=request.user.id)
        else:
            instance = None
        form = AddComment(request.POST or None, instance=instance)
        if form.is_valid():
            instance = form.save(commit=False)
            instance.author = request.user
            instance.post_id = post_id
            instance.save()
            return redirect('blog:post_detail', post_id=post_id)
        return render(request, 'blog/comment.html',
                      context={'form': form, 'comment': instance})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(filter_posts(Post.objects), id=post_id)
    instance = get_object_or_404(Post, pk=post_id)
    form = NewPost(instance=instance)
    if instance.author.username != request.user.username:
        return redirect('blog:post_detail', post_id=post_id)
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:profile', username=request.user.username)
    return render(request, 'blog/create.html',
                  context={'form': form, 'post': post})


@login_required
def delete_comment(request, post_id, comment_id):
    instance = get_object_or_404(Comment, pk=comment_id,
                                 author=request.user.id)
    if request.method == 'POST':
        instance.delete()
        return redirect('blog:post_detail', post_id=post_id)
    return render(request, 'blog/comment.html', context={'comment': instance})
