from django import forms

from .models import Article, Newsletter


class ArticleForm(forms.ModelForm):
    """Form for creating and updating news articles."""

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
