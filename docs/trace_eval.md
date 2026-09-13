# 📊 BÁO CÁO THU HOẠCH NGHIỆM THU BÀI LAB 3 (BƯỚC 3 — SUBMISSION ARTIFACT)

> **Họ và Tên Học viên:** Trần Đại Nhân
> **Mã Sinh Viên / Mã Học viên:** 2A202602642  
> **Chủ đề Lựa chọn:** Trợ lý Quản lý Công việc cá nhân (To-do Task Manager Assistant) — Đề tài Mở (Open Choice), mục 5 trong `docs/DANH_SACH_DE_TAI.md`  

---

## 1. BẢNG CHẤM ĐIỂM AGENTIC FIT SCORING MATRIX (ĐÁNH GIÁ CHỦ ĐỀ)

| Tiêu chí Đánh giá | Mức độ (1 - 5) | Giải trình chi tiết lý do chọn điểm |
| :--- | :---: | :--- |
| **1. Multi-step Reasoning** | 5 / 5 | Agent có tầng **Planner** riêng (`plan_task()` trong `src/app.py`) lập kế hoạch nhiều bước TRƯỚC KHI hành động, rồi bám theo kế hoạch đó qua vòng lặp ReAct true multi-step. Bằng chứng rõ nhất: ở TC05, dù kế hoạch chỉ ghi 1 bước ("Xóa công việc T999"), Agent tự ý mở rộng thành 3 hành động tuần tự (kiểm tra `pending` → kiểm tra `done` → mới `delete_task`) để xác minh chắc chắn trước khi kết luận — hành vi suy luận chủ động, không chỉ máy móc theo kịch bản. |
| **2. Tool Interaction** | 4 / 5 | Hệ thống có 4 Tool CRUD hoàn chỉnh qua MCP Server: `get_tasks_by_status` (Read), `create_task` (Create), `update_task_status` (Update), `delete_task` (Delete) — không thể trả lời hay thao tác chính xác nếu chỉ dựa vào kiến thức nền của LLM vì dữ liệu công việc là động. |
| **3. Dynamic Decision** | 5 / 5 | Agent tự quyết định: có cần gọi Tool hay không (TC01 vs TC02), gọi đúng Tool nào trong 4 Tool sẵn có, và có cơ chế **Reflexion** tường minh — khi một Observation cho thấy Hành động thất bại (`NOT_FOUND`/`EXECUTION_ERROR`/`UNKNOWN_TOOL`), Agent nhận một nhắc nhở tự phản tư (log `action_type: "REFLECTION"`) buộc phải suy xét nguyên nhân trước khi quyết định bước tiếp theo, thay vì lặp lại y nguyên hành động đã sai hoặc bịa đặt kết quả. |
| **4. Long Horizon Goal** | 3 / 5 | Trong phạm vi 1 câu hỏi, Agent giữ mục tiêu xuyên suốt nhờ [KẾ HOẠCH ĐÃ LẬP] + [TIẾN ĐỘ HIỆN TẠI] được nhắc lại ở mỗi vòng lặp (system prompt động) — đây là bước tiến rõ rệt so với thiết kế ReAct Agent Cấp 3 thuần túy, tiệm cận đặc điểm "tự rã mục tiêu" của Cấp 4 (Autonomous Agent). Chưa đạt tối đa vì vẫn chưa có bộ nhớ xuyên suốt NHIỀU câu hỏi khác nhau trong cùng phiên `--interactive` (mỗi câu hỏi mới vẫn lập kế hoạch từ đầu, không kế thừa ngữ cảnh hội thoại trước đó). |
| **TỔNG ĐIỂM AGENTIC FIT** | **17 / 20** | Tổng điểm > 12/20 → Bài toán "Trợ lý Quản lý Công việc" rất phù hợp triển khai Agentic System; với tầng Planner + Reflexion đã bổ sung, hệ thống tiệm cận ranh giới giữa ReAct Agent (Cấp 3) và Autonomous Agent (Cấp 4) theo khung lý thuyết của khóa học. |

---

## 2. TRÍCH XUẤT KẾT QUẢ WATERFALL TRACE LOG (SAU KHI CHẠY TEST SUITE TRÊN API THẬT)

> ⚠️ **YÊU CẦU NGHIỆM THU:** Mở tệp `.env` điền `GEMINI_API_KEY` (hoặc `OPENAI_API_KEY`) để kết nối LLM thật trước khi thực thi `python src/app.py --all`. Bài nộp chỉ dùng Mock Offline Provider sẽ không đạt điểm nghiệm thực tế.

