

# """
# 📤 UPLOADERS - Streamlit upload interface for images and PDFs

# Purpose
# -------
# This file handles file upload UI for the Financial Advisor app.

# It does:
# - render image / PDF upload widgets
# - preview uploaded files
# - process image uploads using vision_llm_wrapper
# - return structured upload + extraction results

# It does NOT:
# - call runner
# - call graph
# - do business logic
# - permanently store files
# """

# from __future__ import annotations
# import sys
# from pathlib import Path
# sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# from dataclasses import dataclass, asdict
# from typing import Optional, List, Dict, Any
# import tempfile
# import mimetypes

# import streamlit as st

# from utils.vision_llm_wrapper import create_vision_wrapper
# from utils.vision_transaction_bridge import vision_result_to_transactions
# from utils.pdf_parser import (
#     extract_text_from_pdf_bytes,
#     parse_bank_text_to_transactions,
# )

# # =========================================================
# # DATA MODELS
# # =========================================================

# @dataclass
# class UploadedFileResult:
#     """
#     Structured result for one uploaded file.
#     """
#     filename: str
#     file_type: str
#     mime_type: str
#     size_bytes: int
#     success: bool
#     extracted: bool
#     extraction_mode: str
#     preview_available: bool
#     vision_result: Optional[Dict[str, Any]] = None
#     error: Optional[str] = None

#     def to_dict(self) -> Dict[str, Any]:
#         return asdict(self)


# @dataclass
# class UploadBatchResult:
#     """
#     Structured result for a batch of uploaded files.
#     """
#     files: List[UploadedFileResult]
#     total_files: int
#     success_count: int
#     extracted_count: int
#     image_count: int
#     pdf_count: int
#     errors: List[str]

#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             "files": [f.to_dict() for f in self.files],
#             "total_files": self.total_files,
#             "success_count": self.success_count,
#             "extracted_count": self.extracted_count,
#             "image_count": self.image_count,
#             "pdf_count": self.pdf_count,
#             "errors": self.errors,
#         }


# # =========================================================
# # STYLES - FIXED FOR DARK MODE READABILITY
# # =========================================================

# def load_uploader_styles():
#     st.markdown(
#         """
#         <style>
#         .uploader-hero {
#             border-radius: 24px;
#             padding: 1.8rem 1.5rem;
#             margin-bottom: 1.2rem;
#             background: linear-gradient(135deg, #4361EE 0%, #7209B7 100%);
#             color: white;
#             box-shadow: 0 18px 40px rgba(67, 97, 238, 0.22);
#         }

#         .uploader-hero h2, .uploader-hero p {
#             color: white !important;
#             margin: 0;
#         }

#         .upload-card {
#             border-radius: 18px;
#             padding: 1.25rem 1.25rem;
#             margin-bottom: 1rem;
#             background: #262730 !important;
#             border: 1px solid #404040;
#             box-shadow: 0 6px 18px rgba(0,0,0,0.2);
#         }
        
#         .upload-card strong {
#             color: #FFFFFF !important;
#             font-size: 1.1rem;
#         }
        
#         .upload-card div, .upload-card span, .upload-card p {
#             color: #E0E0E0 !important;
#         }

#         .upload-soft {
#             border-radius: 16px;
#             padding: 0.9rem 1rem;
#             margin-bottom: 0.75rem;
#             background: #262730 !important;
#             border: 1px solid #404040;
#         }
        
#         .upload-soft strong {
#             color: #4361EE !important;
#         }
        
#         .upload-soft span, .upload-soft div {
#             color: #E0E0E0 !important;
#         }

#         .upload-pill {
#             display: inline-block;
#             padding: 0.25rem 0.75rem;
#             border-radius: 999px;
#             background: #333333 !important;
#             color: #FFFFFF !important;
#             font-size: 0.85rem;
#             font-weight: 600;
#             margin-right: 0.4rem;
#             margin-top: 0.2rem;
#         }

#         .upload-success {
#             border-radius: 14px;
#             padding: 0.85rem 1rem;
#             background: #1E3A2E !important;
#             border: 1px solid #06D6A0;
#             color: #06D6A0 !important;
#             font-weight: 500;
#         }

#         .upload-warning {
#             border-radius: 14px;
#             padding: 0.85rem 1rem;
#             background: #3A2E1E !important;
#             border: 1px solid #FF9F1C;
#             color: #FF9F1C !important;
#             font-weight: 500;
#         }

#         .upload-error {
#             border-radius: 14px;
#             padding: 0.85rem 1rem;
#             background: #3A1E1E !important;
#             border: 1px solid #EF233C;
#             color: #EF233C !important;
#             font-weight: 500;
#         }
        
#         /* Metric text colors */
#         [data-testid="stMetricValue"] {
#             color: #FFFFFF !important;
#             font-size: 1.8rem !important;
#         }
        
#         [data-testid="stMetricLabel"] {
#             color: #E0E0E0 !important;
#             font-size: 1rem !important;
#         }
        
#         /* Expander */
#         .streamlit-expanderHeader {
#             color: #FFFFFF !important;
#             background-color: #262730 !important;
#             border: 1px solid #404040 !important;
#         }
        
#         .streamlit-expanderContent {
#             background-color: #262730 !important;
#             border: 1px solid #404040 !important;
#             border-top: none !important;
#             color: #E0E0E0 !important;
#         }
        
#         /* Markdown text */
#         .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div {
#             color: #E0E0E0 !important;
#         }
        
#         /* Headers */
#         h1, h2, h3, h4, h5, h6 {
#             color: #FFFFFF !important;
#         }
        
#         /* File uploader text */
#         .stFileUploader label, .stFileUploader span {
#             color: #FFFFFF !important;
#         }
        
#         /* Button */
#         .stButton button {
#             background: linear-gradient(135deg, #4361EE 0%, #7209B7 100%) !important;
#             color: white !important;
#             font-size: 1.1rem !important;
#             font-weight: 600 !important;
#             border: none !important;
#         }
        
#         /* Metrics */
#         [data-testid="stMetric"] {
#             background: #262730 !important;
#             border: 1px solid #404040 !important;
#             border-radius: 12px !important;
#             padding: 1rem !important;
#         }
        
#         /* Info boxes */
#         .stAlert {
#             background: #262730 !important;
#             color: #E0E0E0 !important;
#             border: 1px solid #404040 !important;
#         }
#         </style>
#         """,
#         unsafe_allow_html=True,
#     )


# # =========================================================
# # HELPERS
# # =========================================================

# def _render_uploader_hero():
#     st.markdown(
#         """
#         <div class="uploader-hero">
#             <h2>📤 Upload Receipts, Screenshots, or Statements</h2>
#             <p style="margin-top:0.45rem; opacity:0.94;">
#                 Upload financial images for AI extraction. PDFs are accepted too, with graceful fallback behavior.
#             </p>
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )


# def _guess_file_type(filename: str, mime_type: str) -> str:
#     lower_name = filename.lower()

#     if mime_type.startswith("image/"):
#         return "image"
#     if mime_type == "application/pdf" or lower_name.endswith(".pdf"):
#         return "pdf"
#     return "unknown"


# def _pretty_size(size_bytes: int) -> str:
#     if size_bytes < 1024:
#         return f"{size_bytes} B"
#     if size_bytes < 1024 * 1024:
#         return f"{size_bytes / 1024:.1f} KB"
#     return f"{size_bytes / (1024 * 1024):.2f} MB"


# def _save_uploaded_file_to_temp(uploaded_file) -> Path:
#     suffix = Path(uploaded_file.name).suffix or ".bin"
#     with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
#         tmp.write(uploaded_file.getbuffer())
#         return Path(tmp.name)


# def _render_file_badges(file_type: str, mime_type: str, size_bytes: int):
#     st.markdown(
#         f"""
#         <span class="upload-pill">{file_type.upper()}</span>
#         <span class="upload-pill">{mime_type}</span>
#         <span class="upload-pill">{_pretty_size(size_bytes)}</span>
#         """,
#         unsafe_allow_html=True,
#     )


# def _render_vision_result(result: Dict[str, Any]):
#     if not result.get("success", False):
#         st.markdown(
#             f'<div class="upload-error">❌ Extraction failed: {result.get("error", "Unknown error")}</div>',
#             unsafe_allow_html=True,
#         )
#         return

#     data = result.get("data", {}) or {}
#     metadata = result.get("metadata", {}) or {}

#     col1, col2, col3 = st.columns(3)
#     with col1:
#         st.metric("Document Type", str(data.get("document_type", "unknown")).replace("_", " ").title())
#     with col2:
#         st.metric("Confidence", str(data.get("confidence", "unknown")).title())
#     with col3:
#         st.metric("Transactions Found", len(data.get("possible_transactions", []) or []))

