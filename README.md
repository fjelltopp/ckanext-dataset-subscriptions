[![Tests](https://github.com/fjelltopp/ckanext-dataset-subscriptions/workflows/Tests/badge.svg?branch=main)](https://github.com/fjelltopp/ckanext-dataset-subscriptions/actions)

# ckanext-dataset-subscriptions

Send a detailed email notification about followed datasets


## Requirements

Compatibility with core CKAN versions:

| CKAN version    | Compatible?   |
| --------------- | ------------- |
| 2.6 and earlier | not tested    |
| 2.7             | not tested    |
| 2.8             | not tested    |
| 2.9             | yes           |


## Installation

To install ckanext-dataset-subscriptions:

1. Activate your CKAN virtual environment, for example:

     . /usr/lib/ckan/default/bin/activate

2. Clone the source and install it on the virtualenv

    git clone https://github.com/fjelltopp/ckanext-dataset-subscriptions.git
    cd ckanext-dataset-subscriptions
    pip install -e .
	pip install -r requirements.txt

3. Add `dataset-subscriptions` to the `ckan.plugins` setting in your CKAN
   config file (by default the config file is located at
   `/etc/ckan/default/ckan.ini`).

4. Configure email notifications in CKAN: https://docs.ckan.org/en/2.9/maintaining/email-notifications.html

5. Restart CKAN. For example if you've deployed CKAN with Apache on Ubuntu:

     sudo service apache2 reload


## Config settings

None at present


## Developer installation

To install ckanext-dataset-subscriptions for development, activate your CKAN virtualenv and
do:

    git clone https://github.com/fjelltopp/ckanext-dataset-subscriptions.git
    cd ckanext-dataset-subscriptions
    python setup.py develop
    pip install -r dev-requirements.txt


## Tests

To run the tests, do:

    pytest --ckan-ini=test.ini



## License

[AGPL](https://www.gnu.org/licenses/agpl-3.0.en.html)
