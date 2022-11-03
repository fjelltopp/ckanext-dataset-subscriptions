from ckan.plugins import toolkit
import datetime
import logging


logger = logging.getLogger(__name__)


def add_dataset_details_to_activity_list(activity_list, context):
    for index, activity in enumerate(activity_list):
        object_id = activity['object_id']
        try:
            dataset = toolkit.get_action('package_show')(
                        context, {'id': object_id})
        except:
            logger.exception("Unable to get details of package: " + object_id,
            exc_info=True)
            return []
        dataset_name = dataset['name']
        activity_list[index]['dataset_name'] = dataset_name
        if dataset.get('groups'):
            dataset_first_group_title = dataset['groups'][0]['title'] + ' | '
            dataset_groups = dict(title=dataset_first_group_title)
            activity_list[index]['dataset_groups'] = dataset_groups
        else:
            dataset_groups = dict(title='')
            activity_list[index]['dataset_groups'] = dataset_groups
        if dataset.get('program_area'):
            dataset_program_area = dataset['program_area'] + ' | '
            activity_list[index]['dataset_program_area'] = dataset_program_area
        else:
            dataset_program_area = dict(key='program_area', value='')
            activity_list[index]['dataset_program_area'] = ''
    return activity_list


def filter_out_old_activites(activity_list, since):
    strptime = datetime.datetime.strptime
    fmt = '%Y-%m-%dT%H:%M:%S.%f'
    activity_list = [activity for activity in activity_list
                     if strptime(activity['timestamp'], fmt) > since]
    return activity_list
