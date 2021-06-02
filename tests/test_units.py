from unittest.mock import Mock

from main import main

def test_auto():
    data = {}
    req = Mock(get_json=Mock(return_value=data), args=data)
    assert main(req) in ['sent', 'no alert']
