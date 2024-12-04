import pytest
from ckan.tests import factories as ckan_factories


@pytest.fixture
def sysadmin_context():
    sysadmin = ckan_factories.Sysadmin()
    # helpers.call_action sets 'ignore_auth' to True by default
    context = {'user': sysadmin['name'], 'ignore_auth': False}
    return context


@pytest.fixture()
def clean_db(reset_db, migrate_db_for):
    reset_db()
    migrate_db_for("activity")