#     st.markdown(
#         f"""
#         <div class="upload-soft">
#             <strong>Model:</strong> {metadata.get("model", "unknown")}<br/>
#             <strong>Merchant:</strong> {data.get("merchant") or "N/A"}<br/>
#             <strong>Date:</strong> {data.get("date") or "N/A"}<br/>
#             <strong>Currency:</strong> {data.get("currency") or "N/A"}
#         </div>
#         """,
#         unsafe_allow_html=True,
#     )

#     totals = data.get("totals", {}) or {}
#     if any(v for v in totals.values()):
#         st.markdown("#### 💰 Totals")
#         t1, t2, t3 = st.columns(3)
#         with t1:
#             st.metric("Subtotal", totals.get("subtotal") or "—")
#         with t2:
#             st.metric("Tax", totals.get("tax") or "—")
#         with t3:
#             st.metric("Total", totals.get("total") or "—")

#     transactions = data.get("possible_transactions", []) or []
#     if transactions:
#         st.markdown("#### 🧾 Extracted Transactions / Items")
#         for i, txn in enumerate(transactions[:10], start=1):
#             confidence_color = "#06D6A0" if txn.get('confidence') == 'high' else "#FF9F1C" if txn.get('confidence') == 'medium' else "#EF233C"
#             st.markdown(
#                 f"""
#                 <div class="upload-card">
#                     <div style="margin-bottom: 0.5rem;">
#                         <span style="font-size: 1.1rem; font-weight: 600; color: #FFFFFF !important;">
#                             {i}. {txn.get("description", "")}
#                         </span>
#                     </div>
#                     <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
#                         <div><span style="font-weight: 500; color: #E0E0E0;">Date:</span> <span style="color: #FFFFFF;">{txn.get("date") or "N/A"}</span></div>
#                         <div><span style="font-weight: 500; color: #E0E0E0;">Merchant:</span> <span style="color: #FFFFFF;">{txn.get("merchant") or "N/A"}</span></div>
#                         <div><span style="font-weight: 500; color: #E0E0E0;">Amount:</span> <span style="color: {confidence_color}; font-weight: 600;">{txn.get("amount") or "N/A"}</span></div>
#                         <div><span style="font-weight: 500; color: #E0E0E0;">Confidence:</span> <span style="color: {confidence_color}; font-weight: 600;">{txn.get("confidence") or "N/A"}</span></div>
#                     </div>
#                 </div>
#                 """,
#                 unsafe_allow_html=True,
#             )

#     extracted_text = data.get("extracted_text", "")
#     if extracted_text:
#         with st.expander("📝 Extracted Text Preview"):
#             st.text(extracted_text[:3000])

#     notes = data.get("notes")
#     if notes:
#         st.info(notes)


# # =========================================================
# # CORE EXTRACTION LOGIC
# # =========================================================

# def process_uploaded_file_with_vision(
#     uploaded_file,
#     *,
#     task_type: str = "general_financial",
#     model: Optional[str] = None,
# ) -> UploadedFileResult:
#     """
#     Process a single uploaded file.
#     - images -> vision extraction
#     - pdfs -> accepted, but not deeply parsed here
#     """
#     filename = uploaded_file.name
#     mime_type = uploaded_file.type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
#     size_bytes = len(uploaded_file.getvalue())
#     file_type = _guess_file_type(filename, mime_type)

#     try:
#         if file_type == "image":
#             wrapper = create_vision_wrapper(model=model) if model else create_vision_wrapper()
#             image_bytes = uploaded_file.getvalue()

#             # Heuristic task routing from filename / mime
#             lower_name = filename.lower()
#             if "receipt" in lower_name:
#                 vision_result = wrapper.extract_receipt(image_bytes)
#             elif "statement" in lower_name or "bank" in lower_name:
#                 vision_result = wrapper.extract_bank_statement(image_bytes)
#             elif "screen" in lower_name or "screenshot" in lower_name:
#                 vision_result = wrapper.extract_screenshot_text(image_bytes)
#             else:
#                 vision_result = wrapper.extract_financial_document(
#                     image_bytes,
#                     task_type=task_type,
#                 )

#             return UploadedFileResult(
#                 filename=filename,
#                 file_type=file_type,
#                 mime_type=mime_type,
#                 size_bytes=size_bytes,
#                 success=bool(vision_result.get("success", False)),
#                 extracted=True,
#                 extraction_mode="vision_llm",
#                 preview_available=True,
#                 vision_result=vision_result,
#                 error=vision_result.get("error"),
#             )

#         if file_type == "pdf":
#             return UploadedFileResult(
#                 filename=filename,
#                 file_type=file_type,
#                 mime_type=mime_type,
#                 size_bytes=size_bytes,
#                 success=True,
#                 extracted=False,
#                 extraction_mode="pdf_upload_only",
#                 preview_available=False,
#                 vision_result=None,
#                 error=None,
#             )

#         return UploadedFileResult(
#             filename=filename,
#             file_type=file_type,
#             mime_type=mime_type,
#             size_bytes=size_bytes,
#             success=False,
#             extracted=False,
#             extraction_mode="unsupported",
#             preview_available=False,
#             vision_result=None,
#             error=f"Unsupported file type: {mime_type}",
#         )

#     except Exception as e:
#         return UploadedFileResult(
#             filename=filename,
#             file_type=file_type,
#             mime_type=mime_type,
#             size_bytes=size_bytes,
#             success=False,
#             extracted=False,
#             extraction_mode="error",
#             preview_available=False,
#             vision_result=None,
#             error=str(e),
#         )


# def process_uploaded_files(
#     uploaded_files: List[Any],
#     *,
#     task_type: str = "general_financial",
#     model: Optional[str] = None,
# ) -> UploadBatchResult:
#     """
#     Process a batch of uploaded files.
#     """
#     results: List[UploadedFileResult] = []
#     errors: List[str] = []

#     for uploaded_file in uploaded_files:
#         result = process_uploaded_file_with_vision(
#             uploaded_file,
#             task_type=task_type,
#             model=model,
#         )
#         results.append(result)
#         if result.error:
#             errors.append(f"{result.filename}: {result.error}")

#     image_count = sum(1 for r in results if r.file_type == "image")
#     pdf_count = sum(1 for r in results if r.file_type == "pdf")
#     success_count = sum(1 for r in results if r.success)
#     extracted_count = sum(1 for r in results if r.extracted and r.success)

#     return UploadBatchResult(
#         files=results,
#         total_files=len(results),
#         success_count=success_count,
#         extracted_count=extracted_count,
#         image_count=image_count,
#         pdf_count=pdf_count,
#         errors=errors,
#     )


# # =========================================================
# # UI RENDERERS
# # =========================================================

# def render_single_file_upload(
#     *,
#     label: str = "Upload a receipt, screenshot, or PDF",
#     accepted_types: Optional[List[str]] = None,
# ) -> Optional[Any]:
#     """
#     Render a single file uploader and return the uploaded file.
#     """
#     load_uploader_styles()
#     _render_uploader_hero()

#     if accepted_types is None:
#         accepted_types = ["png", "jpg", "jpeg", "webp", "pdf"]

#     uploaded_file = st.file_uploader(
#         label,
#         type=accepted_types,
#         accept_multiple_files=False,
#         help="Images can be extracted with vision AI. PDFs are accepted and can be connected to parsing later.",
#     )

#     return uploaded_file


# def render_multi_file_upload(
#     *,
#     label: str = "Upload one or more receipts, screenshots, or PDFs",
#     accepted_types: Optional[List[str]] = None,
# ) -> List[Any]:
#     """
#     Render a multi-file uploader and return uploaded files.
#     """
#     load_uploader_styles()
#     _render_uploader_hero()

#     if accepted_types is None:
#         accepted_types = ["png", "jpg", "jpeg", "webp", "pdf"]

#     uploaded_files = st.file_uploader(
#         label,
#         type=accepted_types,
#         accept_multiple_files=True,
#         help="Images are AI-extracted. PDFs are accepted and previewed for future handling.",
#     )

#     return uploaded_files or []


# def render_uploaded_file_preview(uploaded_file):
#     """
#     Preview one uploaded file in the UI.
#     """
#     if uploaded_file is None:
#         return

#     filename = uploaded_file.name
#     mime_type = uploaded_file.type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
#     file_type = _guess_file_type(filename, mime_type)
#     size_bytes = len(uploaded_file.getvalue())

