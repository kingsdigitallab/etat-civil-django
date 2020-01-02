import pandas as pd
import pytest
from django.conf import settings
from django.test import RequestFactory

from etat_civil.deeds.tests.factories import DataFactory, SourceFactory
from etat_civil.users.tests.factories import UserFactory


@pytest.fixture(autouse=True)
def media_storage(settings, tmpdir):
    settings.MEDIA_ROOT = tmpdir.strpath


@pytest.fixture
def user() -> settings.AUTH_USER_MODEL:
    return UserFactory()


@pytest.fixture
def request_factory() -> RequestFactory:
    return RequestFactory()


@pytest.fixture
def data() -> DataFactory:
    return DataFactory()


@pytest.fixture
def births_df() -> pd.DataFrame:
    return pd.read_excel("data/raw/test.xlsx", engine="openpyxl", sheet_name="births")


@pytest.fixture
def source() -> SourceFactory:
    return SourceFactory()
