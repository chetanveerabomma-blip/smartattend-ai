import unittest
import sys
import os
import json

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from config import Config
from models import db, Student, AttendanceRecord


class LiveTestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'


class TestLiveRoutesAndFeatures(unittest.TestCase):
    def setUp(self):
        self.app = create_app(LiveTestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_unauthenticated_redirects(self):
        """Unauthenticated requests to protected endpoints redirect to login"""
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 302)
        self.assertIn('/login', res.headers['Location'])

    def test_admin_dashboard_and_chart_api(self):
        """Admin can access dashboard and Chart.js API returns valid structure"""
        self.client.get('/demo-login/admin', follow_redirects=True)
        res = self.client.get('/dashboard')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Executive Intelligence Dashboard', res.data)
        self.assertIn(b'Safe Attendance', res.data)
        self.assertIn(b'Condonable Band', res.data)

        # Chart API
        res_chart = self.client.get('/api/dashboard/charts')
        self.assertEqual(res_chart.status_code, 200)
        data = json.loads(res_chart.data)
        self.assertIn('status_doughnut', data)
        self.assertIn('course_bar', data)
        self.assertIn('trend_line', data)
        self.assertIn('lowest_bar', data)
        self.assertEqual(len(data['status_doughnut']['labels']), 3)

    def test_student_profile_and_simulation(self):
        """Student can view attendance profile and run what-if simulation"""
        self.client.get('/demo-login/student', follow_redirects=True)
        res = self.client.get('/student/profile')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Rahul Verma', res.data)
        self.assertIn(b'What-If', res.data)

        # Get first attendance record for simulation
        rec = AttendanceRecord.query.first()
        sim_payload = {
            "record_id": rec.id,
            "additional_attended": 10,
            "additional_missed": 0
        }
        res_sim = self.client.post(
            '/api/simulate',
            data=json.dumps(sim_payload),
            content_type='application/json'
        )
        self.assertEqual(res_sim.status_code, 200)
        sim_data = json.loads(res_sim.data)
        self.assertTrue(sim_data['success'])
        self.assertEqual(sim_data['simulation']['additional_attended'], 10)

    def test_reports_filtering_and_csv_export(self):
        """Faculty can filter reports and download CSV"""
        self.client.get('/demo-login/faculty', follow_redirects=True)
        res = self.client.get('/reports?report_type=below_75')
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Report Output', res.data)

        res_csv = self.client.get('/reports/export?report_type=below_75')
        self.assertEqual(res_csv.status_code, 200)
        self.assertEqual(res_csv.headers['Content-Type'], 'text/csv; charset=utf-8')
        self.assertIn(b'StudentID,StudentName', res_csv.data)

    def test_single_attendance_save(self):
        """Admin can save and update single student attendance"""
        self.client.get('/demo-login/admin', follow_redirects=True)
        s1 = Student.query.filter_by(student_id='S1').first()
        res_save = self.client.post('/attendance/save', data={
            "student_id": s1.id,
            "course_id": 1,
            "attended": 42,
            "total_conducted": 50,
            "remaining_classes": 20
        }, follow_redirects=True)
        self.assertEqual(res_save.status_code, 200)
        # 42/50 is 84% -> Safe
        self.assertIn(b'84', res_save.data)


if __name__ == '__main__':
    unittest.main()
