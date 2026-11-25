"""Define URL routes for the news application API."""
from django.urls import path
from rest_framework.authtoken.views import obtain_auth_token

from . import api_views


urlpatterns = [
    path(
        "token/",
        obtain_auth_token,
        name="api_token",
    ),
    path(
        "articles/",
        api_views.ArticleListCreateAPIView.as_view(),
        name="api_article_list_create",
    ),
    path(
        "articles/subscribed/",
        api_views.SubscribedArticlesAPIView.as_view(),
        name="api_subscribed_articles",
    ),
    path(
        "articles/<int:pk>/",
        api_views.ArticleDetailAPIView.as_view(),
        name="api_article_detail",
    ),
    path(
        "articles/<int:pk>/approve/",
        api_views.ArticleApprovalAPIView.as_view(),
        name="api_article_approve",
    ),
    path(
        "newsletters/",
        api_views.NewsletterListCreateAPIView.as_view(),
        name="api_newsletter_list_create",
    ),
    path(
        "newsletters/<int:pk>/",
        api_views.NewsletterDetailAPIView.as_view(),
        name="api_newsletter_detail",
    ),
    path(
        "approved/",
        api_views.ApprovedArticleWebhookAPIView.as_view(),
        name="api_approved_webhook",
    ),
]
