"""Provide API views for articles, newsletters and approval webhooks."""
import requests
from .services import notify_article_approved
from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q
from django.shortcuts import get_object_or_404

from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Article, Newsletter, User
from .permissions import (
    IsEditor,
    IsJournalist,
    IsReader,
    IsOwnerOrEditor,
    IsEditorOrJournalist,
)
from .serializers import ArticleSerializer, NewsletterSerializer


class ArticleListCreateAPIView(generics.ListCreateAPIView):
    """List approved articles or allow journalists to create articles."""

    serializer_class = ArticleSerializer

    def get_queryset(self):
        """Return approved articles ordered from newest to oldest."""
        return Article.objects.filter(
            approved=True
        ).select_related("author", "publisher").order_by("-created_at")

    def get_permissions(self):
        """Allow journalists to create articles and authenticated users to list them."""
        if self.request.method == "POST":
            return [IsJournalist()]

        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Save the new article with the authenticated user as its author."""
        serializer.save(author=self.request.user)


class SubscribedArticlesAPIView(generics.ListAPIView):
    """Return approved articles from a reader's subscriptions."""

    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, IsReader]

    def get_queryset(self):
        """Return approved articles from the reader's subscriptions."""
        reader = self.request.user

        return Article.objects.filter(
            approved=True
        ).filter(
            Q(publisher__in=reader.publisher_subscriptions.all())
            | Q(author__in=reader.journalist_subscriptions.all())
        ).select_related(
            "author", "publisher"
        ).distinct().order_by("-created_at")


class ArticleDetailAPIView(
    generics.RetrieveUpdateDestroyAPIView
):
    """Retrieve, update or delete an article according to user role."""

    serializer_class = ArticleSerializer

    def get_permissions(self):
        """Apply permissions according to the requested HTTP method."""
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [IsAuthenticated()]

        return [IsOwnerOrEditor()]

    def get_queryset(self):
        """Return articles the current user is permitted to access."""
        user = self.request.user

        if not user.is_authenticated:
            return Article.objects.none()

        if user.role == "EDITOR":
            return Article.objects.all()

        if user.role == "JOURNALIST":
            if self.request.method in ["GET", "HEAD", "OPTIONS"]:
                return Article.objects.filter(
                    Q(approved=True) | Q(author=user)
                )

            return Article.objects.filter(author=user)

        return Article.objects.filter(approved=True)

class ArticleApprovalAPIView(APIView):
    """Allow editors to approve articles and notify subscribers."""

    permission_classes = [IsEditor]

    def post(self, request, pk):
        """Approve an article and notify its subscribers."""
        article = get_object_or_404(Article, pk=pk)

        if article.approved:
            return Response(
                {"detail": "This article is already approved."},
                status=400,
            )

        article.approved = True
        article.save(update_fields=["approved"])

        notification_results = notify_article_approved(
            article,
            request.auth.key,
        )

        serializer = ArticleSerializer(article)

        return Response(
            {
                "article": serializer.data,
                **notification_results,
            },
            status=200,
        )

class ApprovedArticleWebhookAPIView(APIView):
    """Receive confirmation of an approved article."""

    permission_classes = [IsEditor]

    def post(self, request):
        """Confirm receipt of an approved article webhook."""
        article_id = request.data.get("article_id")

        if not article_id:
            return Response(
                {"detail": "Article ID is required."},
                status=400,
            )

        article = get_object_or_404(Article, pk=article_id)

        if not article.approved:
            return Response(
                {"detail": "The article has not been approved."},
                status=400,
            )

        return Response(
            {
                "received": True,
                "article_id": article.id,
                "title": article.title,
                "approved": article.approved,
            },
            status=200,
        )



class NewsletterListCreateAPIView(generics.ListCreateAPIView):
    """List newsletters or allow editors and journalists to create them."""

    serializer_class = NewsletterSerializer

    def get_queryset(self):
        """Return newsletters ordered from newest to oldest."""
        return Newsletter.objects.select_related(
            "author"
        ).prefetch_related(
            "articles"
        ).order_by("-created_at")

    def get_permissions(self):
        """Allow editors and journalists to create newsletters."""
        if self.request.method == "POST":
            return [IsEditorOrJournalist()]
        return [IsAuthenticated()]

    def perform_create(self, serializer):
        """Save the newsletter with the authenticated user as its author."""
        serializer.save(author=self.request.user)


class NewsletterDetailAPIView(generics.RetrieveUpdateDestroyAPIView):
    """Retrieve, update or delete newsletters according to user role."""

    serializer_class = NewsletterSerializer

    def get_permissions(self):
        """Apply permissions according to the requested HTTP method."""
        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return [IsAuthenticated()]
        return [IsOwnerOrEditor()]

    def get_queryset(self):
        """Return newsletters the current user is permitted to access."""
        user = self.request.user

        if not user.is_authenticated:
            return Newsletter.objects.none()

        if user.role == User.Role.EDITOR:
            return Newsletter.objects.all()

        if user.role == User.Role.JOURNALIST:
            if self.request.method in ["GET", "HEAD", "OPTIONS"]:
                return Newsletter.objects.all()
            return Newsletter.objects.filter(author=user)

        if self.request.method in ["GET", "HEAD", "OPTIONS"]:
            return Newsletter.objects.all()

        return Newsletter.objects.none()
