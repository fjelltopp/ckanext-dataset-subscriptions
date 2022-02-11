import ckan.plugins as plugins
import ckan.plugins.toolkit as toolkit
from ckanext.dataset_subscriptions import actions
from ckanext.dataset_subscriptions.actions import whatsup_notifications


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
            'send_email_notifications': actions.send_email_notifications,
            'user_create': whatsup_notifications.user_create,
            'user_update': whatsup_notifications.user_update,
        }
