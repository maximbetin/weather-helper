import pytest
from datetime import datetime
from src.utils.misc import get_current_date, get_current_datetime, get_timezone, safe_average


def test_get_timezone():
  assert get_timezone().zone == "Europe/Madrid"


def test_get_current_datetime():
  assert isinstance(get_current_datetime(), datetime)


def test_get_current_date():
  assert isinstance(get_current_date(), type(datetime.now().date()))


def test_safe_average():
  assert safe_average([1, 2, 3]) == 2
  assert safe_average([]) is None
  assert safe_average([1, 3]) == 2
  assert safe_average([10, 20, 30, 40, 50]) == 30.0
