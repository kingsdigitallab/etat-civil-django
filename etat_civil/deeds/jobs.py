from django_rq import job


@job
def import_data_async(data):
    data.load_data()
