import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
from ckan.lib.email_notifications import send_notification
import ckanext.dataset_subscriptions.helpers as helpers
import ckan.lib.email_notifications as email_notifications
import ckan.model as model
import ckan.lib.base as base
from ckan.common import config
import unihandecode


@toolkit.chained_action
@toolkit.side_effect_free
def send_email_notifications(original_action, context, data_dict):
    email_notifications._notifications_functions = [dms_notification_provider]
    email_notifications.send_notification = latin_username_send_notification
    return original_action(context, data_dict)


def latin_username_send_notification(user, email_dict):
    # fix for AWS SES not supporting UTF8 encoding of recepient field
    # https://docs.aws.amazon.com/cli/latest/reference/ses/send-email.html
    user['display_name'] = unihandecode.unidecode(user['display_name'])
    return send_notification(user, email_dict)


def dms_notification_provider(user_dict, since):
    # check if email notifications are enabled for this user, otherwise return empty
    if not user_dict.get('activity_streams_email_notifications'):
      return []
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
    return dms_notifications_for_activities(recent_activity_list, user_dict)


def dms_notifications_for_activities(activities, user_dict):
    if not activities:
        return []
    if not user_dict.get('activity_streams_email_notifications'):
        return []
    subject = toolkit.ungettext(
        "{n} new notification from Department of HIV and AIDS Document Management System",
        "{n} new notifications from Department of HIV and AIDS Document Management System",
        len(activities)).format(
                site_title=config.get('ckan.site_title'),
                n=len(activities))
    body = base.render(
            'dataset-subscriptions_email_body.j2',
            extra_vars={'activities': activities})
    notifications = [{
        'subject': subject,
        'body': body
        }]
    return notifications
