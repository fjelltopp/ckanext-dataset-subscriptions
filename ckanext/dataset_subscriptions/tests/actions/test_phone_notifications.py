import pytest
from ckan.tests import helpers
from ckan.tests import factories as ckan_factories
from ckanext.dataset_subscriptions.tests import factories
from ckanext.dataset_subscriptions.actions import phone_notifications
from unittest import mock
import re


# Whatsapp messages must conform to preapproved templates created in Twilio.
# Copy templates here as a regex replacing placeholders e.g. {{1}} with (.*)
WHATSAPP_MESSAGE_TEMPLATES = [
    r"(.*) datasets that you are following have recently been updated in (.*)",
    r"(.*) dataset that you are following has recently been updated in (.*)"
]


def _matches_whatsapp_template(message):
    for template in WHATSAPP_MESSAGE_TEMPLATES:
        if re.compile(template).search(message):
            return True
    return False


@pytest.mark.ckan_config('ckan.plugins')
def create_user_with_resources(with_activity, sms_notifications_enabled, whatsapp_notifications_enabled):
    subscribed_user = factories.User(
        name='user1',
        activity_streams_sms_notifications=sms_notifications_enabled,
        activity_streams_whatsapp_notifications=whatsapp_notifications_enabled,
        phonenumber="+1234"
    )
    active_user = factories.User(name='user2')
    organization = ckan_factories.Organization(
        users=[
            {'name': subscribed_user['name'], 'capacity': 'member'},
            {'name': active_user['name'], 'capacity': 'editor'}
        ]
    )
    if with_activity:
        dataset = ckan_factories.Dataset(
            owner_org=organization['id'],
            type='test-schema',
            user=active_user
        )
        helpers.call_action(
            "follow_dataset", context={"user": subscribed_user["name"]},
            **dataset
            )
        ckan_factories.Resource(
                package_id=dataset['id'],
                user=active_user
        )
    return subscribed_user


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestPhoneNotifications():

    @pytest.mark.parametrize("notifications_enabled", [(False), (True)])
    def test_sms_notifications_disabled_enabled(self, notifications_enabled):
        user = create_user_with_resources(True, notifications_enabled, False)
        notifications = phone_notifications._sms_notifications_enabled(user, {})
        assert notifications == notifications_enabled

    @pytest.mark.usefixtures("with_request_context")
    @mock.patch('ckanext.dataset_subscriptions.actions.phone_notifications.client.messages.create')
    def test_if_sms_notifications_are_generated(self, create_message_mock, sysadmin_context):
        create_user_with_resources(True, True, False)
        expected_sid = 'SM87105da94bff44b999e4e6eb90d8eb6a'
        create_message_mock.return_value.sid = expected_sid
        sid = helpers.call_action("send_phone_notifications")
        assert create_message_mock.called is True
        assert sid[0] == expected_sid

    @pytest.mark.usefixtures("with_request_context")
    @mock.patch('ckanext.dataset_subscriptions.actions.phone_notifications.client.messages.create')
    def test_if_whatsapp_notifications_are_generated(self, create_message_mock, sysadmin_context):
        create_user_with_resources(True, False, True)
        expected_sid = 'SM87105da94bff44b999e4e6eb90d8eb6a'
        create_message_mock.return_value.sid = expected_sid
        sid = helpers.call_action("send_phone_notifications")
        assert create_message_mock.called is True
        assert sid[0] == expected_sid
        call_args = dict(create_message_mock.call_args.kwargs.items())
        assert 'whatsapp:+' in call_args['to']
        assert 'whatsapp:+' in call_args['from_']
        assert _matches_whatsapp_template(call_args['body'])

    @pytest.mark.parametrize('recent_activities', [[1], [1, 2, 3, 4]])
    def test_whatsapp_message_complies_with_templates(self, recent_activities):
        """
        Whatsapp messages must comply with a template preapproved through twilio
        https://www.twilio.com/docs/whatsapp/tutorial/send-whatsapp-notification-messages-templates
        """
        header = phone_notifications._create_message_header(recent_activities)
        assert _matches_whatsapp_template(header)
