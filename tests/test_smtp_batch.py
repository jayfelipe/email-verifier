import pytest
from unittest.mock import patch, MagicMock
from app.smtp_batch import batch_rcpt_check

class DummyServer:
    def __init__(self):
        self.calls = []
    def ehlo(self, name=None): return (250, b'OK')
    def has_extn(self, ext): return False
    def mail(self, addr):
        return (250, b'OK')
    def rcpt(self, addr):
        # accept addresses ending with 'ok.com', reject others
        if addr.endswith("ok.com"):
            return (250, b'2.1.5 OK')
        else:
            return (550, b'5.1.1 User unknown')
    def quit(self): pass
    def close(self): pass

@patch("app.smtp_pool.smtplib.SMTP")
def test_batch_rcpt_check_succeeds(mock_smtp):
    dummy = DummyServer()
    mock_smtp.return_value = dummy
    results = batch_rcpt_check("verifier@our.com", "mx.example.com", ["a@ok.com","b@nope.com"], port=25)
    assert results["a@ok.com"][0] == 250
    assert results["b@nope.com"][0] == 550
