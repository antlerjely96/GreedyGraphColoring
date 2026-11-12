import pandas as pd
import zipfile

def load_data_from_dataset(dataset_path="dataset.zip"):
    student_registrations = {}
    course_enrollments = {}
    course_ids = set()
    rooms_capacity = {}

    if zipfile.is_zipfile(dataset_path):
        with zipfile.ZipFile(dataset_path, 'r') as z:
            enroll_file = next((f for f in z.namelist() if 'enrolement' in f or f.endswith('.stu')), None)
            if not enroll_file:
                raise FileNotFoundError("Không tìm thấy file danh sách sinh viên (.stu hoặc enrolements) trong file ZIP.")
            with z.open(enroll_file) as f:
                lines = f.read().decode('utf-8', errors='ignore').strip().split('\n')

            room_file = next((f for f in z.namelist() if f == 'data' or 'room' in f.lower()), None)
            if room_file:
                with z.open(room_file) as rf:
                    room_lines = rf.read().decode('utf-8', errors='ignore').strip().split('\n')
                    reading_rooms = False
                    for r_line in room_lines:
                        if "ROOMS" in r_line:
                            reading_rooms = True
                            continue
                        if reading_rooms:
                            if "-----" in r_line: continue
                            if not r_line.strip():
                                if len(rooms_capacity) > 0: break
                                continue
                            parts = r_line.strip().split()
                            if len(parts) >= 2 and parts[1].isdigit():
                                r_name = parts[0]
                                r_cap = int(parts[1])
                                if r_name not in rooms_capacity:
                                    rooms_capacity[r_name] = r_cap
    else:
        with open(dataset_path, "r", encoding="utf-8") as f:
            lines = f.read().strip().split('\n')

    if not rooms_capacity:
        rooms_capacity = {f"ROOM_{i}": 100 for i in range(1, 50)}

    for line in lines:
        if not line.strip():
            continue
        parts = line.strip().split()
        if len(parts) >= 2:
            s_id = parts[0]
            c_ids = parts[1:]
            if s_id not in student_registrations:
                student_registrations[s_id] = []
            for c_id in c_ids:
                student_registrations[s_id].append(c_id)
                course_ids.add(c_id)
                course_enrollments[c_id] = course_enrollments.get(c_id, 0) + 1

    course_ids = sorted(list(course_ids))
    num_students = len(student_registrations)

    conflict_matrix = pd.DataFrame(0, index=course_ids, columns=course_ids)
    for s_id, courses in student_registrations.items():
        for i in range(len(courses)):
            for j in range(i + 1, len(courses)):
                c1, c2 = courses[i], courses[j]
                conflict_matrix.loc[c1, c2] += 1
                conflict_matrix.loc[c2, c1] += 1

    return course_ids, course_enrollments, student_registrations, conflict_matrix, num_students, rooms_capacity

