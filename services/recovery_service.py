"""
SmartAttend AI - Recovery Service
Core mathematical models and recovery feasibility calculations.
"""

from typing import Dict, Any, Tuple


def calculate_attendance_percentage(attended: int, total: int) -> float:
    """
    Calculate attendance percentage rounded to two decimal places.
    Handles total == 0 safely without division by zero.
    """
    if total <= 0:
        return 0.0
    return round((attended / total) * 100.0, 2)


def classify_attendance(attended: int, total: int) -> Tuple[str, str, str]:
    """
    Classify attendance status using exact integer threshold arithmetic.
    
    Status definitions:
      OK: Attendance >= 75% (4 * A >= 3 * T)
      CONDONABLE: 65% <= Attendance < 75% (20 * A >= 13 * T and 4 * A < 3 * T)
      SHORTAGE: Attendance < 65% (20 * A < 13 * T)
      NO_DATA: total == 0
      
    Returns:
      (status_code, status_label, badge_color)
    """
    if total < 0 or attended < 0:
        raise ValueError("Attended and total classes must be non-negative integers.")
    if attended > total:
        raise ValueError(f"Attended classes ({attended}) cannot exceed total classes conducted ({total}).")
        
    if total == 0:
        return ("NO_DATA", "No Classes Yet", "secondary")
        
    # Exact integer comparisons
    if 4 * attended >= 3 * total:
        return ("OK", "Safe", "success")
    elif 20 * attended >= 13 * total:
        return ("CONDONABLE", "Condonable", "warning")
    else:
        return ("SHORTAGE", "Shortage", "danger")


def calculate_required_recovery(attended: int, total: int) -> int:
    """
    Calculate minimum additional consecutive classes needed to reach at least 75% attendance.
    
    Formula:
      (A + k) / (T + k) >= 3/4
      4*(A + k) >= 3*(T + k)
      4*A + 4*k >= 3*T + 3*k
      k >= 3*T - 4*A
      k = max(0, 3*T - 4*A)
      
    Returns:
      Minimum integer k >= 0.
    """
    if total < 0 or attended < 0:
        raise ValueError("Attended and total classes must be non-negative.")
    if attended > total:
        raise ValueError("Attended classes cannot exceed total classes.")
    if total == 0:
        return 0
        
    k = max(0, 3 * total - 4 * attended)
    
    # Verification check
    if k > 0:
        # Verify that (attended + k) / (total + k) is indeed >= 0.75
        new_attended = attended + k
        new_total = total + k
        assert 4 * new_attended >= 3 * new_total, "Recovery verification failed: target 75% not reached"
        
    return k


def evaluate_recovery_feasibility(attended: int, total: int, remaining: int) -> Dict[str, Any]:
    """
    Evaluates attendance standing, required recovery classes, and feasibility given remaining classes.
    
    Returns a comprehensive dictionary with:
      - attended: int
      - total: int
      - remaining: int
      - percentage: float
      - status: str ('OK', 'CONDONABLE', 'SHORTAGE', 'NO_DATA')
      - status_label: str
      - status_badge: str
      - required_classes: int
      - feasibility: str ('NOT_REQUIRED', 'POSSIBLE', 'IMPOSSIBLE', 'N/A')
      - feasibility_label: str
      - feasibility_badge: str
      - message: str
      - projected_max_percentage: float (if student attends all remaining classes)
    """
    if remaining < 0:
        raise ValueError("Remaining classes must be non-negative.")
        
    status_code, status_label, status_badge = classify_attendance(attended, total)
    percentage = calculate_attendance_percentage(attended, total)
    
    if total == 0:
        return {
            "attended": attended,
            "total": total,
            "remaining": remaining,
            "percentage": 0.0,
            "status": "NO_DATA",
            "status_label": "No Classes Yet",
            "status_badge": "secondary",
            "required_classes": 0,
            "feasibility": "N/A",
            "feasibility_label": "Not Applicable",
            "feasibility_badge": "secondary",
            "message": "No classes have been conducted yet for this course.",
            "projected_max_percentage": 100.0 if remaining > 0 else 0.0
        }
        
    k = calculate_required_recovery(attended, total)
    
    # Calculate projected max percentage if student attends 100% of remaining classes
    final_total = total + remaining
    max_possible_attended = attended + remaining
    projected_max_pct = calculate_attendance_percentage(max_possible_attended, final_total) if final_total > 0 else 0.0

    if k == 0:
        feasibility = "NOT_REQUIRED"
        feasibility_label = "On Track"
        feasibility_badge = "success"
        message = f"Attendance is safe ({percentage}% >= 75%). Keep attending regularly to maintain your standing."
    elif k <= remaining:
        feasibility = "POSSIBLE"
        feasibility_label = "Recovery Possible"
        feasibility_badge = "info"
        message = (f"Need to attend the next {k} consecutive class{'es' if k != 1 else ''} "
                   f"(out of {remaining} remaining) to reach 75%.")
    else:
        feasibility = "IMPOSSIBLE"
        feasibility_label = "Recovery Impossible"
        feasibility_badge = "danger"
        message = (f"Needs {k} classes to reach 75%, but only {remaining} class{'es' if remaining != 1 else ''} remain. "
                   f"Maximum achievable is {projected_max_pct}%. Immediate academic counselor review required.")

    return {
        "attended": attended,
        "total": total,
        "remaining": remaining,
        "percentage": percentage,
        "status": status_code,
        "status_label": status_label,
        "status_badge": status_badge,
        "required_classes": k,
        "feasibility": feasibility,
        "feasibility_label": feasibility_label,
        "feasibility_badge": feasibility_badge,
        "message": message,
        "projected_max_percentage": projected_max_pct
    }


def simulate_attendance_scenario(attended: int, total: int, additional_attended: int, additional_missed: int = 0) -> Dict[str, Any]:
    """
    What-if simulation tool for students to explore attendance scenarios.
    Formula: ((A + x) / (T + x + y)) * 100
    where:
      x = additional classes attended
      y = additional classes missed
    Does not modify database records.
    """
    if additional_attended < 0 or additional_missed < 0:
        raise ValueError("Simulation counts cannot be negative.")
        
    new_attended = attended + additional_attended
    new_total = total + additional_attended + additional_missed
    
    new_pct = calculate_attendance_percentage(new_attended, new_total)
    status_code, status_label, status_badge = classify_attendance(new_attended, new_total)
    
    return {
        "original_attended": attended,
        "original_total": total,
        "additional_attended": additional_attended,
        "additional_missed": additional_missed,
        "simulated_attended": new_attended,
        "simulated_total": new_total,
        "simulated_percentage": new_pct,
        "simulated_status": status_code,
        "simulated_status_label": status_label,
        "simulated_status_badge": status_badge
    }
