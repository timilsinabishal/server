from django.utils import timezone
from datetime import timedelta

from user.models import (
    User,
    Feature,
)
from deep.tests import TestCase
from entry.models import Lead, Entry, Attribute
from analysis_framework.models import (
    AnalysisFramework,
    AnalysisFrameworkRole,
    Widget,
)
from project.tasks import _generate_entry_stats
from project.models import (
    Project,
    ProjectRole,
    ProjectMembership,
    ProjectJoinRequest,
    ProjectStatus,
    ProjectStatusCondition,
    ProjectUserGroupMembership,
)

from user_group.models import UserGroup

from . import entry_stats_data


# TODO Document properly some of the following complex tests


class ProjectApiTest(TestCase):

    def setUp(self):
        super().setUp()
        # create some users
        self.user1 = self.create(User)
        self.user2 = self.create(User)
        self.user3 = self.create(User)
        # and some user groups
        self.ug1 = self.create(UserGroup, role='admin')
        self.ug1.add_member(self.user1)
        self.ug1.add_member(self.user2)
        self.ug2 = self.create(UserGroup, role='admin')
        self.ug2.add_member(self.user2)
        self.ug2.add_member(self.user3)

    def test_create_project(self):
        project_count = Project.objects.count()

        url = '/api/v1/projects/'
        data = {
            'title': 'Test project',
            'data': {'testKey': 'testValue'},
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(Project.objects.count(), project_count + 1)
        self.assertEqual(response.data['title'], data['title'])

        # Test that the user has been made admin
        self.assertEqual(len(response.data['memberships']), 1)
        self.assertEqual(response.data['memberships'][0]['member'],
                         self.user.pk)

        # assert single membership
        self.assertEqual(len(response.data['memberships']), 1)
        membership = ProjectMembership.objects.get(
            pk=response.data['memberships'][0]['id'])
        self.assertEqual(membership.member.pk, self.user.pk)
        self.assertEqual(membership.role, self.admin_role)

    def create_project(self, title, is_private):
        url = '/api/v1/projects/'
        data = {
            'title': title,
            'is_private': is_private,
        }

        response = self.client.post(url, data)
        return response

    def test_get_projects(self):
        user_fhx = self.create(User)
        self.create(Feature, feature_type=Feature.GENERAL_ACCESS,
                    key=Feature.PRIVATE_PROJECT, title='Private project',
                    users=[user_fhx], email_domains=[])
        self.authenticate(user_fhx)

        self.create_project('Project 1', False)
        self.create_project('Project 2', False)
        self.create_project('Project 3', False)
        self.create_project('Project 4', False)
        self.create_project('Private Project 1', True)

        response = self.client.get('/api/v1/projects/')
        self.assertEqual(len(response.data['results']), 5)

        other_user = self.create(User)
        self.authenticate(other_user)

        # self.create_project('Project 5', False)
        # self.create_project('Private Project 3', True)

        response = self.client.get('/api/v1/projects/')
        self.assertEqual(len(response.data['results']), 4)

    def test_create_private_project(self):
        # project_count = Project.objects.count()
        url = '/api/v1/projects/'
        data = {
            'title': 'Test private project',
            'is_private': 'true',
        }

        user_fhx = self.create(User, email='fhx@togglecorp.com')
        self.create(Feature, feature_type=Feature.GENERAL_ACCESS,
                    key=Feature.PRIVATE_PROJECT, title='Private project',
                    users=[user_fhx], email_domains=[])

        self.authenticate(user_fhx)
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['is_private'], True)
        self.assertEqual(Project.objects.last().is_private, True)

    def test_change_private_project_to_public(self):
        private_project = self.create(Project, is_private=True)
        public_project = self.create(Project, is_private=False)

        # Add roles for self.user
        private_project.add_member(self.user, ProjectRole.get_creator_role())
        public_project.add_member(self.user, ProjectRole.get_creator_role())

        self._change_project_privacy_test(private_project, 403, self.user)
        self._change_project_privacy_test(public_project, 403, self.user)

    def test_create_private_project_unauthorized(self):
        user_fhx = self.create(User, email='fhx@togglecorp.com')
        user_dummy = self.create(User, email='dummy@test.com')

        self.create(Feature, feature_type=Feature.GENERAL_ACCESS,
                    key=Feature.PRIVATE_PROJECT, title='Private project',
                    users=[user_dummy], email_domains=[])

        self.authenticate(user_fhx)
        self.assert_403(self.create_project('Private test', True))

        self.authenticate(user_dummy)
        self.assert_201(self.create_project('Private test', True))

    def test_get_private_project_detail_unauthorized(self):
        user_fhx = self.create(User, email='fhx@togglecorp.com')
        self.create(Feature, feature_type=Feature.GENERAL_ACCESS,
                    key=Feature.PRIVATE_PROJECT, title='Private project',
                    users=[user_fhx], email_domains=[])

        self.authenticate(user_fhx)
        response = self.create_project('Test private project', True)
        self.assert_201(response)

        self.assertEqual(response.data['is_private'], True)
        self.assertEqual(Project.objects.last().is_private, True)

        other_user = self.create(User)
        self.authenticate(other_user)

        new_private_project_id = response.data['id']
        response = self.client.get(f'/api/v1/projects/{new_private_project_id}/')

        self.assert_404(response)

    def test_private_project_use_public_framework(self):
        """Can use public framework"""
        private_project = self.create(Project, is_private=True)
        public_framework = self.create(AnalysisFramework, is_private=False)

        private_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{private_project.id}/'
        data = {
            'title': private_project.title,
            'analysis_framework': public_framework.id,
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

    def test_private_project_use_private_framework_if_framework_member(self):
        """Can use private framework if member of framework"""
        private_project = self.create(Project, is_private=True)
        private_framework = self.create(AnalysisFramework, is_private=False)

        private_framework.add_member(
            self.user,
            private_framework.get_or_create_default_role()
        )

        private_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{private_project.id}/'
        data = {
            'title': private_project.title,
            'analysis_framework': private_framework.id,
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

    def test_private_project_use_private_framework_if_not_framework_member(self):
        """Can't use private framework if not member of framework"""
        private_project = self.create(Project, is_private=True)
        private_framework = self.create(AnalysisFramework, is_private=True)

        private_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{private_project.id}/'
        data = {
            'title': private_project.title,
            'analysis_framework': private_framework.id,
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        # Framework should not be visible if not member,
        # Just send bad request
        self.assert_400(response)

    def test_private_project_use_private_framework_if_framework_member_no_can_use(self):
        """Can't use private framework if member of framework but no can_use permission"""
        private_project = self.create(Project, is_private=True)
        private_framework = self.create(AnalysisFramework, is_private=True)

        framework_role_no_permissions = AnalysisFrameworkRole.objects.create()
        private_framework.add_member(
            self.user,
            framework_role_no_permissions
        )

        private_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{private_project.id}/'
        data = {
            'title': private_project.title,
            'analysis_framework': private_framework.id,
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        # Framework should be visible if member,
        # but forbidden if not permission to use in other projects
        self.assert_403(response)

    def test_public_project_use_public_framework(self):
        """Can use public framework"""
        public_project = self.create(Project, is_private=False)
        public_framework = self.create(AnalysisFramework, is_private=False)

        public_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )

        url = f'/api/v1/projects/{public_project.id}/'
        data = {
            'title': public_project.title,
            'analysis_framework': public_framework.id,
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

    def test_public_project_use_private_framework(self):
        """Can't use private framework even if member"""
        public_project = self.create(Project, is_private=False)
        private_framework = self.create(AnalysisFramework, is_private=True)

        public_project.add_member(
            self.user,
            # Test with role which can modify project
            ProjectRole.get_creator_role(),
        )
        private_framework.add_member(
            self.user,
            private_framework.get_or_create_owner_role(),  # Any role will work which
            # has can_use_in_other_projects True
        )

        url = f'/api/v1/projects/{public_project.id}/'
        data = {
            'title': public_project.title,
            'analysis_framework': private_framework.id,
            # ... don't care other fields
        }
        self.authenticate()
        response = self.client.put(url, data)
        self.assert_200(response)

    def test_project_get_with_user_group_field(self):
        # TODO: can make this more generic for other fields as well
        project = self.create(
            Project,
            user_groups=[],
            title='TestProject',
            role=self.admin_role
        )
        # Add usergroup
        ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        # Now get project and validate fields
        url = '/api/v1/projects/{}/'.format(project.pk)
        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        project = response.json()
        assert 'id' in project
        assert 'userGroups' in project
        assert len(project['userGroups']) > 0
        for ug in project['userGroups']:
            assert isinstance(ug, dict)
            assert 'id' in ug
            assert 'title' in ug

    def test_update_project_add_user_group(self):
        project = self.create(
            Project,
            user_groups=[],
            title='TestProject',
            role=self.admin_role
        )

        memberships = ProjectMembership.objects.filter(project=project)
        initial_member_count = memberships.count()

        url = '/api/v1/project-usergroups/'
        data = {
            'project': project.id,
            'usergroup': self.ug1.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        assert response.status_code == 201

        final_memberships = ProjectMembership.objects.filter(project=project)
        final_member_count = final_memberships.count()
        # now check for members
        self.assertEqual(
            initial_member_count + self.ug1.members.all().count() - 1,
            # -1 because usergroup admin and project admin is common
            final_member_count
        )

    def test_update_project_remove_ug(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )
        # Add usergroups
        ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        project_ug2 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug2,
            project=project
        )

        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        # We keep just ug1, and remove ug2
        url = '/api/v1/project-usergroups/{}/'.format(project_ug2.id)

        self.authenticate()
        response = self.client.delete(url)
        self.assert_204(response)

        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        # now check for members
        self.assertEqual(
            # Subtract all members from second group except
            # the two users that are common in both user groups
            initial_member_count - self.ug2.members.all().count() + 2,
            final_member_count
        )

    def test_add_user_to_usergroup(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )
        # Add usergroups
        project_ug1 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        # Create a new user and add it to project_ug1
        newUser = self.create(User)

        from user_group.models import GroupMembership
        GroupMembership.objects.create(
            member=newUser,
            group=project_ug1.usergroup
        )
        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        self.assertEqual(initial_member_count + 1, final_member_count)

    def test_remove_user_in_only_one_usergroup(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )
        # Add usergroups
        project_ug1 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )

        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        from user_group.models import GroupMembership

        GroupMembership.objects.filter(
            member=self.user1,  # user1 belongs to ug1
            group=project_ug1.usergroup
        ).delete()

        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        self.assertEqual(initial_member_count - 1, final_member_count)

    def test_remove_user_in_only_multiple_usergroups(self):
        project = self.create(
            Project,
            title='TestProject',
            user_groups=[],
            role=self.admin_role
        )

        # Add usergroups
        project_ug1 = ProjectUserGroupMembership.objects.create(
            usergroup=self.ug1,
            project=project
        )
        ProjectUserGroupMembership.objects.create(
            usergroup=self.ug2,
            project=project
        )

        initial_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()

        from user_group.models import GroupMembership

        GroupMembership.objects.filter(
            member=self.user2,  # user1 belongs to ug1 and ug2
            group=project_ug1.usergroup
        ).delete()

        final_member_count = ProjectMembership.objects.filter(
            project=project
        ).count()
        # Should be no change in membeship as user2 is member from ug2 as well
        self.assertEqual(initial_member_count, final_member_count)

    def test_member_of(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = '/api/v1/projects/member-of/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], project.id)

        url = '/api/v1/projects/member-of/?user={}'.format(test_user.id)

        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 0)

    def test_project_of_user(self):
        test_user = self.create(User)

        url = '/api/v1/projects/member-of/?user={}'.format(test_user.id)
        self.authenticate()

        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 0)

        url = '/api/v1/projects/member-of/'
        # authenticate test_user
        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 0)

        # Create another project and add test_user to the project
        project1 = self.create(Project, role=self.admin_role)
        project1.add_member(test_user)

        # authenticate test_user
        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(response.data['count'], 1)
        self.assertEqual(response.data['results'][0]['id'], project1.id)

    def test_add_member(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = '/api/v1/project-memberships/'
        data = {
            'member': test_user.pk,
            'project': project.pk,
            'role': self.normal_role.id,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_201(response)

        self.assertEqual(response.data['role'], data['role'])
        self.assertEqual(response.data['member'], data['member'])
        self.assertEqual(response.data['project'], data['project'])

    def test_add_member_unexistent_role(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = '/api/v1/project-memberships/'
        data = {
            'member': test_user.pk,
            'project': project.pk,
            'role': 9999
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)
        assert 'errors' in response.data

    def test_add_member_duplicate(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        project.add_member(test_user)

        url = '/api/v1/project-memberships/'
        data = {
            'member': test_user.pk,
            'project': project.pk,
        }

        self.authenticate()
        response = self.client.post(url, data)
        self.assert_400(response)
        assert 'errors' in response.data

    def test_options(self):
        url = '/api/v1/project-options/'

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

    def test_join_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)

        url = '/api/v1/projects/{}/join/'.format(project.id)

        self.authenticate(test_user)
        response = self.client.post(url)
        self.assert_201(response)

        self.assertEqual(response.data['project']['id'], project.id)
        self.assertEqual(response.data['requested_by']['id'], test_user.id)

    def test_accept_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/requests/{}/accept/'.format(
            project.id,
            request.id,
        )

        self.authenticate()
        response = self.client.post(url)
        self.assert_200(response)

        self.assertEqual(response.data['responded_by']['id'], self.user.id)
        self.assertEqual(response.data['status'], 'accepted')
        membership = ProjectMembership.objects.filter(
            project=project,
            member=test_user,
            role=self.normal_role,
        )
        self.assertEqual(membership.count(), 1)

    def test_reject_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/requests/{}/reject/'.format(
            project.id,
            request.id,
        )

        self.authenticate()
        response = self.client.post(url)
        self.assert_200(response)

        self.assertEqual(response.data['responded_by']['id'], self.user.id)
        self.assertEqual(response.data['status'], 'rejected')
        membership = ProjectMembership.objects.filter(
            project=project,
            member=test_user,
            role=self.normal_role
        )
        self.assertEqual(membership.count(), 0)

    def test_cancel_request(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )

        url = '/api/v1/projects/{}/join/cancel/'.format(project.id)

        self.authenticate(test_user)
        response = self.client.post(url)
        self.assert_204(response)

        request = ProjectJoinRequest.objects.filter(id=request.id)
        self.assertEqual(request.count(), 0)

    def test_list_request(self):
        project = self.create(Project, role=self.admin_role)
        self.create(ProjectJoinRequest, project=project)
        self.create(ProjectJoinRequest, project=project)
        self.create(ProjectJoinRequest, project=project)

        url = '/api/v1/projects/{}/requests/'.format(project.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        self.assertEqual(len(response.data['results']), 3)
        self.assertEqual(response.data['count'], 3)

    def test_delete_project_admin(self):
        project = self.create(Project, role=self.admin_role)
        url = '/api/v1/projects/{}/'.format(project.id)
        self.authenticate()
        response = self.client.delete(url)
        self.assert_204(response)

    def test_delete_project_normal(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)

        project.add_member(user)

        url = '/api/v1/projects/{}/'.format(project.id)
        self.authenticate(user)

        response = self.client.delete(url)
        self.assert_403(response)

    def test_get_project_role(self):
        project = self.create(Project, role=self.admin_role)
        user = self.create(User)
        project.add_member(user)

        url = '/api/v1/project-roles/'

        self.authenticate()

        response = self.client.get(url)
        self.assert_200(response)

        data = response.json()
        assert "results" in data
        for x in data["results"]:
            assert "setupPermissions" in x
            assert "assessmentPermissions" in x
            assert "entryPermissions" in x
            assert "leadPermissions" in x
            assert "exportPermissions" in x

    def test_can_modify(self):
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        project.add_member(test_user)
        assert project.can_modify(self.user)
        assert not project.can_modify(test_user)

    def test_auto_accept(self):
        # When a project member is added, if there is a pending
        # request for that user, auto accept that request
        project = self.create(Project, role=self.admin_role)
        test_user = self.create(User)
        request = ProjectJoinRequest.objects.create(
            project=project,
            requested_by=test_user,
            role=self.admin_role
        )
        project.add_member(test_user, self.normal_role, self.user)

        request = ProjectJoinRequest.objects.get(id=request.id)
        self.assertEqual(request.status, 'accepted')
        self.assertEqual(request.responded_by, self.user)

    def _test_status_filter(self, and_conditions):
        status = self.create(ProjectStatus, and_conditions=and_conditions)
        self.create(
            ProjectStatusCondition,
            project_status=status,
            condition_type=ProjectStatusCondition.NO_LEADS_CREATED,
            days=5,
        )
        self.create(
            ProjectStatusCondition,
            project_status=status,
            condition_type=ProjectStatusCondition.NO_ENTRIES_CREATED,
            days=5,
        )

        old_date = timezone.now() - timedelta(days=8)

        # One with old lead
        project1 = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project1)
        Lead.objects.filter(pk=lead.pk).update(created_at=old_date)
        Lead.objects.get(pk=lead.pk).save()

        # One with latest lead
        project2 = self.create(Project, role=self.admin_role)
        self.create(Lead, project=project2)

        # One empty
        self.create(Project, role=self.admin_role)

        # One with latest lead but expired entry
        project4 = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project4)
        entry = self.create(Entry, lead=lead)
        Entry.objects.filter(pk=entry.pk).update(created_at=old_date)
        Lead.objects.get(pk=lead.pk).save()

        # One with expired lead and expired entry
        project5 = self.create(Project, role=self.admin_role)
        lead = self.create(Lead, project=project5)
        entry = self.create(Entry, lead=lead)
        Lead.objects.filter(pk=lead.pk).update(created_at=old_date)
        Entry.objects.filter(pk=entry.pk).update(created_at=old_date)
        Lead.objects.get(pk=lead.pk).save()

        url = '/api/v1/projects/?status={}'.format(status.id)

        self.authenticate()
        response = self.client.get(url)
        self.assert_200(response)

        expected = [
            project1.id,
            project5.id,
        ] if and_conditions else [
            project1.id,
            project2.id,
            project4.id,
            project5.id,
        ]
        obtained = [r['id'] for r in response.data['results']]

        self.assertEqual(response.data['count'], len(expected))
        self.assertTrue(sorted(expected) == sorted(obtained))

    def test_status_filter_or_conditions(self):
        self._test_status_filter(False)

    def test_status_filter_and_conditions(self):
        self._test_status_filter(True)

    def test_involvment_filter(self):
        project1 = self.create(Project, role=self.admin_role)
        project2 = self.create(Project, role=self.admin_role)
        project3 = self.create(Project, role=self.admin_role)

        test_user = self.create(User)
        project1.add_member(test_user, role=self.normal_role)
        project2.add_member(test_user, role=self.normal_role)

        url = '/api/v1/projects/?involvement=my_projects'

        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        expected = [
            project1.id,
            project2.id
        ]
        obtained = [r['id'] for r in response.data['results']]

        self.assertEqual(response.data['count'], len(expected))
        self.assertTrue(sorted(expected) == sorted(obtained))

        url = '/api/v1/projects/?involvement=not_my_projects'

        self.authenticate(test_user)
        response = self.client.get(url)
        self.assert_200(response)

        expected = [
            project3.id,
        ]
        obtained = [r['id'] for r in response.data['results']]

        self.assertEqual(response.data['count'], len(expected))
        self.assertTrue(sorted(expected) == sorted(obtained))

    def test_project_role_level(self):
        project = self.create(Project, role=self.smaller_admin_role)
        test_user1 = self.create(User)
        test_user2 = self.create(User)
        m1 = project.add_member(test_user1, role=self.normal_role)
        m2 = project.add_member(test_user2, role=self.admin_role)

        url1 = '/api/v1/project-memberships/{}/'.format(m1.id)
        url2 = '/api/v1/project-memberships/{}/'.format(m2.id)

        # Initial condition: We are Admin
        self.authenticate()

        # Condition 1: We are trying to change a normal
        # user's role to Clairvaoyant One
        data = {
            'role': self.admin_role.id,
        }
        response = self.client.patch(url1, data)
        self.assert_400(response)

        # Condition 2: We are trying to change a normal
        # user's role to Admin
        data = {
            'role': self.smaller_admin_role.id,
        }
        response = self.client.patch(url1, data)
        self.assert_200(response)

        # Condition 3: We are trying to change a CO user
        # when he/she is the only CO user in the project
        data = {
            'role': self.smaller_admin_role.id,
        }
        response = self.client.patch(url2, data)
        self.assert_403(response)

        # Condition 4: We are trying to delete a CO user
        # when he/she is the only CO user in the project
        response = self.client.delete(url2)
        self.assert_403(response)

        # Initial condition: We are a CO user
        self.authenticate(test_user2)

        # Condition 5: We are CO user and are trying to
        # delete ourself when there is no other CO user
        # in the project.
        response = self.client.delete(url2)
        self.assert_403(response)

        # Condition 6: We are CO user and are trying to
        # delete ourself when there is at least one other CO user
        # in the project.
        ProjectMembership.objects.filter(
            project=project,
            member=self.user,
        ).update(role=self.admin_role)

        response = self.client.delete(url2)
        self.assert_204(response)

    def _change_project_privacy_test(self, project, status=403, user=None):
        url = f'/api/v1/projects/{project.id}/'

        changed_privacy = not project.is_private
        put_data = {
            'title': project.title,
            'is_private': changed_privacy,
            # Other fields we don't care
        }
        self.authenticate(user)
        response = self.client.put(url, put_data)
        self.assertEqual(response.status_code, status)

        # Try patching, should give 403 as well
        patch_data = {'is_private': changed_privacy}
        response = self.client.patch(url, patch_data)
        self.assertEqual(response.status_code, status)

    def test_project_entries_stats(self):
        project_user = self.create(User)
        non_project_user = self.create(User)

        af = self.create(AnalysisFramework)
        project = self.create(Project, analysis_framework=af)
        project.add_member(project_user)

        w_data = entry_stats_data.WIDGET_DATA
        a_data = entry_stats_data.ATTRIBUTE_DATA

        lead = self.create(Lead, project=project)
        entry = self.create(
            Entry,
            project=project, analysis_framework=af, lead=lead, entry_type=Entry.EXCERPT,
        )

        # Create widgets, attributes and configs
        invalid_stat_config = {}
        valid_stat_config = {}

        for widget_identifier, data_identifier, config_kwargs in [
            ('widget_1d', 'matrix1dWidget', {}),
            ('widget_2d', 'matrix2dWidget', {}),
            ('geo_widget', 'geoWidget', {}),
            (
                'severity_widget',
                'conditionalWidget',
                {
                    'is_conditional_widget': True,
                    'selectors': ['widgets', 0, 'widget'],
                    'widget_key': 'scalewidget-1',
                    'widget_type': 'scaleWidget',
                },
            ),
            ('reliability_widget', 'scaleWidget', {}),
            ('affected_groups_widget', 'multiselectWidget', {}),
            ('specific_needs_groups_widget', 'multiselectWidget', {}),
        ]:
            widget = self.create(
                Widget, analysis_framework=af,
                properties={'data': w_data[data_identifier]},
            )
            self.create(Attribute, entry=entry, widget=widget, data=a_data[data_identifier])
            valid_stat_config[widget_identifier] = {
                'pk': widget.pk,
                **config_kwargs,
            }
            invalid_stat_config[widget_identifier] = {'pk': 0}

        url = f'/api/v1/projects/{project.pk}/entries-viz/'

        # 404 for non project user
        self.authenticate(non_project_user)
        response = self.client.get(url)
        self.assert_404(response)

        self.authenticate(project_user)

        # 404 for project user if config is not set
        response = self.client.get(url)
        self.assert_404(response)

        af.properties = {'stats_config': invalid_stat_config}
        af.save()

        # 202 if config is set
        response = self.client.get(url)
        self.assert_202(response)

        # 500 if invalid config is set and stat is generated
        _generate_entry_stats(project.pk)
        response = self.client.get(url)
        self.assert_500(response)

        af.properties = {'stats_config': valid_stat_config}
        af.save()

        # 302 (Redirect to data file) if valid config is set and stat is generated
        _generate_entry_stats(project.pk)
        response = self.client.get(url)
        self.assert_302(response)
