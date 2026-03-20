"""
👁️ VISION LLM WRAPPER - Extract structured financial content from images using Groq vision models

Why this file exists
--------------------
Traditional OCR has limitations:
- struggles with image quality
- can't understand context
- no semantic understanding

Vision LLMs solve this by:
- understanding the image semantically
- extracting structured data directly
- handling messy screenshots
- providing confidence scores

This wrapper sends an image to a vision-capable Groq model and asks it to extract
structured financial content such as:
- document type
- merchant name
- transaction date
- amounts (subtotal, tax, total)
- line items
- confidence scores

Best use cases
--------------
- receipt photos from phones
- messy bank screenshots
- cropped banking app images
- OCR fallback when text quality is poor
- multi-document batch processing
"""

from __future__ import annotations
from pathlib import Path
from typing import Any, Dict, Optional, List, Union, Literal
import base64
import json
import mimetypes
import re
import time
import hashlib
from datetime import datetime
from dataclasses import dataclass, asdict
import copy

from groq import Groq
from config import Config


# =========================================================
# TYPES & MODELS
# =========================================================

DocumentType = Literal["receipt", "bank_statement", "screenshot", "unknown", "invoice", "check"]
ConfidenceLevel = Literal["high", "medium", "low"]


@dataclass
class ExtractedTransaction:
    """A single transaction extracted from an image"""
    date: Optional[str]
    description: str
    amount: Optional[str]
    merchant: Optional[str]
    confidence: ConfidenceLevel = "medium"
    
    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractionResult:
    """Complete extraction result from an image"""
    document_type: DocumentType
    extracted_text: str
    merchant: Optional[str]
    date: Optional[str]
    currency: Optional[str]
    totals: Dict[str, Optional[str]]
    possible_transactions: List[ExtractedTransaction]
    confidence: ConfidenceLevel
    notes: str
    processing_time_ms: Optional[float] = None
    model_used: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        result = asdict(self)
        result["possible_transactions"] = [t.to_dict() for t in self.possible_transactions]
        return result


# =========================================================
# VISION LLM WRAPPER
# =========================================================

