from typing import Any, Dict, List, Optional
from datetime import datetime
import json
import re

import tiktoken
from langchain_groq import ChatGroq
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage

from config import Config

class LLMWrapper:
    """
    Wrapper around Groq LLM for consistent usage across the app,
    including token counting + simple call stats.
    """

    def __init__(self):
        self.llm = ChatGroq(**Config.get_llm_kwargs())
        self.encoder = tiktoken.get_encoding("cl100k_base")
        self.total_tokens_used = 0
        self.call_count = 0

    # ----------------------------
    # Token helpers
    # ----------------------------
    def count_text_tokens(self, text: Optional[str]) -> int:
        """Count tokens in text, handling None values"""
        if not text:
            return 0
        return len(self.encoder.encode(text))

    def count_message_tokens(self, msg: BaseMessage) -> int:
        """Count tokens in a message, including metadata"""
        tokens = self.count_text_tokens(getattr(msg, "content", None))

        # Optional fields (not always present)
        name = getattr(msg, "name", None)
        if name:
            tokens += self.count_text_tokens(name)

        # FIXED: Added role check with proper attribute access
        role = getattr(msg, "type", None) or getattr(msg, "role", None)
        if role:
            tokens += self.count_text_tokens(role)

        # Additional kwargs may contain small things (usually negligible)
        # Not counting them unless you explicitly want to.
        return tokens

    def count_messages_tokens(self, messages: List[BaseMessage]) -> int:
        """Count tokens in a list of messages"""
        return sum(self.count_message_tokens(m) for m in messages)

    # ----------------------------
    # LLM invoke with tracking
    # ----------------------------
    def invoke_with_token_tracing(self, messages: List[BaseMessage], **kwargs) -> AIMessage:
        """Invoke LLM and track token usage and performance metrics"""
        self.call_count += 1

        input_tokens = self.count_messages_tokens(messages)

        start_time = datetime.now()
        response: AIMessage = self.llm.invoke(messages, **kwargs)
        duration = (datetime.now() - start_time).total_seconds()

        output_tokens = self.count_text_tokens(response.content)

        # Update totals ONCE
        self.total_tokens_used += (input_tokens + output_tokens)

        # FIXED: Safer metadata handling
        if not hasattr(response, "metadata") or response.metadata is None:
            response.metadata = {}
        
        # FIXED: Use dictionary update properly
        response.metadata.update({
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens_used": self.total_tokens_used,
            "duration_seconds": duration,
            "call_count": self.call_count,
            "model": getattr(self.llm, "model_name", None),
            "timestamp": datetime.now().isoformat()
        })

        return response

    # ----------------------------
    # Structured response helper
    # ----------------------------
    def _strip_code_fences(self, text: str) -> str:
        """Remove markdown code fences from text"""
        if not text:
            return ""
        text = text.strip()
        # Remove ```json ... ``` or ``` ... ```
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()

    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Attempt to parse JSON from text, handling various formats"""
        if not text:
            return None
            
        text = self._strip_code_fences(text)

        # Try direct JSON
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
            return {"value": parsed}
        except Exception:
            pass

        # Try to extract the first {...} block if LLM added extra text
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
                return {"value": parsed}
            except Exception:
                return None

        return None

    # FIXED: Consistent return structure
    def generate_structured_response(
        self,
        system_prompt: str,
        user_prompt: str,
        response_format: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Generate a structured response from the LLM.
        
        Returns:
            Dictionary with consistent structure:
            - "success": bool - Whether parsing succeeded
            - "data": Optional[Dict] - Parsed JSON data if success
            - "raw_response": str - Raw response text
            - "metadata": Dict - Token usage and performance metrics
            - "error": Optional[str] - Error message if failed
        """
        messages: List[BaseMessage] = [
            SystemMessage(content=system_prompt),
            HumanMessage(content=user_prompt),
        ]

        if response_format:
            # NOTE: better to embed format instructions in system_prompt,
            # but this is okay for now.
            messages.append(SystemMessage(content=f"Respond ONLY in this format:\n{response_format}"))

        response = self.invoke_with_token_tracing(messages)
        raw_content = response.content.strip()

        parsed = self._try_parse_json(raw_content)
        
        # FIXED: Consistent return structure
        result = {
            "success": parsed is not None,
            "raw_response": raw_content,
            "metadata": response.metadata,
            "error": None if parsed is not None else "Failed to parse JSON response"
        }
        
        if parsed is not None:
            result["data"] = parsed
        else:
            result["data"] = {"text": raw_content}  # Fallback with text

        return result

    # ----------------------------
    # Stats
    # ----------------------------
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "total_tokens_used": self.total_tokens_used,
            "calls_made": self.call_count,
            "estimated_cost_usd": self.total_tokens_used * 0.00000015 if self.total_tokens_used else 0,  # Rough estimate for Groq
            "average_tokens_per_call": self.total_tokens_used / self.call_count if self.call_count else 0
        }


# Singleton instance
llm_wrapper = LLMWrapper()
