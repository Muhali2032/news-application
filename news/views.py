from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect

from .models import Article, Newsletter
from .forms import ArticleForm, NewsletterForm


def has_role(user, *roles):
    return user.is_authenticated and user.role in roles


def article_list(request):
    articles = Article.objects.filter(approved=True).order_by(
        "-created_at"
    )
    return render(request, "news/article_list.html", {
        "articles": articles
    })


def article_detail(request, pk):
    article = get_object_or_404(
        Article.objects.filter(approved=True), pk=pk
    )
    return render(request, "news/article_detail.html", {
        "article": article
    })

@login_required
def article_create(request):
    if not has_role(request.user, "JOURNALIST"):
        raise PermissionDenied

    form = ArticleForm(request.POST or None)

    # Assign the author before Django validates the form.
    form.instance.author = request.user

    if form.is_valid():
        article = form.save(commit=False)
        article.author = request.user
        article.full_clean()
        article.save()

        messages.success(
            request,
            "Article submitted for approval."
        )
        return redirect("article_list")

    return render(request, "news/article_form.html", {
        "form": form
    })


@login_required
def article_update(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if not has_role(request.user, "JOURNALIST", "EDITOR"):
        raise PermissionDenied

    if request.user.role == "JOURNALIST" and article.author != request.user:
        raise PermissionDenied

    form = ArticleForm(request.POST or None, instance=article)

    if form.is_valid():
        updated_article = form.save(commit=False)
        updated_article.full_clean()
        updated_article.save()
        messages.success(request, "Article updated successfully.")
        return redirect("article_list")

    return render(request, "news/article_form.html", {
        "form": form
    })


@login_required
def article_delete(request, pk):
    article = get_object_or_404(Article, pk=pk)

    if not has_role(request.user, "JOURNALIST", "EDITOR"):
        raise PermissionDenied

    if request.user.role == "JOURNALIST" and article.author != request.user:
        raise PermissionDenied

    if request.method == "POST":
        article.delete()
        messages.success(request, "Article deleted successfully.")
        return redirect("article_list")

    return render(request, "news/article_confirm_delete.html", {
        "article": article
    })


@login_required
def article_approve(request, pk):
    if not has_role(request.user, "EDITOR"):
        raise PermissionDenied

    article = get_object_or_404(Article, pk=pk)

    if request.method == "POST":
        article.approved = True
        article.save(update_fields=["approved"])
        messages.success(request, "Article approved successfully.")
        return redirect("article_list")

    return render(request, "news/article_approve.html", {
        "article": article
    })


def newsletter_list(request):
    newsletters = Newsletter.objects.all().order_by("-created_at")
    return render(request, "news/newsletter_list.html", {
        "newsletters": newsletters
    })


@login_required
def newsletter_create(request):
    if not has_role(request.user, "JOURNALIST", "EDITOR"):
        raise PermissionDenied

    form = NewsletterForm(request.POST or None)

    if form.is_valid():
        newsletter = form.save(commit=False)
        newsletter.author = request.user
        newsletter.full_clean()
        newsletter.save()
        form.save_m2m()
        messages.success(request, "Newsletter created successfully.")
        return redirect("newsletter_list")

    return render(request, "news/newsletter_form.html", {
        "form": form
    })


@login_required
def newsletter_update(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if not has_role(request.user, "JOURNALIST", "EDITOR"):
        raise PermissionDenied

    if request.user.role == "JOURNALIST" and newsletter.author != request.user:
        raise PermissionDenied

    form = NewsletterForm(request.POST or None, instance=newsletter)

    if form.is_valid():
        updated_newsletter = form.save(commit=False)
        updated_newsletter.full_clean()
        updated_newsletter.save()
        form.save_m2m()
        messages.success(request, "Newsletter updated successfully.")
        return redirect("newsletter_list")

    return render(request, "news/newsletter_form.html", {
        "form": form
    })


def newsletter_detail(request, pk):
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(request, "news/newsletter_detail.html", {
        "newsletter": newsletter
    })
@login_required
def pending_articles(request):
    if not has_role(request.user, "EDITOR"):
        raise PermissionDenied

    articles = Article.objects.filter(
        approved=False
    ).order_by("-created_at")

    return render(request, "news/pending_articles.html", {
        "articles": articles
    })
