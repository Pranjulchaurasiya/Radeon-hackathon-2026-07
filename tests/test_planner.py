import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from backend.planner_agent import RailwayPlannerAgent

# Real train IDs from the 2017 Indian Railways dataset seed
PRIORITY_1_ID = "12431 VANDE BHARAT"   # [MODERN-ADDED] priority=1
PRIORITY_2_ID = "14307 PRG-BE PASS"    # [REAL-2017]   priority=2
PRIORITY_3_ID = "477 FTR TRAIN NO"     # [REAL-2017]   priority=3 — real FTR rows 67-68

def test_planner_scenario_a():
    """Test solver feasibility for Scenario A (Express train delay)."""
    planner = RailwayPlannerAgent()
    disruption = {"delay_minutes": 15, "delayed_train": PRIORITY_1_ID}
    result = planner.solve_disruption("scenario_a", disruption)

    assert result["status"] == "FEASIBLE"
    assert len(result["schedule"]) == 3

    # Check priority-1 train (Vande Bharat) received at least 15 min delay
    t1 = next(t for t in result["schedule"] if t["train_id"] == PRIORITY_1_ID)
    assert t1["delay_minutes"] >= 15, (
        f"Expected >= 15 min delay on {PRIORITY_1_ID}, got {t1['delay_minutes']}"
    )
    assert all(t["track_segment"] == "B4" for t in result["schedule"])

def test_planner_scenario_b():
    """Test solver feasibility and platform reassignment for Scenario B (Platform 1 maintenance)."""
    planner = RailwayPlannerAgent()
    disruption = {"closed_platform": 1, "station": "Station X"}
    result = planner.solve_disruption("scenario_b", disruption)

    assert result["status"] == "FEASIBLE"
    assert len(result["schedule"]) == 3

    # Verify priority-1 and priority-2 trains are reassigned to Platform 2
    t1 = next(t for t in result["schedule"] if t["train_id"] == PRIORITY_1_ID)
    t2 = next(t for t in result["schedule"] if t["train_id"] == PRIORITY_2_ID)
    assert t1["assigned_platform"] == 2, f"{PRIORITY_1_ID} should be on Platform 2"
    assert t2["assigned_platform"] == 2, f"{PRIORITY_2_ID} should be on Platform 2"

def test_time_format_no_rollover():
    """Ensure no time string like '08:75' is produced — hour rollover must be handled."""
    from backend.planner_agent import format_time
    assert format_time(8, 0)   == "08:00"
    assert format_time(8, 59)  == "08:59"
    assert format_time(8, 60)  == "09:00"  # rollover
    assert format_time(8, 75)  == "09:15"  # rollover
    assert format_time(8, 120) == "10:00"  # 2-hour boundary
