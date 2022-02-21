import factory

from ckan.tests import factories


class User(factories.User):
    phonenumber = factory.Sequence(lambda n: '123-555-%04d' % n)
    activity_streams_whatsapp_notifications = False