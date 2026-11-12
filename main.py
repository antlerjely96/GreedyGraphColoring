import pandas as pd
import os
from data_loader import load_data_from_dataset
from scheduler import solve_exam_scheduling


def export_concrete_schedule(assigned_slots, assigned_rooms, course_enrollments, strategy_name, timeslots_per_day=3):
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

    file_name = f"Lich_Thi_{strategy_name}.csv"
    df_schedule.to_csv(file_name, index=False, encoding="utf-8-sig")

    print(f"\n[+] Đã xuất lịch thi chi tiết ra file: {file_name}")
    print("\n=== MỘT PHẦN LỊCH THI CHI TIẾT ===")
    print(df_schedule.head(15).to_string(index=False))
    print(f"... (Xem đầy đủ danh sách {len(df_schedule)} môn thi trong file CSV) ...\n")


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
            f"[+] Tải thành công: {num_students} sinh viên, {len(course_ids)} môn thi và {len(rooms_capacity)} phòng học.")
    except Exception as e:
        print(f"[!] Lỗi khi đọc dữ liệu: {e}")
        return

    strategies = ["LDF", "DSATUR", "LEF", "RANDOM"]
    results = []
    best_schedule = None
    best_rooms = None
    best_strategy = ""

    print("[*] Đang chạy thuật toán RÀNG BUỘC KÉP (Phòng thi & Xung đột Ca thi)...\n")

    for s in strategies:
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

        if s == "DSATUR":
            best_schedule = res["Lịch thi"]
            best_rooms = res["Room Allocation"]
            best_strategy = s

    df_results = pd.DataFrame(results)
    print("=== BẢNG ĐÁNH GIÁ CÁC CHIẾN LƯỢC ===")
    print(df_results.to_string(index=False))

    if best_schedule:
        export_concrete_schedule(best_schedule, best_rooms, course_enrollments, best_strategy)


if __name__ == "__main__":
    main()