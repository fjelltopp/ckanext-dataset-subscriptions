import pytest
from ckan.tests import helpers
from ckan.tests import factories as ckan_factories
from ckanext.dataset_subscriptions.tests import factories
from ckanext.dataset_subscriptions.actions import sms_notifications
from unittest import mock


@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
def test_user_create_supports_plugin_extras(sysadmin_context):
    user_dict = {
        "name": "test_user_001",
        "fullname": "Mr. Test User",
        "password": "fjelltopp",
        "display_name": "Mr. Test User",
        "email": "test_user_001@ckan.org",
        "phonenumber": 123,
        "activity_streams_sms_notifications": True
    }

    created_user = helpers.call_action('user_create', context=sysadmin_context, **user_dict)

    for key in ["phonenumber", "activity_streams_sms_notifications"]:
        assert created_user[key] == user_dict[key]


@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
def test_user_update_supports_plugin_extras(sysadmin_context):
    user = factories.User()
    user_dict = {**user, **{
        "phonenumber": 123,
        "activity_streams_sms_notifications": True
        }
    }
    helpers.call_action('user_update', **user_dict)
    updated_user = helpers.call_action('user_show', context=sysadmin_context, include_plugin_extras=True, **user_dict)

    for key in ["phonenumber", "activity_streams_sms_notifications"]:
        assert updated_user[key] == user_dict[key]


@pytest.fixture
def sysadmin_context():
    sysadmin = ckan_factories.Sysadmin()
    # helpers.call_action sets 'ignore_auth' to True by default
    context = {'user': sysadmin['name'], 'ignore_auth': False}
    return context


@pytest.mark.ckan_config('ckan.plugins')
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.usefixtures("clean_db")
def create_user_with_resources(with_activity, with_notifications_enabled):
    if with_notifications_enabled:
        notifications_enabled = True
    else:
        notifications_enabled = False
    subscribed_user = factories.User(name='user1',
                                     activity_streams_sms_notifications=notifications_enabled,
                                     phonenumber="+1234")
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
def test_get_phonenumber(notifications_enabled):
    user = create_user_with_resources(with_activity=True, with_notifications_enabled=notifications_enabled)
    phonenumber = sms_notifications.get_phonenumber(user)
    assert phonenumber == "+1234"


@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.parametrize("notifications_enabled", [(False), (True)])
def test_sms_notifications_disabled_enabled(notifications_enabled):
    user = create_user_with_resources(with_activity=True, with_notifications_enabled=notifications_enabled)
    notifications = sms_notifications.sms_notifications_enabled(user)
    assert notifications == notifications_enabled


@pytest.mark.usefixtures("with_request_context")
@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
@mock.patch('ckanext.dataset_subscriptions.actions.sms_notifications.client.messages.create')
def test_if_notifications_are_generated(create_message_mock, sysadmin_context):
    create_user_with_resources(with_activity=True, with_notifications_enabled=True)
    expected_sid = 'SM87105da94bff44b999e4e6eb90d8eb6a'
    create_message_mock.return_value.sid = expected_sid
    sid = helpers.call_action("send_sms_notifications")
    print(sid)
    assert create_message_mock.called is True
    assert sid[0] == expected_sid
