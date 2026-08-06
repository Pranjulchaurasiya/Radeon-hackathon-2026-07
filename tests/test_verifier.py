import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.verifier_agent import RailwayVerifierAgent

def test_valid_schedule_passes():
    """Confirms a compliant schedule with >= 3 min headway passes verification for standard trains."""
    verifier = RailwayVerifierAgent()
    valid_schedule = [
        {"train_id": "11007 DECCAN EXPRE", "assigned_platform": 1, "rescheduled_arrival": "08:25", "rescheduled_departure": "08:30"},
        {"train_id": "14307 PRG-BE PASS",  "assigned_platform": 1, "rescheduled_arrival": "08:33", "rescheduled_departure": "08:39"},
    ]
    res = verifier.verify_schedule(valid_schedule)
    assert res["passed"] is True
    assert len(res["violations"]) == 0

def test_headway_violation_fails():
    """Confirms separation < 3 mins triggers REJECT and returns suggested constraints."""
    verifier = RailwayVerifierAgent()
    invalid_schedule = [
        {"train_id": "11007 DECCAN EXPRE", "assigned_platform": 1, "rescheduled_arrival": "08:25", "rescheduled_departure": "08:30"},
        {"train_id": "14307 PRG-BE PASS",  "assigned_platform": 1, "rescheduled_arrival": "08:31", "rescheduled_departure": "08:37"},  # Only 1m gap!
    ]
    res = verifier.verify_schedule(invalid_schedule)
    assert res["passed"] is False
    assert len(res["violations"]) > 0
    assert any(c["type"] == "min_headway" for c in res["suggested_constraints"])

def test_cross_hour_headway_correct():
    """Confirms verifier correctly handles schedules that cross the hour boundary."""
    verifier = RailwayVerifierAgent()
    schedule = [
        {"train_id": "11007 DECCAN EXPRE", "assigned_platform": 1, "rescheduled_arrival": "08:55", "rescheduled_departure": "09:02"},
        {"train_id": "14307 PRG-BE PASS",  "assigned_platform": 1, "rescheduled_arrival": "09:05", "rescheduled_departure": "09:18"},
    ]
    res = verifier.verify_schedule(schedule)
    assert res["passed"] is True, f"Cross-hour headway check failed: {res['violations']}"

def test_vande_bharat_dynamic_headway_5m():
    """Confirms Vande Bharat high-speed service triggers dynamic 5-minute safety buffer enforcement."""
    verifier = RailwayVerifierAgent()
    
    # 3-minute gap: Should pass for standard trains, but fail for Vande Bharat
    schedule = [
        {"train_id": "12431 VANDE BHARAT", "assigned_platform": 1, "rescheduled_arrival": "08:20", "rescheduled_departure": "08:25"},
        {"train_id": "14307 PRG-BE PASS",  "assigned_platform": 1, "rescheduled_arrival": "08:28", "rescheduled_departure": "08:35"},
    ]
    res = verifier.verify_schedule(schedule)
    assert res["passed"] is False, "Vande Bharat must require a 5-minute safety buffer."
    
    # 5-minute gap: Should pass
    safe_schedule = [
        {"train_id": "12431 VANDE BHARAT", "assigned_platform": 1, "rescheduled_arrival": "08:20", "rescheduled_departure": "08:25"},
        {"train_id": "14307 PRG-BE PASS",  "assigned_platform": 1, "rescheduled_arrival": "08:30", "rescheduled_departure": "08:37"},
    ]
    safe_res = verifier.verify_schedule(safe_schedule)
    assert safe_res["passed"] is True, f"5-minute gap should satisfy Vande Bharat safety constraints: {safe_res['violations']}"

def test_track_headway_detected_across_platforms():
    """Track separation applies even when trains use different platforms."""
    verifier = RailwayVerifierAgent()
    schedule = [
        {"train_id": "A", "assigned_platform": 1, "track_segment": "B4", "rescheduled_arrival": "08:10", "rescheduled_departure": "08:15"},
        {"train_id": "B", "assigned_platform": 2, "track_segment": "B4", "rescheduled_arrival": "08:12", "rescheduled_departure": "08:17"},
    ]
    res = verifier.verify_schedule(schedule)
    assert res["passed"] is False
    assert any(c["type"] == "track_headway" for c in res["suggested_constraints"])
