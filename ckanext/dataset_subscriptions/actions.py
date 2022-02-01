import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.email_notifications as email_notifications
import ckan.model as model
import ckan.lib.base as base
from ckan.common import config


@toolkit.chained_action
@toolkit.side_effect_free
def send_email_notifications(original_action, context, data_dict):
    email_notifications._notifications_functions = [dms_notification_provider]
    email_notifications.send_notification = dms_send_notification
    return original_action(context, data_dict)

def dms_send_notification(user, email_dict):
    '''Email `email_dict` to `user`.'''
    import ckan.lib.mailer
    if not user.get('email'):
        # FIXME: Raise an exception.
        return
    # fix for AWS SES not supporting UTF8 encoding of recepient field
    # https://docs.aws.amazon.com/cli/latest/reference/ses/send-email.html
    full_name_latin1 = user['display_name'].encode('latin-1', 'replace')
    try:
        ckan.lib.mailer.mail_recipient(full_name_latin1, user['email'],
                email_dict['subject'], email_dict['body'])
    except ckan.lib.mailer.MailerException:
        raise


def _add_dataset_name_to_activity_list(activity_list, context):
        for index, activity in enumerate(activity_list):
            object_id = activity['object_id']
            dataset = toolkit.get_action('package_show')(
                        context, {'id': object_id})
            dataset_name = dataset['name']
            activity_list[index]['dataset_name'] = dataset_name
        return activity_list

def dms_notification_provider(user_dict, since):
    context = {'model': model, 'session': model.Session,
               'user': user_dict['id']}
    activity_list = logic.get_action('dashboard_activity_list')(context, {})
    # Return only activites that contain dataset changes
    activity_list = [activity for activity in activity_list
                     if activity['user_id'] != user_dict['id']
                     and 'package' in activity['activity_type']]
    # We want a notification per changed dataset, not a list of all changes
    deduplicated_activity_list = list({item["object_id"]: item for item in activity_list}.values())
    updated_activity_list = _add_dataset_name_to_activity_list(deduplicated_activity_list, context)
    return dms_notifications_for_activities(updated_activity_list, user_dict)


def dms_notifications_for_activities(activities, user_dict):
    if not activities:
        return []

    if not user_dict.get('activity_streams_email_notifications'):
        return []
    subject = toolkit.ungettext(
        "{n} new notification from {site_title}",
        "{n} new notifications from {site_title}",
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