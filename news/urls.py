from django.urls import path

from . import views


urlpatterns = [
    path("", views.article_list, name="article_list"),
    path(
        "articles/pending/",
        views.pending_articles,
        name="pending_articles",
    ),
    path(
        "articles/<int:pk>/",
        views.article_detail,
        name="article_detail",
    ),
    path(
        "articles/create/",
        views.article_create,
        name="article_create",
    ),
    path(
        "articles/<int:pk>/edit/",
        views.article_update,
        name="article_update",
    ),
    path(
        "articles/<int:pk>/delete/",
        views.article_delete,
        name="article_delete",
    ),
    path(
        "articles/<int:pk>/approve/",
        views.article_approve,
        name="article_approve",
    ),
    path(
        "newsletters/",
        views.newsletter_list,
        name="newsletter_list",
    ),
    path(
        "newsletters/create/",
        views.newsletter_create,
        name="newsletter_create",
    ),
    path(
        "newsletters/<int:pk>/",
        views.newsletter_detail,
        name="newsletter_detail",
    ),
    path(
        "newsletters/<int:pk>/edit/",
        views.newsletter_update,
        name="newsletter_update",
    ),
]
