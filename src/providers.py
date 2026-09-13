"""
🔌 MULTI-PROVIDER LLM ADAPTER (Google Gemini, OpenAI & Offline Mock)
Hỗ trợ Native Tool Calling (đa lượt, true multi-step ReAct) và chuyển đổi linh hoạt qua biến môi trường LLM_PROVIDER.

Định dạng `messages` (chung cho mọi provider, độc lập SDK):
- {"role": "user", "content": str}
- {"role": "assistant", "type": "tool_call", "tool_name": str, "arguments": dict, "tool_call_id": Optional[str]}
- {"role": "tool", "tool_name": str, "content": str, "tool_call_id": Optional[str]}
"""

import os
import re
import sys
import json
from typing import Dict, Any, List
from dotenv import load_dotenv

if sys.stdout.encoding != 'utf-8':
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

load_dotenv()

class BaseLLMProvider:
    """Interface cơ sở cho các LLM Provider hỗ trợ Native Tool Calling"""
    def generate(self, prompt: str, system_prompt: str = "") -> str:
        raise NotImplementedError

    def generate_with_tools(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        raise NotImplementedError


class MockOfflineProvider(BaseLLMProvider):
    """Offline Mock Provider dùng để chạy thử mà không tốn API Key"""
    def __init__(self):
        self.model_name = "Offline-Mock-Model-2026"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        return f"[Mock Chatbot Response]: Xin chào! Tôi đã nhận được câu hỏi '{prompt}'. (Chế độ Chatbot không có Tool tra cứu dữ liệu thời gian thực)."

    def generate_with_tools(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        last_user = next((m["content"] for m in reversed(messages) if m.get("role") == "user"), "")
        prompt_lower = last_user.lower()
        done_tools = {m["tool_name"] for m in messages if m.get("role") == "assistant" and m.get("type") == "tool_call"}

        # Trích xuất thô: tiêu đề trong dấu nháy đơn, ngày dạng dd/mm/yyyy, mã task dạng T + số
        title_match = re.search(r"'([^']+)'", last_user)
        date_match = re.search(r"\d{1,2}/\d{1,2}/\d{4}", last_user)
        task_id_match = re.search(r"\bT\d{3}\b", last_user, re.IGNORECASE)

        if "xóa" in prompt_lower and "delete_task" not in done_tools:
            return {
                "type": "tool_call",
                "tool_name": "delete_task",
                "arguments": {"task_id": (task_id_match.group(0).upper() if task_id_match else "T001")},
                "thought": "Người dùng yêu cầu xóa một công việc. Tôi sẽ gọi tool delete_task."
            }
        if ("kiểm tra" in prompt_lower or "xem" in prompt_lower or "danh sách" in prompt_lower) and "get_tasks_by_status" not in done_tools:
            return {
                "type": "tool_call",
                "tool_name": "get_tasks_by_status",
                "arguments": {"status": "done" if ("đã hoàn thành" in prompt_lower or "done" in prompt_lower) else "pending"},
                "thought": "Người dùng muốn tra cứu danh sách công việc. Tôi sẽ gọi tool get_tasks_by_status."
            }
        if ("cập nhật" in prompt_lower or "đánh dấu" in prompt_lower) and "update_task_status" not in done_tools:
            return {
                "type": "tool_call",
                "tool_name": "update_task_status",
                "arguments": {
                    "task_id": (task_id_match.group(0).upper() if task_id_match else "T001"),
                    "new_status": "done"
                },
                "thought": "Người dùng yêu cầu cập nhật trạng thái công việc. Tôi sẽ gọi tool update_task_status."
            }
        if "tạo" in prompt_lower and "create_task" not in done_tools:
            return {
                "type": "tool_call",
                "tool_name": "create_task",
                "arguments": {
                    "title": (title_match.group(1) if title_match else "Công việc mới"),
                    "due_date": (date_match.group(0) if date_match else "30/09/2026"),
                    "priority": "Cao" if "cao" in prompt_lower else "Trung bình"
                },
                "thought": "Người dùng yêu cầu tạo một công việc mới. Tôi sẽ gọi tool create_task."
            }

        if done_tools:
            return {
                "type": "text",
                "content": f"[Mock Agent Response]: Đã hoàn tất xử lý qua {len(done_tools)} bước công cụ ({', '.join(done_tools)}).",
                "thought": "Đã thu thập đủ Observation cần thiết, tổng hợp câu trả lời cuối cùng."
            }
        return {
            "type": "text",
            "content": "[Mock Agent Response]: Xin chào! Để quản lý công việc hiệu quả, bạn nên phân loại theo mức độ ưu tiên và đặt hạn hoàn thành rõ ràng cho từng đầu việc.",
            "thought": "Câu hỏi chung về quản lý công việc, trả lời trực tiếp không cần gọi Tool."
        }


class GeminiProvider(BaseLLMProvider):
    """Google Gemini Provider (Native Tool Calling với Google GenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gemini-2.5-flash"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            return "[Gemini Error]: Chưa cấu hình GEMINI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from google import genai
            client = genai.Client(api_key=self.api_key)
            contents = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt
            response = client.models.generate_content(model=self.model_name, contents=contents)
            return response.text
        except Exception as e:
            return f"[Gemini Exception]: {str(e)}"

    def generate_with_tools(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_gemini_api_key_here":
            print("ℹ️ [Gemini Provider]: Chưa tìm thấy GEMINI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(messages, tools_schema, system_prompt)

        try:
            from google import genai
            from google.genai import types

            client = genai.Client(api_key=self.api_key)

            # Chuẩn hóa function declarations cho Gemini SDK
            function_declarations = []
            for tool in tools_schema:
                # Bỏ qua các tool schema chưa được định nghĩa hoàn chỉnh
                if not tool.get("name") or not tool.get("parameters"):
                    continue
                function_declarations.append({
                    "name": tool["name"],
                    "description": tool.get("description", ""),
                    "parameters": tool.get("parameters", {})
                })

            config = types.GenerateContentConfig(
                system_instruction=system_prompt if system_prompt else None,
                tools=[{"function_declarations": function_declarations}] if function_declarations else None,
                temperature=0.2
            )

            # Chuyển đổi lịch sử hội thoại chung sang định dạng Content của Gemini
            contents = []
            for m in messages:
                if m["role"] == "user":
                    contents.append(types.Content(role="user", parts=[types.Part(text=m["content"])]))
                elif m["role"] == "assistant" and m.get("type") == "tool_call":
                    contents.append(types.Content(role="model", parts=[types.Part(
                        function_call=types.FunctionCall(name=m["tool_name"], args=m["arguments"])
                    )]))
                elif m["role"] == "tool":
                    try:
                        response_obj = json.loads(m["content"])
                    except Exception:
                        response_obj = {"result": m["content"]}
                    contents.append(types.Content(role="user", parts=[types.Part(
                        function_response=types.FunctionResponse(name=m["tool_name"], response=response_obj)
                    )]))

            response = client.models.generate_content(
                model=self.model_name,
                contents=contents,
                config=config
            )

            # Kiểm tra xem Gemini có trả về Tool Call không
            if response.function_calls:
                call = response.function_calls[0]
                args = dict(call.args) if hasattr(call, 'args') and call.args else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.name,
                    "arguments": args,
                    "tool_call_id": None,
                    "thought": f"Gemini quyết định gọi công cụ '{call.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": response.text or "",
                    "thought": "Gemini phản hồi trực tiếp bằng văn bản (không cần gọi thêm công cụ)."
                }

        except Exception as e:
            print(f"⚠️ [Gemini API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(messages, tools_schema, system_prompt)


class OpenAIProvider(BaseLLMProvider):
    """OpenAI Provider (Native Tool Calling với OpenAI SDK)"""
    def __init__(self, api_key: str = None, model: str = None):
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.model_name = model or os.getenv("LLM_MODEL") or "gpt-4o-mini"

    def generate(self, prompt: str, system_prompt: str = "") -> str:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            return "[OpenAI Error]: Chưa cấu hình OPENAI_API_KEY trong file .env! Đang sử dụng chế độ Mock."
        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)
            messages = []
            if system_prompt:
                messages.append({"role": "system", "content": system_prompt})
            messages.append({"role": "user", "content": prompt})
            response = client.chat.completions.create(model=self.model_name, messages=messages)
            return response.choices[0].message.content or ""
        except Exception as e:
            return f"[OpenAI Exception]: {str(e)}"

    def generate_with_tools(self, messages: List[Dict[str, Any]], tools_schema: List[Dict[str, Any]], system_prompt: str = "") -> Dict[str, Any]:
        if not self.api_key or self.api_key == "your_openai_api_key_here":
            print("ℹ️ [OpenAI Provider]: Chưa tìm thấy OPENAI_API_KEY hợp lệ. Tự động chuyển sang Mock Offline.")
            return MockOfflineProvider().generate_with_tools(messages, tools_schema, system_prompt)

        try:
            from openai import OpenAI
            client = OpenAI(api_key=self.api_key)

            tools = []
            for tool in tools_schema:
                if not tool.get("name"):
                    continue
                tools.append({
                    "type": "function",
                    "function": {
                        "name": tool["name"],
                        "description": tool.get("description", ""),
                        "parameters": tool.get("parameters", {})
                    }
                })

            native_messages = []
            if system_prompt:
                native_messages.append({"role": "system", "content": system_prompt})

            for m in messages:
                if m["role"] == "user":
                    native_messages.append({"role": "user", "content": m["content"]})
                elif m["role"] == "assistant" and m.get("type") == "tool_call":
                    native_messages.append({
                        "role": "assistant",
                        "content": None,
                        "tool_calls": [{
                            "id": m.get("tool_call_id"),
                            "type": "function",
                            "function": {
                                "name": m["tool_name"],
                                "arguments": json.dumps(m["arguments"], ensure_ascii=False)
                            }
                        }]
                    })
                elif m["role"] == "tool":
                    native_messages.append({
                        "role": "tool",
                        "tool_call_id": m.get("tool_call_id"),
                        "content": m["content"]
                    })

            response = client.chat.completions.create(
                model=self.model_name,
                messages=native_messages,
                tools=tools if tools else None,
                tool_choice="auto" if tools else None
            )

            msg = response.choices[0].message
            if msg.tool_calls:
                call = msg.tool_calls[0]
                args = json.loads(call.function.arguments) if call.function.arguments else {}
                return {
                    "type": "tool_call",
                    "tool_name": call.function.name,
                    "arguments": args,
                    "tool_call_id": call.id,
                    "thought": f"OpenAI quyết định gọi công cụ '{call.function.name}' với tham số: {json.dumps(args, ensure_ascii=False)}"
                }
            else:
                return {
                    "type": "text",
                    "content": msg.content or "",
                    "thought": "OpenAI phản hồi trực tiếp bằng văn bản (không cần gọi thêm công cụ)."
                }
        except Exception as e:
            print(f"⚠️ [OpenAI API Warning]: Không thể kết nối live API ({str(e)}). Tự động fallback về Mock.")
            return MockOfflineProvider().generate_with_tools(messages, tools_schema, system_prompt)


def get_llm_provider() -> BaseLLMProvider:
    """Factory function khởi tạo Provider theo LLM_PROVIDER env variable"""
    provider_type = os.getenv("LLM_PROVIDER", "gemini").lower()

    if provider_type == "gemini":
        key = os.getenv("GEMINI_API_KEY")
        if key and key != "your_gemini_api_key_here":
            return GeminiProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "openai":
        key = os.getenv("OPENAI_API_KEY")
        if key and key != "your_openai_api_key_here":
            return OpenAIProvider()
        else:
            return MockOfflineProvider()
    elif provider_type == "mock":
        return MockOfflineProvider()
    else:
        return MockOfflineProvider()