class VisionLLMWrapper:
    """
    Wrapper around Groq vision-capable model for financial image extraction
    
    Features:
    - Multiple document type support (receipts, statements, screenshots)
    - Confidence scoring for each extracted field
    - Batch processing of multiple images
    - Image preprocessing suggestions
    - Cost tracking
    - Caching for identical images
    """
    
    # Available Groq vision models
    VISION_MODELS = {
        "llama-3.2-11b-vision-preview": {"context": 8192, "cost_per_mtok": 0.08},
        "llama-3.2-90b-vision-preview": {"context": 8192, "cost_per_mtok": 0.19},
    }
    
    def __init__(self, model: Optional[str] = None):
        """
        Initialize vision wrapper with specified model.
        
        Args:
            model: Groq vision model name (defaults to 11B model for speed/cost balance)
        """
        self.client = Groq(api_key=Config.GROQ_API_KEY)
        self.model = model or Config.VISION_MODEL
        self.call_count = 0
        self.total_tokens_used = 0
        self.cache = {}  # Simple in-memory cache for identical images
        
        if self.model not in self.VISION_MODELS:
            print(f"⚠️ Warning: No local metadata found for model '{self.model}'. Cost estimation may be unavailable.")
    # =========================================================
    # PUBLIC METHODS
    # =========================================================
    
    def extract_financial_document(
        self,
        image_input: Union[str, Path, bytes],
        *,
        task_type: str = "general_financial",
        custom_prompt: Optional[str] = None,
        use_cache: bool = True,
        return_raw: bool = False,
        temperature: float = 0.1,
        max_tokens: int = 1024,
    ) -> Dict[str, Any]:
        """
        Main entry point - extract structured financial data from an image.
        
        Args:
            image_input: File path, Path object, or raw bytes
            task_type: Type of document ('general_financial', 'receipt', 'bank_statement', 'screenshot_text')
            custom_prompt: Optional override / extra instructions
            use_cache: Whether to cache results for identical images
            return_raw: If True, returns raw model output instead of parsed result
            temperature: Model temperature (0.0-1.0, lower = more deterministic)
            max_tokens: Maximum tokens in response
            
        Returns:
            Dictionary with structure:
            {
                "success": bool,
                "data": ExtractionResult (as dict),
                "raw_response": Optional[str],
                "metadata": {...},
                "error": Optional[str]
            }
        """
        start_time = time.time()
        self.call_count += 1
        
        try:
            # Load and prepare image
            image_bytes = self._load_image_bytes(image_input)
            image_hash = hashlib.md5(image_bytes).hexdigest()
            
            # Check cache
            if use_cache and image_hash in self.cache:
                cached = copy.deepcopy(self.cache[image_hash])
                cached["metadata"]["from_cache"] = True
                return cached
            
            mime_type = self._guess_mime_type(image_input, image_bytes)
            image_b64 = self._encode_image_base64(image_bytes)
            
            # Build prompts
            system_prompt = self._build_system_prompt(task_type)
            user_prompt = self._build_user_prompt(task_type=task_type, custom_prompt=custom_prompt)
            
            # Call Groq vision model
            completion = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": system_prompt
                    },
                    {
                        "role": "user",
                        "content": [
                            {
                                "type": "text",
                                "text": user_prompt
                            },
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{mime_type};base64,{image_b64}"
                                }
                            }
                        ]
                    }
                ],
                temperature=temperature,
                max_completion_tokens=max_tokens,
                top_p=1,
                stream=False,
            )
            
            # Extract response
            raw_response = completion.choices[0].message.content if completion.choices else ""
            
            # Track token usage if available
            if getattr(completion, "usage", None) and getattr(completion.usage, "total_tokens", None) is not None:
                self.total_tokens_used += completion.usage.total_tokens
            
            # If returning raw response only
            if return_raw:
                return {
                    "success": True,
                    "data": None,
                    "raw_response": raw_response,
                    "metadata": self._build_metadata(start_time, mime_type, task_type),
                    "error": None
                }
            
            # Parse JSON response
            parsed = self._try_parse_json(raw_response)
            
            if parsed is None:
                return {
                    "success": False,
                    "data": None,
                    "raw_response": raw_response,
                    "metadata": self._build_metadata(start_time, mime_type, task_type),
                    "error": "Failed to parse JSON response from model"
                }
            
            # Validate and normalize
            validated = self._validate_extraction_output(parsed)
            
            # Convert to ExtractionResult dataclass
            result = self._dict_to_extraction_result(validated)
            result.processing_time_ms = round((time.time() - start_time) * 1000, 2)
            result.model_used = self.model
            
            # Build final response
            response = {
                "success": True,
                "data": result.to_dict(),
                "raw_response": raw_response,
                "metadata": self._build_metadata(start_time, mime_type, task_type),
                "error": None
            }
            
            # Cache if requested
            if use_cache:
                self.cache[image_hash] = response
            
            return response
            
        except Exception as e:
            return {
                "success": False,
                "data": None,
                "raw_response": "",
                "metadata": self._build_metadata(start_time, "unknown", task_type),
                "error": str(e)
            }
    
    def extract_multiple_documents(
        self,
        image_inputs: List[Union[str, Path, bytes]],
        *,
        task_type: str = "general_financial",
        parallel: bool = False,
        **kwargs
    ) -> List[Dict[str, Any]]:
        """
        Extract data from multiple images.
        
        Args:
            image_inputs: List of images to process
            task_type: Type of document
            parallel: Whether to process in parallel (requires threading)
            **kwargs: Additional args passed to extract_financial_document
        
        Returns:
            List of results in same order as inputs
        """
        results = []
        
        if parallel and len(image_inputs) > 1:
            # Parallel processing with threads
            import threading
            import queue
            
            result_queue = queue.Queue()
            
            def process_image(img_input, index):
                result = self.extract_financial_document(img_input, task_type=task_type, **kwargs)
                result_queue.put((index, result))
            
            threads = []
            for i, img_input in enumerate(image_inputs):
                thread = threading.Thread(target=process_image, args=(img_input, i))
                thread.start()
                threads.append(thread)
            
            for thread in threads:
                thread.join()
            
            # Collect results in original order
            results = [None] * len(image_inputs)
            while not result_queue.empty():
                index, result = result_queue.get()
                results[index] = result
        
        else:
            # Sequential processing
            for img_input in image_inputs:
                result = self.extract_financial_document(img_input, task_type=task_type, **kwargs)
                results.append(result)
        
        return results
    
    def extract_receipt(self, image_input: Union[str, Path, bytes], **kwargs) -> Dict[str, Any]:
        """Convenience method for receipt extraction"""
        return self.extract_financial_document(image_input, task_type="receipt", **kwargs)
    
    def extract_bank_statement(self, image_input: Union[str, Path, bytes], **kwargs) -> Dict[str, Any]:
        return self.extract_financial_document(image_input, task_type="bank_statement", **kwargs)
    
    def extract_screenshot_text(self, image_input: Union[str, Path, bytes], **kwargs) -> Dict[str, Any]:
        """Convenience method for screenshot text extraction"""
        return self.extract_financial_document(image_input, task_type="screenshot_text", **kwargs)
    
    # =========================================================
    # STATISTICS & METRICS
    # =========================================================
    
    def get_stats(self) -> Dict[str, Any]:
        """Get usage statistics"""
        return {
            "model": self.model,
            "call_count": self.call_count,
            "total_tokens_used": self.total_tokens_used,
            "estimated_cost": self._estimate_cost(),
            "cache_size": len(self.cache),
            "available_models": list(self.VISION_MODELS.keys())
        }
    
    def clear_cache(self):
        """Clear the in-memory cache"""
        self.cache.clear()
        print("✅ Cache cleared")
    
    # =========================================================
    # IMAGE HELPERS
    # =========================================================
    
    def _load_image_bytes(self, image_input: Union[str, Path, bytes]) -> bytes:
        """Load image bytes from path or accept raw bytes directly"""
        if isinstance(image_input, bytes):
            return image_input
        
        path = Path(image_input)
        if not path.exists():
            raise FileNotFoundError(f"Image not found: {path}")
        if not path.is_file():
            raise ValueError(f"Path is not a file: {path}")
        
        return path.read_bytes()
    
    def _guess_mime_type(self, image_input: Union[str, Path, bytes], image_bytes: bytes) -> str:
        """Guess mime type for the uploaded image. Default to image/png if unknown."""
        if isinstance(image_input, (str, Path)):
            mime_type, _ = mimetypes.guess_type(str(image_input))
            if mime_type and mime_type.startswith("image/"):
                return mime_type
        
        # Try to detect from magic bytes
        if image_bytes.startswith(b'\xff\xd8'):
            return "image/jpeg"
        if image_bytes.startswith(b'\x89PNG\r\n\x1a\n'):
            return "image/png"
        if image_bytes.startswith(b'GIF87a') or image_bytes.startswith(b'GIF89a'):
            return "image/gif"
        if image_bytes.startswith(b'RIFF') and image_bytes[8:12] == b'WEBP':
            return "image/webp"
        
        return "image/png"
    
    def _encode_image_base64(self, image_bytes: bytes) -> str:
        """Convert image bytes to base64 string"""
        return base64.b64encode(image_bytes).decode("utf-8")
    
    def _build_metadata(self, start_time: float, mime_type: str, task_type: str) -> Dict[str, Any]:
        """Build metadata dictionary"""
        return {
            "model": self.model,
            "call_count": self.call_count,
            "total_tokens": self.total_tokens_used,
            "duration_seconds": round(time.time() - start_time, 3),
            "mime_type": mime_type,
            "task_type": task_type,
            "timestamp": datetime.now().isoformat(),
        }
    
    def _estimate_cost(self) -> float:
        """Estimate cost based on token usage"""
        if self.model in self.VISION_MODELS:
            cost_per_mtok = self.VISION_MODELS[self.model]["cost_per_mtok"]
            return (self.total_tokens_used / 1_000_000) * cost_per_mtok
        return 0.0
    
    # =========================================================
    # PROMPTS
    # =========================================================
    
    def _build_system_prompt(self, task_type: str) -> str:
        """System prompt for financial document extraction"""
        base_prompt = """You are a financial document extraction assistant specialized in extracting structured data from images of financial documents.

Your task:
- Read the image carefully
- Extract only what is actually visible
- Do NOT invent missing information
- Return ONLY valid JSON
- If a value is unclear or missing, use null
- If confidence is uncertain, set confidence to "low"

CRITICAL RULES:
- Do NOT add explanations outside the JSON
- Do NOT wrap JSON in markdown code blocks
- Do NOT add any commentary
- Return pure, parseable JSON only

Return ONLY the JSON object with no leading or trailing commentary:

{
  "document_type": "receipt | bank_statement | screenshot | invoice | check | unknown",
  "extracted_text": "full readable text visible in the image",
  "merchant": "string or null",
  "date": "string (YYYY-MM-DD preferred) or null",
  "currency": "string (USD, EUR, etc.) or null",
  "totals": {
    "subtotal": "string or null",
    "tax": "string or null",
    "total": "string or null"
  },
  "possible_transactions": [
    {
      "date": "string or null",
      "description": "string",
      "amount": "string or null",
      "merchant": "string or null",
      "confidence": "high | medium | low"
    }
  ],
  "confidence": "high | medium | low",
  "notes": "short explanation of any ambiguity or extraction challenges"
}

For receipt images:
- Extract line items as possible_transactions
- Each line item becomes a transaction with description and amount

For bank statements:
- Extract each transaction row as a separate possible_transaction
- Include date, description, amount

For screenshots:
- Extract all visible financial text
- Group logically into possible_transactions if multiple items visible
"""
        
        # Task-specific additions
        task_additions = {
            "receipt": "\n\nThis is a RECEIPT image. Focus on extracting merchant, date, line items, subtotal, tax, and total.",
            "bank_statement": "\n\nThis is a BANK STATEMENT screenshot. Focus on extracting account information and transaction rows.",
            "screenshot_text": "\n\nThis is a SCREENSHOT. Extract all visible financial text and structure it logically.",
            "general_financial": "",
        }
        
        return base_prompt + task_additions.get(task_type, "")
    
    def _build_user_prompt(self, *, task_type: str, custom_prompt: Optional[str] = None) -> str:
        """Build task-specific user prompt"""
        task_map = {
            "general_financial": (
                "This image may contain financial information. Extract all readable text and structure it according to the JSON schema."
            ),
            "receipt": (
                "This is a receipt image. Extract:\n"
                "- Merchant name\n"
                "- Date (prefer YYYY-MM-DD format)\n"
                "- Currency\n"
                "- Subtotal, tax, and total\n"
                "- Each line item as a separate transaction in possible_transactions\n"
                "If any field is unclear or missing, use null."
            ),
            "bank_statement": (
                "This is a bank statement or account screenshot. Extract:\n"
                "- Account information if visible\n"
                "- Each transaction row as a separate entry in possible_transactions\n"
                "For each transaction, include date, description, and amount.\n"
                "If amounts are negative (withdrawals), include the minus sign."
            ),
            "screenshot_text": (
                "This is a screenshot of financial information. Extract:\n"
                "- All visible text\n"
                "- Structure any apparent transactions into possible_transactions\n"
                "- If multiple logical sections exist, note them in extracted_text"
            ),
        }

        base_prompt = task_map.get(task_type, task_map['general_financial'])
        
        if custom_prompt:
            base_prompt += f"\n\nAdditional instructions:\n{custom_prompt}"
        
        return base_prompt
    
    # =========================================================
    # RESPONSE PARSING
    # =========================================================
    
    def _strip_code_fences(self, text: str) -> str:
        """Remove markdown code fences if model returns them"""
        if not text:
            return ""
        text = text.strip()
        # Remove ```json ... ``` or ``` ... ```
        text = re.sub(r"^```(?:json)?\s*", "", text)
        text = re.sub(r"\s*```$", "", text)
        return text.strip()
    
    def _try_parse_json(self, text: str) -> Optional[Dict[str, Any]]:
        """Safely parse JSON from model output."""
        if not text:
            return None

        text = self._strip_code_fences(text)

        # Direct parse
        try:
            parsed = json.loads(text)
            if isinstance(parsed, dict):
                return parsed
        except Exception:
            pass

        # Fallback: extract first {...} block
        match = re.search(r"\{.*\}", text, flags=re.DOTALL)
        if match:
            try:
                parsed = json.loads(match.group(0))
                if isinstance(parsed, dict):
                    return parsed
            except Exception:
                pass

        return None
    
    def _validate_extraction_output(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize the model output into a stable shape."""
        defaults = {
            "document_type": "unknown",
            "extracted_text": "",
            "merchant": None,
            "date": None,
            "currency": None,
            "totals": {
                "subtotal": None,
                "tax": None,
                "total": None,
            },
            "possible_transactions": [],
            "confidence": "low",
            "notes": "",
        }

        # Fill missing top-level keys
        for key, default_value in defaults.items():
            if key not in data:
                data[key] = default_value

        # Normalize enums
        valid_doc_types = {"receipt", "bank_statement", "screenshot", "invoice", "check", "unknown"}
        if data.get("document_type") not in valid_doc_types:
            data["document_type"] = "unknown"

        valid_conf = {"high", "medium", "low"}
        if data.get("confidence") not in valid_conf:
            data["confidence"] = "low"

        # Normalize text-like fields
        for field in ["extracted_text", "merchant", "date", "currency", "notes"]:
            value = data.get(field)
            if value is None:
                continue
            if not isinstance(value, str):
                data[field] = str(value)
            else:
                data[field] = value.strip()

        # Normalize totals
        totals = data.get("totals")
        if not isinstance(totals, dict):
            totals = defaults["totals"].copy()
        for key in ["subtotal", "tax", "total"]:
            if key not in totals:
                totals[key] = None
            elif totals[key] is not None and not isinstance(totals[key], str):
                totals[key] = str(totals[key])
        data["totals"] = totals

        # Normalize possible_transactions
        txns = data.get("possible_transactions")
        if not isinstance(txns, list):
            txns = []

        normalized_txns = []
        for item in txns:
            if not isinstance(item, dict):
                continue
            
            # Get confidence for this transaction
            txn_conf = item.get("confidence", "medium")
            if txn_conf not in valid_conf:
                txn_conf = "medium"
            
            normalized_txns.append({
                "date": str(item.get("date")).strip() if item.get("date") is not None else None,
                "description": str(item.get("description", "")).strip(),
                "amount": str(item.get("amount")).strip() if item.get("amount") is not None else None,
                "merchant": str(item.get("merchant")).strip() if item.get("merchant") is not None else None,
                "confidence": txn_conf,
            })
        data["possible_transactions"] = normalized_txns

        return data
    
    def _dict_to_extraction_result(self, data: Dict[str, Any]) -> ExtractionResult:
        """Convert validated dict to ExtractionResult dataclass"""
        transactions = [
            ExtractedTransaction(
                date=t.get("date"),
                description=t.get("description", ""),
                amount=t.get("amount"),
                merchant=t.get("merchant"),
                confidence=t.get("confidence", "medium")
            )
            for t in data.get("possible_transactions", [])
        ]
        
        return ExtractionResult(
            document_type=data.get("document_type", "unknown"),
            extracted_text=data.get("extracted_text", ""),
            merchant=data.get("merchant"),
            date=data.get("date"),
            currency=data.get("currency"),
            totals=data.get("totals", {}),
            possible_transactions=transactions,
            confidence=data.get("confidence", "low"),
            notes=data.get("notes", ""),
        )


# =========================================================
# FACTORY FUNCTIONS
# =========================================================

def create_vision_wrapper(model: Optional[str] =None) -> VisionLLMWrapper:
    """Create a vision wrapper instance with specified model"""
    model = model or Config.VISION_MODEL
    return VisionLLMWrapper(model=model)


# =========================================================
# EXAMPLE USAGE
# =========================================================

if __name__ == "__main__":
    """
    Example:
        python -m utils.vision_llm_wrapper
    """
    print("=" * 70)
    print("👁️ VISION LLM WRAPPER TEST")
    print("=" * 70)
    
    wrapper = create_vision_wrapper()
    
    # Test with a sample image if available
    sample_path = Path("sample_receipt.jpg")
    if sample_path.exists():
        print(f"\n📄 Testing receipt extraction with: {sample_path}")
        
        result = wrapper.extract_receipt(sample_path)
        
        print(f"\n✅ Success: {result['success']}")
        if result['success']:
            data = result['data']
            print(f"   Document Type: {data['document_type']}")
            print(f"   Merchant: {data['merchant']}")
            print(f"   Date: {data['date']}")
            print(f"   Total: {data['totals']['total']}")
            print(f"   Confidence: {data['confidence']}")
            print(f"   Transactions: {len(data['possible_transactions'])}")
        else:
            print(f"❌ Error: {result['error']}")
    else:
        print(f"\n⚠️  Sample file not found: {sample_path}")
    
    # Print stats
    print(f"\n📊 Stats: {wrapper.get_stats()}")