#     st.markdown(f"### 📎 {filename}")
#     _render_file_badges(file_type, mime_type, size_bytes)

#     if file_type == "image":
#         st.image(uploaded_file, caption=filename, use_container_width=True)
#     elif file_type == "pdf":
#         st.markdown(
#             '<div class="upload-warning">📄 PDF uploaded successfully. Deep extraction is not wired in this UI yet, but the file is accepted.</div>',
#             unsafe_allow_html=True,
#         )
#     else:
#         st.warning("Preview not available for this file type.")


# def render_upload_and_extract_panel(
#     *,
#     allow_multiple: bool = False,
#     task_type: str = "general_financial",
#     model: Optional[str] = None,
# ) -> Optional[Dict[str, Any]]:
#     """
#     Full uploader panel:
#     - upload file(s)
#     - preview
#     - extract on button click
#     - render results
#     - return structured batch result as dict
#     """
#     load_uploader_styles()
#     _render_uploader_hero()

#     accepted_types = ["png", "jpg", "jpeg", "webp", "pdf"]

#     if allow_multiple:
#         uploaded_files = st.file_uploader(
#             "Upload files",
#             type=accepted_types,
#             accept_multiple_files=True,
#             help="Upload one or more receipts, screenshots, statements, or PDFs.",
#         )
#         uploaded_files = uploaded_files or []
#     else:
#         uploaded_file = st.file_uploader(
#             "Upload a file",
#             type=accepted_types,
#             accept_multiple_files=False,
#             help="Upload a receipt, screenshot, statement image, or PDF.",
#         )
#         uploaded_files = [uploaded_file] if uploaded_file else []

#     if not uploaded_files:
#         return None

#     st.markdown("## 👀 Preview")
#     for file in uploaded_files:
#         render_uploaded_file_preview(file)

#     process_clicked = st.button(
#         "✨ Extract with Vision AI",
#         type="primary",
#         use_container_width=True,
#     )

#     if not process_clicked:
#         return None

#     with st.spinner("Extracting financial content from uploaded file(s)..."):
#         batch_result = process_uploaded_files(
#             uploaded_files,
#             task_type=task_type,
#             model=model,
#         )

#     st.markdown("## 📊 Upload Summary")
#     c1, c2, c3, c4 = st.columns(4)
#     with c1:
#         st.metric("Total Files", batch_result.total_files)
#     with c2:
#         st.metric("Images", batch_result.image_count)
#     with c3:
#         st.metric("PDFs", batch_result.pdf_count)
#     with c4:
#         st.metric("Extracted", batch_result.extracted_count)

#     for file_result in batch_result.files:
#         st.markdown("---")
#         st.markdown(f"### 📄 {file_result.filename}")
#         _render_file_badges(file_result.file_type, file_result.mime_type, file_result.size_bytes)

#         if file_result.file_type == "pdf":
#             st.markdown(
#                 '<div class="upload-warning">📄 PDF accepted. Current UI path is image-first, so no deep extraction was attempted here.</div>',
#                 unsafe_allow_html=True,
#             )
#             continue

#         if file_result.vision_result:
#             _render_vision_result(file_result.vision_result)
#         elif file_result.error:
#             st.markdown(
#                 f'<div class="upload-error">❌ {file_result.error}</div>',
#                 unsafe_allow_html=True,
#             )

#     if batch_result.errors:
#         with st.expander("⚠️ Processing Errors"):
#             for err in batch_result.errors:
#                 st.write(f"- {err}")

#     return batch_result.to_dict()


# # =========================================================
# # CONVENIENCE HELPERS FOR OTHER UI FILES
# # =========================================================

# def render_image_upload_for_vision(
#     *,
#     model: Optional[str] = None,
# ) -> Optional[Dict[str, Any]]:
#     """
#     Convenience renderer for a single image-first extraction flow.
#     Returns the first file's vision result if available.
#     """
#     batch = render_upload_and_extract_panel(
#         allow_multiple=False,
#         task_type="general_financial",
#         model=model,
#     )

#     if not batch:
#         return None

#     files = batch.get("files", [])
#     for f in files:
#         vision_result = f.get("vision_result")
#         if vision_result:
#             return vision_result

#     return None

# # =========================================================
# # VISION -> TRANSACTION GLUE
# # =========================================================

# def extract_transactions_from_uploaded_file(
#     uploaded_file,
#     *,
#     student_id: str,
#     task_type: str = "general_financial",
#     model: Optional[str] = None,
# ) -> Dict[str, Any]:
#     """
#     Upload helper that:
#     1. processes the file with vision
#     2. converts extracted result into Transaction objects immediately

#     Returns:
#         {
#             "success": bool,
#             "file_result": UploadedFileResult as dict,
#             "vision_result": dict | None,
#             "bridge_result": dict | None,
#             "transactions": list[Transaction],
#             "transaction_count": int,
#             "errors": list[str]
#         }
#     """
#     file_result = process_uploaded_file_with_vision(
#         uploaded_file,
#         task_type=task_type,
#         model=model,
#     )

#     errors: List[str] = []
#     transactions = []
#     bridge_result = None
#     vision_result = file_result.vision_result

#     if not file_result.success:
#         if file_result.error:
#             errors.append(file_result.error)

#         return {
#             "success": False,
#             "file_result": file_result.to_dict(),
#             "vision_result": vision_result,
#             "bridge_result": None,
#             "transactions": [],
#             "transaction_count": 0,
#             "errors": errors,
#         }

#     if file_result.file_type != "image":
#         errors.append("Only image uploads can currently be converted directly into transactions.")

#         return {
#             "success": False,
#             "file_result": file_result.to_dict(),
#             "vision_result": vision_result,
#             "bridge_result": None,
#             "transactions": [],
#             "transaction_count": 0,
#             "errors": errors,
#         }

#     if not vision_result or not vision_result.get("success", False):
#         errors.append("Vision extraction did not return a usable result.")

#         return {
#             "success": False,
#             "file_result": file_result.to_dict(),
#             "vision_result": vision_result,
#             "bridge_result": None,
#             "transactions": [],
#             "transaction_count": 0,
#             "errors": errors,
#         }

#     bridge = vision_result_to_transactions(
#         vision_output=vision_result,
#         student_id=student_id,
#     )

#     bridge_result = bridge.to_dict()
#     transactions = bridge.transactions

#     if bridge.errors:
#         errors.extend(bridge.errors)

#     return {
#         "success": len(transactions) > 0,
#         "file_result": file_result.to_dict(),
#         "vision_result": vision_result,
#         "bridge_result": bridge_result,
#         "transactions": transactions,
#         "transaction_count": len(transactions),
#         "errors": errors,
#     }


# def extract_transactions_from_uploaded_files(
#     uploaded_files: List[Any],
#     *,
#     student_id: str,
#     task_type: str = "general_financial",
#     model: Optional[str] = None,
# ) -> Dict[str, Any]:
#     """
#     Batch helper that:
#     1. processes multiple uploaded files
#     2. converts all valid image vision results into Transaction objects

#     Returns:
#         {
#             "success": bool,
#             "files_processed": int,
#             "files_succeeded": int,
#             "transactions": list[Transaction],
#             "transaction_count": int,
#             "results": list[dict],
#             "errors": list[str]
#         }
#     """
#     all_transactions = []
#     per_file_results = []
#     all_errors: List[str] = []
#     files_succeeded = 0

#     for uploaded_file in uploaded_files:
#         result = extract_transactions_from_uploaded_file(
#             uploaded_file,
#             student_id=student_id,
#             task_type=task_type,
#             model=model,
#         )
#         per_file_results.append(result)

#         if result["success"]:
#             files_succeeded += 1
#             all_transactions.extend(result["transactions"])

#         if result["errors"]:
#             all_errors.extend([f"{uploaded_file.name}: {err}" for err in result["errors"]])

#     return {
#         "success": len(all_transactions) > 0,
#         "files_processed": len(uploaded_files),
#         "files_succeeded": files_succeeded,
#         "transactions": all_transactions,
#         "transaction_count": len(all_transactions),
#         "results": per_file_results,
#         "errors": all_errors,
#     }


# def render_upload_extract_and_convert_panel(
#     *,
#     student_id: str,
#     allow_multiple: bool = False,
#     task_type: str = "general_financial",
#     model: Optional[str] = None,
# ) -> Optional[Dict[str, Any]]:
#     """
#     Full UI flow:
#     - upload
#     - preview
#     - extract with vision
#     - convert directly to Transaction objects

#     Returns structured result including transactions.
#     """
#     load_uploader_styles()
#     _render_uploader_hero()

#     accepted_types = ["png", "jpg", "jpeg", "webp", "pdf"]

