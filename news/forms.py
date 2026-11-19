from django import forms
from django.contrib.auth.forms import UserCreationForm

from .models import Article, Newsletter, Publisher, User


class UserRegistrationForm(UserCreationForm):
    """Form for registering new readers."""

    class Meta:
        model = User
        fields = ["username", "email", "first_name", "last_name"]


class ArticleForm(forms.ModelForm):
    """Form for creating and updating news articles."""

    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)

        if user and user.role == User.Role.EDITOR:
            self.fields["publisher"].queryset = Publisher.objects.all()

        elif user and user.role == User.Role.JOURNALIST:
            self.fields["publisher"].queryset = Publisher.objects.filter(
                journalists=user
            )

        else:
            self.fields["publisher"].queryset = Publisher.objects.none()

    class Meta:
        model = Article
        fields = ["title", "content", "publisher"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "content": forms.Textarea(
                attrs={"class": "form-control", "rows": 8}
            ),
            "publisher": forms.Select(
                attrs={"class": "form-control"}
            ),
        }


class NewsletterForm(forms.ModelForm):
    """Form for creating and updating newsletters."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["articles"].queryset = Article.objects.filter(
            approved=True
        ).order_by("-created_at")

    class Meta:
        model = Newsletter
        fields = ["title", "description", "articles"]
        widgets = {
            "title": forms.TextInput(
                attrs={"class": "form-control"}
            ),
            "description": forms.Textarea(
                attrs={"class": "form-control", "rows": 5}
            ),
            "articles": forms.SelectMultiple(
                attrs={"class": "form-control"}
            ),
        }
