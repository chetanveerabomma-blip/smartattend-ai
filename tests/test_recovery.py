import unittest
import sys
import os

# Add parent directory to path so tests can import services
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.recovery_service import (
    calculate_attendance_percentage,
    classify_attendance,
    calculate_required_recovery,
    evaluate_recovery_feasibility,
    simulate_attendance_scenario
)


class TestAttendanceRecovery(unittest.TestCase):
    
    def test_case_1_safe_attendance(self):
        """Case 1: 40 attended / 50 total -> Expected: 80%, OK"""
        pct = calculate_attendance_percentage(40, 50)
        status, label, badge = classify_attendance(40, 50)
        self.assertEqual(pct, 80.0)
        self.assertEqual(status, "OK")

    def test_case_2_condonable_attendance(self):
        """Case 2: 36 attended / 50 total -> Expected: 72%, CONDONABLE"""
        pct = calculate_attendance_percentage(36, 50)
        status, label, badge = classify_attendance(36, 50)
        self.assertEqual(pct, 72.0)
        self.assertEqual(status, "CONDONABLE")

    def test_case_3_shortage_attendance(self):
        """Case 3: 32 attended / 50 total -> Expected: 64%, SHORTAGE"""
        pct = calculate_attendance_percentage(32, 50)
        status, label, badge = classify_attendance(32, 50)
        self.assertEqual(pct, 64.0)
        self.assertEqual(status, "SHORTAGE")

    def test_case_4_recovery_calculation(self):
        """Case 4: 30 attended / 50 total -> Expected: 60%, SHORTAGE, Expected recovery: 30 classes"""
        pct = calculate_attendance_percentage(30, 50)
        status, label, badge = classify_attendance(30, 50)
        k = calculate_required_recovery(30, 50)
        self.assertEqual(pct, 60.0)
        self.assertEqual(status, "SHORTAGE")
        self.assertEqual(k, 30)
        # Verification: (30 + 30) / (50 + 30) = 60 / 80 = 75%
        self.assertEqual(calculate_attendance_percentage(30 + k, 50 + k), 75.0)

    def test_case_5_exact_75_boundary(self):
        """Case 5: 45 attended / 60 total -> Expected: 75%, OK, Expected recovery: 0"""
        pct = calculate_attendance_percentage(45, 60)
        status, label, badge = classify_attendance(45, 60)
        k = calculate_required_recovery(45, 60)
        self.assertEqual(pct, 75.0)
        self.assertEqual(status, "OK")
        self.assertEqual(k, 0)

    def test_case_6_exact_65_boundary(self):
        """Case 6: 65 attended / 100 total -> Expected: 65%, CONDONABLE"""
        pct = calculate_attendance_percentage(65, 100)
        status, label, badge = classify_attendance(65, 100)
        self.assertEqual(pct, 65.0)
        self.assertEqual(status, "CONDONABLE")

    def test_case_7_zero_classes(self):
        """Case 7: 0 attended / 0 total -> Expected: safely handled without division by zero"""
        pct = calculate_attendance_percentage(0, 0)
        status, label, badge = classify_attendance(0, 0)
        k = calculate_required_recovery(0, 0)
        self.assertEqual(pct, 0.0)
        self.assertEqual(status, "NO_DATA")
        self.assertEqual(k, 0)

    def test_case_8_attended_greater_than_total(self):
        """Case 8: Attended greater than total -> Expected: validation error"""
        with self.assertRaises(ValueError):
            classify_attendance(55, 50)
        with self.assertRaises(ValueError):
            calculate_required_recovery(55, 50)

    def test_case_9_recovery_impossible(self):
        """Case 9: Recovery required = 30, remaining = 20 -> Expected: IMPOSSIBLE"""
        # For 30 attended / 50 total, k = 30. If remaining = 20:
        result = evaluate_recovery_feasibility(30, 50, 20)
        self.assertEqual(result["required_classes"], 30)
        self.assertEqual(result["feasibility"], "IMPOSSIBLE")

    def test_case_10_recovery_possible(self):
        """Case 10: Recovery required = 30, remaining = 40 -> Expected: POSSIBLE"""
        # For 30 attended / 50 total, k = 30. If remaining = 40:
        result = evaluate_recovery_feasibility(30, 50, 40)
        self.assertEqual(result["required_classes"], 30)
        self.assertEqual(result["feasibility"], "POSSIBLE")

    def test_scenario_simulation(self):
        """Test what-if simulation logic"""
        sim = simulate_attendance_scenario(30, 50, additional_attended=10, additional_missed=0)
        self.assertEqual(sim["simulated_attended"], 40)
        self.assertEqual(sim["simulated_total"], 60)
        # 40/60 = 66.67% -> CONDONABLE
        self.assertAlmostEqual(sim["simulated_percentage"], 66.67, places=2)
        self.assertEqual(sim["simulated_status"], "CONDONABLE")


if __name__ == '__main__':
    unittest.main()
