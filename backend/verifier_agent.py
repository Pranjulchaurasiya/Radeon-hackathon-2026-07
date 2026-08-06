from typing import List, Dict, Any

class RailwayVerifierAgent:
    """Deterministic Rule Checker for Railway Safety Constraints."""

    MIN_HEADWAY_MINUTES = 3

    def _get_headway_requirement(self, tid1: str, tid2: str) -> int:
        """Dynamic headway calculation based on operational safety characteristics.
        High-speed express services (Vande Bharat) require a larger safety buffer (5 min)
        due to high-velocity signaling blocks, while standard passenger/freight requires 3 min.
        """
        if "VANDE BHARAT" in tid1.upper() or "VANDE BHARAT" in tid2.upper():
            return 5
        return 3

    def verify_schedule(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates the schedule against safety rules:
        1. Track headway rule (dynamic buffer per track segment based on speed/type)
        2. Platform occupancy isolation (single occupancy per platform)
        """
        violations = []
        suggested_constraints = []

        # Convert "HH:MM" into total integer minutes from midnight
        def to_total_minutes(hhmm: str) -> int:
            parts = hhmm.strip().split(":")
            return int(parts[0]) * 60 + int(parts[1])

        parsed_schedule = []
        for t in schedule:
            arr_min = to_total_minutes(t["rescheduled_arrival"])
            dep_min = to_total_minutes(t["rescheduled_departure"])
            parsed_schedule.append({
                "train_id": t["train_id"],
                "platform": t["assigned_platform"],
                "arr_min": arr_min,
                "dep_min": dep_min,
                "track_segment": t.get("track_segment", "UNKNOWN")
            })

        # Check pairwise safety constraints
        for i in range(len(parsed_schedule)):
            for j in range(i + 1, len(parsed_schedule)):
                t1 = parsed_schedule[i]
                t2 = parsed_schedule[j]
                
                # Retrieve dynamic headway safety requirements based on train profiles
                req_headway = self._get_headway_requirement(t1["train_id"], t2["train_id"])

                # Rule 1: trains entering the same signalling block must retain
                # arrival headway even when assigned platforms differ.
                if (t1["track_segment"] != "UNKNOWN" and
                        t1["track_segment"] == t2["track_segment"] and
                        abs(t1["arr_min"] - t2["arr_min"]) < req_headway):
                    earlier, later = (t1, t2) if t1["arr_min"] <= t2["arr_min"] else (t2, t1)
                    violations.append(
                        f"Track Headway Violation: {later['train_id']} enters {later['track_segment']} "
                        f"only {later['arr_min'] - earlier['arr_min']}m after {earlier['train_id']} "
                        f"(minimum required for speed profile: {req_headway}m)."
                    )
                    suggested_constraints.append({
                        "type": "track_headway", "trains": (earlier["train_id"], later["train_id"]),
                        "buffer": req_headway
                    })

                # Rule 2: Same Platform Clearance
                if t1["platform"] == t2["platform"]:
                    if t1["arr_min"] <= t2["arr_min"]:
                        gap = t2["arr_min"] - t1["dep_min"]
                        if gap < req_headway:
                            msg = (f"Headway Violation: {t2['train_id']} arrives at Platform {t2['platform']} "
                                   f"only {gap}m after {t1['train_id']} departs (minimum required for speed profile: {req_headway}m).")
                            violations.append(msg)
                            suggested_constraints.append({
                                "type": "min_headway",
                                "trains": (t1["train_id"], t2["train_id"]),
                                "buffer": req_headway
                            })
                    else:
                        gap = t1["arr_min"] - t2["dep_min"]
                        if gap < req_headway:
                            msg = (f"Headway Violation: {t1['train_id']} arrives at Platform {t1['platform']} "
                                   f"only {gap}m after {t2['train_id']} departs (minimum required for speed profile: {req_headway}m).")
                            violations.append(msg)
                            suggested_constraints.append({
                                "type": "min_headway",
                                "trains": (t2["train_id"], t1["train_id"]),
                                "buffer": req_headway
                            })

        passed = (len(violations) == 0)
        return {
            "passed": passed,
            "violations": violations,
            "suggested_constraints": suggested_constraints
        }
