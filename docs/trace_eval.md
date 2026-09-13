# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Trần Đại Nhân
> **Mã Sinh Viên / Mã Học viên:** 2A202602642  
> **Chủ đề Lựa chọn:** Trợ lý Quản lý Công việc cá nhân (To-do Task Manager Assistant) — Đề tài Mở (Open Choice), mục 5 trong `docs/DANH_SACH_DE_TAI.md`  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 4 / 5 | TC04 minh chứng Agent thực sự tách yêu cầu thành 2 bước tuần tự: gọi `get_tasks_by_status` trước, đọc Observation, rồi mới quyết định gọi tiếp `update_task_status` — vòng lặp ReAct đã được nâng cấp thành true multi-step (LLM được hỏi lại sau mỗi Observation thay vì dừng sau 1 lượt Tool). Chưa đạt tối đa vì bài toán chưa cần lập kế hoạch (planning) nhiều tầng phức tạp hơn nữa. |
| **2. Tool Interaction** | 4 / 5 | Hệ thống có 4 Tool CRUD hoàn chỉnh qua MCP Server: `get_tasks_by_status` (Read), `create_task` (Create), `update_task_status` (Update), `delete_task` (Delete) — không thể trả lời hay thao tác chính xác nếu chỉ dựa vào kiến thức nền của LLM vì dữ liệu công việc là động. |
| **3. Dynamic Decision** | 4 / 5 | Agent tự quyết định: có cần gọi Tool hay không (TC01 vs TC02), gọi đúng Tool nào trong 4 Tool sẵn có, và xử lý linh hoạt khi tham số không khớp dữ liệu thực tế (TC05: xóa mã không tồn tại → nhận NOT_FOUND và phản hồi đúng thay vì bịa đặt "đã xóa thành công"). |
| **4. Long Horizon Goal** | 2 / 5 | Mỗi truy vấn trong bài Lab là một phiên độc lập (không có bộ nhớ hội thoại xuyên suốt nhiều lượt hỏi-đáp của người dùng), nên chưa thể hiện rõ việc giữ mục tiêu dài hạn qua nhiều lượt tương tác như một Agent cấp 4 (Autonomous Agent). |
| **TỔNG ĐIỂM AGENTIC FIT** | **14 / 20** | Tổng điểm > 12/20 → Bài toán "Trợ lý Quản lý Công việc" phù hợp để triển khai dưới dạng ReAct Agent (Cấp 3), không cần đến Autonomous Agent (Cấp 4). |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json`, sinh ra từ phản hồi **OpenAI GPT-4o-mini thật** (chạy `python src/app.py --all` với `LLM_PROVIDER=openai`). Đây là log của **TC04**, thể hiện đúng **true multi-step ReAct**: Agent tự gọi liên tiếp 2 Tool khác nhau (`get_tasks_by_status` rồi `update_task_status`) qua 2 vòng lặp riêng biệt trước khi tổng hợp Final Answer ở vòng thứ 3:

```json
[
  {
    "step": 1,
    "query": "Trước tiên hãy kiểm tra xem có công việc nào đã hoàn thành (done) chưa, sau đó cập nhật công việc có mã T001 sang trạng thái 'done'.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "get_tasks_by_status",
    "arguments": { "status": "done" },
    "observation": {
      "status": "SUCCESS",
      "filter_status": "done",
      "count": 2,
      "tasks": [
        { "task_id": "T003", "title": "Nộp bài Lab 3 ReAct Agent", "due_date": "15/09/2026", "priority": "Cao", "status": "done" },
        { "task_id": "T004", "title": "Dọn dẹp hộp thư email", "due_date": "22/09/2026", "priority": "Thấp", "status": "done" }
      ]
    },
    "latency_ms": 623.3
  },
  {
    "step": 2,
    "query": "Trước tiên hãy kiểm tra xem có công việc nào đã hoàn thành (done) chưa, sau đó cập nhật công việc có mã T001 sang trạng thái 'done'.",
    "action_type": "TOOL_EXECUTION",
    "tool_name": "update_task_status",
    "arguments": { "task_id": "T001", "new_status": "done" },
    "observation": {
      "status": "SUCCESS",
      "task_id": "T001",
      "new_status": "done",
      "message": "Đã cập nhật công việc 'Hoàn thành báo cáo tuần' (mã T001) sang trạng thái 'done'."
    },
    "latency_ms": 757.25
  },
  {
    "step": 3,
    "query": "Trước tiên hãy kiểm tra xem có công việc nào đã hoàn thành (done) chưa, sau đó cập nhật công việc có mã T001 sang trạng thái 'done'.",
    "action_type": "FINAL_ANSWER",
    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi thêm công cụ).",
    "output": "Tôi đã kiểm tra và tìm thấy 2 công việc đã hoàn thành... Công việc có mã T001 đã được cập nhật thành công sang trạng thái 'done'.",
    "latency_ms": 1457.68
  }
]
```

> 📄 Toàn bộ 10 sự kiện của cả 5 Test Cases (TC01-TC05) được lưu đầy đủ tại [`docs/trace_waterfall.json`](trace_waterfall.json).

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` (`OPENAI_API_KEY`, `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4o-mini`) và xác nhận Agent chạy mượt mà trên LLM API thật.
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 5 lượt trên cả 4 loại Tool (TC02: `get_tasks_by_status`; TC03: `create_task`; TC04: `get_tasks_by_status` **+** `update_task_status` — 2 lượt liên tiếp trong cùng 1 câu hỏi; TC05: `delete_task`). TC01 trả lời trực tiếp, đúng như kỳ vọng (câu hỏi chung không cần Tool).
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân (`K4A-DAY03-TranDaiNhan-2A202602642`).

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
