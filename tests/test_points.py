from flask import current_app, Response, url_for
import pytest
from unittest.mock import MagicMock


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


def test_search_points(client, elastic_mock):
    search_points_mock = MagicMock(return_value={"some": "value"})
    elastic_mock.return_value.search_points = search_points_mock
    res = client.post(url_for('points.search_points'),
                      json={
                          "phrase": "some phrase",
                          "point_type": "some type",
                          "top_right": "top right",
                          "bottom_left": "bottom left",
                          "water": "water",
                          "fire": "fire",
                          "is_disabled": "is disabled",
                          "report_reason": True
                      }
    )
    assert res.json == {"some": "value"}
    search_points_mock.assert_called_with(phrase="some phrase", point_type="some type", top_right="top right",
                                          bottom_left="bottom left", water="water", fire="fire",
                                          is_disabled="is disabled", report_reason=True)
