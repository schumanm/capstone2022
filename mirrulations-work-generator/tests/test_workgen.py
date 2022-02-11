from fakeredis import FakeRedis
from mirrcore.job_queue import JobQueue
from mirrcore.regulations_api import RegulationsAPI
from mirrmock.mock_dataset import MockDataSet
from mirrmock.mock_data_storage import MockDataStorage
from mirrgen.work_generator import WorkGenerator
import redis

class BusyRedis():
    def ping(self):
        raise redis.BusyLoadingError

class LoadedRedis():
    def ping(self):
        return True


def test_work_generator_single_page(requests_mock, mocker):
    mocker.patch('time.sleep')
    results = MockDataSet(150).get_results()
    requests_mock.get('https://api.regulations.gov/v4/documents', results)

    database = FakeRedis()
    api = RegulationsAPI('FAKE_KEY')
    job_queue = JobQueue(database)

    storage = MockDataStorage()

    generator = WorkGenerator(job_queue, api, storage)
    generator.download('documents')

    assert database.llen('jobs_waiting_queue') == 150


def test_work_generator_large(requests_mock, mocker):
    mocker.patch('time.sleep')
    results = MockDataSet(6666).get_results()
    requests_mock.get('https://api.regulations.gov/v4/documents', results)

    database = FakeRedis()
    api = RegulationsAPI('FAKE_KEY')
    job_queue = JobQueue(database)

    storage = MockDataStorage()
    generator = WorkGenerator(job_queue, api, storage)
    generator.download('documents')

    assert database.llen('jobs_waiting_queue') == 6666


def test_work_generator_retries_after_500(requests_mock, mocker):
    mocker.patch('time.sleep')
    results = MockDataSet(150).get_results()
    results.insert(0, {'json': '{}', 'status_code': 500})
    requests_mock.get('https://api.regulations.gov/v4/documents', results)

    database = FakeRedis()
    api = RegulationsAPI('FAKE_KEY')
    job_queue = JobQueue(database)

    storage = MockDataStorage()
    generator = WorkGenerator(job_queue, api, storage)
    generator.download('documents')

    assert len(requests_mock.request_history) == 2

def test_when_redis_loading_is_unavailable():
    database = BusyRedis()
    # Missing some kind of way to put fake redis in the loading state
    is_available = is_redis_available(database)
    assert is_available is False


def test_when_redis_done_loading_is_available():
    database = LoadedRedis()
    is_available = is_redis_available(database)
    assert is_available is True
