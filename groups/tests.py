"""Tests for the Groups app."""

from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from .models import Group, GroupMembership, GroupPost

User = get_user_model()


class GroupModelTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="groupadmin", password="testpass123"
        )

    def test_create_group(self):
        group = Group.objects.create(
            name="Test Group",
            description="A test group",
            admin=self.user,
        )
        self.assertEqual(group.name, "Test Group")
        self.assertEqual(group.admin, self.user)
        self.assertEqual(group.member_count, 0)

    def test_group_str(self):
        group = Group.objects.create(name="Test Group", admin=self.user)
        self.assertEqual(str(group), "Test Group")

    def test_group_absolute_url(self):
        group = Group.objects.create(name="Test Group", admin=self.user)
        self.assertEqual(
            group.get_absolute_url(),
            reverse("groups:group_detail", kwargs={"pk": group.pk}),
        )

    def test_group_membership_created(self):
        group = Group.objects.create(name="Test Group", admin=self.user)
        other = User.objects.create_user(username="member1", password="testpass123")
        membership = GroupMembership.objects.create(
            user=other, group=group, role="member"
        )
        self.assertEqual(membership.role, "member")
        self.assertEqual(str(membership), "member1 in Test Group")

    def test_group_membership_unique_together(self):
        group = Group.objects.create(name="Test Group", admin=self.user)
        GroupMembership.objects.create(user=self.user, group=group, role="admin")
        with self.assertRaises(Exception):
            GroupMembership.objects.create(user=self.user, group=group, role="member")

    def test_group_post_created(self):
        group = Group.objects.create(name="Test Group", admin=self.user)
        post = GroupPost.objects.create(
            group=group, author=self.user, content="Hello group!"
        )
        self.assertEqual(post.content, "Hello group!")
        self.assertEqual(group.posts.count(), 1)

    def test_group_post_str(self):
        group = Group.objects.create(name="Test Group", admin=self.user)
        post = GroupPost.objects.create(
            group=group, author=self.user, content="Hello group!"
        )
        expected = self.user.username + " in Test Group: " + post.content[:50]
        self.assertEqual(str(post), expected)

    def test_member_count_property(self):
        group = Group.objects.create(name="Test Group", admin=self.user)
        other1 = User.objects.create_user(username="u1", password="testpass123")
        other2 = User.objects.create_user(username="u2", password="testpass123")
        GroupMembership.objects.create(user=other1, group=group, role="member")
        GroupMembership.objects.create(user=other2, group=group, role="member")
        self.assertEqual(group.member_count, 2)


class GroupViewTests(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpass123"
        )

    def test_group_list_requires_login(self):
        response = self.client.get(reverse("groups:group_list"))
        self.assertRedirects(
            response,
            "/accounts/login/?next=" + reverse("groups:group_list"),
        )

    def test_group_list_logged_in(self):
        self.client.login(username="testuser", password="testpass123")
        Group.objects.create(name="Test Group", admin=self.user)
        response = self.client.get(reverse("groups:group_list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Group")

    def test_create_group(self):
        self.client.login(username="testuser", password="testpass123")
        response = self.client.post(
            reverse("groups:group_create"),
            {"name": "New Group", "description": "A new test group"},
        )
        self.assertRedirects(response, reverse("groups:group_list"))
        self.assertTrue(Group.objects.filter(name="New Group").exists())

    def test_create_group_auto_join_as_admin(self):
        self.client.login(username="testuser", password="testpass123")
        self.client.post(
            reverse("groups:group_create"),
            {"name": "AutoJoin Group"},
        )
        group = Group.objects.get(name="AutoJoin Group")
        self.assertTrue(
            GroupMembership.objects.filter(
                user=self.user, group=group, role="admin"
            ).exists()
        )

    def test_group_detail(self):
        self.client.login(username="testuser", password="testpass123")
        group = Group.objects.create(name="Test Group", admin=self.user)
        response = self.client.get(
            reverse("groups:group_detail", kwargs={"pk": group.pk})
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Group")

    def test_group_detail_shows_is_member(self):
        self.client.login(username="testuser", password="testpass123")
        group = Group.objects.create(name="Test Group", admin=self.user)
        GroupMembership.objects.create(user=self.user, group=group, role="admin")
        response = self.client.get(
            reverse("groups:group_detail", kwargs={"pk": group.pk})
        )
        self.assertTrue(response.context["is_member"])

    def test_join_group(self):
        self.client.login(username="testuser", password="testpass123")
        other = User.objects.create_user(username="admin1", password="testpass123")
        group = Group.objects.create(name="Joinable Group", admin=other)
        response = self.client.post(
            reverse("groups:group_toggle", kwargs={"pk": group.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["is_member"])

    def test_leave_group(self):
        self.client.login(username="testuser", password="testpass123")
        other = User.objects.create_user(username="admin1", password="testpass123")
        group = Group.objects.create(name="Leavable Group", admin=other)
        GroupMembership.objects.create(user=self.user, group=group, role="member")
        response = self.client.post(
            reverse("groups:group_toggle", kwargs={"pk": group.pk})
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data["is_member"])

    def test_admin_cannot_leave_group(self):
        self.client.login(username="testuser", password="testpass123")
        group = Group.objects.create(name="My Group", admin=self.user)
        GroupMembership.objects.create(user=self.user, group=group, role="admin")
        response = self.client.post(
            reverse("groups:group_toggle", kwargs={"pk": group.pk})
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("admin", response.json()["error"])

    def test_create_group_post(self):
        self.client.login(username="testuser", password="testpass123")
        group = Group.objects.create(name="Test Group", admin=self.user)
        GroupMembership.objects.create(user=self.user, group=group, role="admin")
        response = self.client.post(
            reverse("groups:group_post", kwargs={"pk": group.pk}),
            {"content": "Hello members!"},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["created"])

    def test_create_group_post_non_member_forbidden(self):
        self.client.login(username="testuser", password="testpass123")
        other = User.objects.create_user(username="admin1", password="testpass123")
        group = Group.objects.create(name="Test Group", admin=other)
        response = self.client.post(
            reverse("groups:group_post", kwargs={"pk": group.pk}),
            {"content": "Hello!"},
        )
        self.assertEqual(response.status_code, 403)

    def test_create_group_post_empty_content(self):
        self.client.login(username="testuser", password="testpass123")
        group = Group.objects.create(name="Test Group", admin=self.user)
        GroupMembership.objects.create(user=self.user, group=group, role="admin")
        response = self.client.post(
            reverse("groups:group_post", kwargs={"pk": group.pk}),
            {"content": ""},
        )
        self.assertEqual(response.status_code, 400)
        self.assertIn("error", response.json())
