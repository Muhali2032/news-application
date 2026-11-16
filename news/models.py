
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    """Custom user model supporting readers, editors and journalists."""

    class Role(models.TextChoices):
        READER = "READER", "Reader"
        EDITOR = "EDITOR", "Editor"
        JOURNALIST = "JOURNALIST", "Journalist"

    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.READER
    )

    publisher_subscriptions = models.ManyToManyField(
        "Publisher",
        blank=True,
        related_name="subscribed_readers"
    )

    journalist_subscriptions = models.ManyToManyField(
        "self",
        symmetrical=False,
        blank=True,
        related_name="subscribed_by"
    )

    def __str__(self):
        return f"{self.username} ({self.get_role_display()})"


class Publisher(models.Model):
    """A publication managed by editors and associated journalists."""

    name = models.CharField(max_length=150, unique=True)
    description = models.TextField(blank=True)

    editors = models.ManyToManyField(
        User,
        blank=True,
        related_name="managed_publishers"
    )

    journalists = models.ManyToManyField(
        User,
        blank=True,
        related_name="associated_publishers"
    )

    def __str__(self):
        return self.name


class Article(models.Model):
    """An article belonging to an independent journalist or publisher."""

    title = models.CharField(max_length=200)
    content = models.TextField()

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="articles"
    )

    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="articles"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    approved = models.BooleanField(default=False)

    def clean(self):
        if self.author.role != User.Role.JOURNALIST:
            raise ValidationError(
                "An article author must be a journalist."
            )

    def __str__(self):
        return self.title


class Newsletter(models.Model):
    """A curated collection of articles managed by journalists and editors."""

    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="newsletters"
    )

    articles = models.ManyToManyField(
        Article,
        blank=True,
        related_name="newsletters"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def clean(self):
        if self.author.role not in [
            User.Role.JOURNALIST,
            User.Role.EDITOR
        ]:
            raise ValidationError(
                "Only journalists and editors can create newsletters."
            )

    def __str__(self):
        return self.title

    