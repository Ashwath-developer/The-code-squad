from services.sms_service import SmsService

def test_simulated_success():
    result = SmsService("simulation").send("+919876543210", "Emergency", recipient_id=1)
    assert result["status"] == "success"
    assert result["provider"] == "simulation"

def test_invalid_phone():
    result = SmsService("simulation").send("invalid", "Emergency")
    assert result["status"] == "failed"

def test_real_sms_requires_credentials():
    result = SmsService("real").send("+919876543210", "Emergency")
    assert result["status"] == "failed"
