import copy
import logging
from ckan.plugins import toolkit
import ckan.lib.base as base
import ckan.logic as logic
import ckan.model as model
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import timedelta, datetime
from ckanext.dataset_subscriptions import helpers


logger = logging.getLogger(__name__)


ACCOUNT_SID = toolkit.config.get('ckanext.dataset_subscriptions.twilio_account_sid')
AUTH_TOKEN = toolkit.config.get('ckanext.dataset_subscriptions.twilio_auth_token')
SENDER_NR = toolkit.config.get('ckanext.dataset_subscriptions.whatsapp_sender_nr')
client = Client(ACCOUNT_SID, AUTH_TOKEN)


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


def whatsapp_notifications_enabled(user_dict):
    if "activity_streams_whatsapp_notifications" in user_dict and "phonenumber" in user_dict:
        if user_dict["activity_streams_whatsapp_notifications"] and user_dict["phonenumber"]:
            return True
    return False


def get_phonenumber(user_dict):
    phonenumber = user_dict["phonenumber"]
    return phonenumber


def send_whatsapp_notifications(context, data_dict):
    context = {'model': model, 'session': model.Session, 'ignore_auth': True}
    users = logic.get_action('user_list')(context, {'all_fields': True})
    notification_sids = []
    for user in users:
        user = logic.get_action('user_show')(context, {'id': user['id'],
                                                       'include_plugin_extras': False})
        if whatsapp_notifications_enabled:
            get_phonenumber(user)
            notification_sids.append(prepare_whatsapp_notifications(user))
    return notification_sids


def _whatsapp_notification_time_delta_utc():
    since_hours = toolkit.config.get(
            'ckanext.dataset_subscriptions.whatsapp_notifications_hours_since', 1)
    since_delta = timedelta(hours=int(since_hours))
    since_datetime = (datetime.utcnow() - since_delta)
    return since_datetime


def prepare_whatsapp_notifications(user):
    whatsapp_notifications_since = _whatsapp_notification_time_delta_utc()
    activity_stream_last_viewed = (
            model.Dashboard.get(user['id']).activity_stream_last_viewed)
    since = max(whatsapp_notifications_since, activity_stream_last_viewed)
    return dms_whatsapp_notification_provider(user, since)


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
    activity_list_with_dataset_name = helpers.add_dataset_details_to_activity_list(deduplicated_activity_list, context)
    recent_activity_list = helpers.filter_out_old_activites(activity_list_with_dataset_name, since)
    if recent_activity_list:
        user_phonenumber = get_phonenumber(user_dict)
        return send_whatsapp_notification(recent_activity_list, user_phonenumber)


def send_whatsapp_notification(activities, phonenumber):
    from_nr = "whatsapp:" + SENDER_NR
    to_nr = "whatsapp:" + phonenumber
    nr_of_datasets_to_display = toolkit.config.get('ckanext.dataset_subscriptions.whatsapp_nr_of_datasets_to_display', 2)
    header = toolkit.ungettext(
        "{n} dataset have recently been updated in {site_title}",
        "{n} datasets have recently been updated in {site_title}",
        len(activities)).format(
                site_title=toolkit.config.get('ckan.site_title'),
                n=len(activities))
    message_body = base.render(
            'dataset-subscriptions_whatsapp_body.j2',
            extra_vars={'activities': activities, 'header': header, 'nr_of_datasets_to_display': nr_of_datasets_to_display})
    try:
        message = client.messages.create(
                                from_=from_nr,
                                body=message_body,
                                to=to_nr
                                )
    except TwilioRestException:
        logger.exception("Failed to send whatsapp message", exec_info=True)
        return
    return message.sid
