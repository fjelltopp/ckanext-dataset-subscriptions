import pytest
from ckan.tests import helpers
from ckan.tests import factories


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
