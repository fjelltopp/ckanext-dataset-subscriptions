import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.dataset_subscriptions.actions import email_notifications, phone_notifications, user


class DatasetSubscriptionsPlugin(plugins.SingletonPlugin):
    plugins.implements(plugins.IConfigurer)
    plugins.implements(plugins.IActions)

    # IConfigurer
    def update_config(self, config_):
        toolkit.add_template_directory(config_, 'templates')
        toolkit.add_public_directory(config_, 'public')
        toolkit.add_resource('assets', 'ckanext-dataset-subscriptions')

    # IActions
    def get_actions(self):
        return {
            'send_email_notifications': email_notifications.send_email_notifications,
            'send_phone_notifications': phone_notifications.send_phone_notifications,
            'user_create': user.user_create,
            'user_update': user.user_update,
            'user_show': user.user_show,
            'user_list': user.user_list
        }
