"""
Tests for groups app — written BEFORE implementation (TDD).
Covers models, views, permissions, and post integration.
"""
from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse


class GroupModelTests(TestCase):
    """Tests for the Group model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(
            username="alice", password="secret"
        )

    def setUp(self):
        from groups.models import Group
        self.Group = Group

    def test_create_group(self):
        """Can create a group with an admin."""
        group = self.Group.objects.create(
            name="Python Developers",
            description="A group for Python devs",
            admin=self.admin,
        )
        self.assertEqual(self.Group.objects.count(), 1)
        self.assertEqual(group.name, "Python Developers")
        self.assertEqual(group.admin, self.admin)

    def test_group_str(self):
        """String representation is the group name."""
        group = self.Group.objects.create(
            name="Python Developers",
            admin=self.admin,
        )
        self.assertEqual(str(group), "Python Developers")

    def test_group_cover_field(self):
        """Group has an optional cover image field."""
        group = self.Group(
            name="Test Group",
            admin=self.admin,
        )
        self.assertTrue(hasattr(group, "cover"))
        # cover is optional — no file means falsy, not None
        self.assertFalse(bool(group.cover))

    def test_group_created_at(self):
        """Group has auto-set created_at."""
        from django.utils import timezone
        group = self.Group.objects.create(
            name="Test Group",
            admin=self.admin,
        )
        self.assertIsNotNone(group.created_at)


class GroupMembershipModelTests(TestCase):
    """Tests for the GroupMembership model."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.member = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from groups.models import Group, GroupMembership
        self.Group = Group
        self.GroupMembership = GroupMembership
        self.group = self.Group.objects.create(
            name="Test Group",
            admin=self.admin,
        )

    def test_add_member(self):
        """Can add a user as a member."""
        self.GroupMembership.objects.create(
            group=self.group,
            user=self.member,
        )
        self.assertEqual(self.GroupMembership.objects.count(), 1)
        self.assertIn(self.member, self.group.members.all())

    def test_membership_default_role(self):
        """Default role is 'member'."""
        membership = self.GroupMembership.objects.create(
            group=self.group,
            user=self.member,
        )
        self.assertEqual(membership.role, "member")

    def test_membership_admin_role_on_create(self):
        """Admin user added at group creation gets 'admin' role."""
        self.GroupMembership.objects.create(
            group=self.group,
            user=self.admin,
            role="admin",
        )
        self.assertTrue(
            self.GroupMembership.objects.filter(
                group=self.group, user=self.admin, role="admin",
            ).exists()
        )

    def test_membership_unique_together(self):
        """Each user can only be a member once per group."""
        self.GroupMembership.objects.create(
            group=self.group, user=self.member,
        )
        from django.db import IntegrityError
        with self.assertRaises(IntegrityError):
            self.GroupMembership.objects.create(
                group=self.group, user=self.member,
            )

    def test_membership_joined_at(self):
        """Membership records when user joined."""
        membership = self.GroupMembership.objects.create(
            group=self.group,
            user=self.member,
        )
        self.assertIsNotNone(membership.joined_at)

    def test_membership_str(self):
        """String representation shows user and group."""
        membership = self.GroupMembership.objects.create(
            group=self.group,
            user=self.member,
        )
        self.assertIn(self.member.username, str(membership))
        self.assertIn(self.group.name, str(membership))

    def test_group_members_relationship(self):
        """Group has a members queryset via through model."""
        self.GroupMembership.objects.create(
            group=self.group, user=self.member,
        )
        members = self.group.members.all()
        self.assertIn(self.member, members)


