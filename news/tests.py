"""Test news application API access, permissions and notifications."""
from unittest.mock import Mock, patch

from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APIClient

from .models import Article, Newsletter, Publisher, User


class NewsAPITests(TestCase):
    """Test article access, role permissions and approval notifications."""

    def setUp(self):
        """Create test users and articles for API tests."""
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

    def test_unauthenticated_users_cannot_access_protected_api_endpoints(self):
        """Verify that protected API endpoints reject unauthenticated users."""

        get_endpoints = [
            "/api/articles/",
            "/api/articles/subscribed/",
            f"/api/articles/{self.approved_article.id}/",
            "/api/newsletters/",
        ]

        for endpoint in get_endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.get(endpoint)

                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

        post_endpoints = [
            "/api/articles/",
            "/api/newsletters/",
            f"/api/articles/{self.pending_article.id}/approve/",
            "/api/approved/",
        ]

        for endpoint in post_endpoints:
            with self.subTest(endpoint=endpoint):
                response = self.client.post(endpoint, {}, format="json")

                self.assertEqual(
                    response.status_code,
                    status.HTTP_401_UNAUTHORIZED,
                )

    def test_user_can_obtain_api_token(self):
        """Verify that a user can obtain an API authentication token."""
        response = self.client.post(
            "/api/token/",
            {
                "username": "test_reader",
                "password": "TestPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertIn("token", response.data)

    def test_invalid_credentials_cannot_obtain_api_token(self):
        """Verify that invalid credentials cannot obtain an API token."""
        response = self.client.post(
            "/api/token/",
            {
                "username": "test_reader",
                "password": "WrongPassword123",
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )

    def test_reader_can_retrieve_approved_article(self):
        """Verify that a reader can retrieve an approved article."""
        self.client.force_authenticate(user=self.reader)

        response = self.client.get(
            f"/api/articles/{self.approved_article.id}/"
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_200_OK,
        )
        self.assertEqual(
            response.data["id"],
            self.approved_article.id,
        )

    def test_reader_only_sees_approved_articles(self):
        """Verify that readers only see approved articles."""
        self.client.force_authenticate(user=self.reader)

        response = self.client.get("/api/articles/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            self.approved_article.id,
        )

    def test_reader_cannot_create_article(self):
        """Verify that readers cannot create articles through the API."""
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
        """Verify that journalists can create articles through the API."""
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
        """Verify that readers receive articles from subscribed journalists."""
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
        """Verify that journalists cannot edit another journalist's article."""
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

    @patch("news.services.requests.post")
    @patch("news.services.send_mail")
    def test_editor_approval_sends_notifications(
        self,
        mock_send_mail,
        mock_requests_post,
    ):
        """Verify that article approval triggers email and
        webhook notifications."""
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

    @patch("news.services.requests.post")
    @patch("news.services.send_mail")
    def test_website_editor_approval_sends_notifications(
        self,
        mock_send_mail,
        mock_requests_post,
    ):
        """Verify that website approval triggers email and
        webhook notifications."""
        self.reader.journalist_subscriptions.add(self.journalist)

        self.assertTrue(
            self.client.login(
                username="test_editor",
                password="TestPassword123",
            )
        )

        mock_send_mail.return_value = 1

        mock_webhook_response = Mock()
        mock_webhook_response.raise_for_status.return_value = None
        mock_requests_post.return_value = mock_webhook_response

        response = self.client.post(
            f"/articles/{self.pending_article.id}/approve/"
        )

        self.assertEqual(response.status_code, 302)

        self.pending_article.refresh_from_db()
        self.assertTrue(self.pending_article.approved)

        mock_send_mail.assert_called_once()
        self.assertIn(
            "reader@example.com",
            mock_send_mail.call_args.kwargs["recipient_list"],
        )

        mock_requests_post.assert_called_once()

    def test_webhook_rejects_unapproved_article(self):
        """Verify that the webhook rejects articles awaiting approval."""
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
        """Verify that editors can delete articles."""
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
        """Verify that journalists can create newsletters."""
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
        """Verify that editors can create newsletters."""
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
        """Verify that readers cannot create newsletters."""
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
        """Verify that readers can view newsletters."""
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
        """Verify that journalists cannot edit another
        journalist's newsletter."""
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
        """Verify that editors can edit another journalist's newsletter."""
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

    def test_journalist_can_use_associated_publisher(self):
        """Verify that journalists can use their associated publishers."""
        publisher = Publisher.objects.create(
            name="Associated Publisher",
            description="A publisher associated with the journalist.",
        )
        publisher.journalists.add(self.journalist)

        self.client.force_authenticate(user=self.journalist)

        response = self.client.post(
            "/api/articles/",
            {
                "title": "Publisher Article",
                "content": "An article for an associated publisher.",
                "publisher": publisher.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_201_CREATED,
        )
        self.assertEqual(response.data["publisher"], publisher.id)

    def test_journalist_cannot_use_unassociated_publisher(self):
        """Verify that journalists cannot use unassociated publishers."""
        publisher = Publisher.objects.create(
            name="Unassociated Publisher",
            description="A publisher not associated with the journalist.",
        )

        self.client.force_authenticate(user=self.journalist)

        response = self.client.post(
            "/api/articles/",
            {
                "title": "Unauthorised Publisher Article",
                "content": "This article should be rejected.",
                "publisher": publisher.id,
            },
            format="json",
        )

        self.assertEqual(
            response.status_code,
            status.HTTP_400_BAD_REQUEST,
        )
        self.assertEqual(
            Article.objects.filter(
                title="Unauthorised Publisher Article"
            ).count(),
            0,
        )

    def test_reader_only_receives_articles_from_subscribed_publishers(self):
        """Verify that readers only receive articles from
        subscribed publishers."""
        subscribed_publisher = Publisher.objects.create(
            name="Subscribed Publisher",
            description="A publisher the reader follows.",
        )

        other_publisher = Publisher.objects.create(
            name="Other Publisher",
            description="A publisher the reader does not follow.",
        )

        self.reader.publisher_subscriptions.add(subscribed_publisher)

        subscribed_article = Article.objects.create(
            title="Subscribed Publisher Article",
            content="This article belongs to the subscribed publisher.",
            author=self.journalist,
            publisher=subscribed_publisher,
            approved=True,
        )

        Article.objects.create(
            title="Other Publisher Article",
            content="This article belongs to another publisher.",
            author=self.journalist,
            publisher=other_publisher,
            approved=True,
        )

        self.client.force_authenticate(user=self.reader)

        response = self.client.get("/api/articles/subscribed/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data), 1)
        self.assertEqual(
            response.data[0]["id"],
            subscribed_article.id,
        )


class WebsiteSubscriptionTests(TestCase):
    """Test website subscription management and access permissions."""

    def setUp(self):
        """Create users and a publisher for website subscription tests."""
        self.reader = User.objects.create_user(
            username="subscription_reader",
            password="TestPassword123",
            role=User.Role.READER,
        )

        self.journalist = User.objects.create_user(
            username="subscription_journalist",
            password="TestPassword123",
            role=User.Role.JOURNALIST,
        )

        self.other_journalist = User.objects.create_user(
            username="other_subscription_journalist",
            password="TestPassword123",
            role=User.Role.JOURNALIST,
        )

        self.editor = User.objects.create_user(
            username="subscription_editor",
            password="TestPassword123",
            role=User.Role.EDITOR,
        )

        self.publisher = Publisher.objects.create(
            name="Subscription Test Publisher",
            description="Publisher for website subscription tests.",
        )

    def test_reader_can_view_subscription_management_page(self):
        """Verify that readers can open the subscription page."""
        self.client.login(
            username="subscription_reader",
            password="TestPassword123",
        )

        response = self.client.get(
            reverse("manage_subscriptions")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/manage_subscriptions.html",
        )

    def test_reader_can_save_journalist_and_publisher_subscriptions(self):
        """Verify that readers can save both types of subscriptions."""
        self.client.login(
            username="subscription_reader",
            password="TestPassword123",
        )

        response = self.client.post(
            reverse("manage_subscriptions"),
            {
                "journalists": [self.journalist.pk],
                "publishers": [self.publisher.pk],
            },
        )

        self.assertRedirects(
            response,
            reverse("manage_subscriptions"),
        )

        self.assertTrue(
            self.reader.journalist_subscriptions.filter(
                pk=self.journalist.pk
            ).exists()
        )

        self.assertTrue(
            self.reader.publisher_subscriptions.filter(
                pk=self.publisher.pk
            ).exists()
        )

    def test_journalists_and_editors_cannot_access_reader_pages(self):
        """Verify that non-readers cannot access subscription pages."""
        for user in [self.journalist, self.editor]:
            self.client.force_login(user)

            for url_name in [
                "manage_subscriptions",
                "subscribed_articles",
            ]:
                response = self.client.get(reverse(url_name))
                self.assertEqual(response.status_code, 403)

    def test_reader_sees_only_approved_subscribed_articles(self):
        """Verify that readers see approved articles from subscriptions."""
        self.reader.journalist_subscriptions.add(self.journalist)
        self.reader.publisher_subscriptions.add(self.publisher)

        journalist_article = Article.objects.create(
            title="Subscribed Journalist Article",
            content="Approved journalist article.",
            author=self.journalist,
            approved=True,
        )

        Article.objects.create(
            title="Pending Journalist Article",
            content="This article is not approved.",
            author=self.journalist,
            approved=False,
        )

        publisher_article = Article.objects.create(
            title="Subscribed Publisher Article",
            content="Approved publisher article.",
            author=self.other_journalist,
            publisher=self.publisher,
            approved=True,
        )

        Article.objects.create(
            title="Unsubscribed Journalist Article",
            content="This journalist is not subscribed to.",
            author=self.other_journalist,
            approved=True,
        )

        self.client.login(
            username="subscription_reader",
            password="TestPassword123",
        )

        response = self.client.get(
            reverse("subscribed_articles")
        )

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/subscribed_articles.html",
        )

        displayed_articles = list(response.context["articles"])

        self.assertEqual(
            {article.pk for article in displayed_articles},
            {journalist_article.pk, publisher_article.pk},
        )


class NewsletterWebsiteDeletionTests(TestCase):
    """Test website newsletter deletion permissions."""
    # Existing newsletter deletion tests remain unchanged

    def setUp(self):
        """Create users and a newsletter for website deletion tests."""
        self.reader = User.objects.create_user(
            username="website_reader",
            password="TestPassword123",
            role=User.Role.READER,
        )

        self.journalist = User.objects.create_user(
            username="website_journalist",
            password="TestPassword123",
            role=User.Role.JOURNALIST,
        )

        self.other_journalist = User.objects.create_user(
            username="other_website_journalist",
            password="TestPassword123",
            role=User.Role.JOURNALIST,
        )

        self.editor = User.objects.create_user(
            username="website_editor",
            password="TestPassword123",
            role=User.Role.EDITOR,
        )

        self.newsletter = Newsletter.objects.create(
            title="Test Newsletter",
            description="Newsletter deletion test.",
            author=self.journalist,
        )

        self.delete_url = reverse(
            "newsletter_delete",
            args=[self.newsletter.pk],
        )

    def test_journalist_can_delete_own_newsletter(self):
        """Verify that journalists can delete their own newsletters."""
        self.client.login(
            username="website_journalist",
            password="TestPassword123",
        )

        response = self.client.post(self.delete_url)

        self.assertRedirects(
            response,
            reverse("newsletter_list"),
        )
        self.assertFalse(
            Newsletter.objects.filter(
                pk=self.newsletter.pk
            ).exists()
        )

    def test_journalist_cannot_delete_another_journalists_newsletter(self):
        """Verify that journalists cannot delete another
        journalist's newsletter."""
        self.client.login(
            username="other_website_journalist",
            password="TestPassword123",
        )

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Newsletter.objects.filter(
                pk=self.newsletter.pk
            ).exists()
        )

    def test_editor_can_delete_another_journalists_newsletter(self):
        """Verify that editors can delete another journalist's newsletter."""
        self.client.login(
            username="website_editor",
            password="TestPassword123",
        )

        response = self.client.post(self.delete_url)

        self.assertRedirects(
            response,
            reverse("newsletter_list"),
        )
        self.assertFalse(
            Newsletter.objects.filter(
                pk=self.newsletter.pk
            ).exists()
        )

    def test_reader_cannot_delete_newsletter(self):
        """Verify that readers cannot delete newsletters."""
        self.client.login(
            username="website_reader",
            password="TestPassword123",
        )

        response = self.client.post(self.delete_url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(
            Newsletter.objects.filter(
                pk=self.newsletter.pk
            ).exists()
        )

    def test_get_request_displays_confirmation_without_deleting(self):
        """Verify that GET displays confirmation without
        deleting the newsletter."""
        self.client.login(
            username="website_journalist",
            password="TestPassword123",
        )

        response = self.client.get(self.delete_url)

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(
            response,
            "news/newsletter_confirm_delete.html",
        )
        self.assertTrue(
            Newsletter.objects.filter(
                pk=self.newsletter.pk
            ).exists()
        )
