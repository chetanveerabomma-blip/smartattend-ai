"""
SmartAttend AI - Streaming CSV Import Service
Implements memory-conscious streaming row-by-row processing, validation,
configurable batching, and dual-mode snapshot/aggregation handling.
"""

import csv
import io
import uuid
from typing import Dict, Any, Generator, Tuple
from datetime import datetime, timezone
from models import db, Student, Course, AttendanceRecord, ImportJob


def stream_csv_rows(file_stream) -> Generator[Tuple[int, Dict[str, str]], None, None]:
    """
    Generator yielding (row_number, row_dict) one row at a time.
    Avoids loading millions of rows into an in-memory list.
    """
    # Ensure text mode stream
    if isinstance(file_stream, io.BytesIO):
        file_stream = io.TextIOWrapper(file_stream, encoding='utf-8', errors='replace')
    elif hasattr(file_stream, 'read') and isinstance(file_stream.read(0), bytes):
        file_stream = io.TextIOWrapper(file_stream, encoding='utf-8', errors='replace')
        
    reader = csv.DictReader(file_stream)
    
    # Normalize fieldnames
    if reader.fieldnames:
        reader.fieldnames = [f.strip().replace(' ', '').replace('_', '').lower() for f in reader.fieldnames]

    row_num = 1  # Header is row 1
    for row in reader:
        row_num += 1
        # Normalize keys in row
        clean_row = {}
        for k, v in row.items():
            if k:
                clean_row[k.strip().replace(' ', '').replace('_', '').lower()] = v.strip() if v else ''
        yield row_num, clean_row


def validate_csv_row(row_num: int, row_data: Dict[str, str], student_cache: Dict[str, int], course_cache: Dict[str, int]) -> Tuple[bool, str, Dict[str, Any]]:
    """
    Validates a single CSV record without blocking the entire import.
    Returns: (is_valid, error_reason, parsed_data)
    """
    # Keys can be 'studentid', 'courseid', 'attended', 'total', 'remainingclasses'
    student_id = row_data.get('studentid') or row_data.get('student')
    course_id = row_data.get('courseid') or row_data.get('course')
    attended_str = row_data.get('attended')
    total_str = row_data.get('total') or row_data.get('totalconducted')
    remaining_str = row_data.get('remainingclasses') or row_data.get('remaining') or '0'

    if not student_id:
        return False, f"Row {row_num}: Missing StudentID", {}
    if not course_id:
        return False, f"Row {row_num}: Missing CourseID", {}
    if attended_str is None or attended_str == '':
        return False, f"Row {row_num}: Missing Attended count", {}
    if total_str is None or total_str == '':
        return False, f"Row {row_num}: Missing Total conducted count", {}

    # Parse integers
    try:
        attended = int(attended_str)
        total = int(total_str)
        remaining = int(remaining_str)
    except ValueError:
        return False, f"Row {row_num}: Attended, Total, and Remaining must be valid integers", {}

    # Logical validations
    if attended < 0:
        return False, f"Row {row_num}: Attended classes cannot be negative ({attended})", {}
    if total < 0:
        return False, f"Row {row_num}: Total classes cannot be negative ({total})", {}
    if remaining < 0:
        return False, f"Row {row_num}: Remaining classes cannot be negative ({remaining})", {}
    if attended > total:
        return False, f"Row {row_num}: Attended classes ({attended}) cannot exceed total classes conducted ({total})", {}

    # Existence checks
    student_pk = student_cache.get(student_id.upper())
    if not student_pk:
        # Check database
        student_obj = Student.query.filter(func_upper(Student.student_id) == student_id.upper()).first()
        if not student_obj:
            return False, f"Row {row_num}: Student ID '{student_id}' does not exist in database", {}
        student_pk = student_obj.id
        student_cache[student_id.upper()] = student_pk

    course_pk = course_cache.get(course_id.upper())
    if not course_pk:
        course_obj = Course.query.filter(func_upper(Course.course_id) == course_id.upper()).first()
        if not course_obj:
            return False, f"Row {row_num}: Course ID '{course_id}' does not exist in database", {}
        course_pk = course_obj.id
        course_cache[course_id.upper()] = course_pk

    return True, "", {
        "student_id": student_id.upper(),
        "student_pk": student_pk,
        "course_id": course_id.upper(),
        "course_pk": course_pk,
        "attended": attended,
        "total": total,
        "remaining": remaining
    }


def func_upper(col):
    """Helper for case-insensitive lookup"""
    return db.func.upper(col)