#     if allow_multiple:
#         uploaded_files = st.file_uploader(
#             "Upload files",
#             type=accepted_types,
#             accept_multiple_files=True,
#             help="Upload receipts, screenshots, statement images, or PDFs.",
#         )
#         uploaded_files = uploaded_files or []
#     else:
#         uploaded_file = st.file_uploader(
#             "Upload a file",
#             type=accepted_types,
#             accept_multiple_files=False,
#             help="Upload a receipt, screenshot, statement image, or PDF.",
#         )
#         uploaded_files = [uploaded_file] if uploaded_file else []

#     if not uploaded_files:
#         return None

#     st.markdown("## 👀 Preview")
#     for file in uploaded_files:
#         render_uploaded_file_preview(file)

#     process_clicked = st.button(
#         "✨ Extract and Convert to Transactions",
#         type="primary",
#         use_container_width=True,
#     )

#     if not process_clicked:
#         return None

#     with st.spinner("Extracting and converting uploaded file(s)..."):
#         if allow_multiple:
#             result = extract_transactions_from_uploaded_files(
#                 uploaded_files,
#                 student_id=student_id,
#                 task_type=task_type,
#                 model=model,
#             )
#         else:
#             result = extract_transactions_from_uploaded_file(
#                 uploaded_files[0],
#                 student_id=student_id,
#                 task_type=task_type,
#                 model=model,
#             )

#     st.markdown("## 📊 Conversion Summary")

#     if allow_multiple:
#         c1, c2, c3 = st.columns(3)
#         with c1:
#             st.metric("Files Processed", result.get("files_processed", 0))
#         with c2:
#             st.metric("Files Succeeded", result.get("files_succeeded", 0))
#         with c3:
#             st.metric("Transactions Created", result.get("transaction_count", 0))
#     else:
#         c1, c2 = st.columns(2)
#         with c1:
#             st.metric("Success", "Yes" if result.get("success") else "No")
#         with c2:
#             st.metric("Transactions Created", result.get("transaction_count", 0))

#     transactions = result.get("transactions", [])
#     if transactions:
#         st.success(f"✅ Created {len(transactions)} transaction(s).")

#         preview_rows = []
#         for txn in transactions:
#             preview_rows.append({
#                 "date": str(txn.date),
#                 "description": txn.description,
#                 "merchant": txn.merchant or "",
#                 "category": txn.category,
#                 "type": txn.transaction_type.value if hasattr(txn.transaction_type, "value") else str(txn.transaction_type),
#                 "amount": float(txn.amount),
#             })

#         st.dataframe(preview_rows, use_container_width=True, hide_index=True)
#     else:
#         st.warning("No transactions were created from the uploaded file(s).")

#     errors = result.get("errors", [])
#     if errors:
#         with st.expander("⚠️ Errors / Notes"):
#             for err in errors:
#                 st.write(f"- {err}")

#     return result

# def extract_transactions_from_pdf_upload(
#     uploaded_file,
#     *,
#     student_id: str,
# ) -> Dict[str, Any]:
#     """
#     Convert uploaded PDF bank statement into Transaction objects.
#     """
#     filename = uploaded_file.name
#     mime_type = uploaded_file.type or "application/pdf"
#     size_bytes = len(uploaded_file.getvalue())

#     try:
#         pdf_bytes = uploaded_file.getvalue()
#         raw_text = extract_text_from_pdf_bytes(pdf_bytes)

#         if not raw_text.strip():
#             return {
#                 "success": False,
#                 "file_type": "pdf",
#                 "filename": filename,
#                 "raw_text": "",
#                 "transactions": [],
#                 "transaction_count": 0,
#                 "errors": ["No extractable text found in PDF."],
#             }

#         parsed = parse_bank_text_to_transactions(
#             raw_text=raw_text,
#             student_id=student_id,
#             source="pdf",
#             use_llm_fallback=True,
#         )

#         return {
#             "success": len(parsed.transactions) > 0,
#             "file_type": "pdf",
#             "filename": filename,
#             "raw_text": raw_text,
#             "transactions": parsed.transactions,
#             "transaction_count": len(parsed.transactions),
#             "skipped_lines": parsed.skipped_lines,
#             "errors": parsed.errors,
#             "llm_calls": parsed.llm_calls,
#         }

#     except Exception as e:
#         return {
#             "success": False,
#             "file_type": "pdf",
#             "filename": filename,
#             "raw_text": "",
#             "transactions": [],
#             "transaction_count": 0,
#             "errors": [str(e)],
#         }

# # =========================================================
# # DEMO
# # =========================================================

# if __name__ == "__main__":
#     st.set_page_config(page_title="Uploaders", layout="wide")
#     load_uploader_styles()

#     result = render_upload_and_extract_panel(
#         allow_multiple=True,
#         task_type="general_financial",
#     )

#     if result:
#         with st.expander("🧩 Raw Upload Result"):
#             st.json(result)















from __future__ import annotations

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from dataclasses import dataclass, asdict
from typing import Optional, List, Dict, Any
import mimetypes

import streamlit as st
import fitz
from utils.vision_llm_wrapper import create_vision_wrapper
from utils.vision_transaction_bridge import vision_result_to_transactions
from utils.pdf_parser import (
    extract_text_from_pdf_bytes,
    parse_bank_text_to_transactions,
)

# =========================================================
# DATA MODELS
# =========================================================

@dataclass
class UploadedFileResult:
    """
    Structured result for one uploaded file.
    """
    filename: str
    file_type: str
    mime_type: str
    size_bytes: int
    success: bool
    extracted: bool
    extraction_mode: str
    preview_available: bool
    vision_result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class UploadBatchResult:
    """
    Structured result for a batch of uploaded files.
    """
    files: List[UploadedFileResult]
    total_files: int
    success_count: int
    extracted_count: int
    image_count: int
    pdf_count: int
    errors: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "files": [f.to_dict() for f in self.files],
            "total_files": self.total_files,
            "success_count": self.success_count,
            "extracted_count": self.extracted_count,
            "image_count": self.image_count,
            "pdf_count": self.pdf_count,
            "errors": self.errors,
        }


# =========================================================
# STYLES
# =========================================================

