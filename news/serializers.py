"""Define serializers for news application API data."""
from rest_framework import serializers

from .models import Article, Newsletter, Publisher, User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for displaying user information."""

    class Meta:
        """Define the user fields exposed by the API."""
        model = User
        fields = [
            "id",
            "username",
            "role",
            "publisher_subscriptions",
            "journalist_subscriptions",
        ]
        read_only_fields = fields


class PublisherSerializer(serializers.ModelSerializer):
    """Serializer for displaying publisher information."""

    class Meta:
        """Define the publisher fields exposed by the API."""
        model = Publisher
        fields = [
            "id",
            "name",
            "description",
            "editors",
            "journalists",
        ]
        read_only_fields = fields


class ArticleSerializer(serializers.ModelSerializer):
    """Serializer for creating and displaying news articles."""

    author = serializers.PrimaryKeyRelatedField(read_only=True)

    publisher = serializers.PrimaryKeyRelatedField(
        queryset=Publisher.objects.all(),
        allow_null=True,
        required=False,
    )

    approved = serializers.BooleanField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        """Define the article fields and read-only API fields."""
        model = Article
        fields = [
            "id",
            "title",
            "content",
            "author",
            "publisher",
            "created_at",
            "approved",
        ]
        read_only_fields = ["id", "author", "created_at", "approved"]

    def validate_publisher(self, publisher):
        """
        Ensure journalists only use publishers they are
        associated with.
        """
        request = self.context.get("request")

        if (
            request
            and request.user.role == User.Role.JOURNALIST
            and publisher is not None
            and not publisher.journalists.filter(
                pk=request.user.pk
            ).exists()
        ):
            raise serializers.ValidationError(
                "You can only select publishers you are associated with."
            )

        return publisher


class NewsletterSerializer(serializers.ModelSerializer):
    """Serializer for creating and displaying newsletters."""

    author = serializers.PrimaryKeyRelatedField(read_only=True)

    articles = serializers.PrimaryKeyRelatedField(
        queryset=Article.objects.filter(approved=True),
        many=True,
        required=False,
    )

    created_at = serializers.DateTimeField(read_only=True)

    class Meta:
        """Define the newsletter fields and read-only API fields."""
        model = Newsletter
        fields = [
            "id",
            "title",
            "description",
            "author",
            "articles",
            "created_at",
        ]
        read_only_fields = ["id", "author", "created_at"]

    def validate(self, data):
        """Ensure only journalists and editors can create newsletters."""
        request = self.context.get("request")

        if request and request.user.role not in [
            User.Role.JOURNALIST,
            User.Role.EDITOR,
        ]:
            raise serializers.ValidationError(
                "Only journalists and editors can create newsletters."
            )

        return data

