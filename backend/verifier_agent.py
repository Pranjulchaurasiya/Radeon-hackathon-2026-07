from typing import List, Dict, Any

class RailwayVerifierAgent:
    """Deterministic Rule Checker for Railway Safety Constraints."""

    MIN_HEADWAY_MINUTES = 3

    def verify_schedule(self, schedule: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Validates the schedule against safety rules:
        1. Track headway rule (min 3 mins buffer per track segment)
        2. Platform occupancy isolation (single occupancy per platform)
        """
        violations = []
        suggested_constraints = []

        # Convert "HH:MM" into total integer minutes from midnight
        # MUST use h*60+m — NOT just split(":")[1] — or cross-hour comparisons break
        # e.g. "09:05" and "08:55" both give "05"/"55" without the hour, making
        # 09:05 appear EARLIER than 08:55 which is wrong.
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
                "dep_min": dep_min
                ,"track_segment": t.get("track_segment", "UNKNOWN")
            })

        # Check pairwise safety constraints
        for i in range(len(parsed_schedule)):
            for j in range(i + 1, len(parsed_schedule)):
                t1 = parsed_schedule[i]
                t2 = parsed_schedule[j]

                # Rule 1: trains entering the same signalling block must retain
                # a three-minute arrival headway even when assigned platforms differ.
                if (t1["track_segment"] != "UNKNOWN" and
                        t1["track_segment"] == t2["track_segment"] and
                        abs(t1["arr_min"] - t2["arr_min"]) < self.MIN_HEADWAY_MINUTES):
                    earlier, later = (t1, t2) if t1["arr_min"] <= t2["arr_min"] else (t2, t1)
                    violations.append(
                        f"Track Headway Violation: {later['train_id']} enters {later['track_segment']} "
                        f"only {later['arr_min'] - earlier['arr_min']}m after {earlier['train_id']} "
                        f"(minimum required: {self.MIN_HEADWAY_MINUTES}m)."
                    )
                    suggested_constraints.append({
                        "type": "track_headway", "trains": (earlier["train_id"], later["train_id"]),
                        "buffer": self.MIN_HEADWAY_MINUTES
                    })

                # Rule 2: Same Platform Clearance
                if t1["platform"] == t2["platform"]:
                    # Check overlap or insufficient headway
                    # Headway requirement: if t1 arrives first, t2 must arrive >= t1.dep + 3m
                    if t1["arr_min"] <= t2["arr_min"]:
                        gap = t2["arr_min"] - t1["dep_min"]
                        if gap < self.MIN_HEADWAY_MINUTES:
                            msg = (f"Headway Violation: {t2['train_id']} arrives at Platform {t2['platform']} "
                                   f"only {gap}m after {t1['train_id']} departs (minimum required: {self.MIN_HEADWAY_MINUTES}m).")
                            violations.append(msg)
                            suggested_constraints.append({
                                "type": "min_headway",
                                "trains": (t1["train_id"], t2["train_id"]),
                                "buffer": self.MIN_HEADWAY_MINUTES
                            })
                    else:
                        gap = t1["arr_min"] - t2["dep_min"]
                        if gap < self.MIN_HEADWAY_MINUTES:
                            msg = (f"Headway Violation: {t1['train_id']} arrives at Platform {t1['platform']} "
                                   f"only {gap}m after {t2['train_id']} departs (minimum required: {self.MIN_HEADWAY_MINUTES}m).")
                            violations.append(msg)
                            suggested_constraints.append({
                                "type": "min_headway",
                                "trains": (t2["train_id"], t1["train_id"]),
                                "buffer": self.MIN_HEADWAY_MINUTES
                            })

        passed = (len(violations) == 0)
        return {
            "passed": passed,
            "violations": violations,
            "suggested_constraints": suggested_constraints
        }
