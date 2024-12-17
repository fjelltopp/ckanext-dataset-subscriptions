import copy
import logging
from ckan.plugins import toolkit
import ckan.model as model
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException

ACCOUNT_SID = toolkit.config.get('ckanext.dataset_subscriptions.twilio_account_sid')
AUTH_TOKEN = toolkit.config.get('ckanext.dataset_subscriptions.twilio_auth_token')


logger = logging.getLogger(__name__)
client = Client(ACCOUNT_SID, AUTH_TOKEN)


CUSTOM_FIELDS = [
    {'name': 'phonenumber', 'default': ''},
    {'name': 'activity_streams_sms_notifications', 'default': False},
    {'name': 'activity_streams_whatsapp_notifications', 'default': False},
]

DATASET_SUBSCRIPTIONS = 'dataset_subscriptions'


@toolkit.chained_action
@toolkit.side_effect_free
def user_show(original_action, context, data_dict):
    user = original_action(context, data_dict)
    user_obj = _get_user_obj(context)

    plugin_extras = _setup_plugin_extras(user_obj.plugin_extras)
    dataset_subscriptions_extras = _init_plugin_extras(plugin_extras[DATASET_SUBSCRIPTIONS])
    for field in CUSTOM_FIELDS:
        user[field['name']] = dataset_subscriptions_extras[field['name']]

    return user


@toolkit.chained_action
def user_create(original_action, context, data_dict):
    for field in CUSTOM_FIELDS:
        if not field['name'] in data_dict:
            data_dict[field['name']] = field['default']

    user_dict = original_action(context, data_dict)
    user_obj = _get_user_obj(context)

    plugin_extras = _setup_plugin_extras(user_obj.plugin_extras)
    dataset_subscriptions_extras = plugin_extras[DATASET_SUBSCRIPTIONS]
    for field in CUSTOM_FIELDS:
        dataset_subscriptions_extras[field['name']] = data_dict[field['name']]
    _validate_plugin_extras(dataset_subscriptions_extras)
    user_obj.plugin_extras = plugin_extras
    model_ = context.get('model', model)
    model_.Session.commit()

    for field in CUSTOM_FIELDS:
        user_dict[field['name']] = dataset_subscriptions_extras[field['name']]
    return user_dict


@toolkit.chained_action
def user_update(original_action, context, data_dict):
    for field in CUSTOM_FIELDS:
        if not field['name'] in data_dict:
            data_dict[field['name']] = field['default']

    user_dict = original_action(context, data_dict)
    user_obj = _get_user_obj(context)

    plugin_extras = _setup_plugin_extras(user_obj.plugin_extras)
    dataset_subscriptions_extras = plugin_extras[DATASET_SUBSCRIPTIONS]
    for field in CUSTOM_FIELDS:
        dataset_subscriptions_extras[field['name']] = data_dict[field['name']]
    _validate_plugin_extras(dataset_subscriptions_extras)
    user_obj.plugin_extras = plugin_extras
    model_ = context.get('model', model)
    model_.Session.commit()

    for field in CUSTOM_FIELDS:
        user_dict[field['name']] = dataset_subscriptions_extras[field['name']]
    return user_dict


@toolkit.chained_action
@toolkit.side_effect_free
def user_list(original_action, context, data_dict):
    user_list = original_action(context, data_dict)
    include_plugin_extras = toolkit.asbool(data_dict.get('include_plugin_extras', False))
    all_fields = toolkit.asbool(data_dict.get('all_fields', True))
    if all_fields and include_plugin_extras:
        for index, user in enumerate(user_list):
            user_list[index] = toolkit.get_action('user_show')(context, {'id': user['name']})
    return user_list


def _setup_plugin_extras(plugin_extras):
    out_dict = copy.deepcopy(plugin_extras)
    if not out_dict:
        out_dict = {}
    if DATASET_SUBSCRIPTIONS not in out_dict:
        out_dict[DATASET_SUBSCRIPTIONS] = {}
    return out_dict


def _get_user_obj(context):
    if 'user_obj' in context:
        return context['user_obj']
    user = context.get('user')
    model_ = context.get('model', model)
    user_obj = model_.User.get(user)
    if not user_obj:
        raise toolkit.ObjectNotFound("User not found")
    return user_obj


def _init_plugin_extras(extras):
    if not extras:
        extras = {}
    out_dict = {}
    for field in CUSTOM_FIELDS:
        out_dict[field['name']] = extras.get(field['name'], field['default'])
    return out_dict


def _validate_plugin_extras(extras):
    errors = {}
    if extras.get('phonenumber'):
        try:
            client.lookups.phone_numbers(extras['phonenumber']).fetch(type=['carrier'])
        except TwilioRestException as e:
            if e.status == 404:
                errors['phonenumber'] = [toolkit._(f'Invalid phonenumber: {extras["phonenumber"]}')]
            else:
                logger.exception(
                    f"Failed to reach Twilio API to verify phonenumber {extras['phonenumber']}",
                    exc_info=True
                )
        except Exception:
            logger.exception(
                f"Failed to reach Twilio API to verify phonenumber {extras['phonenumber']}",
                exc_info=True
            )
    if toolkit.asbool(extras.get('activity_streams_sms_notifications')):
        if not extras.get('phonenumber'):
            errors['activity_streams_sms_notifications'] = [
                toolkit._('No phone number given')
            ]
    if toolkit.asbool(extras.get('activity_streams_whatsapp_notifications')):
        if not extras.get('phonenumber'):
            errors['activity_streams_whatsapp_notifications'] = [
                toolkit._('No phone number given')
            ]
    if errors:
        raise toolkit.ValidationError(errors)
