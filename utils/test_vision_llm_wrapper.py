"""
🧪 TEST VISION LLM WRAPPER - Comprehensive test suite for image-based financial document extraction

What this tests
---------------
- receipt extraction
- bank statement extraction
- screenshot extraction
- batch processing
- cache behavior
- error handling
- custom prompt behavior
- wrapper stats

How to run
----------
Quick mode:
    python -m utils.test_vision_llm_wrapper --quick

Full mode:
    python -m utils.test_vision_llm_wrapper
"""

import sys
from pathlib import Path
import time
from typing import Dict, Any, List
import io

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from PIL import Image, ImageDraw, ImageFont

from config import Config
from utils.vision_llm_wrapper import create_vision_wrapper


# =========================================================
# TEST IMAGE GENERATORS
# =========================================================

def _load_font(size: int, bold: bool = False):
    """
    Try to load a common font. If unavailable, fall back to default.
    """
    candidates = []
    if bold:
        candidates = [
            "Arial Bold.ttf",
            "arialbd.ttf",
            "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        ]
    else:
        candidates = [
            "Arial.ttf",
            "arial.ttf",
            "/System/Library/Fonts/Supplemental/Arial.ttf",
        ]

    for candidate in candidates:
        try:
            return ImageFont.truetype(candidate, size)
        except Exception:
            continue

    return ImageFont.load_default()


def create_test_receipt_image() -> bytes:
    """
    Generate a synthetic receipt image as PNG bytes.
    """
    img = Image.new("RGB", (800, 1000), color="white")
    draw = ImageDraw.Draw(img)

    font = _load_font(20, bold=False)
    font_small = _load_font(16, bold=False)
    font_large = _load_font(28, bold=True)

    y = 50
    lines = [
        ("STARBUCKS COFFEE", font_large, 35),
        ("123 Main Street", font, 22),
        ("San Francisco, CA", font, 22),
        ("Tel: (415) 555-0123", font, 22),
        ("----------------------------------------", font_small, 20),
        ("12/25/2025  3:45 PM", font, 22),
        ("Store #: 12345", font_small, 20),
        ("Reg: 03  Tran: 4567", font_small, 20),
        ("----------------------------------------", font_small, 20),
        ("1x  Caffe Latte         $4.95", font, 22),
        ("1x  Cappuccino          $4.75", font, 22),
        ("1x  Blueberry Muffin    $3.50", font, 22),
        ("----------------------------------------", font_small, 20),
        ("Subtotal                $13.20", font, 22),
        ("Tax (8.5%)              $1.12", font, 22),
        ("----------------------------------------", font_small, 20),
        ("TOTAL                   $14.32", font_large, 30),
        ("Payment: Credit Card", font_small, 20),
        ("Card: **** **** **** 1234", font_small, 20),
        ("Approval Code: 123456", font_small, 20),
        ("Thank you for visiting!", font, 22),
    ]

    for text, current_font, step in lines:
        draw.text((50, y), text, fill="black", font=current_font)
        y += step

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


def create_test_bank_statement_image() -> bytes:
    """
    Generate a synthetic bank statement image as PNG bytes.
    """
    img = Image.new("RGB", (1000, 1200), color="white")
    draw = ImageDraw.Draw(img)

    font = _load_font(18, bold=False)
    font_bold = _load_font(20, bold=True)
    font_small = _load_font(14, bold=False)
    font_large = _load_font(24, bold=True)

    y = 40

    header_lines = [
        ("CHASE BANK", font_large, 30),
        ("Account Statement", font_bold, 26),
        ("March 1 - March 31, 2025", font, 22),
        ("Account: **** **** **** 1234", font, 22),
        ("Customer: ALEX JOHNSON", font, 22),
        ("------------------------------------------------------------", font_small, 18),
    ]

    for text, current_font, step in header_lines:
        draw.text((50, y), text, fill="black", font=current_font)
        y += step

    y += 10

    draw.text((50, y), "Date", fill="darkblue", font=font_bold)
    draw.text((200, y), "Description", fill="darkblue", font=font_bold)
    draw.text((650, y), "Amount", fill="darkblue", font=font_bold)
    y += 30

    transactions = [
        ("03/01", "STARBUCKS #12345", "-$4.95"),
        ("03/02", "AMAZON.COM*KINDLE", "-$29.99"),
        ("03/05", "TRADER JOES", "-$67.32"),
        ("03/07", "DIRECT DEPOSIT - PAYROLL", "+$2,800.00"),
        ("03/10", "SPOTIFY USA", "-$9.99"),
        ("03/12", "SHELL OIL", "-$45.67"),
        ("03/15", "NETFLIX.COM", "-$15.99"),
        ("03/18", "UBER TRIP", "-$24.50"),
        ("03/20", "TARGET", "-$89.43"),
        ("03/22", "WHOLE FOODS", "-$134.21"),
        ("03/25", "RENT PAYMENT", "-$1,200.00"),
        ("03/28", "ATM WITHDRAWAL", "-$60.00"),
        ("03/30", "INTEREST PAYMENT", "+$0.32"),
    ]

    for tx_date, desc, amount in transactions:
        draw.text((50, y), tx_date, fill="black", font=font)
        draw.text((200, y), desc[:36], fill="black", font=font)
        color = "green" if amount.startswith("+") else "red"
        draw.text((650, y), amount, fill=color, font=font)
        y += 24

    y += 20
    summary_lines = [
        ("Beginning Balance: $2,345.67", font, 22),
        ("Ending Balance:    $3,456.78", font, 22),
        ("Total Deposits:    $2,800.32", font, 22),
        ("Total Withdrawals: $1,689.21", font, 22),
    ]

    for text, current_font, step in summary_lines:
        draw.text((50, y), text, fill="black", font=current_font)
        y += step

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


def create_test_screenshot_image() -> bytes:
    """
    Generate a synthetic mobile banking screenshot as PNG bytes.
    """
    img = Image.new("RGB", (600, 1000), color="#f0f0f0")
    draw = ImageDraw.Draw(img)

    font = _load_font(16, bold=False)
    font_small = _load_font(13, bold=False)
    font_bold = _load_font(20, bold=True)
    font_large = _load_font(24, bold=True)

    # Status bar
    draw.rectangle([0, 0, 600, 40], fill="#1a1a1a")
    draw.text((20, 10), "9:41", fill="white", font=font)
    draw.text((470, 10), "4G 100%", fill="white", font=font)

    y = 60
    draw.text((20, y), "CHASE", fill="#007bff", font=font_large)
    y += 35
    draw.text((20, y), "Total Balance", fill="gray", font=font)
    y += 22
    draw.text((20, y), "$3,456.78", fill="black", font=font_large)
    y += 50

    # Quick actions
    draw.rectangle([20, y, 180, y + 60], fill="#007bff")
    draw.text((75, y + 20), "Send", fill="white", font=font)
    draw.rectangle([210, y, 370, y + 60], fill="#28a745")
    draw.text((250, y + 20), "Deposit", fill="white", font=font)
    draw.rectangle([400, y, 560, y + 60], fill="#dc3545")
    draw.text((455, y + 20), "Pay", fill="white", font=font)
    y += 90

    draw.text((20, y), "Recent Transactions", fill="black", font=font_bold)
    y += 30

    transactions = [
        ("Today", "Starbucks", "-$4.95"),
        ("Yesterday", "Amazon", "-$29.99"),
        ("Mar 12", "Trader Joes", "-$67.32"),
        ("Mar 10", "Payroll Deposit", "+$2,800.00"),
        ("Mar 8", "Spotify", "-$9.99"),
    ]

    for date_str, merchant, amount in transactions:
        draw.rectangle([20, y, 560, y + 55], fill="white", outline="#dddddd")
        icon_color = "#28a745" if amount.startswith("+") else "#dc3545"
        draw.ellipse([35, y + 17, 55, y + 37], fill=icon_color)

        draw.text((70, y + 5), merchant, fill="black", font=font_bold)
        draw.text((70, y + 27), date_str, fill="gray", font=font_small)

        color = "green" if amount.startswith("+") else "red"
        draw.text((445, y + 15), amount, fill=color, font=font_bold)
        y += 60

    img_bytes = io.BytesIO()
    img.save(img_bytes, format="PNG")
    return img_bytes.getvalue()


# =========================================================
# ASSERTION / PRINT HELPERS
# =========================================================

def assert_basic_success_shape(result: Dict[str, Any]) -> None:
    """
    Basic structural validation for wrapper responses.
    """
    assert isinstance(result, dict), "Result must be a dict"
    assert "success" in result, "Missing 'success'"
    assert "metadata" in result, "Missing 'metadata'"
    assert "error" in result, "Missing 'error'"

    if result["success"]:
        assert "data" in result, "Missing 'data' for successful result"
        assert isinstance(result["data"], dict), "'data' must be a dict when success=True"


def print_result(result: Dict[str, Any], title: str):
    """
    Pretty print extraction result for human inspection.
    """
    print(f"\n{'=' * 70}")
    print(f"📄 {title}")
    print(f"{'=' * 70}")

    if not result.get("success", False):
        print(f"❌ Error: {result.get('error', 'Unknown error')}")
        print(f"Metadata: {result.get('metadata', {})}")
        return

    data = result.get("data", {})
    metadata = result.get("metadata", {})

    print(f"✅ Success! (took {metadata.get('duration_seconds', 0):.2f}s)")
    print(f"   Model: {metadata.get('model', 'unknown')}")
    print(f"   Tokens (cumulative): {metadata.get('total_tokens', 'N/A')}")
    print(f"   From cache: {metadata.get('from_cache', False)}")

    print(f"\n📊 DOCUMENT TYPE: {str(data.get('document_type', 'unknown')).upper()}")
    print(f"   Confidence: {str(data.get('confidence', 'unknown')).upper()}")
    print(f"   Merchant: {data.get('merchant', 'N/A')}")
    print(f"   Date: {data.get('date', 'N/A')}")
    print(f"   Currency: {data.get('currency', 'N/A')}")

    totals = data.get("totals", {})
    if isinstance(totals, dict) and any(v for v in totals.values()):
        print("\n💰 TOTALS:")
        for key, value in totals.items():
            if value:
                print(f"   {key.capitalize()}: {value}")

    transactions = data.get("possible_transactions", [])
    if isinstance(transactions, list) and transactions:
        print(f"\n📋 EXTRACTED TRANSACTIONS ({len(transactions)}):")
        for i, tx in enumerate(transactions[:5], start=1):
            conf = tx.get("confidence", "medium")
            emoji = "🟢" if conf == "high" else "🟡" if conf == "medium" else "🔴"
            amount_display = tx.get("amount") or "N/A"
            print(
                f"   {i}. {emoji} "
                f"{tx.get('date', 'N/A')} | "
                f"{tx.get('description', '')[:30]:30} | "
                f"{amount_display}"
            )

    extracted_text = data.get("extracted_text", "")
    if extracted_text:
        preview = extracted_text[:250] + "..." if len(extracted_text) > 250 else extracted_text
        print(f"\n📝 TEXT PREVIEW:\n{preview}")

    notes = data.get("notes", "")
    if notes:
        print(f"\n📌 Notes: {notes}")


# =========================================================
# TESTS
# =========================================================

def test_receipt_extraction():
    """
    Test synthetic receipt extraction.
    """
    print("\n🧪 TEST: Receipt Extraction")

    wrapper = create_vision_wrapper()
    receipt_bytes = create_test_receipt_image()

    result = wrapper.extract_receipt(receipt_bytes)
    assert_basic_success_shape(result)
    print_result(result, "RECEIPT EXTRACTION")

    assert result["success"], "Receipt extraction should succeed"
    data = result["data"]
    assert data["document_type"] in {"receipt", "unknown", "screenshot"}, f"Unexpected doc type: {data['document_type']}"
    assert "confidence" in data, "Missing confidence field"

    if data.get("possible_transactions"):
        print(f"✅ Found {len(data['possible_transactions'])} extracted items")


def test_bank_statement_extraction():
    """
    Test synthetic bank statement extraction.
    """
    print("\n🧪 TEST: Bank Statement Extraction")

    wrapper = create_vision_wrapper()
    statement_bytes = create_test_bank_statement_image()

    result = wrapper.extract_bank_statement(statement_bytes)
    assert_basic_success_shape(result)
    print_result(result, "BANK STATEMENT EXTRACTION")

    assert result["success"], "Bank statement extraction should succeed"


def test_screenshot_extraction():
    """
    Test synthetic mobile screenshot extraction.
    """
    print("\n🧪 TEST: Screenshot Extraction")

    wrapper = create_vision_wrapper()
    screenshot_bytes = create_test_screenshot_image()

    result = wrapper.extract_screenshot_text(screenshot_bytes)
    assert_basic_success_shape(result)
    print_result(result, "SCREENSHOT EXTRACTION")

    assert result["success"], "Screenshot extraction should succeed"


def test_different_models():
    """
    Compare default configured model against an optional second model.
    """
    print("\n🧪 TEST: Model Comparison")

    receipt_bytes = create_test_receipt_image()

    # Model from config
    wrapper_primary = create_vision_wrapper(model=Config.VISION_MODEL)
    result_primary = wrapper_primary.extract_receipt(receipt_bytes)
    assert_basic_success_shape(result_primary)

    print(f"\n📊 Primary Model ({wrapper_primary.model}):")
    print(f"   Success: {result_primary['success']}")
    print(f"   Time: {result_primary['metadata'].get('duration_seconds', 0):.2f}s")

    # Optional comparison model - only use if you explicitly want a second model
    optional_second_model = None

    if optional_second_model:
        try:
            wrapper_secondary = create_vision_wrapper(model=optional_second_model)
            result_secondary = wrapper_secondary.extract_receipt(receipt_bytes)
            assert_basic_success_shape(result_secondary)

            print(f"\n📊 Secondary Model ({wrapper_secondary.model}):")
            print(f"   Success: {result_secondary['success']}")
            print(f"   Time: {result_secondary['metadata'].get('duration_seconds', 0):.2f}s")
        except Exception as e:
            print(f"⚠️ Secondary model test skipped: {e}")
    else:
        print("ℹ️ No secondary comparison model configured; skipping second-model test.")


def test_batch_processing():
    """
    Test multi-image extraction in sequential and parallel mode.
    """
    print("\n🧪 TEST: Batch Processing")

    wrapper = create_vision_wrapper()

    images = [
        create_test_receipt_image(),
        create_test_bank_statement_image(),
        create_test_screenshot_image(),
    ]

    print("\n📊 Sequential processing...")
    start = time.time()
    results_seq = wrapper.extract_multiple_documents(images, parallel=False)
    seq_time = time.time() - start

    print(f"   Processed {len(results_seq)} images in {seq_time:.2f}s")
    success_count_seq = sum(1 for r in results_seq if r["success"])
    print(f"   Success rate: {success_count_seq}/{len(results_seq)}")

    for result in results_seq:
        assert_basic_success_shape(result)

    if len(images) > 1:
        print("\n📊 Parallel processing...")
        start = time.time()
        results_par = wrapper.extract_multiple_documents(images, parallel=True)
        par_time = time.time() - start

        print(f"   Processed {len(results_par)} images in {par_time:.2f}s")
        success_count_par = sum(1 for r in results_par if r["success"])
        print(f"   Success rate: {success_count_par}/{len(results_par)}")

        if par_time > 0:
            print(f"   Speedup: {seq_time / par_time:.1f}x")

        for result in results_par:
            assert_basic_success_shape(result)


def test_cache_functionality():
    """
    Test that cache hit behavior works and returns metadata flag.
    """
    print("\n🧪 TEST: Cache Functionality")

    wrapper = create_vision_wrapper()
    receipt_bytes = create_test_receipt_image()

    print("\n📊 First call (cache miss expected):")
    start = time.time()
    result1 = wrapper.extract_receipt(receipt_bytes, use_cache=True)
    time1 = time.time() - start
    assert_basic_success_shape(result1)
    print(f"   Time: {time1:.2f}s")

    print("\n📊 Second call (cache hit expected):")
    start = time.time()
    result2 = wrapper.extract_receipt(receipt_bytes, use_cache=True)
    time2 = time.time() - start
    assert_basic_success_shape(result2)
    print(f"   Time: {time2:.4f}s")

    assert result2.get("metadata", {}).get("from_cache", False), "Second call should come from cache"
    if time2 > 0:
        print(f"✅ Cache speedup: {time1 / time2:.1f}x")

    print("\n📊 Cache bypass:")
    start = time.time()
    result3 = wrapper.extract_receipt(receipt_bytes, use_cache=False)
    time3 = time.time() - start
    assert_basic_success_shape(result3)
    print(f"   Time: {time3:.2f}s")

    assert not result3.get("metadata", {}).get("from_cache", False), "Cache bypass should not report from_cache=True"


def test_error_handling():
    """
    Test graceful failure on bad inputs.
    """
    print("\n🧪 TEST: Error Handling")

    wrapper = create_vision_wrapper()

    print("\n📊 Non-existent file:")
    result_missing = wrapper.extract_receipt("nonexistent_image.jpg")
    assert_basic_success_shape(result_missing)
    print(f"   Success: {result_missing['success']}")
    print(f"   Error: {result_missing.get('error', 'N/A')}")
    assert not result_missing["success"], "Should fail with non-existent file"

    print("\n📊 Invalid bytes:")
    invalid_bytes = b"this is not a valid image payload"
    result_invalid = wrapper.extract_receipt(invalid_bytes)
    assert_basic_success_shape(result_invalid)
    print(f"   Success: {result_invalid['success']}")
    print(f"   Error: {result_invalid.get('error', 'N/A')}")
    assert not result_invalid["success"], "Should fail gracefully with invalid input bytes"


def test_custom_prompt():
    """
    Test custom prompt without changing the required schema.
    """
    print("\n🧪 TEST: Custom Prompt")

    wrapper = create_vision_wrapper()
    receipt_bytes = create_test_receipt_image()

    result_standard = wrapper.extract_receipt(receipt_bytes)
    assert_basic_success_shape(result_standard)

    custom_prompt = (
        "Focus carefully on merchant, date, subtotal, tax, and total. "
        "If line items are visible, include them in possible_transactions. "
        "Do not change the required JSON schema."
    )

    result_custom = wrapper.extract_financial_document(
        receipt_bytes,
        task_type="receipt",
        custom_prompt=custom_prompt,
    )
    assert_basic_success_shape(result_custom)

    print("\n📊 Standard vs Custom:")
    print(f"   Standard success: {result_standard['success']}")
    print(f"   Custom success:   {result_custom['success']}")
    print(f"   Standard confidence: {result_standard.get('data', {}).get('confidence', 'N/A')}")
    print(f"   Custom confidence:   {result_custom.get('data', {}).get('confidence', 'N/A')}")

    assert result_standard["success"] and result_custom["success"], "Both extractions should succeed"


def test_stats_and_cache():
    """
    Test wrapper stats and cache management.
    """
    print("\n🧪 TEST: Stats and Cache")

    wrapper = create_vision_wrapper()
    receipt_bytes = create_test_receipt_image()

    for _ in range(3):
        wrapper.extract_receipt(receipt_bytes)

    stats = wrapper.get_stats()
    print("\n📊 Statistics:")
    print(f"   Model: {stats['model']}")
    print(f"   Call count: {stats['call_count']}")
    print(f"   Total tokens: {stats['total_tokens_used']}")
    print(f"   Estimated cost: ${stats['estimated_cost']:.6f}")
    print(f"   Cache size: {stats['cache_size']}")

    assert stats["call_count"] >= 1, "Should record calls"

    print("\n📊 Clearing cache...")
    wrapper.clear_cache()
    stats_after = wrapper.get_stats()
    print(f"   Cache size after clear: {stats_after['cache_size']}")
    assert stats_after["cache_size"] == 0, "Cache should be empty after clear"


# =========================================================
# RUNNERS
# =========================================================

def run_all_tests():
    """
    Run the full test suite.
    """
    print("=" * 80)
    print("👁️👁️👁️ VISION LLM WRAPPER COMPREHENSIVE TEST SUITE 👁️👁️👁️")
    print("=" * 80)

    if not Config.GROQ_API_KEY:
        print("\n❌ GROQ_API_KEY not found in config/.env. Tests skipped.")
        return

    test_receipt_extraction()
    test_bank_statement_extraction()
    test_screenshot_extraction()
    test_different_models()
    test_batch_processing()
    test_cache_functionality()
    test_error_handling()
    test_custom_prompt()
    test_stats_and_cache()

    print("\n" + "=" * 80)
    print("✅ ALL VISION LLM WRAPPER TESTS COMPLETE")
    print("=" * 80)


def run_quick_tests():
    """
    Run a smaller, cheaper subset of tests.
    """
    print("=" * 80)
    print("👁️ VISION LLM WRAPPER QUICK TESTS")
    print("=" * 80)

    if not Config.GROQ_API_KEY:
        print("\n❌ GROQ_API_KEY not found in config/.env. Tests skipped.")
        return

    test_receipt_extraction()
    test_cache_functionality()
    test_error_handling()

    print("\n" + "=" * 80)
    print("✅ QUICK TESTS COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--quick":
        run_quick_tests()
    else:
        run_all_tests()