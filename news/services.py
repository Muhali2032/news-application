"""Provide notification services for approved news articles."""
import requests

from django.conf import settings
from django.core.mail import send_mail
from django.db.models import Q

from .models import User


def notify_article_approved(article, token_key):
    """
    Notify readers and call the internal API after article approval.
    """

    # Find readers subscribed to the journalist or publisher.
    subscriber_filter = Q(
        journalist_subscriptions=article.author
    )

    if article.publisher_id:
        subscriber_filter |= Q(
            publisher_subscriptions=article.publisher
        )

    subscribers = User.objects.filter(
        role=User.Role.READER
    ).filter(
        subscriber_filter
    ).exclude(
        email__exact=""
    ).distinct()

    recipient_list = list(
        subscribers.values_list("email", flat=True)
    )

    # Send email notifications.
    email_count = 0
    email_error = None

    if recipient_list:
        try:
            email_count = send_mail(
                subject=f"New approved article: {article.title}",
                message=(
                    f"Hello,\n\n"
                    f"A new article has been approved: "
                    f"{article.title}\n\n"
                    f"Published by: {article.author.username}\n"
                ),
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=recipient_list,
                fail_silently=False,
            )
        except Exception as exc:
            email_error = str(exc)

    # Send a POST request to the internal REST API.
    webhook_sent = False
    webhook_error = None

    try:
        webhook_response = requests.post(
            settings.APPROVED_ARTICLE_WEBHOOK_URL,
            json={
                "article_id": article.id,
                "title": article.title,
            },
            headers={
                "Authorization": f"Token {token_key}",
            },
            timeout=5,
        )

        webhook_response.raise_for_status()
        webhook_sent = True

    except requests.RequestException as exc:
        webhook_error = str(exc)

    return {
        "notification_emails_sent": email_count,
        "email_error": email_error,
        "webhook_sent": webhook_sent,
        "webhook_error": webhook_error,
    }
