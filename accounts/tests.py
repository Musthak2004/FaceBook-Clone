from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class CustomUserModelTests(TestCase):

    def setUp(self):
        self.User = get_user_model()

    def test_create_user(self):
        user = self.User.objects.create_user(
            email='test@example.com',
            username='testuser',
            password='testpass123'
        )
        self.assertEqual(user.email, 'test@example.com')
        self.assertEqual(user.username, 'testuser')
        self.assertTrue(user.check_password('testpass123'))
        self.assertFalse(user.is_email_verified)

    def test_create_superuser(self):
        admin = self.User.objects.create_superuser(
            email='admin@example.com',
            username='admin',
            password='adminpass123'
        )
        self.assertTrue(admin.is_superuser)
        self.assertTrue(admin.is_staff)

    def test_email_unique(self):
        self.User.objects.create_user(
            email='dup@example.com', username='user1', password='pass123'
        )
        with self.assertRaises(Exception):
            self.User.objects.create_user(
                email='dup@example.com', username='user2', password='pass456'
            )

    def test_str_returns_email(self):
        user = self.User.objects.create_user(
            email='str@example.com', username='strtest', password='pass123'
        )
        self.assertEqual(str(user), 'str@example.com')

    def test_get_absolute_url(self):
        user = self.User.objects.create_user(
            email='url@example.com', username='urltest', password='pass123'
        )
        self.assertEqual(
            user.get_absolute_url(),
            reverse('accounts:profile', kwargs={'username': 'urltest'})
        )


class SignUpViewTests(TestCase):

    def test_signup_page_renders(self):
        response = self.client.get(reverse('accounts:signup'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/signup.html')

    def test_signup_success(self):
        response = self.client.post(reverse('accounts:signup'), {
            'email': 'newuser@example.com',
            'username': 'newuser',
            'first_name': 'New',
            'last_name': 'User',
            'password1': 'Str0ng!Pass',
            'password2': 'Str0ng!Pass',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('login'))
        self.assertTrue(get_user_model().objects.filter(email='newuser@example.com').exists())

    def test_signup_form_invalid(self):
        response = self.client.post(reverse('accounts:signup'), {
            'email': 'bad-email',
            'username': '',
            'password1': 'pass',
            'password2': 'different',
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(get_user_model().objects.filter(email='bad-email').exists())


class LoginViewTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='login@example.com', username='logintest', password='testpass123'
        )

    def test_login_page_renders(self):
        response = self.client.get(reverse('login'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'registration/login.html')

    def test_login_success(self):
        response = self.client.post(reverse('login'), {
            'username': 'login@example.com',
            'password': 'testpass123',
        })
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse('home'))

    def test_login_invalid(self):
        response = self.client.post(reverse('login'), {
            'username': 'login@example.com',
            'password': 'wrongpass',
        })
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct')


class ProfileViewTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='profile@example.com', username='profiletest', password='pass123'
        )

    def test_profile_requires_login(self):
        response = self.client.get(
            reverse('accounts:profile', kwargs={'username': 'profiletest'})
        )
        self.assertEqual(response.status_code, 302)

    def test_profile_renders_for_authenticated(self):
        self.client.login(email='profile@example.com', password='pass123')
        response = self.client.get(
            reverse('accounts:profile', kwargs={'username': 'profiletest'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile.html')

    def test_profile_edit_own(self):
        self.client.login(email='profile@example.com', password='pass123')
        response = self.client.get(
            reverse('accounts:profile_edit', kwargs={'username': 'profiletest'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'accounts/profile_edit.html')

    def test_profile_edit_other_user(self):
        other = self.User.objects.create_user(
            email='other@example.com', username='otheruser', password='pass123'
        )
        self.client.login(email='profile@example.com', password='pass123')
        response = self.client.get(
            reverse('accounts:profile_edit', kwargs={'username': 'otheruser'})
        )
        self.assertEqual(response.status_code, 403)

    def test_profile_edit_saves_bio(self):
        self.client.login(email='profile@example.com', password='pass123')
        response = self.client.post(
            reverse('accounts:profile_edit', kwargs={'username': 'profiletest'}),
            {'first_name': 'Profile', 'last_name': 'Test', 'bio': 'Hello, this is my bio!'}
        )
        self.assertRedirects(
            response,
            reverse('accounts:profile', kwargs={'username': 'profiletest'})
        )
        self.user.refresh_from_db()
        self.assertEqual(self.user.bio, 'Hello, this is my bio!')

    def test_profile_shows_bio(self):
        self.user.bio = 'My awesome bio'
        self.user.location = 'New York'
        self.user.save()
        self.client.login(email='profile@example.com', password='pass123')
        response = self.client.get(
            reverse('accounts:profile', kwargs={'username': 'profiletest'})
        )
        self.assertContains(response, 'My awesome bio')
        self.assertContains(response, 'New York')

    def test_profile_default_avatar(self):
        self.client.login(email='profile@example.com', password='pass123')
        response = self.client.get(
            reverse('accounts:profile', kwargs={'username': 'profiletest'})
        )
        self.assertContains(response, 'default-avatar.svg')


class EmailVerificationTests(TestCase):

    def setUp(self):
        self.User = get_user_model()
        self.user = self.User.objects.create_user(
            email='verify@example.com', username='verifytest', password='pass123'
        )

    def test_verify_email_invalid_token(self):
        from django.utils.http import urlsafe_base64_encode
        from django.utils.encoding import force_bytes
        uid = urlsafe_base64_encode(force_bytes(self.user.pk))
        response = self.client.get(
            reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': 'bad-token'})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Invalid or expired')

    def test_verify_email_valid_token(self):
        from accounts.utils import generate_verification_token
        uid, token = generate_verification_token(self.user)
        response = self.client.get(
            reverse('accounts:verify_email', kwargs={'uidb64': uid, 'token': token})
        )
        self.assertRedirects(response, reverse('login'))
        self.user.refresh_from_db()
        self.assertTrue(self.user.is_email_verified)
