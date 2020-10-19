import pytest
from unittest.mock import MagicMock
from wiating_backend.elastic import Point, NotDefined, Elasticsearch


@pytest.fixture
def elasticsearch(mocker):
    return mocker.patch('wiating_backend.elastic.ES', autospec=True)


def test_elasticsearch_search_points_phrase(elasticsearch):
    es = Elasticsearch('some string')
    search_mock = MagicMock()
    elasticsearch.return_value.search = search_mock
    es.search_points(phrase="some phrase")

    search_mock.assert_called_with(index='wiaty', body={'query': {'bool': {'must': [{
                                      "multi_match": {
                                          "query": "some phrase",
                                          "fields": [
                                              "name^3",
                                              "description",
                                              "directions"
                                          ]
                                      }
                                  }]}}})


def test_elasticsearch_search_points_report_reason_true(elasticsearch):
    es = Elasticsearch('some string')
    search_mock = MagicMock()
    elasticsearch.return_value.search = search_mock
    es.search_points(report_reason=True)

    search_mock.assert_called_with(index='wiaty',
                                   body={'query': {'bool': {'filter': [{'exists': {'field': 'report_reason'}}]}}})


def test_elasticsearch_search_points_report_reason_false(elasticsearch):
    es = Elasticsearch('some string')
    search_mock = MagicMock()
    elasticsearch.return_value.search = search_mock
    es.search_points(report_reason=False)

    search_mock.assert_called_with(index='wiaty',
                                   body={'query': {'bool': {'must_not': [{'exists': {'field': 'report_reason'}}]}}})


def test_elasticsearch_search_points_report_reason_true_phrase(elasticsearch):
    es = Elasticsearch('some string')
    search_mock = MagicMock()
    elasticsearch.return_value.search = search_mock
    es.search_points(phrase="some phrase", report_reason=True)

    search_mock.assert_called_with(index='wiaty',
                                   body={'query': {'bool': {'must': [{
                                       "multi_match": {
                                           "query": "some phrase",
                                           "fields": [
                                               "name^3",
                                               "description",
                                               "directions"
                                           ]
                                       }
                                   }], 'filter': [{'exists': {'field': 'report_reason'}}]}}})


def test_createPoint():
    point = Point(name='some name', description='some desc', directions='some directions',
                  lat="15", lon="20", point_type="SHED", water_exists=True, water_comment="some water comment",
                  fire_exists=True, fire_comment="some fire comment", created_by='some id', last_modified_by='other id',
                  report_reason="some reason")
    assert point.last_modified_by == "other id"
    assert point.created_by == "some id"


def test_newPoint():
    point = Point.new_point(name='some name', description='some desc', directions='some directions',
                            lat="15", lon="20", point_type="SHED", water_exists=True,
                            water_comment="some water comment",
                            fire_exists=True, fire_comment="some fire comment", user_sub="some sub")
    assert point.last_modified_by == "some sub"
    assert point.created_by == "some sub"


@pytest.fixture
def point_from_dict():
    body = {"_id": "7g5qqnABsqio5qhd0cbc", "_index": "wiaty_images1", "_primary_term": 1, "_seq_no": 29626, "_source":
        {"created_timestamp": "1583403492", "created_by": "some id", "description": "EDIT: XII 2018: wiata spalona",
         "directions": "", "fire_comment": None, "fire_exists": None, "images":
             [{"created_timestamp": "1583403492", "name": "f660785da287e72143a5eddf77d37440.jpg",
               "created_by": "someone"}],
         "location": {"lat": "50.763923", "lon": "16.180389"},
         "name": "G\u00f3ry Wa\u0142brzyskie, masyw Che\u0142mca", "type": "SHED",
         "water_comment": None, "water_exists": None, "last_modified_timestamp": "1583403439",
         "report_reason": "some reason", "last_modified_by": "other id"},
            "_type": "_doc", "_version": 12, "found": True}
    return Point.from_dict(body=body)


def test_pointFromDict(point_from_dict):
    assert point_from_dict.created_by == "some id"
    assert point_from_dict.description == "EDIT: XII 2018: wiata spalona"


def test_changePointName(point_from_dict):
    changes = point_from_dict.modify(name="changed name", description=NotDefined(), directions=NotDefined(),
                                     lat=NotDefined(), lon=NotDefined(), point_type=NotDefined(),
                                     water_exists=NotDefined(), fire_exists=NotDefined(), water_comment=NotDefined(),
                                     fire_comment=NotDefined(), user_sub=NotDefined(), is_disabled=NotDefined())
    assert changes == {'name': {'new_value': 'changed name', 'old_value': 'Góry Wałbrzyskie, masyw Chełmca'}}


def test_changePointLat(point_from_dict):
    changes = point_from_dict.modify(name=NotDefined(), description=NotDefined(), directions=NotDefined(),
                                     lat="49", lon=NotDefined(), point_type=NotDefined(),
                                     water_exists=NotDefined(), fire_exists=NotDefined(), water_comment=NotDefined(),
                                     fire_comment=NotDefined(), user_sub=NotDefined(), is_disabled=NotDefined())
    assert changes == {'lat': {'new_value': '49', 'old_value': '50.763923'}}


def test_pointToDictWithId(point_from_dict):
    result = point_from_dict.to_dict(with_id=True)
    assert result == {"created_timestamp": "1583403492", "description": "EDIT: XII 2018: wiata spalona",
                      "directions": "", "fire_comment": None, "fire_exists": None, "images":
                          [{"created_timestamp": "1583403492", "name": "f660785da287e72143a5eddf77d37440.jpg"}],
                      "location": {"lat": "50.763923", "lon": "16.180389"},
                      "name": "G\u00f3ry Wa\u0142brzyskie, masyw Che\u0142mca", "type": "SHED",
                      "water_comment": None, "water_exists": None, "last_modified_timestamp": "1583403439",
                      "id": "7g5qqnABsqio5qhd0cbc", "is_disabled": False, "report_reason": "some reason"}


def test_pointToDictWithoutId(point_from_dict):
    result = point_from_dict.to_dict()
    assert result == {"created_timestamp": "1583403492", "description": "EDIT: XII 2018: wiata spalona",
                      "directions": "", "fire_comment": None, "fire_exists": None, "images":
                          [{"created_timestamp": "1583403492", "name": "f660785da287e72143a5eddf77d37440.jpg"}],
                      "location": {"lat": "50.763923", "lon": "16.180389"},
                      "name": "G\u00f3ry Wa\u0142brzyskie, masyw Che\u0142mca", "type": "SHED",
                      "water_comment": None, "water_exists": None, "last_modified_timestamp": "1583403439",
                      "is_disabled": False,
                      "report_reason": "some reason"}


def test_reportReasonAppend():
    point = Point(name='some name', description='some desc', directions='some directions',
                  lat="15", lon="20", point_type="SHED", water_exists=True, water_comment="some water comment",
                  fire_exists=True, fire_comment="some fire comment", created_by='some id', last_modified_by='other id')

    assert point.report_reason == None
    point.report_reason_append("some reason")
    assert point.report_reason == ["some reason"]
    point.report_reason_append("another reason")
    assert point.report_reason == ["some reason", "another reason"]


def test_reportReasonReplace(point_from_dict):
    point_from_dict.report_reason_replace("another reason")
    assert point_from_dict.report_reason == ["another reason"]