def load_uploader_styles():
    st.markdown(
        """
        <style>
        .uploader-hero {
            border-radius: 24px;
            padding: 1.8rem 1.5rem;
            margin-bottom: 1.2rem;
            background: linear-gradient(135deg, #4361EE 0%, #7209B7 100%);
            color: white;
            box-shadow: 0 18px 40px rgba(67, 97, 238, 0.22);
        }

        .uploader-hero h2, .uploader-hero p {
            color: white !important;
            margin: 0;
        }

        .upload-card {
            border-radius: 18px;
            padding: 1.25rem 1.25rem;
            margin-bottom: 1rem;
            background: #262730 !important;
            border: 1px solid #404040;
            box-shadow: 0 6px 18px rgba(0,0,0,0.2);
        }

        .upload-card strong {
            color: #FFFFFF !important;
            font-size: 1.1rem;
        }

        .upload-card div, .upload-card span, .upload-card p {
            color: #E0E0E0 !important;
        }

        .upload-soft {
            border-radius: 16px;
            padding: 0.9rem 1rem;
            margin-bottom: 0.75rem;
            background: #262730 !important;
            border: 1px solid #404040;
        }

        .upload-soft strong {
            color: #4361EE !important;
        }

        .upload-soft span, .upload-soft div {
            color: #E0E0E0 !important;
        }

        .upload-pill {
            display: inline-block;
            padding: 0.25rem 0.75rem;
            border-radius: 999px;
            background: #333333 !important;
            color: #FFFFFF !important;
            font-size: 0.85rem;
            font-weight: 600;
            margin-right: 0.4rem;
            margin-top: 0.2rem;
        }

        .upload-success {
            border-radius: 14px;
            padding: 0.85rem 1rem;
            background: #1E3A2E !important;
            border: 1px solid #06D6A0;
            color: #06D6A0 !important;
            font-weight: 500;
        }

        .upload-warning {
            border-radius: 14px;
            padding: 0.85rem 1rem;
            background: #3A2E1E !important;
            border: 1px solid #FF9F1C;
            color: #FF9F1C !important;
            font-weight: 500;
        }

        .upload-error {
            border-radius: 14px;
            padding: 0.85rem 1rem;
            background: #3A1E1E !important;
            border: 1px solid #EF233C;
            color: #EF233C !important;
            font-weight: 500;
        }

        [data-testid="stMetricValue"] {
            color: #FFFFFF !important;
            font-size: 1.8rem !important;
        }

        [data-testid="stMetricLabel"] {
            color: #E0E0E0 !important;
            font-size: 1rem !important;
        }

        .streamlit-expanderHeader {
            color: #FFFFFF !important;
            background-color: #262730 !important;
            border: 1px solid #404040 !important;
        }

        .streamlit-expanderContent {
            background-color: #262730 !important;
            border: 1px solid #404040 !important;
            border-top: none !important;
            color: #E0E0E0 !important;
        }

        .stMarkdown p, .stMarkdown li, .stMarkdown span, .stMarkdown div {
            color: #E0E0E0 !important;
        }

        h1, h2, h3, h4, h5, h6 {
            color: #FFFFFF !important;
        }

        .stFileUploader label, .stFileUploader span {
            color: #FFFFFF !important;
        }

        .stButton button {
            background: linear-gradient(135deg, #4361EE 0%, #7209B7 100%) !important;
            color: white !important;
            font-size: 1.1rem !important;
            font-weight: 600 !important;
            border: none !important;
        }

        [data-testid="stMetric"] {
            background: #262730 !important;
            border: 1px solid #404040 !important;
            border-radius: 12px !important;
            padding: 1rem !important;
        }

        .stAlert {
            background: #262730 !important;
            color: #E0E0E0 !important;
            border: 1px solid #404040 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


# =========================================================
# HELPERS
# =========================================================

def _render_uploader_hero():
    st.markdown(
        """
        <div class="uploader-hero">
            <h2>📤 Upload Receipts, Screenshots, or Statements</h2>
            <p style="margin-top:0.45rem; opacity:0.94;">
                Upload financial images or PDF bank statements for automatic extraction and transaction conversion.
            </p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def _guess_file_type(filename: str, mime_type: str) -> str:
    lower_name = filename.lower()

    if mime_type.startswith("image/"):
        return "image"
    if mime_type == "application/pdf" or lower_name.endswith(".pdf"):
        return "pdf"
    return "unknown"


def _pretty_size(size_bytes: int) -> str:
    if size_bytes < 1024:
        return f"{size_bytes} B"
    if size_bytes < 1024 * 1024:
        return f"{size_bytes / 1024:.1f} KB"
    return f"{size_bytes / (1024 * 1024):.2f} MB"


def _render_file_badges(file_type: str, mime_type: str, size_bytes: int):
    st.markdown(
        f"""
        <span class="upload-pill">{file_type.upper()}</span>
        <span class="upload-pill">{mime_type}</span>
        <span class="upload-pill">{_pretty_size(size_bytes)}</span>
        """,
        unsafe_allow_html=True,
    )


def _render_vision_result(result: Dict[str, Any]):
    if not result.get("success", False):
        st.markdown(
            f'<div class="upload-error">❌ Extraction failed: {result.get("error", "Unknown error")}</div>',
            unsafe_allow_html=True,
        )
        return

    data = result.get("data", {}) or {}
    metadata = result.get("metadata", {}) or {}

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Document Type", str(data.get("document_type", "unknown")).replace("_", " ").title())
    with col2:
        st.metric("Confidence", str(data.get("confidence", "unknown")).title())
    with col3:
        st.metric("Transactions Found", len(data.get("possible_transactions", []) or []))

    st.markdown(
        f"""
        <div class="upload-soft">
            <strong>Model:</strong> {metadata.get("model", "unknown")}<br/>
            <strong>Merchant:</strong> {data.get("merchant") or "N/A"}<br/>
            <strong>Date:</strong> {data.get("date") or "N/A"}<br/>
            <strong>Currency:</strong> {data.get("currency") or "N/A"}
        </div>
        """,
        unsafe_allow_html=True,
    )

    totals = data.get("totals", {}) or {}
    if any(v for v in totals.values()):
        st.markdown("#### 💰 Totals")
        t1, t2, t3 = st.columns(3)
        with t1:
            st.metric("Subtotal", totals.get("subtotal") or "—")
        with t2:
            st.metric("Tax", totals.get("tax") or "—")
        with t3:
            st.metric("Total", totals.get("total") or "—")

    transactions = data.get("possible_transactions", []) or []
    if transactions:
        st.markdown("#### 🧾 Extracted Transactions / Items")
        for i, txn in enumerate(transactions[:10], start=1):
            confidence_color = "#06D6A0" if txn.get("confidence") == "high" else "#FF9F1C" if txn.get("confidence") == "medium" else "#EF233C"
            st.markdown(
                f"""
                <div class="upload-card">
                    <div style="margin-bottom: 0.5rem;">
                        <span style="font-size: 1.1rem; font-weight: 600; color: #FFFFFF !important;">
                            {i}. {txn.get("description", "")}
                        </span>
                    </div>
                    <div style="display: grid; grid-template-columns: repeat(2, 1fr); gap: 0.5rem;">
                        <div><span style="font-weight: 500; color: #E0E0E0;">Date:</span> <span style="color: #FFFFFF;">{txn.get("date") or "N/A"}</span></div>
                        <div><span style="font-weight: 500; color: #E0E0E0;">Merchant:</span> <span style="color: #FFFFFF;">{txn.get("merchant") or "N/A"}</span></div>
                        <div><span style="font-weight: 500; color: #E0E0E0;">Amount:</span> <span style="color: {confidence_color}; font-weight: 600;">{txn.get("amount") or "N/A"}</span></div>
                        <div><span style="font-weight: 500; color: #E0E0E0;">Confidence:</span> <span style="color: {confidence_color}; font-weight: 600;">{txn.get("confidence") or "N/A"}</span></div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )

    extracted_text = data.get("extracted_text", "")
    if extracted_text:
        with st.expander("📝 Extracted Text Preview"):
            st.text(extracted_text[:3000])

    notes = data.get("notes")
    if notes:
        st.info(notes)


def _render_pdf_vision_result(result: Dict[str, Any]):
    if not result.get("success", False):
        errs = result.get("errors", [])
        msg = errs[0] if errs else "PDF extraction failed."
        st.markdown(
            f'<div class="upload-error">❌ {msg}</div>',
            unsafe_allow_html=True,
        )
        return

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Document Type", "PDF via Vision")
    with col2:
        st.metric("Pages Processed", result.get("page_count", 0))
    with col3:
        st.metric("Transactions Parsed", result.get("transaction_count", 0))

    st.markdown(
        f"""
        <div class="upload-soft">
            <strong>Extraction Mode:</strong> pdf_vision_pages<br/>
            <strong>Pages Succeeded:</strong> {result.get("pages_succeeded", 0)}<br/>
            <strong>Errors:</strong> {len(result.get("errors", []))}
        </div>
        """,
        unsafe_allow_html=True,
    )

    transactions = result.get("transactions", []) or []
    if transactions:
        preview_rows = []
        for txn in transactions[:20]:
            preview_rows.append({
                "date": str(txn.date),
                "description": txn.description,
                "merchant": txn.merchant or "",
                "category": txn.category,
                "type": txn.transaction_type.value if hasattr(txn.transaction_type, "value") else str(txn.transaction_type),
                "amount": float(txn.amount),
            })
        st.dataframe(preview_rows, width="stretch", hide_index=True)

    vision_results = result.get("vision_results", [])
    if vision_results:
        with st.expander("🧠 Page-by-page Vision Results"):
            for item in vision_results:
                page_num = item.get("page_number")
                page_result = item.get("result", {})
                st.markdown(f"**Page {page_num}**")
                if page_result.get("success"):
                    data = page_result.get("data", {}) or {}
                    st.write({
                        "document_type": data.get("document_type"),
                        "merchant": data.get("merchant"),
                        "date": data.get("date"),
                        "transactions_found": len(data.get("possible_transactions", []) or []),
                        "confidence": data.get("confidence"),
                    })
                else:
                    st.write({"error": page_result.get("error", "Unknown error")})

    errors = result.get("errors", [])
    if errors:
        with st.expander("⚠️ PDF Vision Errors"):
            for err in errors[:50]:
                st.write(f"- {err}")


# =========================================================
# CORE EXTRACTION LOGIC
# =========================================================

def process_uploaded_file_with_vision(
    uploaded_file,
    *,
    task_type: str = "general_financial",
    model: Optional[str] = None,
) -> UploadedFileResult:
    """
    Process a single uploaded image file with vision.
    PDFs are accepted by the UI, but not extracted in this function.
    """
    filename = uploaded_file.name
    mime_type = uploaded_file.type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    size_bytes = len(uploaded_file.getvalue())
    file_type = _guess_file_type(filename, mime_type)

    try:
        if file_type == "image":
            wrapper = create_vision_wrapper(model=model) if model else create_vision_wrapper()
            image_bytes = uploaded_file.getvalue()

            lower_name = filename.lower()
            if "receipt" in lower_name:
                vision_result = wrapper.extract_receipt(image_bytes)
            elif "statement" in lower_name or "bank" in lower_name:
                vision_result = wrapper.extract_bank_statement(image_bytes,
                                                               max_tokens = 4000,
                                                               temperature = 0.1)
            elif "screen" in lower_name or "screenshot" in lower_name:
                vision_result = wrapper.extract_screenshot_text(image_bytes)
            else:
                vision_result = wrapper.extract_financial_document(
                    image_bytes,
                    task_type="general_financial",
                    max_tokens=3000,
                    temperature=0.1
                )

            return UploadedFileResult(
                filename=filename,
                file_type=file_type,
                mime_type=mime_type,
                size_bytes=size_bytes,
                success=bool(vision_result.get("success", False)),
                extracted=True,
                extraction_mode="vision_llm",
                preview_available=True,
                vision_result=vision_result,
                error=vision_result.get("error"),
            )

        if file_type == "pdf":
            return UploadedFileResult(
                filename=filename,
                file_type=file_type,
                mime_type=mime_type,
                size_bytes=size_bytes,
                success=True,
                extracted=False,
                extraction_mode="pdf_file_received",
                preview_available=False,
                vision_result=None,
                error=None,
            )

        return UploadedFileResult(
            filename=filename,
            file_type=file_type,
            mime_type=mime_type,
            size_bytes=size_bytes,
            success=False,
            extracted=False,
            extraction_mode="unsupported",
            preview_available=False,
            vision_result=None,
            error=f"Unsupported file type: {mime_type}",
        )

    except Exception as e:
        return UploadedFileResult(
            filename=filename,
            file_type=file_type,
            mime_type=mime_type,
            size_bytes=size_bytes,
            success=False,
            extracted=False,
            extraction_mode="error",
            preview_available=False,
            vision_result=None,
            error=str(e),
        )


def process_uploaded_files(
    uploaded_files: List[Any],
    *,
    task_type: str = "general_financial",
    model: Optional[str] = None,
) -> UploadBatchResult:
    """
    Process a batch of uploaded files for extraction preview.
    Images are extracted with vision. PDFs are accepted and counted.
    """
    results: List[UploadedFileResult] = []
    errors: List[str] = []

    for uploaded_file in uploaded_files:
        result = process_uploaded_file_with_vision(
            uploaded_file,
            task_type=task_type,
            model=model,
        )
        results.append(result)
        if result.error:
            errors.append(f"{result.filename}: {result.error}")

    image_count = sum(1 for r in results if r.file_type == "image")
    pdf_count = sum(1 for r in results if r.file_type == "pdf")
    success_count = sum(1 for r in results if r.success)
    extracted_count = sum(1 for r in results if r.extracted and r.success)

    return UploadBatchResult(
        files=results,
        total_files=len(results),
        success_count=success_count,
        extracted_count=extracted_count,
        image_count=image_count,
        pdf_count=pdf_count,
        errors=errors,
    )


# =========================================================
# PDF + IMAGE CONVERSION HELPERS
# =========================================================

def extract_transactions_from_pdf_upload(
    uploaded_file,
    *,
    student_id: str,
) -> Dict[str, Any]:
    """
    Convert uploaded PDF bank statement into Transaction objects.
    """
    filename = uploaded_file.name
    mime_type = uploaded_file.type or "application/pdf"
    size_bytes = len(uploaded_file.getvalue())

    try:
        pdf_bytes = uploaded_file.getvalue()
        raw_text = extract_text_from_pdf_bytes(pdf_bytes)

        if not raw_text.strip():
            return {
                "success": False,
                "file_result": {
                    "filename": filename,
                    "file_type": "pdf",
                    "mime_type": mime_type,
                    "size_bytes": size_bytes,
                    "success": False,
                    "extracted": False,
                    "extraction_mode": "pdf_text_parse",
                    "preview_available": False,
                    "vision_result": None,
                    "error": "No extractable text found in PDF.",
                },
                "vision_result": None,
                "bridge_result": None,
                "raw_text": "",
                "transactions": [],
                "transaction_count": 0,
                "skipped_lines": [],
                "errors": ["No extractable text found in PDF."],
                "llm_calls": 0,
            }

        parsed = parse_bank_text_to_transactions(
            raw_text=raw_text,
            student_id=student_id,
            source="pdf",
            use_llm_fallback=True,
        )

        return {
            "success": len(parsed.transactions) > 0,
            "file_result": {
                "filename": filename,
                "file_type": "pdf",
                "mime_type": mime_type,
                "size_bytes": size_bytes,
                "success": len(parsed.transactions) > 0,
                "extracted": True,
                "extraction_mode": "pdf_text_parse",
                "preview_available": False,
                "vision_result": None,
                "error": None,
            },
            "vision_result": None,
            "bridge_result": None,
            "raw_text": raw_text,
            "transactions": parsed.transactions,
            "transaction_count": len(parsed.transactions),
            "skipped_lines": parsed.skipped_lines,
            "errors": parsed.errors,
            "llm_calls": parsed.llm_calls,
        }

    except Exception as e:
        return {
            "success": False,
            "file_result": {
                "filename": filename,
                "file_type": "pdf",
                "mime_type": mime_type,
                "size_bytes": size_bytes,
                "success": False,
                "extracted": False,
                "extraction_mode": "pdf_text_parse",
                "preview_available": False,
                "vision_result": None,
                "error": str(e),
            },
            "vision_result": None,
            "bridge_result": None,
            "raw_text": "",
            "transactions": [],
            "transaction_count": 0,
            "skipped_lines": [],
            "errors": [str(e)],
            "llm_calls": 0,
        }


def extract_transactions_from_uploaded_file(
    uploaded_file,
    *,
    student_id: str,
    task_type: str = "general_financial",
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Unified upload helper:
    - image uploads -> vision -> transaction bridge
    - PDF uploads -> pdf pages -> vision -> transaction bridge
    """
    filename = uploaded_file.name
    mime_type = uploaded_file.type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    file_type = _guess_file_type(filename, mime_type)

    # PDF via vision path
    if file_type == "pdf":
        return extract_transactions_from_pdf_via_vision(
            uploaded_file,
            student_id=student_id,
            model=model,
        )

    # Image path
    file_result = process_uploaded_file_with_vision(
        uploaded_file,
        task_type=task_type,
        model=model,
    )

    errors: List[str] = []
    transactions = []
    bridge_result = None
    vision_result = file_result.vision_result

    if not file_result.success:
        if file_result.error:
            errors.append(file_result.error)

        return {
            "success": False,
            "file_result": file_result.to_dict(),
            "vision_result": vision_result,
            "bridge_result": None,
            "transactions": [],
            "transaction_count": 0,
            "errors": errors,
        }

    if file_result.file_type != "image":
        errors.append(f"Unsupported conversion path for file type: {file_result.file_type}")
        return {
            "success": False,
            "file_result": file_result.to_dict(),
            "vision_result": vision_result,
            "bridge_result": None,
            "transactions": [],
            "transaction_count": 0,
            "errors": errors,
        }

    if not vision_result or not vision_result.get("success", False):
        errors.append("Vision extraction did not return a usable result.")
        return {
            "success": False,
            "file_result": file_result.to_dict(),
            "vision_result": vision_result,
            "bridge_result": None,
            "transactions": [],
            "transaction_count": 0,
            "errors": errors,
        }

    bridge = vision_result_to_transactions(
        vision_output=vision_result,
        student_id=student_id,
    )

    bridge_result = bridge.to_dict()
    transactions = bridge.transactions

    if bridge.errors:
        errors.extend(bridge.errors)

    return {
        "success": len(transactions) > 0,
        "file_result": file_result.to_dict(),
        "vision_result": vision_result,
        "bridge_result": bridge_result,
        "transactions": transactions,
        "transaction_count": len(transactions),
        "errors": errors,
    }


def extract_transactions_from_uploaded_files(
    uploaded_files: List[Any],
    *,
    student_id: str,
    task_type: str = "general_financial",
    model: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Batch helper that:
    - processes multiple uploaded files
    - converts images and PDFs into Transaction objects
    """
    all_transactions = []
    per_file_results = []
    all_errors: List[str] = []
    files_succeeded = 0

    for uploaded_file in uploaded_files:
        result = extract_transactions_from_uploaded_file(
            uploaded_file,
            student_id=student_id,
            task_type=task_type,
            model=model,
        )
        per_file_results.append(result)

        if result["success"]:
            files_succeeded += 1
            all_transactions.extend(result["transactions"])

        if result["errors"]:
            all_errors.extend([f"{uploaded_file.name}: {err}" for err in result["errors"]])

    return {
        "success": len(all_transactions) > 0,
        "files_processed": len(uploaded_files),
        "files_succeeded": files_succeeded,
        "transactions": all_transactions,
        "transaction_count": len(all_transactions),
        "results": per_file_results,
        "errors": all_errors,
    }


# =========================================================
# UI RENDERERS
# =========================================================

def render_single_file_upload(
    *,
    label: str = "Upload a receipt, screenshot, or PDF",
    accepted_types: Optional[List[str]] = None,
) -> Optional[Any]:
    """
    Render a single file uploader and return the uploaded file.
    """
    load_uploader_styles()
    _render_uploader_hero()

    if accepted_types is None:
        accepted_types = ["png", "jpg", "jpeg", "webp", "pdf"]

    uploaded_file = st.file_uploader(
        label,
        type=accepted_types,
        accept_multiple_files=False,
        help="Images are extracted with vision AI. PDFs are parsed as bank statement text where possible.",
    )

    return uploaded_file


def render_multi_file_upload(
    *,
    label: str = "Upload one or more receipts, screenshots, or PDFs",
    accepted_types: Optional[List[str]] = None,
) -> List[Any]:
    """
    Render a multi-file uploader and return uploaded files.
    """
    load_uploader_styles()
    _render_uploader_hero()

    if accepted_types is None:
        accepted_types = ["png", "jpg", "jpeg", "webp", "pdf"]

    uploaded_files = st.file_uploader(
        label,
        type=accepted_types,
        accept_multiple_files=True,
        help="Images use vision extraction. PDFs use statement text parsing when possible.",
    )

    return uploaded_files or []


def render_uploaded_file_preview(uploaded_file):
    """
    Preview one uploaded file in the UI.
    """
    if uploaded_file is None:
        return

    filename = uploaded_file.name
    mime_type = uploaded_file.type or mimetypes.guess_type(filename)[0] or "application/octet-stream"
    file_type = _guess_file_type(filename, mime_type)
    size_bytes = len(uploaded_file.getvalue())

    st.markdown(f"### 📎 {filename}")
    _render_file_badges(file_type, mime_type, size_bytes)

    if file_type == "image":
        st.image(uploaded_file, caption=filename, width="stretch")
    elif file_type == "pdf":
        st.markdown(
            '<div class="upload-success">📄 PDF uploaded successfully. It can be parsed as a bank statement.</div>',
            unsafe_allow_html=True,
        )
    else:
        st.warning("Preview not available for this file type.")


def render_upload_and_extract_panel(
    *,
    allow_multiple: bool = False,
    task_type: str = "general_financial",
    model: Optional[str] = None,
    uploader_key: str = "upload_extract_panel",
) -> Optional[Dict[str, Any]]:
    """
    Extraction-only panel:
    - images -> vision extraction preview
    - PDFs -> accepted, but this panel is mainly for previewing extraction paths
    """
    load_uploader_styles()
    _render_uploader_hero()

    accepted_types = ["png", "jpg", "jpeg", "webp", "pdf"]

    if allow_multiple:
        uploaded_files = st.file_uploader(
            "Upload files",
            type=accepted_types,
            ultiple_files=True,
            help="Upload one or more receipts, screenshots, statements, or PDFs.",
            key=f"{uploader_key}_multi",
)
        uploaded_files = uploaded_files or []
    else:
        uploaded_file = st.file_uploader(
    "Upload a file",
    type=accepted_types,
    accept_multiple_files=False,
    help="Upload a receipt, screenshot, statement image, or PDF.",
    key=f"{uploader_key}_single",
)
        uploaded_files = [uploaded_file] if uploaded_file else []

    if not uploaded_files:
        return None

    st.markdown("## 👀 Preview")
    for file in uploaded_files:
        render_uploaded_file_preview(file)

    process_clicked = st.button(
        "✨ Extract Preview",
        type="primary",
        width="stretch",
    )

    if not process_clicked:
        return None

    with st.spinner("Processing uploaded file(s)..."):
        batch_result = process_uploaded_files(
            uploaded_files,
            task_type=task_type,
            model=model,
        )

    st.markdown("## 📊 Upload Summary")
    c1, c2, c3, c4 = st.columns(4)
    with c1:
        st.metric("Total Files", batch_result.total_files)
    with c2:
        st.metric("Images", batch_result.image_count)
    with c3:
        st.metric("PDFs", batch_result.pdf_count)
    with c4:
        st.metric("Extracted", batch_result.extracted_count)

    for file_result in batch_result.files:
        st.markdown("---")
        st.markdown(f"### 📄 {file_result.filename}")
        _render_file_badges(file_result.file_type, file_result.mime_type, file_result.size_bytes)

        if file_result.file_type == "pdf":
            st.markdown(
                '<div class="upload-warning">📄 This panel is extraction-preview focused. Use the convert panel to parse PDF statements into transactions.</div>',
                unsafe_allow_html=True,
            )
            continue

        if file_result.vision_result:
            _render_vision_result(file_result.vision_result)
        elif file_result.error:
            st.markdown(
                f'<div class="upload-error">❌ {file_result.error}</div>',
                unsafe_allow_html=True,
            )

    if batch_result.errors:
        with st.expander("⚠️ Processing Errors"):
            for err in batch_result.errors:
                st.write(f"- {err}")

    return batch_result.to_dict()


def render_image_upload_for_vision(
    *,
    model: Optional[str] = None,
) -> Optional[Dict[str, Any]]:
    """
    Convenience renderer for a single image-first extraction flow.
    Returns the first file's vision result if available.
    """
    batch = render_upload_and_extract_panel(
        allow_multiple=False,
        task_type="general_financial",
        model=model,
    )

    if not batch:
        return None

    files = batch.get("files", [])
    for f in files:
        vision_result = f.get("vision_result")
        if vision_result:
            return vision_result

    return None


def render_upload_extract_and_convert_panel(
    *,
    student_id: str,
    allow_multiple: bool = False,
    task_type: str = "general_financial",
    model: Optional[str] = None,
    uploader_key: str = "upload_convert_panel",
) -> Optional[Dict[str, Any]]:
    """
    Full UI flow:
    - upload
    - preview
    - extract
    - convert directly to Transaction objects

    Supports:
    - images -> vision + bridge
    - PDFs -> text extraction + statement parsing
    """
    load_uploader_styles()
    _render_uploader_hero()

    accepted_types = ["png", "jpg", "jpeg", "webp", "pdf"]

    if allow_multiple:
        uploaded_files = st.file_uploader(
    "Upload files",
    type=accepted_types,
    accept_multiple_files=True,
    help="Upload receipts, screenshots, statement images, or PDFs.",
    key=f"{uploader_key}_multi",
)
        uploaded_files = uploaded_files or []
    else:
        uploaded_file = st.file_uploader(
    "Upload a file",
    type=accepted_types,
    accept_multiple_files=False,
    help="Upload a receipt, screenshot, statement image, or PDF.",
    key=f"{uploader_key}_single",
)
        uploaded_files = [uploaded_file] if uploaded_file else []

    if not uploaded_files:
        return None

    st.markdown("## 👀 Preview")
    for file in uploaded_files:
        render_uploaded_file_preview(file)

    process_clicked = st.button(
        "✨ Extract and Convert to Transactions",
        type="primary",
        width="stretch",
    )

    if not process_clicked:
        return None

    with st.spinner("Extracting and converting uploaded file(s)..."):
        if allow_multiple:
            result = extract_transactions_from_uploaded_files(
                uploaded_files,
                student_id=student_id,
                task_type=task_type,
                model=model,
            )
        else:
            result = extract_transactions_from_uploaded_file(
                uploaded_files[0],
                student_id=student_id,
                task_type=task_type,
                model=model,
            )

    st.markdown("## 📊 Conversion Summary")

    if allow_multiple:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Files Processed", result.get("files_processed", 0))
        with c2:
            st.metric("Files Succeeded", result.get("files_succeeded", 0))
        with c3:
            st.metric("Transactions Created", result.get("transaction_count", 0))
    else:
        c1, c2 = st.columns(2)
        with c1:
            st.metric("Success", "Yes" if result.get("success") else "No")
        with c2:
            st.metric("Transactions Created", result.get("transaction_count", 0))

    # Render per-file result details
    if allow_multiple:
        per_file_results = result.get("results", [])
        for idx, file_result in enumerate(per_file_results, start=1):
            st.markdown("---")
            file_meta = file_result.get("file_result", {})
            st.markdown(f"### 📄 File {idx}: {file_meta.get('filename', 'Unknown')}")

            if file_meta.get("file_type") == "pdf":
                _render_pdf_vision_result(file_result)
            else:
                if file_result.get("vision_result"):
                    _render_vision_result(file_result["vision_result"])

                bridge_result = file_result.get("bridge_result")
                if bridge_result:
                    skipped_items = bridge_result.get("skipped_items", [])
                    errors = bridge_result.get("errors", [])
                    if skipped_items or errors:
                        with st.expander("⚠️ Image Bridge Notes"):
                            for item in skipped_items[:10]:
                                st.write(f"- Skipped: {item}")
                            for err in errors[:10]:
                                st.write(f"- Error: {err}")
    else:
        file_meta = result.get("file_result", {})
        if file_meta.get("file_type") == "pdf":
            _render_pdf_vision_result(result)
        else:
            if result.get("vision_result"):
                _render_vision_result(result["vision_result"])

            bridge_result = result.get("bridge_result")
            if bridge_result:
                skipped_items = bridge_result.get("skipped_items", [])
                errors = bridge_result.get("errors", [])
                if skipped_items or errors:
                    with st.expander("⚠️ Image Bridge Notes"):
                        for item in skipped_items[:10]:
                            st.write(f"- Skipped: {item}")
                        for err in errors[:10]:
                            st.write(f"- Error: {err}")

    transactions = result.get("transactions", [])
    if transactions:
        st.success(f"✅ Created {len(transactions)} transaction(s).")

        preview_rows = []
        for txn in transactions:
            preview_rows.append({
                "date": str(txn.date),
                "description": txn.description,
                "merchant": txn.merchant or "",
                "category": txn.category,
                "type": txn.transaction_type.value if hasattr(txn.transaction_type, "value") else str(txn.transaction_type),
                "amount": float(txn.amount),
            })

        st.dataframe(preview_rows, width="stretch", hide_index=True)
    else:
        st.warning("No transactions were created from the uploaded file(s).")

    errors = result.get("errors", [])
    if errors:
        with st.expander("⚠️ Errors / Notes"):
            for err in errors:
                st.write(f"- {err}")

    return result

def pdf_bytes_to_page_images(
    pdf_bytes: bytes,
    *,
    zoom: float = 2.0,
    image_format: str = "png",
) -> List[bytes]:
    """
    Convert PDF bytes into a list of page images as raw bytes.

    Args:
        pdf_bytes: Uploaded PDF content
        zoom: Render scale factor (2.0 = good quality for OCR/vision)
        image_format: "png" recommended

    Returns:
        List of image bytes, one per page
    """
    images: List[bytes] = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")

    try:
        matrix = fitz.Matrix(zoom, zoom)

        for page in doc:
            pix = page.get_pixmap(matrix=matrix, alpha=False)
            img_bytes = pix.tobytes(image_format)
            images.append(img_bytes)
    finally:
        doc.close()

    return images

def guess_pdf_page_task_type(filename: str) -> str:
    """
    Lightweight heuristic for PDF page extraction mode.
    """
    lower_name = filename.lower()
    if "statement" in lower_name or "bank" in lower_name or "chase" in lower_name:
        return "bank_statement"
    return "general_financial"


def extract_transactions_from_pdf_via_vision(
    uploaded_file,
    *,
    student_id: str,
    model: Optional[str] = None,
    max_pages: Optional[int] = None,
) -> Dict[str, Any]:
    """
    Convert uploaded PDF into page images, run each page through vision,
    then bridge into Transaction objects.

    Returns:
        {
            "success": bool,
            "file_result": {...},
            "vision_results": list[dict],
            "bridge_results": list[dict],
            "transactions": list[Transaction],
            "transaction_count": int,
            "page_count": int,
            "pages_succeeded": int,
            "errors": list[str],
        }
    """
    filename = uploaded_file.name
    mime_type = uploaded_file.type or "application/pdf"
    size_bytes = len(uploaded_file.getvalue())

    errors: List[str] = []
    all_transactions = []
    vision_results: List[Dict[str, Any]] = []
    bridge_results: List[Dict[str, Any]] = []

    try:
        pdf_bytes = uploaded_file.getvalue()
        page_images = pdf_bytes_to_page_images(pdf_bytes)

        if not page_images:
            return {
                "success": False,
                "file_result": {
                    "filename": filename,
                    "file_type": "pdf",
                    "mime_type": mime_type,
                    "size_bytes": size_bytes,
                    "success": False,
                    "extracted": False,
                    "extraction_mode": "pdf_vision_pages",
                    "preview_available": False,
                    "vision_result": None,
                    "error": "No pages could be rendered from the PDF.",
                },
                "vision_results": [],
                "bridge_results": [],
                "transactions": [],
                "transaction_count": 0,
                "page_count": 0,
                "pages_succeeded": 0,
                "errors": ["No pages could be rendered from the PDF."],
            }

        if max_pages is not None:
            page_images = page_images[:max_pages]

        wrapper = create_vision_wrapper(model=model) if model else create_vision_wrapper()
        task_type = guess_pdf_page_task_type(filename)

        pages_succeeded = 0

        for page_index, image_bytes in enumerate(page_images, start=1):
            try:
                if task_type == "bank_statement":
                    vision_result = wrapper.extract_bank_statement(image_bytes,
                                                                   max_tokens = 4000,
                                                                   temperature = 0.1)
                else:
                    vision_result = wrapper.extract_financial_document(
                        image_bytes,
                        task_type="general_financial",
                        max_tokens=3000,
                        temperature=0.1
                    )

                vision_results.append({
                    "page_number": page_index,
                    "result": vision_result,
                })

                if not vision_result.get("success", False):
                    errors.append(f"Page {page_index}: vision extraction failed")
                    continue

                bridge = vision_result_to_transactions(
                    vision_output=vision_result,
                    student_id=student_id,
                )

                bridge_dict = bridge.to_dict()
                bridge_dict["page_number"] = page_index
                bridge_results.append(bridge_dict)

                if bridge.errors:
                    errors.extend([f"Page {page_index}: {err}" for err in bridge.errors])

                if bridge.transactions:
                    pages_succeeded += 1
                    all_transactions.extend(bridge.transactions)

            except Exception as e:
                errors.append(f"Page {page_index}: {str(e)}")

        deduped_transactions = _deduplicate_transactions(all_transactions)

        success = len(deduped_transactions) > 0

        return {
            "success": success,
            "file_result": {
                "filename": filename,
                "file_type": "pdf",
                "mime_type": mime_type,
                "size_bytes": size_bytes,
                "success": success,
                "extracted": True,
                "extraction_mode": "pdf_vision_pages",
                "preview_available": False,
                "vision_result": None,
                "error": None if success else "No transactions extracted from PDF pages.",
            },
            "vision_results": vision_results,
            "bridge_results": bridge_results,
            "transactions": deduped_transactions,
            "transaction_count": len(deduped_transactions),
            "page_count": len(page_images),
            "pages_succeeded": pages_succeeded,
            "errors": errors,
        }

    except Exception as e:
        return {
            "success": False,
            "file_result": {
                "filename": filename,
                "file_type": "pdf",
                "mime_type": mime_type,
                "size_bytes": size_bytes,
                "success": False,
                "extracted": False,
                "extraction_mode": "pdf_vision_pages",
                "preview_available": False,
                "vision_result": None,
                "error": str(e),
            },
            "vision_results": [],
            "bridge_results": [],
            "transactions": [],
            "transaction_count": 0,
            "page_count": 0,
            "pages_succeeded": 0,
            "errors": [str(e)],
        }

def _deduplicate_transactions(transactions: List[Any]) -> List[Any]:
    """
    Remove likely duplicates across PDF pages.
    """
    seen = set()
    deduped = []

    for txn in transactions:
        key = (
            str(getattr(txn, "date", "")),
            round(float(getattr(txn, "amount", 0.0)), 2),
            (getattr(txn, "description", "") or "").strip().lower(),
            (getattr(txn, "merchant", "") or "").strip().lower(),
        )
        if key not in seen:
            seen.add(key)
            deduped.append(txn)

    return deduped




# =========================================================
# DEMO
# =========================================================

if __name__ == "__main__":
    st.set_page_config(page_title="Uploaders", layout="wide")
    load_uploader_styles()

    result = render_upload_extract_and_convert_panel(
        student_id="STU_DEMO_001",
        allow_multiple=True,
        task_type="general_financial",
    )

    if result:
        with st.expander("🧩 Raw Upload Result"):
            st.json(result)