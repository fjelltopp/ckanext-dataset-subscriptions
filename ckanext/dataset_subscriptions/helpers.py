from ckan.plugins import toolkit
import datetime


def add_dataset_details_to_activity_list(activity_list, context):
    for index, activity in enumerate(activity_list):
        object_id = activity['object_id']
        dataset = toolkit.get_action('package_show')(
                    context, {'id': object_id})
        dataset_name = dataset['name']
        activity_list[index]['dataset_name'] = dataset_name
        if dataset['groups']:
            dataset_first_group_title = dataset['groups'][0]['title'] + ' | '
            dataset_groups = dict(title=dataset_first_group_title)
            activity_list[index]['dataset_groups'] = dataset_groups
        else:
            dataset_groups = dict(title='')
            activity_list[index]['dataset_groups'] = dataset_groups
        program_area_found = False
        if dataset['extras']:
            for dataset in dataset['extras']:
                if dataset['key'] == 'program_area':
                    dataset['value'] = dataset['value'] + ' | '
                    dataset_extras = dataset
                    activity_list[index]['dataset_extras'] = dataset_extras
                    program_area_found = True
        if not program_area_found:
            dataset_extras = dict(key='program_area', value='')
            activity_list[index]['dataset_extras'] = dataset_extras
    return activity_list


def filter_out_old_activites(activity_list, since):
    strptime = datetime.datetime.strptime
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    activity_list = [activity for activity in activity_list
                     if strptime(activity['timestamp'], fmt) > since]
    return activity_list
