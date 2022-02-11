from ckan.plugins import toolkit


@toolkit.chained_action
def user_create(original_action, context, data_dict):
    original_action(context, data_dict)


@toolkit.chained_action
def user_update(original_action, context, data_dict):
    original_action(context, data_dict)
