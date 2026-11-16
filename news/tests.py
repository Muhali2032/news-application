from unittest.mock import Mock, patch

from django.test import TestCase
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Article, Newsletter, User


class NewsAPITests(TestCase):
    """Test article access, role permissions and approval notifications."""

    def setUp(self):
        self.client = APIClient()

        self.reader = User.objects.create_user(
            username="test_reader",
            password="TestPassword123",
            role=User.Role.READER,
            email="reader@example.com",
        )

        self.journalist = User.objects.create_user(
            username="test_journalist",
            password="TestPassword123",
            role=User.Role.JOURNALIST,
        )

        self.other_journalist = User.objects.create_user(
            username="other_journalist",
            password="TestPassword123",
            role=User.Role.JOURNALIST,
        )

        self.editor = User.objects.create_user(
            username="test_editor",
            password="TestPassword123",
            role=User.Role.EDITOR,
        )

        self.approved_article = Article.objects.create(
            title="Approved Test Article",
            content="This article is approved.",
            author=self.journalist,
            approved=True,
        )

        self.pending_article = Article.objects.create(
            title="Pending Test Article",
            content="This article is awaiting approval.",
            author=self.journalist,
            approved=False,
        )

    def test_reader_only_sees_approved_articles(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.get("/api/articles/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.approved_article.id,
        )

    def test_reader_cannot_create_article(self):
        self.client.force_authenticate(user=self.reader)

        response = self.client.post(
            "/api/articles/",
            {
                "title": "Reader Article",
                "content": "Readers cannot publish articles.",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_403_FORBIDDEN,
        )

    def test_journalist_can_create_article(self):
        self.client.force_authenticate(user=self.journalist)

        response = self.client.post(
            "/api/articles/",
            {
                "title": "New Journalist Article",
                "content": "This article was created through the API.",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(response.data["author"], self.journalist.id)
        self.assertFalse(response.data["approved"])

    def test_reader_only_receives_subscribed_articles(self):
        self.reader.journalist_subscriptions.add(self.journalist)

        self.client.force_authenticate(user=self.reader)

        Article.objects.create(
            title="Another Journalist Article",
            content="This journalist is not subscribed to.",
            author=self.other_journalist,
            approved=True,
        )

        response = self.client.get("/api/articles/subscribed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["author"],
            self.journalist.id,
        )

    def test_journalist_cannot_edit_another_journalists_article(self):
        self.client.force_authenticate(user=self.other_journalist)

        response = self.client.put(
            f"/api/articles/{self.approved_article.id}/",
            {
                "title": "Unauthorised Edit",
                "content": "This edit should not be allowed.",
            },
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_404_NOT_FOUND,
        )

    @patch("news.api_views.requests.post")
    @patch("news.api_views.send_mail")
    def test_editor_approval_sends_notifications(
        self,
        mock_send_mail,
        mock_requests_post,
    ):
        self.reader.journalist_subscriptions.add(self.journalist)

        token = Token.objects.create(user=self.editor)
        self.client.credentials(
            HTTP_AUTHORIZATION=f"Token {token.key}"
        )

        mock_send_mail.return_value = 1

        mock_webhook_response = Mock()
        mock_webhook_response.raise_for_status.return_value = None
        mock_requests_post.return_value = mock_webhook_response

        response = self.client.post(
            f"/api/articles/{self.pending_article.id}/approve/"
        )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["article"]["approved"])
        self.assertEqual(response.data["notification_emails_sent"], 1)
        self.assertIsNone(response.data["email_error"])
        self.assertTrue(response.data["webhook_sent"])
        self.assertIsNone(response.data["webhook_error"])

        mock_send_mail.assert_called_once()
        self.assertIn(
            "reader@example.com",
            mock_send_mail.call_args.kwargs["recipient_list"],
        )

        mock_requests_post.assert_called_once()

    def test_webhook_rejects_unapproved_article(self):
        self.client.force_authenticate(user=self.editor)

        response = self.client.post(
            "/api/approved/",
            {"article_id": self.pending_article.id},
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_editor_can_delete_article(self):
        self.client.force_authenticate(user=self.editor)

        response = self.client.delete(
            f"/api/articles/{self.approved_article.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_204_NO_CONTENT,
        )
        self.assertFalse(
            Article.objects.filter(
                id=self.approved_article.id
            ).exists()
        )


    def test_journalist_can_create_newsletter(self):
        self.client.force_authenticate(user=self.journalist)
        response = self.client.post(
            "/api/newsletters/",
            {
                "title": "Weekly News",
                "description": "A weekly news update.",
                "articles": [self.approved_article.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], self.journalist.id)

    def test_editor_can_create_newsletter(self):
        self.client.force_authenticate(user=self.editor)
        response = self.client.post(
            "/api/newsletters/",
            {
                "title": "Editor's Newsletter",
                "description": "An editorial news update.",
                "articles": [self.approved_article.id],
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data["author"], self.editor.id)

    def test_reader_cannot_create_newsletter(self):
        self.client.force_authenticate(user=self.reader)
        response = self.client.post(
            "/api/newsletters/",
            {
                "title": "Reader Newsletter",
                "description": "This should not be allowed.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_reader_can_view_newsletters(self):
        newsletter = Newsletter.objects.create(
            title="Public Newsletter",
            description="A newsletter for readers.",
            author=self.journalist,
        )
        self.client.force_authenticate(user=self.reader)
        response = self.client.get("/api/newsletters/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(response.data[0]["id"], newsletter.id)

    def test_journalist_cannot_edit_another_journalists_newsletter(self):
        newsletter = Newsletter.objects.create(
            title="Another Journalist's Newsletter",
            description="Owned by another journalist.",
            author=self.journalist,
        )
        self.client.force_authenticate(user=self.other_journalist)
        response = self.client.put(
            f"/api/newsletters/{newsletter.id}/",
            {
                "title": "Unauthorised Change",
                "description": "This edit should be blocked.",
            },
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_editor_can_edit_another_journalists_newsletter(self):
        newsletter = Newsletter.objects.create(
            title="Journalist Newsletter",
            description="Original description.",
            author=self.journalist,
        )
        self.client.force_authenticate(user=self.editor)
        response = self.client.patch(
            f"/api/newsletters/{newsletter.id}/",
            {"title": "Editor's Updated Title"},
            format="json",
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        newsletter.refresh_from_db()
        self.assertEqual(newsletter.title, "Editor's Updated Title")
