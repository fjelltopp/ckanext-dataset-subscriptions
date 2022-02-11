import copy
import os
from ckan.plugins import toolkit
import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
from twilio.rest import Client
from datetime import timedelta, datetime
from ckanext.dataset_subscriptions import actions


CUSTOM_FIELDS = [
    {'name': 'phonenumber', 'default': ''},
    {'name': 'activity_streams_whatsapp_notifications', 'default': False},
]

DATASET_SUBSCRIPTIONS = 'dataset_subscriptions'


@toolkit.chained_action
@toolkit.side_effect_free
def user_show(original_action, context, data_dict):
    user = original_action(context, data_dict)
    user_obj = _get_user_obj(context)

    plugin_extras = _init_plugin_extras(user_obj.plugin_extras)
    dataset_subscriptions_extras = _validate_plugin_extras(plugin_extras[DATASET_SUBSCRIPTIONS])
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

    plugin_extras = _init_plugin_extras(user_obj.plugin_extras)
    dataset_subscriptions_extras = plugin_extras[DATASET_SUBSCRIPTIONS]
    for field in CUSTOM_FIELDS:
        dataset_subscriptions_extras[field['name']] = data_dict[field['name']]
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

    plugin_extras = _init_plugin_extras(user_obj.plugin_extras)
    dataset_subscriptions_extras = plugin_extras[DATASET_SUBSCRIPTIONS]
    for field in CUSTOM_FIELDS:
        dataset_subscriptions_extras[field['name']] = data_dict[field['name']]
    user_obj.plugin_extras = plugin_extras
    model_ = context.get('model', model)
    model_.Session.commit()

    for field in CUSTOM_FIELDS:
        user_dict[field['name']] = dataset_subscriptions_extras[field['name']]
    return user_dict


def _init_plugin_extras(plugin_extras):
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


def _validate_plugin_extras(extras):
    if not extras:
        extras = {}
    out_dict = {}
    for field in CUSTOM_FIELDS:
        out_dict[field['name']] = extras.get(field['name'], field['default'])
    return out_dict


def get_phonenumber(user_dict):
    activity_streams_whatsapp_notifications = True
    if activity_streams_whatsapp_notifications:
        try:
            phonenumber = "+48123123123"
            return phonenumber
        except KeyError:
            return False


def send_whatsapp_notifications(context, data_dict):
    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    users = logic.get_action('user_list')(context, {'all_fields': True})
    for user in users:
        user = logic.get_action('user_show')(context, {'id': user['id'],
                                                       'include_plugin_extras': True})
        if get_phonenumber(user):
            prepare_whatsapp_notifications(user)


def prepare_whatsapp_notifications(user):
    whatsapp_notifications_since = toolkit.config.get(
            'ckanext.dataset_subscriptions.whatsapp_notifications_hours_since', 1)
    whatsapp_notifications_since = int(whatsapp_notifications_since)
    whatsapp_notifications_since = timedelta(hours=whatsapp_notifications_since)
    whatsapp_notifications_since = (datetime.utcnow()
                                    - whatsapp_notifications_since)
    activity_stream_last_viewed = (
            model.Dashboard.get(user['id']).activity_stream_last_viewed)
    since = max(whatsapp_notifications_since, activity_stream_last_viewed)
    dms_whatsapp_notification_provider(user, since)


def dms_whatsapp_notification_provider(user_dict, since):
    context = {'model': model, 'session': model.Session,
               'user': user_dict['id']}
    activity_list = logic.get_action('dashboard_activity_list')(context, {})
    dataset_activity_list = [activity for activity in activity_list
                             if activity['user_id'] != user_dict['id']
                             and 'package' in activity['activity_type']]
    # We want a notification per changed dataset, not a list of all changes
    timestamp_sorted_activity_list = sorted(dataset_activity_list,
                                            key=lambda item: item['timestamp'])
    deduplicated_activity_list = list({item["object_id"]:
                                       item for item in timestamp_sorted_activity_list}.values())
    activity_list_with_dataset_name = actions._add_dataset_name_to_activity_list(deduplicated_activity_list, context)
    recent_activity_list = actions._filter_out_old_activites(activity_list_with_dataset_name, since)
    if recent_activity_list:
        user_phonenumber = get_phonenumber(user_dict)
        return send_whatsapp_notification(recent_activity_list, user_phonenumber)


def send_whatsapp_notification(activities, phonenumber):
    account_sid = toolkit.config.get('ckanext.dataset_subscriptions.twilio_account_sid')
    auth_token = toolkit.config.get('ckanext.dataset_subscriptions.twilio_auth_token')
    sender_nr = toolkit.config.get('ckanext.dataset_subscriptions.whatsapp_sender_nr')
    client = Client(account_sid, auth_token)
    from_nr = "whatsapp:" + sender_nr
    to_nr = "whatsapp:" + phonenumber
    message_body = base.render(
            'dataset-subscriptions_whatsapp_body.j2',
            extra_vars={'activities': activities})
    message = client.messages.create(
                            from_=from_nr,
                            body=message_body,
                            to=to_nr
                            )
    print(message.sid)
    return message.sid