Đoạn trích xuất log tiêu biểu từ file `docs/trace_waterfall.json`, sinh ra từ phản hồi **OpenAI GPT-4o-mini thật** (chạy `python src/app.py --all` với `LLM_PROVIDER=openai`). Đây là log **TC05** — bằng chứng rõ nhất cho tầng **Planner + Reflexion** mới bổ sung: Agent lập kế hoạch 1 bước, nhưng khi thực thi lại tự mở rộng thành 2 lượt tra cứu xác minh trước khi thử xóa, gặp thất bại `NOT_FOUND` thì được nhắc **Reflexion** để tự phản tư thay vì bịa kết quả, rồi mới tổng hợp câu trả lời trung thực:

```json
[
  {
    "step": 0,
    "query": "Hãy xóa giúp tôi công việc có mã T999.",
    "action_type": "PLAN",
    "thought": "Lập kế hoạch nhiều bước trước khi thực thi ReAct Loop.",
    "plan": ["Xóa công việc có mã T999"],
    "latency_ms": 0.0
  },
  {
    "step": 1,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "get_tasks_by_status",
    "arguments": { "status": "pending" },
    "observation": { "status": "SUCCESS", "filter_status": "pending", "count": 2, "tasks": ["...(T002, T005)"] },
    "latency_ms": 1422.11
  },
  {
    "step": 2,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "get_tasks_by_status",
    "arguments": { "status": "done" },
    "observation": { "status": "SUCCESS", "filter_status": "done", "count": 3, "tasks": ["...(T001, T003, T004)"] },
    "latency_ms": 810.87
  },
  {
    "step": 3,
    "action_type": "TOOL_EXECUTION",
    "tool_name": "delete_task",
    "arguments": { "task_id": "T999" },
    "observation": { "status": "NOT_FOUND", "message": "Không tìm thấy công việc có mã 'T999' để xóa." },
    "latency_ms": 705.99
  },
  {
    "step": 3,
    "action_type": "REFLECTION",
    "thought": "⚠️ [Reflexion] Hành động 'delete_task' vừa rồi KHÔNG thành công như mong đợi (status=NOT_FOUND). Hãy đọc kỹ Observation ở trên, suy xét nguyên nhân..., rồi quyết định: thử lại với tham số khác, chọn Tool phù hợp hơn, hoặc dừng lại và báo trung thực cho người dùng.",
    "observation": { "status": "NOT_FOUND", "message": "Không tìm thấy công việc có mã 'T999' để xóa." },
    "latency_ms": 0.0
  },
  {
    "step": 4,
    "action_type": "FINAL_ANSWER",
    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi thêm công cụ).",
    "output": "Công việc có mã \"T999\" không tồn tại trong hệ thống, vì tôi đã kiểm tra cả công việc đang chờ xử lý và công việc đã hoàn thành, nhưng không tìm thấy mã này. Vậy nên, tôi không thể xóa công việc \"T999\" vì nó không có trong danh sách.",
    "latency_ms": 1199.63
  }
]
```

> 📄 Toàn bộ 18 sự kiện của cả 5 Test Cases (TC01-TC05), bao gồm cả các bước `PLAN` và `REFLECTION`, được lưu đầy đủ tại [`docs/trace_waterfall.json`](trace_waterfall.json).

---

## 3. TỔNG KẾT KẾT QUẢ NGHIỆM THU & NỘP BÀI

- [x] Đã điền API Key thật trong `.env` (`OPENAI_API_KEY`, `LLM_PROVIDER=openai`, `LLM_MODEL=gpt-4o-mini`) và xác nhận Agent chạy mượt mà trên LLM API thật.
- **Tổng số Test Cases đã chạy thành công:** 5 / 5 test cases.
- **Số lượt gọi Tool qua MCP Server chính xác:** 7 lượt trên cả 4 loại Tool (TC02: `get_tasks_by_status`; TC03: `create_task`; TC04: `get_tasks_by_status` **+** `update_task_status`; TC05: `get_tasks_by_status` (pending) **+** `get_tasks_by_status` (done) **+** `delete_task` — Agent tự xác minh 2 lần trước khi thử xóa). TC01 trả lời trực tiếp, đúng như kỳ vọng (câu hỏi chung không cần Tool).
- **Cơ chế Planner + Reflexion:** Mỗi câu hỏi đều có 1 sự kiện `PLAN` mở đầu trace; TC05 phát sinh thêm 1 sự kiện `REFLECTION` khi `delete_task` trả về `NOT_FOUND`, chứng minh Agent tự phản tư thay vì bịa kết quả.
- **Kết quả đẩy Repo nộp bài:** [x] Đã Commit và Push mã nguồn thành công lên GitHub cá nhân (`K4A-DAY03-TranDaiNhan-2A202602642`).

---

> ✅ **HOÀN TẤT NỘP BÀI:** Sao chép đường link GitHub Repository cá nhân của bạn và dán vào ô nộp bài trên hệ thống LMS VLearn để hoàn tất Bài Lab 3!
