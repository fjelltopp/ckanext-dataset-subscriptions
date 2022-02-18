import copy

from ckan import model
from ckan.plugins import toolkit

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
            raise toolkit.ValidationError({field['name']: [f"{field['name']} must be specified"]})

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
            raise toolkit.ValidationError({field['name']: [f"{field['name']} must be specified"]})

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
