"""
🛠️ TOOL DEFINITIONS & EXECUTION BACKEND
Mã nguồn chứa danh sách Tool Schemas (JSON Schema) và Execution Layer phục vụ cho MCP Server.
Chủ đề: Trợ lý Quản lý Công việc (To-do Task Manager Assistant).
"""

import json
import os
from typing import Dict, Any

# ==============================================================================
# 1. KHAI BÁO TOOL SCHEMAS CHUẨN NATIVE JSON SCHEMA (TASK 1.2)
# ==============================================================================

TOOLS_SCHEMA = [
    # Tool 1: Tra cứu danh sách công việc theo trạng thái
    {
        "name": "get_tasks_by_status",
        "description": "Tra cứu danh sách công việc (task) theo trạng thái hiện tại (đang chờ xử lý hoặc đã hoàn thành).",
        "parameters": {
            "type": "object",
            "properties": {
                "status": {
                    "type": "string",
                    "description": "Trạng thái công việc cần tra cứu, ví dụ 'pending' (đang chờ xử lý) hoặc 'done' (đã hoàn thành). Truyền đúng theo yêu cầu của người dùng dù giá trị đó có tồn tại trong hệ thống hay không."
                }
            },
            "required": ["status"]
        }
    },

    # Tool 2: Tạo công việc mới
    {
        "name": "create_task",
        "description": "Tạo một công việc (task) mới với tiêu đề, hạn hoàn thành và mức độ ưu tiên.",
        "parameters": {
            "type": "object",
            "properties": {
                "title": {
                    "type": "string",
                    "description": "Tiêu đề / nội dung công việc cần tạo (ví dụ: 'Hoàn thành báo cáo tuần')."
                },
                "due_date": {
                    "type": "string",
                    "description": "Hạn hoàn thành công việc (ví dụ: '20/09/2026')."
                },
                "priority": {
                    "type": "string",
                    "description": "Mức độ ưu tiên của công việc.",
                    "enum": ["Cao", "Trung bình", "Thấp"]
                }
            },
            "required": ["title", "due_date"]
        }
    },

    # Tool 3: Cập nhật trạng thái công việc
    {
        "name": "update_task_status",
        "description": "Cập nhật trạng thái của một công việc đã tồn tại theo mã công việc (task_id).",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Mã công việc cần cập nhật (ví dụ: 'T001')."
                },
                "new_status": {
                    "type": "string",
                    "description": "Trạng thái mới cần gán cho công việc, ví dụ 'pending' hoặc 'done'."
                }
            },
            "required": ["task_id", "new_status"]
        }
    },

    # Tool 4: Xóa công việc
    {
        "name": "delete_task",
        "description": "Xóa một công việc khỏi hệ thống theo mã công việc (task_id).",
        "parameters": {
            "type": "object",
            "properties": {
                "task_id": {
                    "type": "string",
                    "description": "Mã công việc cần xóa (ví dụ: 'T001')."
                }
            },
            "required": ["task_id"]
        }
    }
]

# ==============================================================================
# 2. MÔ PHỎNG DỮ LIỆU & HÀM THỰC THI TOOL (EXECUTION LAYER)
# ==============================================================================

_DEFAULT_TASKS_DB = {
    "T001": {
        "title": "Hoàn thành báo cáo tuần",
        "due_date": "20/09/2026",
        "priority": "Cao",
        "status": "pending"
    },
    "T002": {
        "title": "Chuẩn bị slide họp nhóm",
        "due_date": "18/09/2026",
        "priority": "Trung bình",
        "status": "pending"
    },
    "T003": {
        "title": "Nộp bài Lab 3 ReAct Agent",
        "due_date": "15/09/2026",
        "priority": "Cao",
        "status": "done"
    },
    "T004": {
        "title": "Dọn dẹp hộp thư email",
        "due_date": "22/09/2026",
        "priority": "Thấp",
        "status": "done"
    }
}

# File lưu trạng thái để dữ liệu công việc sống sót qua các lần chạy khác nhau
# của chương trình (mỗi lần restart Python, dict trong RAM sẽ mất nếu không có file này).
_STATE_FILE = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "tasks_state.json")


