"""Configure Django admin for the news application."""

from django.contrib import admin

from django.contrib.auth.admin import UserAdmin

from .models import User, Publisher, Article, Newsletter


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    """Configure administration for readers, editors and journalists."""

    list_display = (
        "username",
        "email",
        "role",
        "is_staff",
        "is_active",
    )
    list_filter = ("role", "is_staff", "is_active")
    fieldsets = UserAdmin.fieldsets + (
        ("News Application Details", {
            "fields": (
                "role",
                "publisher_subscriptions",
                "journalist_subscriptions",
            )
        }),
    )
    add_fieldsets = UserAdmin.add_fieldsets + (
        ("News Application Details", {
            "fields": ("role",)
        }),
    )
    filter_horizontal = (
        "groups",
        "user_permissions",
        "publisher_subscriptions",
        "journalist_subscriptions",
    )


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Configure the administration of publishers."""

    list_display = ("name",)
    search_fields = ("name",)
    filter_horizontal = ("editors", "journalists")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Configure the administration of news articles."""

    list_display = (
        "title",
        "author",
        "publisher",
        "approved",
        "created_at",
    )
    list_filter = ("approved", "publisher", "created_at")
    search_fields = ("title", "content", "author__username")


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Configure the administration of newsletters."""

    list_display = ("title", "author", "created_at")
    search_fields = ("title", "description", "author__username")
    filter_horizontal = ("articles",)
