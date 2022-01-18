import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
import ckan.logic as logic
import ckan.lib.helpers as helpers
import ckan.lib.email_notifications as email_notifications
import ckan.model as model
import ckan.lib.base as base
from ckan.common import ungettext, config


@toolkit.chained_action
@toolkit.side_effect_free
def send_email_notifications(original_action, context, data_dict):
    email_notifications._notifications_functions = [dms_notification_provider]
    return original_action(context, data_dict)


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
    # Add dataset name to activity list
    for index, activity in enumerate(deduplicated_activity_list):
        object_id = activity['object_id']
        dataset = toolkit.get_action('package_show')(
                    context, {'id': object_id})
        dataset_name = dataset['name']
        print(dataset_name)
        deduplicated_activity_list[index]['dataset_name'] = dataset_name
    return dms_notifications_for_activities(deduplicated_activity_list, user_dict)


def dms_notifications_for_activities(activities, user_dict):
    '''Return one or more email notifications covering the given activities.

    This function handles grouping multiple activities into a single digest
    email.

    :param activities: the activities to consider
    :type activities: list of activity dicts like those returned by
        ckan.logic.action.get.dashboard_activity_list()

    :returns: a list of email notifications
    :rtype: list of dicts each with keys 'subject' and 'body'

    '''
    if not activities:
        return []

    if not user_dict.get('activity_streams_email_notifications'):
        return []
    subject = ungettext(
        "{n} new notification from {site_title}",
        "{n} new notifications from {site_title}",
        len(activities)).format(
                site_title=config.get('ckan.site_title'),
                n=len(activities))
    body = base.render(
            'email_body.j2',
            extra_vars={'activities': activities})
    notifications = [{
        'subject': subject,
        'body': body
        }]
    print(activities)

    return notifications


class DatasetSubscriptionsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)

    # IConfigurer

    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('fanstatic',
                             'dataset_subscriptions')

    def get_actions(self):
        return {
            u'send_email_notifications': send_email_notifications
        }
