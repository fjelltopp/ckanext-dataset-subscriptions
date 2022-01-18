import ckanext.dataset_subscriptions.plugin as plugin
from ckan.tests import factories
import ckan.lib.email_notifications as email_notifications
import ckan.tests.helpers as helpers
import pytest
import datetime
import mock


# Create resources
@pytest.mark.ckan_config('ckan.plugins', 'dataset_subscriptions')
@pytest.mark.usefixtures("with_plugins")
@pytest.mark.usefixtures("clean_db")
def create_resources(create_resource):
    subscribed_user = factories.User(name='user5', activity_streams_email_notifications=True)
    active_user = factories.User(name='user6')
    organization = factories.Organization(
        users=[
            {'name': subscribed_user['name'], 'capacity': 'member'},
            {'name': active_user['name'], 'capacity': 'editor'}
        ]
    )
    if create_resource:
        dataset = factories.Dataset(
            owner_org=organization['id'],
            type='test-schema',
            user=active_user
        )
        helpers.call_action(
            "follow_dataset", context={"user": subscribed_user["name"]}, **dataset
        )
        factories.Resource(
                 package_id=dataset['id'],
                 user=active_user
        )
    return subscribed_user

# Test with no dataset updates
@pytest.mark.usefixtures("clean_db")
def test_with_no_activity():
    user=create_resources(create_resource=False)
    activities = [activity for activity in 
                helpers.call_action("dashboard_activity_list", context={"user": user["id"]})
                if "package" in activity["activity_type"]]
    assert [activity["activity_type"] for activity in activities] == []

# Test with dataset updates
@pytest.mark.usefixtures("clean_db")
def test_with_activity():
    user=create_resources(create_resource=True)
    activity_list = helpers.call_action("dashboard_activity_list", context={"user": user["id"]})
    # We'll be returning only package notifications
    filtered_activity_list = [activity for activity in activity_list
                if "package" in activity["activity_type"]]
    assert ["package" in activity["activity_type"] for activity in filtered_activity_list]
    

# Test notification function "injection"
@pytest.mark.usefixtures("with_request_context", "clean_db")
@pytest.mark.ckan_config("ckan.activity_streams_email_notifications", True)
@mock.patch("ckan.logic.action.update.request")
def test_send_notification(mock_request):
    user=create_resources(create_resource=True)
    notifications = email_notifications.get_notifications(user, datetime.datetime.fromtimestamp(3600))
    # we expect two notifications - one for a new dataset and one for a resource
    assert [ "2 new activities from CKAN" in notification["subject"]  for notification
            in notifications ]
