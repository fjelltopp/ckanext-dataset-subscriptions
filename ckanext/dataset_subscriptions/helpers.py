from ckan.plugins import toolkit
import datetime


def add_dataset_name_to_activity_list(activity_list, context):
    for index, activity in enumerate(activity_list):
        object_id = activity['object_id']
        dataset = toolkit.get_action('package_show')(
                    context, {'id': object_id})
        dataset_name = dataset['name']
        activity_list[index]['dataset_name'] = dataset_name
    return activity_list


def filter_out_old_activites(activity_list, since):
    strptime = datetime.datetime.strptime
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    activity_list = [activity for activity in activity_list
                     if strptime(activity['timestamp'], fmt) > since]
    return activity_list
