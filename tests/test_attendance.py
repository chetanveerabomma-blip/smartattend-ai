import unittest
import io
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app
from config import Config
from models import db, User, Student, Course, AttendanceRecord
from services.import_service import process_attendance_csv_stream


class TestConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False


class TestSmartAttendApp(unittest.TestCase):
    def setUp(self):
        self.app = create_app(TestConfig)
        self.client = self.app.test_client()
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self):
        db.session.remove()
        db.drop_all()
        self.app_context.pop()

    def test_database_seeded_on_init(self):
        """Verify initial users and sample students exist"""
        admin = User.query.filter_by(username='admin').first()
        self.assertIsNotNone(admin)
        self.assertTrue(admin.check_password('admin123'))
        
        # S1 Rahul Verma exists
        s1 = Student.query.filter_by(student_id='S1').first()
        self.assertIsNotNone(s1)
        self.assertEqual(s1.name, 'Rahul Verma')

    def test_demo_login_admin(self):
        """Test 1-click admin demo login sets session"""
        res = self.client.get('/demo-login/admin', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        with self.client.session_transaction() as sess:
            self.assertEqual(sess['role'], 'admin')
            self.assertEqual(sess['username'], 'admin')

    def test_demo_login_student(self):
        """Test 1-click student demo login redirects to profile"""
        res = self.client.get('/demo-login/student', follow_redirects=True)
        self.assertEqual(res.status_code, 200)
        self.assertIn(b'Rahul Verma', res.data)

    def test_attendance_csv_import_snapshot_and_aggregate(self):
        """Test streaming CSV processing in both Snapshot and Aggregate modes"""
        csv_content = (
            "StudentID,CourseID,Attended,Total,RemainingClasses\n"
            "S1,CS101,35,50,20\n"
            "S2,CS101,40,50,20\n"
        )
        stream = io.StringIO(csv_content)
        result = process_attendance_csv_stream(stream, "test_upload.csv", import_mode="snapshot")
        self.assertTrue(result["success"])
        self.assertEqual(result["total_rows"], 2)
        self.assertEqual(result["valid_rows"], 2)

        # Check that S1 attendance is now 35 / 50
        s1 = Student.query.filter_by(student_id='S1').first()
        c1 = Course.query.filter_by(course_id='CS101').first()
        rec = AttendanceRecord.query.filter_by(student_id=s1.id, course_id=c1.id).first()
        self.assertEqual(rec.attended, 35)
        self.assertEqual(rec.total_conducted, 50)
        self.assertEqual(rec.percentage, 70.0)
        self.assertEqual(rec.status, "CONDONABLE")

        # Now test Aggregate mode with +5 attended / +5 total
        csv_agg = (
            "StudentID,CourseID,Attended,Total,RemainingClasses\n"
            "S1,CS101,5,5,15\n"
        )
        stream_agg = io.StringIO(csv_agg)
        result_agg = process_attendance_csv_stream(stream_agg, "test_agg.csv", import_mode="aggregate")
        self.assertTrue(result_agg["success"])

        # Reload record: 35 + 5 = 40 attended, 50 + 5 = 55 total -> 72.73%
        rec_after = AttendanceRecord.query.filter_by(student_id=s1.id, course_id=c1.id).first()
        self.assertEqual(rec_after.attended, 40)
        self.assertEqual(rec_after.total_conducted, 55)

    def test_csv_validation_invalid_rows(self):
        """Test that invalid rows (attended > total, negative, non-existent) are caught and reported"""
        invalid_csv = (
            "StudentID,CourseID,Attended,Total,RemainingClasses\n"
            "S1,CS101,60,50,20\n"  # attended > total
            "S1,CS101,-5,50,20\n"  # negative
            "NONEXISTENT,CS101,10,20,10\n"  # unknown student
        )
        stream = io.StringIO(invalid_csv)
        result = process_attendance_csv_stream(stream, "test_invalid.csv", import_mode="snapshot")
        self.assertTrue(result["success"])
        self.assertEqual(result["invalid_rows"], 3)
        self.assertEqual(result["valid_rows"], 0)
        self.assertEqual(len(result["error_log"]), 3)


if __name__ == '__main__':
    unittest.main()
