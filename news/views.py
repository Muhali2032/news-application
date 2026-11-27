"""Provide website views for news articles and newsletters."""
from rest_framework.authtoken.models import Token
from .services import notify_article_approved
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import PermissionDenied
from django.shortcuts import render, get_object_or_404, redirect

from django.db.models import Q

from .models import Article, Newsletter, Publisher, User
from .forms import (
    ArticleForm,
    NewsletterForm,
    PublisherForm,
    ReaderSubscriptionForm,
    UserRegistrationForm,
)


def has_role(user, *roles):
    """Check whether an authenticated user has one of the specified roles."""
    return user.is_authenticated and user.role in roles


def register(request):
    """Register a new reader account."""

    if request.user.is_authenticated:
        return redirect("article_list")

    if request.method == "POST":
        form = UserRegistrationForm(request.POST)

        if form.is_valid():
            form.save()
            messages.success(
                request,
                "Registration successful. Please log in."
            )
            return redirect("login")
    else:
        form = UserRegistrationForm()

    return render(
        request,
        "registration/registration.html",
        {"form": form}
        )


def article_list(request):
    """Display approved articles in newest-first order."""
    articles = Article.objects.filter(approved=True).order_by(
        "-created_at"
    )
    return render(request, "news/article_list.html", {
        "articles": articles
    })


def article_detail(request, pk):
    """Display the details of an approved article."""
    article = get_object_or_404(
        Article.objects.filter(approved=True), pk=pk
    )
    return render(request, "news/article_detail.html", {
        "article": article
    })


@login_required
def article_create(request):
    """Allow journalists to publish independent articles or submit publisher articles."""
    if not has_role(request.user, User.Role.JOURNALIST):
        raise PermissionDenied

    form = ArticleForm(request.POST or None, user=request.user)
    form.instance.author = request.user

    if request.method == "POST" and form.is_valid():
        article = form.save(commit=False)
        article.author = request.user

        # Independent articles can be published by their journalist.
        # Publisher articles must remain pending for editor approval.
        article.approved = article.publisher_id is None

        article.full_clean()
        article.save()

        if article.approved:
            token, created = Token.objects.get_or_create(
                user=request.user
            )
            results = notify_article_approved(article, token.key)

            if results["email_error"] or results["webhook_error"]:
                messages.warning(
                    request,
                    "Your article was published, but one or more notifications failed.",
                )
            else:
                messages.success(
                    request,
                    "Your independent article has been published.",
                )
        else:
            messages.success(
                request,
                "Your article has been submitted for editor approval.",
            )

        return redirect("article_list")

    return render(
        request,
        "news/article_form.html",
        {"form": form},
    )


@login_required
def article_update(request, pk):
    """Allow authorised users to update an article."""
    article = get_object_or_404(Article, pk=pk)

    if not has_role(request.user, "JOURNALIST", "EDITOR"):
        raise PermissionDenied

    if request.user.role == "JOURNALIST" and article.author != request.user:
        raise PermissionDenied

    form = ArticleForm(
        request.POST or None,
        instance=article,
        user=request.user,
        )

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
    """Allow authorised users to delete an article."""
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
    """Allow editors to approve articles and process notifications."""
    if not has_role(request.user, "EDITOR"):
        raise PermissionDenied

    article = get_object_or_404(Article, pk=pk)

    if article.approved:
        messages.info(request, "This article is already approved.")
        return redirect("article_list")

    if request.method == "POST":
        article.approved = True
        article.save(update_fields=["approved"])

        # Obtain the editor's API token for the internal webhook.
        token, created = Token.objects.get_or_create(
            user=request.user
        )

        # Send subscriber notifications and call the webhook.
        results = notify_article_approved(
            article,
            token.key,
        )

        if results["email_error"]:
            messages.warning(
                request,
                "The article was approved, but email notification failed."
            )

        if results["webhook_error"]:
            messages.warning(
                request,
                "The article was approved, but the internal webhook failed."
            )

        if not results["email_error"] and not results["webhook_error"]:
            messages.success(
                request,
                "Article approved and notifications processed successfully."
            )

        return redirect("article_list")

    return render(
        request,
        "news/article_approve.html",
        {"article": article}
    )