class GroupPostIntegrationTests(TestCase):
    """Tests that Post model supports nullable group FK."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.member = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from groups.models import Group
        from posts.models import Post
        self.Post = Post
        self.group = Group.objects.create(
            name="Test Group",
            admin=self.admin,
        )

    def test_post_has_group_field(self):
        """Post model has a nullable group FK field."""
        self.assertTrue(hasattr(self.Post(), "group"))
        field = self.Post._meta.get_field("group")
        self.assertTrue(field.null)

    def test_create_post_in_group(self):
        """Can create a post associated with a group."""
        post = self.Post.objects.create(
            author=self.member,
            content="Group post!",
            group=self.group,
        )
        self.assertEqual(post.group, self.group)

    def test_post_without_group(self):
        """Post without group is fine (regular feed post)."""
        post = self.Post.objects.create(
            author=self.member,
            content="Regular post",
        )
        self.assertIsNone(post.group)

    def test_group_posts_query(self):
        """Can query posts by group."""
        self.Post.objects.create(
            author=self.member, content="In group",
            group=self.group,
        )
        self.Post.objects.create(
            author=self.member, content="Not in group",
        )
        group_posts = self.Post.objects.filter(group=self.group)
        self.assertEqual(group_posts.count(), 1)
        self.assertEqual(group_posts.first().content, "In group")


class GroupListViewTests(TestCase):
    """Tests for group list view."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def setUp(self):
        from groups.models import Group
        self.Group = Group
        Group.objects.create(name="Group A", admin=self.user)
        Group.objects.create(name="Group B", admin=self.user)

    def test_list_authenticated(self):
        """Authenticated user sees group list."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("groups:list"))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Group A")
        self.assertContains(response, "Group B")

    def test_list_anonymous_redirect(self):
        """Anonymous user redirected to login."""
        response = self.client.get(reverse("groups:list"))
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_list_pagination(self):
        """Group list uses pagination."""
        for i in range(25):
            self.Group.objects.create(
                name=f"Group {i}", admin=self.user,
            )
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("groups:list"))
        self.assertIn("page_obj", response.context)
        self.assertIn("is_paginated", response.context)


class GroupDetailViewTests(TestCase):
    """Tests for group detail view."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.member = User.objects.create_user(
            username="bob", password="secret"
        )
        cls.non_member = User.objects.create_user(
            username="charlie", password="secret"
        )

    def setUp(self):
        from groups.models import Group, GroupMembership
        from posts.models import Post
        self.Group = Group
        self.Post = Post
        self.group = Group.objects.create(
            name="Test Group",
            description="A test group",
            admin=self.admin,
        )
        GroupMembership.objects.create(
            group=self.group, user=self.admin, role="admin",
        )
        GroupMembership.objects.create(
            group=self.group, user=self.member,
        )

    def test_detail_authenticated_member(self):
        """Member can view group detail."""
        self.client.login(username="bob", password="secret")
        response = self.client.get(
            reverse("groups:detail", kwargs={"pk": self.group.pk}),
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Test Group")

    def test_detail_authenticated_non_member(self):
        """Non-member can view public group detail."""
        self.client.login(username="charlie", password="secret")
        response = self.client.get(
            reverse("groups:detail", kwargs={"pk": self.group.pk}),
        )
        self.assertEqual(response.status_code, 200)

    def test_detail_anonymous_redirect(self):
        """Anonymous redirected from group detail."""
        response = self.client.get(
            reverse("groups:detail", kwargs={"pk": self.group.pk}),
        )
        self.assertEqual(response.status_code, 302)

    def test_detail_shows_group_posts(self):
        """Group detail page shows posts in the group."""
        self.Post.objects.create(
            author=self.member, content="Group post!",
            group=self.group,
        )
        self.client.login(username="bob", password="secret")
        response = self.client.get(
            reverse("groups:detail", kwargs={"pk": self.group.pk}),
        )
        self.assertContains(response, "Group post!")

    def test_detail_shows_member_count(self):
        """Group detail shows how many members."""
        self.client.login(username="bob", password="secret")
        response = self.client.get(
            reverse("groups:detail", kwargs={"pk": self.group.pk}),
        )
        # Should show member count
        member_count = self.group.members.count()
        self.assertIn(str(member_count), str(response.content))


class GroupCreateViewTests(TestCase):
    """Tests for creating a group."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.user = User.objects.create_user(
            username="alice", password="secret"
        )

    def test_create_view_authenticated(self):
        """Authenticated user sees creation form."""
        self.client.login(username="alice", password="secret")
        response = self.client.get(reverse("groups:create"))
        self.assertEqual(response.status_code, 200)

    def test_create_view_anonymous_redirect(self):
        """Anonymous user redirected from create."""
        response = self.client.get(reverse("groups:create"))
        self.assertEqual(response.status_code, 302)

    def test_create_group(self):
        """POST creates a group with current user as admin."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("groups:create"),
            {
                "name": "New Group",
                "description": "A new group",
            },
        )
        self.assertEqual(response.status_code, 302)
        from groups.models import Group
        group = Group.objects.first()
        self.assertIsNotNone(group)
        self.assertEqual(group.name, "New Group")
        self.assertEqual(group.admin, self.user)
        # User should be added as admin member
        self.assertIn(self.user, group.members.all())

    def test_create_group_empty_name(self):
        """Creating a group with empty name shows error."""
        self.client.login(username="alice", password="secret")
        response = self.client.post(
            reverse("groups:create"),
            {"name": "", "description": "No name"},
        )
        self.assertEqual(response.status_code, 200)  # re-renders form


class GroupJoinViewTests(TestCase):
    """Tests for joining/leaving a public group."""

    @classmethod
    def setUpTestData(cls):
        User = get_user_model()
        cls.admin = User.objects.create_user(
            username="alice", password="secret"
        )
        cls.member = User.objects.create_user(
            username="bob", password="secret"
        )

    def setUp(self):
        from groups.models import Group, GroupMembership
        self.Group = Group
        self.GroupMembership = GroupMembership
        self.group = Group.objects.create(
            name="Public Group",
            admin=self.admin,
        )
        self.GroupMembership.objects.create(
            group=self.group, user=self.admin, role="admin",
        )

    def test_join_group(self):
        """POST join adds user to members."""
        self.client.login(username="bob", password="secret")
        response = self.client.post(
            reverse("groups:join", kwargs={"pk": self.group.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.member, self.group.members.all())

    def test_leave_group(self):
        """POST leave removes user from members."""
        self.GroupMembership.objects.create(
            group=self.group, user=self.member,
        )
        self.client.login(username="bob", password="secret")
        response = self.client.post(
            reverse("groups:join", kwargs={"pk": self.group.pk}),
        )
        self.assertEqual(response.status_code, 302)
        # After toggle: should leave
        self.assertNotIn(self.member, self.group.members.all())

    def test_join_anonymous_redirect(self):
        """Anonymous user cannot join groups."""
        response = self.client.post(
            reverse("groups:join", kwargs={"pk": self.group.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn("login", response.url.lower())

    def test_double_join_does_not_error(self):
        """Joining twice (already member) is idempotent (leaves)."""
        self.GroupMembership.objects.create(
            group=self.group, user=self.member,
        )
        self.client.login(username="bob", password="secret")
        # First leave
        self.client.post(
            reverse("groups:join", kwargs={"pk": self.group.pk}),
        )
        # Second: join again
        response = self.client.post(
            reverse("groups:join", kwargs={"pk": self.group.pk}),
        )
        self.assertEqual(response.status_code, 302)
        self.assertIn(self.member, self.group.members.all())
