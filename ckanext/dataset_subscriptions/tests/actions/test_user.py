import pytest
from ckan.plugins import toolkit
from ckan.tests import helpers
from ckan.tests import factories
from unittest import mock
from twilio.base.exceptions import TwilioRestException
from contextlib import nullcontext


@pytest.mark.usefixtures("with_plugins", "clean_db")
class TestUserActions():

    def test_user_create_supports_plugin_extras(self, sysadmin_context):
        user_dict = {
            "name": "test_user_001",
            "fullname": "Mr. Test User",
            "password": "fjelltopp",
            "display_name": "Mr. Test User",
            "email": "test_user_001@ckan.org",
            "phonenumber": "+447855474558",
            "activity_streams_sms_notifications": True
        }
        created_user = helpers.call_action('user_create', context=sysadmin_context, **user_dict)
        for key in ["phonenumber", "activity_streams_sms_notifications"]:
            assert created_user[key] == user_dict[key]

    def test_user_update_supports_plugin_extras(self, sysadmin_context):
        user = factories.User()
        user_dict = {**user, **{
            "phonenumber": 123,
            "activity_streams_sms_notifications": True
            }
        }
        helpers.call_action('user_update', **user_dict)
        updated_user = helpers.call_action(
            'user_show',
            context=sysadmin_context,
            include_plugin_extras=True,
            **user_dict
        )
        for key in ["phonenumber", "activity_streams_sms_notifications"]:
            assert updated_user[key] == user_dict[key]

    @mock.patch('ckanext.dataset_subscriptions.actions.user.client')
    def test_user_validate_plugin_extras_valid_phonenumber(self, client_mock, sysadmin_context):
        phonenumber = 123
        client_mock.lookups.phone_numbers(phonenumber).fetch.side_effect = TwilioRestException(404, "not found")
        user_dict = {
            "name": "test_user_001",
            "fullname": "Mr. Test User",
            "password": "fjelltopp",
            "display_name": "Mr. Test User",
            "email": "test_user_001@ckan.org",
            "phonenumber": phonenumber,
            "activity_streams_sms_notifications": True
        }
        with pytest.raises(toolkit.ValidationError, match="Invalid phonenumber"):
            helpers.call_action('user_create', context=sysadmin_context, **user_dict)

    @pytest.mark.parametrize('phonenumber, enable_sms, enable_whatsapp, expectation', [
        ("", False, False, nullcontext(1)),
        ("", False, True, pytest.raises(toolkit.ValidationError)),
        ("", True, False, pytest.raises(toolkit.ValidationError)),
        ("", True, True, pytest.raises(toolkit.ValidationError))
    ])
    def test_user_validate_plugin_extras_requires_phonenumber(self, phonenumber, enable_sms,
                                                              enable_whatsapp, expectation, sysadmin_context):
        user_dict = {
            "name": "test_user_001",
            "fullname": "Mr. Test User",
            "password": "fjelltopp",
            "display_name": "Mr. Test User",
            "email": "test_user_001@ckan.org",
            "phonenumber": phonenumber,
            "activity_streams_sms_notifications": enable_sms,
            "activity_streams_whatsapp_notifications": enable_whatsapp
        }
        with expectation:
            helpers.call_action('user_create', context=sysadmin_context, **user_dict)
