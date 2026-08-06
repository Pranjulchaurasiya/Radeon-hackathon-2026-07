import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.verifier_agent import RailwayVerifierAgent

def test_valid_schedule_passes():
    """Confirms a compliant schedule with >= 3 min headway passes verification."""
    verifier = RailwayVerifierAgent()
    valid_schedule = [
        {"train_id": "12431 VANDE BHARAT", "assigned_platform": 1, "rescheduled_arrival": "08:25", "rescheduled_departure": "08:30"},
        {"train_id": "14307 PRG-BE PASS",  "assigned_platform": 1, "rescheduled_arrival": "08:33", "rescheduled_departure": "08:39"},
    ]
    res = verifier.verify_schedule(valid_schedule)
    assert res["passed"] is True
    assert len(res["violations"]) == 0

def test_headway_violation_fails():
    """Confirms separation < 3 mins triggers REJECT and returns suggested constraints."""
    verifier = RailwayVerifierAgent()
    invalid_schedule = [
        {"train_id": "12431 VANDE BHARAT", "assigned_platform": 1, "rescheduled_arrival": "08:25", "rescheduled_departure": "08:30"},
        {"train_id": "14307 PRG-BE PASS",  "assigned_platform": 1, "rescheduled_arrival": "08:31", "rescheduled_departure": "08:37"},  # Only 1m gap!
    ]
    res = verifier.verify_schedule(invalid_schedule)
    assert res["passed"] is False
    assert len(res["violations"]) > 0
    assert any(c["type"] == "min_headway" for c in res["suggested_constraints"])

def test_cross_hour_headway_correct():
    """Confirms verifier correctly handles schedules that cross the hour boundary.
    Bug that existed before: split(':')[1] only gave minutes, making 09:05 appear
    EARLIER than 08:55 (05 < 55). This test would fail with the old parser."""
    verifier = RailwayVerifierAgent()
    schedule = [
        {"train_id": "12431 VANDE BHARAT", "assigned_platform": 1, "rescheduled_arrival": "08:55", "rescheduled_departure": "09:02"},
        {"train_id": "14307 PRG-BE PASS",  "assigned_platform": 1, "rescheduled_arrival": "09:05", "rescheduled_departure": "09:18"},
    ]
    res = verifier.verify_schedule(schedule)
    # 09:05 - 09:02 = 3 min gap — exactly meets minimum, should PASS
    assert res["passed"] is True, f"Cross-hour headway check failed: {res['violations']}"

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
