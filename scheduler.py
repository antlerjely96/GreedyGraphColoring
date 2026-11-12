import time
import numpy as np
import random

TIMESLOTS_PER_DAY = 3


def solve_exam_scheduling(ordering_strategy, course_ids, course_enrollments, student_registrations, conflict_matrix,
                          num_students, rooms_capacity):
    start_time = time.time()

    # Chuyển ma trận Pandas thành Danh sách kề (Adjacency List) để chạy cực nhanh
    adj = {c: [] for c in course_ids}
    degrees = {c: 0 for c in course_ids}

    c_list = list(course_ids)
    matrix_vals = conflict_matrix.values
    for i in range(len(c_list)):
        for j in range(i + 1, len(c_list)):
            if matrix_vals[i, j] > 0:
                adj[c_list[i]].append(c_list[j])
                adj[c_list[j]].append(c_list[i])
                degrees[c_list[i]] += 1
                degrees[c_list[j]] += 1

    enrollments = course_enrollments.copy()
    assigned_slots = {}
    assigned_rooms_per_course = {}
    available_rooms_per_slot = {}

    # Sắp xếp danh sách phòng từ lớn đến bé một lần duy nhất
    original_rooms_desc = sorted(list(rooms_capacity.items()), key=lambda x: x[1], reverse=True)

    saturation_degrees = {c: 0 for c in course_ids}
    neighbor_slots = {c: set() for c in course_ids}
    unassigned = set(course_ids)

    while unassigned:
        # Lựa chọn phần tử theo chiến lược
        if ordering_strategy == "LDF":
            curr = max(unassigned, key=lambda c: (degrees[c], enrollments[c]))
        elif ordering_strategy == "LEF":
            curr = max(unassigned, key=lambda c: (enrollments[c], degrees[c]))
        elif ordering_strategy == "DSATUR":
            curr = max(unassigned, key=lambda c: (saturation_degrees[c], degrees[c], enrollments[c]))
        elif ordering_strategy == "RANDOM":
            # Chọn ngẫu nhiên an toàn trực tiếp từ tập hợp unassigned
            curr = random.choice(list(unassigned))

        num_students_exam = enrollments[curr]
        slot = 0

        while True:
            conflict = False

            # RÀNG BUỘC 1: Không trùng ca thi (dùng Adjacency List tra cứu O(1))
            for neighbor in adj[curr]:
                if assigned_slots.get(neighbor) == slot:
                    conflict = True
                    break

            if conflict:
                slot += 1
                continue

            # RÀNG BUỘC 2: Xếp phòng và ghép phòng theo sức chứa
            if slot not in available_rooms_per_slot:
                available_rooms_per_slot[slot] = original_rooms_desc.copy()

            avail_rooms = available_rooms_per_slot[slot]
            allocated_rooms = []
            alloc_indices = []

            # Tìm phòng đơn Best Fit
            best_idx = -1
            min_diff = float('inf')
            for i, r in enumerate(avail_rooms):
                if r[1] >= num_students_exam and (r[1] - num_students_exam) < min_diff:
                    best_idx = i
                    min_diff = r[1] - num_students_exam

            if best_idx != -1:
                allocated_rooms.append(avail_rooms[best_idx])
                alloc_indices.append(best_idx)
            else:
                # Ghép nhiều phòng nếu không có phòng đơn nào đủ lớn
                cap_acc = 0
                for i, r in enumerate(avail_rooms):
                    allocated_rooms.append(r)
                    alloc_indices.append(i)
                    cap_acc += r[1]
                    if cap_acc >= num_students_exam:
                        break

                if cap_acc < num_students_exam:
                    conflict = True

            if not conflict:
                for idx in sorted(alloc_indices, reverse=True):
                    avail_rooms.pop(idx)
                assigned_rooms_per_course[curr] = allocated_rooms
                break

            slot += 1

        assigned_slots[curr] = slot
        unassigned.remove(curr)

        # Cập nhật bậc bão hòa cho DSATUR
        for neighbor in adj[curr]:
            if neighbor in unassigned:
                if slot not in neighbor_slots[neighbor]:
                    neighbor_slots[neighbor].add(slot)
                    saturation_degrees[neighbor] = len(neighbor_slots[neighbor])

    runtime = (time.time() - start_time) * 1000
    total_timeslots = max(assigned_slots.values()) + 1
    total_days = int(np.ceil(total_timeslots / TIMESLOTS_PER_DAY))

    consecutive_penalty = 0
    same_day_penalty = 0

    for s_id, courses in student_registrations.items():
        slots = sorted([assigned_slots[c] for c in courses])
        for i in range(len(slots) - 1):
            s1, s2 = slots[i], slots[i + 1]
            if s1 // TIMESLOTS_PER_DAY == s2 // TIMESLOTS_PER_DAY:
                if s2 - s1 == 1:
                    consecutive_penalty += 10
                else:
                    same_day_penalty += 5

    total_penalty = consecutive_penalty + same_day_penalty

    return {
        "Chiến lược": ordering_strategy,
        "TG chạy (ms)": round(runtime, 2),
        "Tổng số ca": total_timeslots,
        "Tổng số ngày": total_days,
        "Điểm phạt P": total_penalty,
        "P trung bình/SV": round(total_penalty / num_students, 2),
        "Lịch thi": assigned_slots,
        "Room Allocation": assigned_rooms_per_course
    }

