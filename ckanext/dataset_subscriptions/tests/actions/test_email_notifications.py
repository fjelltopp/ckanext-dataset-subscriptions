from ckan.tests import factories as ckan_factories
from ckanext.dataset_subscriptions.tests import factories as plugin_factories
import ckanext.activity.email_notifications as email_notifications
import ckan.tests.helpers as helpers
import pytest
import datetime


@pytest.mark.ckan_config('ckan.plugins')
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.usefixtures("clean_db")
def create_user_with_resources(with_activity):
    subscribed_user = plugin_factories.User(
        name='user1',
        activity_streams_email_notifications=True
    )
    active_user = plugin_factories.User(name='user2')
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
def test_with_no_dataset_updates():
    user = create_user_with_resources(with_activity=False)
    activities = [activity for activity in
                  helpers.call_action("dashboard_activity_list",
                                      context={"user": user["id"]})
                  if "package" in activity["activity_type"]]
    assert [activity["activity_type"] for activity in activities] == []


@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
def test_with_dataset_updates():
    user = create_user_with_resources(with_activity=True)
    activity_list = helpers.call_action("dashboard_activity_list",
                                        context={"user": user["id"]})
    # We'll be returning only package notifications
    filtered_activity_list = [activity for activity in activity_list
                              if "package" in activity["activity_type"]]
    assert ["package" in activity["activity_type"]
            for activity in filtered_activity_list]


@pytest.mark.usefixtures("with_request_context")
@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.ckan_config("ckan.activity_streams_email_notifications", True)
def test_send_notification_injection():
    user = create_user_with_resources(with_activity=True)
    notifications = email_notifications.get_notifications(user,
                                                          datetime.datetime.fromtimestamp(3600))
    # we expect two notifications, one for a new dataset and one for a resource
    assert ["2 new activities from CKAN" in notification["subject"]
            for notification in notifications]


@pytest.mark.usefixtures("with_request_context")
@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.ckan_config("ckan.activity_streams_email_notifications", True)
def test_dataset_subscriptions_notification_email_flow(mail_server):
    create_user_with_resources(with_activity=True)
    helpers.call_action("send_email_notifications")
    msgs = mail_server.get_smtp_messages()
    assert len(msgs) == 1
