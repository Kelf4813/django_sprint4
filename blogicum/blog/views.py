from django.contrib.auth import get_user_model
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect, render

from blog import constants
from .forms import AddComment, NewPost, ProfileEdit
from .models import Category, Comment, Post
from .moduls import annotate_comments, filter_posts, filter_posts_time

User = get_user_model()


def index(request):
    posts = annotate_comments(filter_posts_time(Post.objects)).order_by(
        '-pub_date')
    paginator = Paginator(posts, constants.POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(
        request,
        template_name=constants.BLOG_INDEX,
        context={'page_obj': page_obj})


def post_detail(request, post_id):
    post = get_object_or_404(Post.objects.filter((Q(is_published=True) & Q(
        category__is_published=True)) | Q(author=request.user.id)), id=post_id)
    comments = post.comment.all().order_by('created_at')
    form = AddComment(
        request.POST or None,
        files=request.FILES or None
    )
    if form.is_valid():
        instance = form.save(commit=False)
        instance.post_id = post_id
        instance.save()
        return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)
    return render(
        request,
        template_name=constants.BLOG_DETAIL,
        context={'post': post, 'form': form, 'comments': comments})


def category_posts(request, category_slug):
    category = get_object_or_404(Category, slug=category_slug,
                                 is_published=True)
    post_list = annotate_comments(
        filter_posts_time(category.category.all())).order_by('-pub_date')
    paginator = Paginator(post_list, constants.POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, template_name=constants.BLOG_CATEGORY,
                  context={'category': category, 'page_obj': page_obj})


def profile(request, username):
    profile = get_object_or_404(User, username=username)
    posts = annotate_comments(profile.author.all()).order_by('-pub_date')
    if username != request.user.username:
        posts = filter_posts_time(posts).order_by('-pub_date')
    paginator = Paginator(posts, constants.POSTS_LIMIT)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    return render(request, template_name=constants.BLOG_PROFILE,
                  context={'page_obj': page_obj, 'profile': profile})


@login_required
def edit_profile(request):
    user = request.user
    form = ProfileEdit(instance=user)
    if request.method == 'POST':
        form = ProfileEdit(request.POST, instance=user)
        if form.is_valid():
            form.save()
            return redirect(constants.BLOG_PROFILE_NAME,
                            username=user.username)

    return render(request, constants.BLOG_USER, context={'form': form})


@login_required
def create_post(request, post_id=None):
    user = request.user
    if post_id is not None:
        instance = get_object_or_404(Post, id=post_id)
        if instance.author.username != user.username:
            return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)
    else:
        instance = None
    form = NewPost(request.POST or None,
                   files=request.FILES or None,
                   instance=instance)
    if form.is_valid():
        instance = form.save(commit=False)
        instance.author = request.user
        instance.save()
        return redirect(constants.BLOG_PROFILE_NAME, username=user.username)
    return render(request, constants.BLOG_CREATE, context={'form': form})


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
            return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)
        return render(request, constants.BLOG_COMMENT,
                      context={'form': form, 'comment': instance})


@login_required
def delete_post(request, post_id):
    post = get_object_or_404(filter_posts(Post.objects), id=post_id)
    instance = get_object_or_404(Post, pk=post_id)
    form = NewPost(instance=instance)
    if instance.author.username != request.user.username:
        return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)
    if request.method == 'POST':
        instance.delete()
        return redirect(constants.BLOG_PROFILE_NAME,
                        username=request.user.username)
    return render(request, constants.BLOG_CREATE,
                  context={'form': form, 'post': post})


@login_required
def delete_comment(request, post_id, comment_id):
    instance = get_object_or_404(Comment, pk=comment_id,
                                 author=request.user.id)
    if request.method == 'POST':
        instance.delete()
        return redirect(constants.BLOG_POST_DETAIL, post_id=post_id)
    return render(request, constants.BLOG_COMMENT,
                  context={'comment': instance})