def newsletter_list(request):
    """Display newsletters in newest-first order."""
    newsletters = Newsletter.objects.all().order_by("-created_at")
    return render(request, "news/newsletter_list.html", {
        "newsletters": newsletters
    })


@login_required
def newsletter_create(request):
    """Allow journalists and editors to create newsletters."""
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
    """Allow authorised users to update newsletters."""
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


@login_required
def newsletter_delete(request, pk):
    """Allow authorised users to delete newsletters."""
    newsletter = get_object_or_404(Newsletter, pk=pk)

    if not has_role(request.user, "JOURNALIST", "EDITOR"):
        raise PermissionDenied

    if (
        request.user.role == "JOURNALIST"
        and newsletter.author != request.user
    ):
        raise PermissionDenied

    if request.method == "POST":
        newsletter.delete()
        messages.success(
            request,
            "Newsletter deleted successfully."
        )
        return redirect("newsletter_list")

    return render(
        request,
        "news/newsletter_confirm_delete.html",
        {"newsletter": newsletter},
    )


def newsletter_detail(request, pk):
    """Display the details of a newsletter."""
    newsletter = get_object_or_404(Newsletter, pk=pk)
    return render(request, "news/newsletter_detail.html", {
        "newsletter": newsletter
    })


@login_required
def pending_articles(request):
    """Display pending articles to authorised editors."""
    if not has_role(request.user, "EDITOR"):
        raise PermissionDenied

    articles = Article.objects.filter(
        approved=False,
        publisher__isnull=False,
    ).order_by("-created_at")

    return render(request, "news/pending_articles.html", {
        "articles": articles
    })


@login_required
def manage_subscriptions(request):
    """Allow readers to manage journalist and publisher subscriptions."""
    if not has_role(request.user, User.Role.READER):
        raise PermissionDenied

    form = ReaderSubscriptionForm(
        request.POST or None,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save(request.user)
        messages.success(
            request,
            "Your subscriptions have been updated.",
        )
        return redirect("manage_subscriptions")

    return render(
        request,
        "news/manage_subscriptions.html",
        {"form": form},
    )


@login_required
def publisher_list(request):
    """Display publishers for editors to manage."""
    if not has_role(request.user, User.Role.EDITOR):
        raise PermissionDenied

    publishers = Publisher.objects.prefetch_related(
        "editors",
        "journalists",
    ).order_by("name")

    return render(
        request,
        "news/publisher_list.html",
        {"publishers": publishers},
    )


@login_required
def publisher_create(request):
    """Allow editors to create publishers and assign members."""
    if not has_role(request.user, User.Role.EDITOR):
        raise PermissionDenied

    form = PublisherForm(request.POST or None, user=request.user)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Publisher created successfully.")
        return redirect("publisher_list")

    return render(
        request,
        "news/publisher_form.html",
        {"form": form, "title": "Create Publisher"},
    )


@login_required
def publisher_update(request, pk):
    """Allow editors to update publishers and manage their members."""
    if not has_role(request.user, User.Role.EDITOR):
        raise PermissionDenied

    publisher = get_object_or_404(Publisher, pk=pk)
    form = PublisherForm(
        request.POST or None,
        instance=publisher,
        user=request.user,
    )

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Publisher updated successfully.")
        return redirect("publisher_list")

    return render(
        request,
        "news/publisher_form.html",
        {"form": form, "title": "Edit Publisher"},
    )


@login_required
def subscribed_articles(request):
    """Display approved articles from the reader's subscriptions."""
    if not has_role(request.user, User.Role.READER):
        raise PermissionDenied

    articles = Article.objects.filter(
        approved=True
    ).filter(
        Q(
            publisher__in=request.user.publisher_subscriptions.all()
        )
        | Q(
            author__in=request.user.journalist_subscriptions.all()
        )
    ).select_related(
        "author",
        "publisher",
    ).distinct().order_by("-created_at")

    return render(
        request,
        "news/subscribed_articles.html",
        {"articles": articles},
    )
