import pytest
from ckan.tests import helpers, factories


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
        "activity_streams_whatsapp_notifications": True
    }

    created_user = helpers.call_action('user_create', context=sysadmin_context, **user_dict)

    assert created_user["plugin_extras"] == {
        "dataset_subscriptions": {
            "phonenumber": 123,
            "activity_streams_whatsapp_notifications": True
        }
    }


@pytest.mark.usefixtures("clean_db")
@pytest.mark.usefixtures("with_plugins")
def test_user_update_supports_plugin_extras(sysadmin_context):
    user = factories.User()
    user_dict = {**user, **{
        "phonenumber": 123,
        "activity_streams_whatsapp_notifications": True
        }
    }
    updated_user = helpers.call_action('user_update', context=sysadmin_context, **user_dict)

    assert updated_user["plugin_extras"] == {
        "dataset_subscriptions": {
            "phonenumber": 123,
            "activity_streams_whatsapp_notifications": True
        }
    }


@pytest.fixture
def sysadmin_context():
    sysadmin = factories.Sysadmin()
    # helpers.call_action sets 'ignore_auth' to True by default
    context = {'user': sysadmin['name'], 'ignore_auth': False}
    return context
