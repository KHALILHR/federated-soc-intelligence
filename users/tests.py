from django.test import TestCase, Client
from django.urls import reverse

from .models import Organization, User


class AdminPanelPermissionTests(TestCase):
    """Only SOC Managers can access the admin panel."""

    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(name='Test Org', domain='test.org')

        self.manager = User.objects.create_user(
            username='manager1',
            password='pass12345',
            role=User.Role.SOC_MANAGER,
            organization=self.org,
        )
        self.analyst = User.objects.create_user(
            username='analyst1',
            password='pass12345',
            role=User.Role.SECURITY_ANALYST,
            organization=self.org,
        )

    def test_admin_panel_requires_login(self):
        response = self.client.get(reverse('users:admin_panel'))
        self.assertRedirects(response, '/users/login/?next=/users/soc-admin/')

    def test_analyst_redirected_from_admin_panel(self):
        self.client.login(username='analyst1', password='pass12345')
        response = self.client.get(reverse('users:admin_panel'))
        self.assertRedirects(response, reverse('dashboard:index'))

    def test_manager_can_access_admin_panel(self):
        self.client.login(username='manager1', password='pass12345')
        response = self.client.get(reverse('users:admin_panel'))
        self.assertEqual(response.status_code, 200)

    def test_admin_panel_shows_org_users(self):
        self.client.login(username='manager1', password='pass12345')
        response = self.client.get(reverse('users:admin_panel'))
        self.assertContains(response, 'analyst1')


class OrganizationCRUDTests(TestCase):
    """SOC Managers can create, edit, and delete organizations."""

    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(name='HQ Org', domain='hq.org')
        self.manager = User.objects.create_user(
            username='mgr',
            password='pass12345',
            role=User.Role.SOC_MANAGER,
            organization=self.org,
        )
        self.client.login(username='mgr', password='pass12345')

    def test_create_organization(self):
        response = self.client.post(reverse('users:org_create'), {
            'name': 'New Org',
            'domain': 'new.org',
            'is_active': True,
        })
        self.assertRedirects(response, reverse('users:admin_panel'))
        self.assertTrue(Organization.objects.filter(name='New Org').exists())

    def test_edit_organization(self):
        response = self.client.post(reverse('users:org_edit', args=[self.org.id]), {
            'name': 'HQ Org Updated',
            'domain': 'hq.org',
            'is_active': True,
        })
        self.assertRedirects(response, reverse('users:admin_panel'))
        self.org.refresh_from_db()
        self.assertEqual(self.org.name, 'HQ Org Updated')

    def test_delete_organization(self):
        other_org = Organization.objects.create(name='To Delete', domain='del.org')
        response = self.client.post(reverse('users:org_delete', args=[other_org.id]))
        self.assertRedirects(response, reverse('users:admin_panel'))
        self.assertFalse(Organization.objects.filter(name='To Delete').exists())


class UserCRUDTests(TestCase):
    """SOC Managers can create, edit, and delete users in their own org."""

    def setUp(self):
        self.client = Client()
        self.org = Organization.objects.create(name='Sec Org', domain='sec.org')
        self.manager = User.objects.create_user(
            username='sec_mgr',
            password='pass12345',
            role=User.Role.SOC_MANAGER,
            organization=self.org,
        )
        self.client.login(username='sec_mgr', password='pass12345')

    def test_create_user_in_own_org(self):
        response = self.client.post(reverse('users:user_create'), {
            'username': 'new_analyst',
            'email': 'analyst@sec.org',
            'password': 'ComplexPass1!',
            'confirm_password': 'ComplexPass1!',
            'role': User.Role.SECURITY_ANALYST,
            'clearance_level': 2,
            'mfa_enabled': False,
        })
        self.assertRedirects(response, reverse('users:admin_panel'))
        new_user = User.objects.get(username='new_analyst')
        self.assertEqual(new_user.organization, self.org)

    def test_cannot_create_user_mismatched_passwords(self):
        response = self.client.post(reverse('users:user_create'), {
            'username': 'bad_user',
            'email': '',
            'password': 'Pass1!',
            'confirm_password': 'Diff1!',
            'role': User.Role.SECURITY_ANALYST,
            'clearance_level': 1,
            'mfa_enabled': False,
        })
        self.assertEqual(response.status_code, 200)
        self.assertFalse(User.objects.filter(username='bad_user').exists())

    def test_edit_user_in_own_org(self):
        target = User.objects.create_user(
            username='editable_user',
            password='pass12345',
            role=User.Role.SECURITY_ANALYST,
            organization=self.org,
        )
        response = self.client.post(reverse('users:user_edit', args=[target.id]), {
            'username': 'editable_user',
            'email': 'updated@sec.org',
            'role': User.Role.NODE_ADMIN,
            'clearance_level': 3,
            'mfa_enabled': True,
        })
        self.assertRedirects(response, reverse('users:admin_panel'))
        target.refresh_from_db()
        self.assertEqual(target.role, User.Role.NODE_ADMIN)

    def test_cannot_edit_user_from_other_org(self):
        other_org = Organization.objects.create(name='Other Org', domain='other.org')
        other_user = User.objects.create_user(
            username='other_user',
            password='pass12345',
            role=User.Role.SECURITY_ANALYST,
            organization=other_org,
        )
        response = self.client.post(reverse('users:user_edit', args=[other_user.id]), {
            'username': 'other_user',
            'email': 'hacked@other.org',
            'role': User.Role.SOC_MANAGER,
            'clearance_level': 5,
            'mfa_enabled': False,
        })
        self.assertEqual(response.status_code, 404)

    def test_delete_user_in_own_org(self):
        target = User.objects.create_user(
            username='deleteable',
            password='pass12345',
            role=User.Role.READONLY,
            organization=self.org,
        )
        response = self.client.post(reverse('users:user_delete', args=[target.id]))
        self.assertRedirects(response, reverse('users:admin_panel'))
        self.assertFalse(User.objects.filter(username='deleteable').exists())

    def test_cannot_delete_user_from_other_org(self):
        other_org = Organization.objects.create(name='Ext Org', domain='ext.org')
        other_user = User.objects.create_user(
            username='ext_user',
            password='pass12345',
            role=User.Role.SECURITY_ANALYST,
            organization=other_org,
        )
        response = self.client.post(reverse('users:user_delete', args=[other_user.id]))
        self.assertEqual(response.status_code, 404)
        self.assertTrue(User.objects.filter(username='ext_user').exists())
