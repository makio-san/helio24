import pytest
from scripts.audit_history_publication import inspect_header


def test_later_document_creation_is_not_event_or_publication_time():
    result = inspect_header(':Created: 2014 Sep 05 0357 UT\n:Date: 2014 09 03\n')
    assert result['hours_after_report_day_start'] == 51.95
    assert result['availability_verified'] is False


@pytest.mark.parametrize('text', [':Date: 2014 09 03\n',
    ':Created: 2014 Sep 02 0357 UT\n:Date: 2014 09 03\n'])
def test_incomplete_or_inconsistent_headers_fail_closed(text):
    with pytest.raises(ValueError):
        inspect_header(text)
