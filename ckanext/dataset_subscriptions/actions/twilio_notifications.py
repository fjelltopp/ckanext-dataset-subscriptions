import logging
from ckan.plugins import toolkit
from twilio.rest import Client
from twilio.base.exceptions import TwilioRestException
from datetime import timedelta, datetime, timezone
from ckanext.dataset_subscriptions import helpers


ACCOUNT_SID = toolkit.config.get('ckanext.dataset_subscriptions.twilio_account_sid')
AUTH_TOKEN = toolkit.config.get('ckanext.dataset_subscriptions.twilio_auth_token')
SENDER_NR = toolkit.config.get('ckanext.dataset_subscriptions.sms_sender_nr')


client = Client(ACCOUNT_SID, AUTH_TOKEN)
logger = logging.getLogger(__name__)


def send_twilio_notifications(context, data_dict):
    message_sids = []
    toolkit.check_access('send_email_notifications', context, data_dict)
    users = toolkit.get_action('user_list')(
        {'ignore_auth': True},
        {'all_fields': True, 'include_plugin_extras': True}
    )
    for user in users:
        if _twilio_notifications_enabled(user):
            recent_activities = _get_recent_activity_list(user, context)
            if recent_activities:
                message_body = _create_message(recent_activities)
                if _sms_notifications_enabled(user):
                    message_sids.append(_send_sms_message(message_body, user['phonenumber']))
                if _whatsapp_notifications_enabled(user):
                    message_sids.append(_send_whatsapp_message(message_body, user['phonenumber']))
    return message_sids


def _sms_notifications_enabled(user_dict):
    if user_dict.get("activity_streams_sms_notifications") and user_dict.get("phonenumber"):
        return True
    return False


def _whatsapp_notifications_enabled(user_dict):
    if user_dict.get("activity_streams_whatsapp_notifications") and user_dict.get("phonenumber"):
        return True
    return False


def _twilio_notifications_enabled(user_dict):
    if _sms_notifications_enabled(user_dict) or _whatsapp_notifications_enabled(user_dict):
        return True
    return False


def _twilio_notification_time_delta_utc():
    since_hours = toolkit.config.get('ckanext.dataset_subscriptions.sms_notifications_hours_since', 1)
    since_delta = timedelta(hours=int(since_hours))
    since_datetime = (datetime.utcnow() - since_delta)
    return since_datetime


def _get_recent_activity_list(user_dict, context):
    # Only raise notifications for activities since last message, or last view of the dashboard
    dashboard_last_viewed = (context['model'].Dashboard.get(user_dict['id']).activity_stream_last_viewed)
    since = max(_twilio_notification_time_delta_utc(), dashboard_last_viewed)
    # Get activities for only changes to datasets, within the desired period, not made by notifiee
    activity_list = toolkit.get_action('dashboard_activity_list')({'user': user_dict['id']}, {})
    dataset_activity_list = [activity for activity in activity_list
                             if activity['user_id'] != user_dict['id']
                             and 'package' in activity['activity_type']]
    # We want the latest notification per changed dataset, not all changes
    timestamp_sorted_activity_list = sorted(dataset_activity_list, key=lambda item: item['timestamp'])
    deduplicated_activity_list = list({
        item["object_id"]: item for item in timestamp_sorted_activity_list
    }.values())
    activity_list_with_dataset_name = helpers.add_dataset_details_to_activity_list(deduplicated_activity_list)
    recent_activity_list = helpers.filter_out_old_activites(activity_list_with_dataset_name, since)
    return recent_activity_list


def _create_message(activities):
    nr_of_datasets_to_display = toolkit.config.get('ckanext.dataset_subscriptions.sms_nr_of_datasets_to_display', 2)
    header = toolkit.ungettext(
        "{n} dataset have recently been updated in {site_title}",
        "{n} datasets have recently been updated in {site_title}",
        len(activities)).format(
                site_title=toolkit.config.get('ckan.site_title'),
                n=len(activities))
    return toolkit.render(
        'dataset-subscriptions_sms_body.j2',
        extra_vars={
            'activities': activities,
            'header': header,
            'nr_of_datasets_to_display': nr_of_datasets_to_display
        }
    )


def _send_sms_message(message_body, phonenumber):
    try:
        message = client.messages.create(
            from_=SENDER_NR,
            body=message_body,
            to=phonenumber
        )
    except TwilioRestException:
        logger.exception(f"Failed to send sms message to {phonenumber}", exc_info=True)
        return
    return message.sid


def _send_whatsapp_message(message_body, phonenumber):
    return f"whatsapp-message-sid-{phonenumber}"
