from ckan.plugins import toolkit


@toolkit.chained_action
def user_create(original_action, context, data_dict):
    _process_dataset_subscriptions_data_dict_values(data_dict)
    return original_action(context, data_dict)


@toolkit.chained_action
def user_update(original_action, context, data_dict):
    _process_dataset_subscriptions_data_dict_values(data_dict)
    return original_action(context, data_dict)


def _process_dataset_subscriptions_data_dict_values(data_dict):
    phonenumber = data_dict.get('phonenumber')
    activity_streams_whatsup_notifications = data_dict.get('activity_streams_whatsup_notifications')

    if phonenumber or activity_streams_whatsup_notifications:
        if "plugin_extras" not in data_dict:
            data_dict["plugin_extras"] = {}
        if "dataset_subscriptions" not in data_dict["plugin_extras"]:
            data_dict["plugin_extras"]["dataset_subscriptions"] = {}

        if phonenumber:
            del data_dict["phonenumber"]
            data_dict["plugin_extras"]["dataset_subscriptions"]["phonenumber"] = phonenumber
        if activity_streams_whatsup_notifications:
            del data_dict["activity_streams_whatsup_notifications"]
            data_dict["plugin_extras"]["dataset_subscriptions"]["activity_streams_whatsup_notifications"] = activity_streams_whatsup_notifications
