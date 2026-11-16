
from rest_framework import serializers

from .models import Article, Newsletter, Publisher, User


class UserSerializer(serializers.ModelSerializer):
    """Serializer for displaying user information."""

    class Meta:
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
        request = self.context.get("request")

        if request and request.user.role not in [
            User.Role.JOURNALIST,
            User.Role.EDITOR,
        ]:
            raise serializers.ValidationError(
                "Only journalists and editors can create newsletters."
            )

        return data