def _load_state():
    """Nạp TASKS_DB + bộ đếm task_id từ file trạng thái nếu có, ngược lại dùng dữ liệu mẫu mặc định."""
    if os.path.exists(_STATE_FILE):
        try:
            with open(_STATE_FILE, "r", encoding="utf-8") as f:
                saved = json.load(f)
            return saved.get("tasks", _DEFAULT_TASKS_DB), saved.get("next_task_seq", len(_DEFAULT_TASKS_DB) + 1)
        except Exception:
            pass
    return dict(_DEFAULT_TASKS_DB), len(_DEFAULT_TASKS_DB) + 1


def _save_state():
    """Ghi TASKS_DB + bộ đếm task_id hiện tại ra file trạng thái để lần chạy sau nạp lại được."""
    os.makedirs(os.path.dirname(_STATE_FILE), exist_ok=True)
    with open(_STATE_FILE, "w", encoding="utf-8") as f:
        json.dump({"tasks": TASKS_DB, "next_task_seq": _next_task_seq}, f, ensure_ascii=False, indent=2)


TASKS_DB, _next_task_seq = _load_state()


def execute_get_tasks_by_status(status: str) -> str:
    """Thực thi tra cứu danh sách công việc theo trạng thái"""
    status_norm = status.strip().lower()
    matched = [
        {"task_id": task_id, **task}
        for task_id, task in TASKS_DB.items()
        if task["status"] == status_norm
    ]
    return json.dumps({
        "status": "SUCCESS",
        "filter_status": status_norm,
        "count": len(matched),
        "tasks": matched
    }, ensure_ascii=False)


def execute_create_task(title: str, due_date: str, priority: str = "Trung bình") -> str:
    """Thực thi tạo công việc mới"""
    global _next_task_seq
    task_id = f"T{_next_task_seq:03d}"
    _next_task_seq += 1

    TASKS_DB[task_id] = {
        "title": title,
        "due_date": due_date,
        "priority": priority,
        "status": "pending"
    }
    _save_state()

    return json.dumps({
        "status": "SUCCESS",
        "task_id": task_id,
        "title": title,
        "due_date": due_date,
        "priority": priority,
        "message": f"Đã tạo công việc '{title}' (mã {task_id}) với hạn hoàn thành {due_date}, ưu tiên {priority}."
    }, ensure_ascii=False)


def execute_update_task_status(task_id: str, new_status: str) -> str:
    """Thực thi cập nhật trạng thái công việc theo mã task_id"""
    key = task_id.strip().upper()
    task = TASKS_DB.get(key)
    if not task:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy công việc có mã '{task_id}' để cập nhật."
        }, ensure_ascii=False)

    task["status"] = new_status.strip().lower()
    _save_state()
    return json.dumps({
        "status": "SUCCESS",
        "task_id": key,
        "new_status": task["status"],
        "message": f"Đã cập nhật công việc '{task['title']}' (mã {key}) sang trạng thái '{task['status']}'."
    }, ensure_ascii=False)


def execute_delete_task(task_id: str) -> str:
    """Thực thi xóa công việc theo mã task_id"""
    key = task_id.strip().upper()
    task = TASKS_DB.pop(key, None)
    if not task:
        return json.dumps({
            "status": "NOT_FOUND",
            "message": f"Không tìm thấy công việc có mã '{task_id}' để xóa."
        }, ensure_ascii=False)
    _save_state()

    return json.dumps({
        "status": "SUCCESS",
        "task_id": key,
        "message": f"Đã xóa công việc '{task['title']}' (mã {key})."
    }, ensure_ascii=False)


# Router gọi tool thực tế
TOOL_ROUTER = {
    "get_tasks_by_status": execute_get_tasks_by_status,
    "create_task": execute_create_task,
    "update_task_status": execute_update_task_status,
    "delete_task": execute_delete_task
}

def dispatch_tool_call(tool_name: str, arguments: Dict[str, Any]) -> str:
    """Hàm trung chuyển thực thi tool"""
    if tool_name in TOOL_ROUTER:
        try:
            return TOOL_ROUTER[tool_name](**arguments)
        except Exception as e:
            return json.dumps({"status": "EXECUTION_ERROR", "error": str(e)}, ensure_ascii=False)
    return json.dumps({"status": "UNKNOWN_TOOL", "error": f"Tool '{tool_name}' không tồn tại!"}, ensure_ascii=False)
