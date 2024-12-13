import pytest
from ckan.tests import helpers
from ckan.tests import factories as ckan_factories
from ckanext.dataset_subscriptions.tests import factories
from ckanext.dataset_subscriptions.actions import twilio_notifications
from unittest import mock


@pytest.mark.ckan_config('ckan.plugins')
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.usefixtures("clean_db")
def create_user_with_resources(with_activity,
                               sms_notifications_enabled,
                               whatsapp_notifications_enabled):
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


@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.parametrize("notifications_enabled", [(False), (True)])
def test_sms_notifications_disabled_enabled(notifications_enabled):
    user = create_user_with_resources(True, notifications_enabled, False)
    notifications = twilio_notifications._sms_notifications_enabled(user)
    assert notifications == notifications_enabled


@pytest.mark.usefixtures("with_request_context")
@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
@mock.patch('ckanext.dataset_subscriptions.actions.twilio_notifications.client.messages.create')
def test_if_sms_notifications_are_generated(create_message_mock, sysadmin_context):
    create_user_with_resources(True, True, False)
    expected_sid = 'SM87105da94bff44b999e4e6eb90d8eb6a'
    create_message_mock.return_value.sid = expected_sid
    sid = helpers.call_action("send_sms_notifications")
    print(sid)
    assert create_message_mock.called is True
    assert sid[0] == expected_sid


@pytest.mark.usefixtures("with_request_context")
@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
@mock.patch('ckanext.dataset_subscriptions.actions.twilio_notifications.client.messages.create')
def test_if_whatsapp_notifications_are_generated(create_message_mock, sysadmin_context):
    create_user_with_resources(True, False, True)
    expected_sid = 'SM87105da94bff44b999e4e6eb90d8eb6a'
    create_message_mock.return_value.sid = expected_sid
    sid = helpers.call_action("send_sms_notifications")
    print(sid)
    assert create_message_mock.called is True
    assert sid[0] == expected_sid
    call_args = dict(create_message_mock.call_args.kwargs.items())
    assert 'whatsapp:+' in call_args['to']
    assert 'whatsapp:+' in call_args['from_']

