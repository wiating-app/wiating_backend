from flask import current_app, Response, url_for
import pytest



@pytest.fixture
def elastic_mock(mocker):
    return mocker.patch('wiating_backend.points.Elasticsearch', autospec=True)


def test_get_get_point(client, elastic_mock):
    assert client.get(url_for('points.get_point')).status_code == 405


def test_post_get_point(client, elastic_mock):
    elastic_mock.return_value.get_point.return_value = {'a': '3'}
    res = client.post(url_for('points.get_point'), json={'id': 1})
    assert res.status_code == 200
    assert res.json == {'a': '3'}


def test_get_get_points(client, elastic_mock):
    assert client.get(url_for('points.get_points')).status_code == 405


def test_post_get_points(client, elastic_mock):
    elastic_mock.return_value.get_points.return_value = {'a': '3'}
    res = client.post(url_for('points.get_points'), json={'top_right': 1, 'bottom_left': 2})
    assert res.status_code == 200
    assert res.json == {'a': '3'}
