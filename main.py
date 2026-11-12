import pandas as pd
import os
from collections import defaultdict
from data_loader import load_data_from_dataset
from scheduler import solve_exam_scheduling


def export_concrete_schedule(assigned_slots, assigned_rooms, course_enrollments, strategy_name, student_registrations,
                             timeslots_per_day=3):
    schedule_data = []
    ca_thi_labels = ["Sáng", "Chiều", "Tối"]

    for course, slot in assigned_slots.items():
        day = (slot // timeslots_per_day) + 1
        slot_in_day = slot % timeslots_per_day

        allocated_rooms = assigned_rooms.get(course, [])
        room_names = [r[0] for r in allocated_rooms]
        assigned_cap = sum([r[1] for r in allocated_rooms])
        num_students = course_enrollments.get(course, 0)

        assigned_room_str = " + ".join(room_names)

        schedule_data.append({
            "Mã Môn Thi": course,
            "Số Lượng SV": num_students,
            "Ngày Thi": f"Ngày {day}",
            "Ca Thi": ca_thi_labels[slot_in_day],
            "Phòng Thi": assigned_room_str,
            "Sức Chứa Phòng": assigned_cap,
            "Slot Toán Học": slot
        })

    df_schedule = pd.DataFrame(schedule_data)
    df_schedule = df_schedule.sort_values(by=["Slot Toán Học", "Mã Môn Thi"])
    df_schedule = df_schedule.drop(columns=["Slot Toán Học"])

    # Định dạng .xlsx vì định dạng CSV không hỗ trợ tính năng tạo nhiều Sheet
    file_name = f"Lich_Thi_{strategy_name}.xlsx"

    # Nghịch đảo từ student_registrations -> danh sách SV theo môn
    course_students = defaultdict(list)
    for s_id, courses in student_registrations.items():
        for c in courses:
            course_students[c].append(s_id)

    # Mở ExcelWriter để ghi nhiều sheet
    with pd.ExcelWriter(file_name, engine='openpyxl') as writer:
        # 1. Ghi lịch tổng quát
        df_schedule.to_excel(writer, sheet_name="Lịch Tổng Quát", index=False)

        # 2. Ghi danh sách sinh viên cho TỪNG MÔN THI
        for course in df_schedule["Mã Môn Thi"].tolist():
            # Xử lý tên sheet hợp lệ (tối đa 31 ký tự, không chứa ký tự đặc biệt)
            sheet_name = str(course)[:31].translate(str.maketrans("", "", ":/\\?*[]"))

            students = course_students.get(course, [])

            # Lấy thông tin phòng, ca thi của môn này
            room_info = df_schedule[df_schedule["Mã Môn Thi"] == course].iloc[0]

            course_data = []
            for s_id in sorted(students):
                course_data.append({
                    "Mã Sinh Viên": s_id,
                    "Mã Môn Thi": course,
                    "Ngày Thi": room_info["Ngày Thi"],
                    "Ca Thi": room_info["Ca Thi"],
                    "Phòng Thi": room_info["Phòng Thi"]
                })

            if course_data:
                df_course = pd.DataFrame(course_data)
                df_course.to_excel(writer, sheet_name=sheet_name, index=False)

    print(f"  -> Đã xuất lịch thi và danh sách SV ra file: {file_name}")


def main():
    dataset_path = "Nott.zip"

    print(f"[*] Đang tải và xử lý dữ liệu từ {dataset_path}...")
    if not os.path.exists(dataset_path):
        print(f"[!] Lỗi: Không tìm thấy file {dataset_path}.")
        return

    try:
        course_ids, course_enrollments, student_registrations, conflict_matrix, num_students, rooms_capacity = load_data_from_dataset(
            dataset_path)
        print(
            f"[+] Tải thành công: {num_students} sinh viên, {len(course_ids)} môn thi và {len(rooms_capacity)} phòng học.\n")
    except Exception as e:
        print(f"[!] Lỗi khi đọc dữ liệu: {e}")
        return

    strategies = ["LDF", "DSATUR", "LEF", "RANDOM"]
    results = []

    print("[*] Đang chạy thuật toán Xếp lịch & Phân phòng (Sẽ xuất 4 file EXCEL)...")

    for s in strategies:
        print(f"\n[*] Đang chạy chiến lược: {s}...")
        res = solve_exam_scheduling(s, course_ids, course_enrollments, student_registrations, conflict_matrix,
                                    num_students, rooms_capacity)

        results.append({
            "Chiến lược": res["Chiến lược"],
            "TG chạy (ms)": res["TG chạy (ms)"],
            "Tổng số ca": res["Tổng số ca"],
            "Tổng số ngày": res["Tổng số ngày"],
            "Điểm phạt P": res["Điểm phạt P"],
            "P trung bình/SV": res["P trung bình/SV"]
        })

        # Truyền thêm student_registrations vào hàm xuất file
        export_concrete_schedule(res["Lịch thi"], res["Room Allocation"], course_enrollments, s, student_registrations)

    df_results = pd.DataFrame(results)
    print("\n=== BẢNG ĐÁNH GIÁ CÁC CHIẾN LƯỢC ===")
    print(df_results.to_string(index=False))


if __name__ == "__main__":
    main()