def process_attendance_csv_stream(file_stream, filename: str, import_mode: str = 'snapshot', batch_size: int = 500) -> Dict[str, Any]:
    """
    Streaming processor for attendance files.
    - Reads line-by-line using a generator.
    - import_mode = 'snapshot': updates records with uploaded totals.
    - import_mode = 'aggregate': increments existing counts (for attendance session logs).
    - Writes to DB in configurable batch chunks within transactions.
    - Retains O(U) memory complexity where U is unique (student, course) pairs.
    """
    job_id = str(uuid.uuid4())[:12]
    import_job = ImportJob(
        job_id=job_id,
        filename=filename,
        import_mode=import_mode,
        status='processing'
    )
    db.session.add(import_job)
    db.session.commit()

    student_cache = {s.student_id.upper(): s.id for s in Student.query.all()}
    course_cache = {c.course_id.upper(): c.id for c in Course.query.all()}

    total_rows = 0
    valid_rows = 0
    invalid_rows = 0
    created_count = 0
    updated_count = 0
    error_log = []

    # Aggregates accumulator for the batch: key is (student_pk, course_pk)
    # If file contains duplicate pairs, we combine them according to import_mode before saving
    batch_records = {}

    try:
        for row_num, row_data in stream_csv_rows(file_stream):
            total_rows += 1
            is_valid, error_msg, parsed = validate_csv_row(row_num, row_data, student_cache, course_cache)

            if not is_valid:
                invalid_rows += 1
                if len(error_log) < 100:  # Keep top 100 errors to prevent runaway memory
                    error_log.append(error_msg)
                continue

            valid_rows += 1
            key = (parsed['student_pk'], parsed['course_pk'])

            if import_mode == 'aggregate':
                if key in batch_records:
                    batch_records[key]['attended'] += parsed['attended']
                    batch_records[key]['total'] += parsed['total']
                    batch_records[key]['remaining'] = parsed['remaining']
                else:
                    batch_records[key] = {
                        'student_pk': parsed['student_pk'],
                        'course_pk': parsed['course_pk'],
                        'attended': parsed['attended'],
                        'total': parsed['total'],
                        'remaining': parsed['remaining']
                    }
            else:  # Snapshot mode: last entry overrides earlier in file
                batch_records[key] = {
                    'student_pk': parsed['student_pk'],
                    'course_pk': parsed['course_pk'],
                    'attended': parsed['attended'],
                    'total': parsed['total'],
                    'remaining': parsed['remaining']
                }

            # Batch flush to database if batch threshold reached
            if len(batch_records) >= batch_size:
                c, u = _flush_batch_to_db(batch_records, import_mode)
                created_count += c
                updated_count += u
                batch_records.clear()

        # Flush any remaining items in batch
        if batch_records:
            c, u = _flush_batch_to_db(batch_records, import_mode)
            created_count += c
            updated_count += u
            batch_records.clear()

        # Mark job complete
        import_job.status = 'completed'
        import_job.total_rows = total_rows
        import_job.processed_rows = valid_rows + invalid_rows
        import_job.valid_rows = valid_rows
        import_job.invalid_rows = invalid_rows
        import_job.summary_text = (
            f"Mode: {import_mode.title()} | Total Rows: {total_rows} | "
            f"Valid: {valid_rows} | Invalid: {invalid_rows} | "
            f"New Records: {created_count} | Updated Records: {updated_count}"
        )
        import_job.error_details = "\n".join(error_log) if error_log else "None"
        import_job.completed_at = datetime.now(timezone.utc)
        db.session.commit()

        return {
            "success": True,
            "job_id": job_id,
            "import_mode": import_mode,
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "created_count": created_count,
            "updated_count": updated_count,
            "error_log": error_log
        }

    except Exception as e:
        db.session.rollback()
        import_job.status = 'failed'
        import_job.error_details = str(e)
        import_job.completed_at = datetime.now(timezone.utc)
        db.session.commit()
        return {
            "success": False,
            "job_id": job_id,
            "error": str(e),
            "total_rows": total_rows,
            "valid_rows": valid_rows,
            "invalid_rows": invalid_rows,
            "error_log": error_log
        }


def _flush_batch_to_db(batch_records: Dict[Tuple[int, int], Dict[str, Any]], import_mode: str) -> Tuple[int, int]:
    """
    Flushes a dictionary batch of student-course records inside a database transaction.
    """
    created = 0
    updated = 0

    for (student_pk, course_pk), item in batch_records.items():
        existing = AttendanceRecord.query.filter_by(
            student_id=student_pk,
            course_id=course_pk
        ).first()

        if existing:
            if import_mode == 'aggregate':
                existing.attended += item['attended']
                existing.total_conducted += item['total']
                existing.remaining_classes = item['remaining']
            else:  # snapshot mode
                existing.attended = item['attended']
                existing.total_conducted = item['total']
                existing.remaining_classes = item['remaining']
            existing.last_updated = datetime.now(timezone.utc)
            updated += 1
        else:
            new_record = AttendanceRecord(
                student_id=student_pk,
                course_id=course_pk,
                attended=item['attended'],
                total_conducted=item['total'],
                remaining_classes=item['remaining'],
                last_updated=datetime.now(timezone.utc)
            )
            db.session.add(new_record)
            created += 1

    db.session.commit()
    return created, updated
