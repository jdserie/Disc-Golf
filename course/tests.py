from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Course, Review


class CourseFlows(TestCase):
    def setUp(self):
        self.course = Course.objects.create(
            course_name='Sahm Park', city='Indianapolis', holes=18, tee_type='Concrete',
        )
        self.player = get_user_model().objects.create_user('player', password='demo-pass-4982')

    def test_public_views_and_search(self):
        for name in ('pages-home', 'groupHome', 'goalsHome', 'processHome', 'reviewCourse', 'register', 'login'):
            self.assertEqual(self.client.get(reverse(name)).status_code, 200, name)
        self.assertContains(self.client.get(reverse('courseHome'), {'q': 'INDIANAPOLIS'}), 'Sahm Park')
        self.assertNotContains(self.client.get(reverse('courseHome'), {'q': 'missing'}), 'Sahm Park')
        self.assertEqual(self.client.get(reverse('courseInfo', args=[999])).status_code, 404)

    def test_regular_user_cannot_archive_or_delete_courses(self):
        self.client.force_login(self.player)
        payload = {'id': self.course.pk, 'play': 'True'}
        self.assertEqual(self.client.post(reverse('courseHome'), payload).status_code, 403)
        self.assertEqual(self.client.post(reverse('deleteCourse'), payload).status_code, 403)
        self.course.refresh_from_db()
        self.assertFalse(self.course.play)

    def test_staff_can_archive_restore_and_delete(self):
        self.player.is_staff = True
        self.player.save(update_fields=['is_staff'])
        self.client.force_login(self.player)
        for value, expected in [('True', True), ('False', False), ('True', True)]:
            response = self.client.post(reverse('courseHome'), {'id': self.course.pk, 'play': value})
            self.assertRedirects(response, reverse('courseHome'))
            self.course.refresh_from_db()
            self.assertEqual(self.course.play, expected)
        self.client.post(reverse('deleteCourse'), {'id': self.course.pk})
        self.assertFalse(Course.objects.filter(pk=self.course.pk).exists())

    def test_reviews_require_login_and_ownership(self):
        payload = {'crse': self.course.pk, 'thoughts': 'Great course.'}
        self.assertEqual(self.client.post(reverse('addReview'), payload).status_code, 302)
        self.assertFalse(Review.objects.exists())
        self.client.force_login(self.player)
        self.assertEqual(self.client.post(reverse('addReview'), {**payload, 'thoughts': ''}).status_code, 400)
        self.assertEqual(self.client.post(reverse('addReview'), payload).status_code, 302)
        review = Review.objects.get()
        self.assertEqual(review.author, self.player)
        other = get_user_model().objects.create_user('other-player')
        self.client.force_login(other)
        self.assertEqual(self.client.post(reverse('deleteReview'), {'id': review.pk}).status_code, 404)
        self.client.force_login(self.player)
        self.assertEqual(self.client.post(reverse('deleteReview'), {'id': review.pk}).status_code, 302)

    def test_register_login_profile_and_sign_out(self):
        password = 'new-player-credential-117'
        response = self.client.post(reverse('register'), {
            'username': 'new-player', 'email': 'player@example.com', 'password1': password, 'password2': password,
        })
        self.assertRedirects(response, reverse('login'))
        response = self.client.post(reverse('login'), {'username': 'new-player', 'password': password})
        self.assertRedirects(response, reverse('pages-home'))
        self.assertContains(self.client.get(reverse('profile')), 'Your profile')
        self.assertEqual(self.client.get(reverse('logout')).status_code, 405)
        self.assertRedirects(self.client.post(reverse('logout')), reverse('pages-home'))
