from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase

from feedback.context_processors import feedback_notifications
from feedback.models import Feedback

User = get_user_model()


class FeedbackNotificationTest(TestCase):
    def setUp(self):
        self.factory = RequestFactory()
        self.user = User.objects.create_user(username='testuser', password='password')

    def test_has_waiting_feedback(self):
        # Create feedback with WAITING_USER status
        Feedback.objects.create(user=self.user, content="Test feedback", status="WAITING_USER")

        request = self.factory.get('/')
        request.user = self.user

        context = feedback_notifications(request)
        self.assertTrue(context['has_waiting_feedback'])
        self.assertFalse(context['has_recent_activity'])

    def test_has_recent_activity(self):
        # Create feedback with NEW status (recent)
        Feedback.objects.create(user=self.user, content="Recent feedback", status="NEW")

        request = self.factory.get('/')
        request.user = self.user

        context = feedback_notifications(request)
        self.assertFalse(context['has_waiting_feedback'])
        self.assertTrue(context['has_recent_activity'])
