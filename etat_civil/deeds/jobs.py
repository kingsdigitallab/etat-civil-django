from deeds.models import import_data
from django_rq import job


@job
def import_data_async(user, data):
    import_data(data)
