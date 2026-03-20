"""
🏦 PDF PARSER (Text -> Transactions)

Rules-first parser with LLM fallback (Groq) for messy / ambiguous lines.

Design:
- Deterministic regex parsing handles most cases quickly.
- LLM is called ONLY when:
  - category is "other" OR
  - transaction_type is unclear OR
  - we can't confidently parse merchant/category from description

Input:
- raw_text (string) from a PDF extraction step (you can add that later)

Output:
- ParsedResult { transactions, skipped_lines, errors, llm_calls }
"""

# Raw PDF Text
#     ↓
# _candidate_lines() → Filter to probable transaction lines
#     ↓
# For each line:
#     ↓
# _parse_line() → Extract date, amount, description
#     ↓
# _infer_type() → Rules-based type detection (fast!)
#     ↓
# _guess_category() → Keyword matching (fast!)
#     ↓
# Is category "other" or low confidence?
#     ├── NO  → ✅ Use rule-based result
#     └── YES → 🤖 Call LLM (expensive but accurate)
#               ↓
#               Validate LLM response
#               ↓
#               Apply safe overrides
#     ↓
# Create Transaction object
#     ↓
# Return ParsedResult

from __future__ import annotations
import re
import json
from dataclasses import dataclass
from datetime import date
from typing import Any, Dict, List, Optional, Tuple

from schemas.transaction import Transaction, TransactionType, Category
from utils.llm_wrapper import llm_wrapper
from pathlib import Path
import fitz

# -------------------------
# Result container
# -------------------------
@dataclass
class ParsedResult:
    transactions: List[Transaction]
    skipped_lines: List[str]
    errors: List[str]
    llm_calls: int

# -------------------------
# Config / constants
# -------------------------
ALLOWED_CATEGORIES = {
    "food","groceries","dining_out","coffee",
    "housing","rent","utilities","internet","phone",
    "transport","gas","uber","public_transit",
    "entertainment","streaming","games","movies",
    "shopping","clothing","electronics","amazon",
    "education","tuition","books","supplies",
    "health","medical","gym","pharmacy",
    "personal_care","haircut","cosmetics",
    "travel","flights","hotels",
    "income","salary","gift","refund",
    "transfer","savings","investment",
    "other"
}

# Data Patterns (deterministic is best here)
DATA_PATTERNS = [
    # 01/31/2026 or 1/3/2026
    r"(?P<mm>\d{1,2})/(?P<dd>\d{1,2})/(?P<yyyy>\d{4})",
    # 2026-01-31
    r"(?P<yyyy>\d{4})-(?P<mm>\d{1,2})-(?P<dd>\d{1,2})",
    # 31-Jan-2026
    r"(?P<dd>\d{1,2})-(?P<mon>[A-Za-z]{3})-(?P<yyyy>\d{4})",
]

MONTH_MAP = {
    "jan": 1, "feb": 2, "mar": 3, "apr": 4, "may": 5, "jun": 6,
    "jul": 7, "aug": 8, "sep": 9, "oct": 10, "nov": 11, "dec": 12,
}

# Amount patterns:
# -123.45, 123.45, $123.45, (123.45)
AMOUNT_RE = re.compile(
    r"""
    (?P<paren_open>\()?\s*                      # optional opening parenthesis
    (?P<prefix>[-+])?\s*                        # optional leading sign
    \$?\s*                                      # optional $
    (?P<number>\d{1,3}(?:,\d{3})*|\d+)          # number with optional commas
    (?P<decimal>\.\d{2})?                       # optional .xx
    \s*(?P<suffix>[-+])?\s*                     # optional trailing sign (e.g., 500.00-)
    (?P<crdr>\bCR\b|\bDR\b)?\s*                 # optional CR/DR markers
    (?P<paren_close>\))?                        # optional closing parenthesis
    """,
    re.VERBOSE | re.IGNORECASE,
)

# quick keyword mapping (high precision, not exhaustive)
CATEGORY_KEYWORDS: List[Tuple[str, str]] = [
    ("walmart", "groceries"),
    ("target", "shopping"),
    ("whole foods", "groceries"),
    ("trader joe", "groceries"),
    ("costco", "groceries"),
    ("kroger", "groceries"),
    ("shell", "gas"),
    ("chevron", "gas"),
    ("exxon", "gas"),
    ("uber", "uber"),
    ("lyft", "uber"),
    ("netflix", "streaming"),
    ("spotify", "streaming"),
    ("hulu", "streaming"),
    ("amazon", "amazon"),
    ("prime", "amazon"),
    ("apple.com", "electronics"),
    ("best buy", "electronics"),
    ("rent", "rent"),
    ("mortgage", "housing"),
    ("electric", "utilities"),
    ("water", "utilities"),
    ("insurance", "housing"),
    ("salary", "salary"),
    ("payroll", "salary"),
    ("refund", "refund"),
    ("interest", "investment"),
]

INCOME_KEYWORDS = [
    # Paychecks & direct deposits
    "payroll", "salary", "direct deposit", "direct dep",
    "ach credit", "paycheck", "wages", "compensation",
    
    # Freelance / gig income
    "stripe payout", "square payout", "venmo credit",
    "paypal credit", "zelle credit", "cash app credit",
    "doordash payout", "uber payout", "lyft payout",
    
    # Refunds & reversals
    "refund", "reversal", "return credit", "credit adjustment",
    "chargeback", "dispute credit",
    
    # Interest & investment returns
    "interest paid", "interest credit", "dividend",
    "cashback", "cash back", "rewards redemption",
    "bonus credit", "rebate",
    
    # Transfers IN (explicit)
    "transfer from", "deposit from", "incoming wire",
    "wire in", "incoming transfer",
]

TRANSFER_KEYWORDS = [
    # Card payments (highest priority — must come first in logic)
    "payment thank you", "payment received", "payment posted",
    "autopay payment", "auto pay", "card payment",
    "bill payment", "online payment", "minimum payment",
    "statement payment",

    # Peer-to-peer
    "zelle", "venmo", "paypal", "cash app", "square cash",
    "apple pay", "google pay", "samsung pay",

    # Bank transfers
    "transfer to", "transfer out", "online transfer",
    "mobile transfer", "xfer", "tfr",
    "wire transfer", "wire out", "outgoing wire",

    # ACH (neutral direction — context dependent)
    "ach debit", "ach transfer",

    # Savings moves
    "to savings", "to checking", "to investment",
    "sweep", "auto save",

    # Loan / rent payments
    "mortgage payment", "loan payment", "student loan",
    "rent payment",
]

def _has_any(text: str, keywords: list[str]) -> bool:
    t = (text or "").lower()
    return any(k in t for k in keywords)


def detect_statement_mode(raw_text: str) -> str:
    t = (raw_text or "").lower()
    if any(k in t for k in ["credit card", "cardmember", "card account", "statement balance"]):
        return "credit_card"
    return "bank_account"

# -------------------------
# Public API
# -------------------------

def parse_bank_text_to_transactions(
    raw_text: str,
    student_id: str,
    *,
    source: str = "pdf",
    use_llm_fallback: bool = True,
    max_llm_calls: int = 20,
) -> ParsedResult:
    """
    Convert extracted statement text to Transactions.
    Handles credit-card and bank-account modes; merchant always tracked.
    """
    transactions, skipped, errors = [], [], []
    llm_calls = 0

    if not raw_text or not raw_text.strip():
        return ParsedResult([], [], ["Empty raw_text input"], 0)

    statement_mode = detect_statement_mode(raw_text) # <- new
    lines = _candidate_lines(raw_text)

    for idx, line in enumerate(lines):
        merchant_value = None
        try:
            parsed = _parse_line(line)
            if not parsed:
                skipped.append(line)
                continue

            txn_date, amount_signed, desc = parsed
            amount_abs = abs(amount_signed)

            # 1) Rules inference with mode
            txn_type_rules = _infer_type(line, amount_signed, statement_mode=statement_mode)
            category_rules, cat_conf = _guess_category(desc)

            # merchant guess
            if desc:
                mg = desc.split(" ")[0] if " " in desc else desc.split(" | ")[0]
                merchant_value = mg.strip(" -|").strip()[:30] or None

            txn_type_final = txn_type_rules or TransactionType.EXPENSE
            category_final = category_rules if category_rules in ALLOWED_CATEGORIES else "other"
            parser_path, llm_conf = "rules", "low"

            # 2) LLM fallback
            if use_llm_fallback and llm_calls < max_llm_calls:
                needs_llm = category_final == "other" or txn_type_rules is None or cat_conf == "low"
                if needs_llm:
                    llm_out = _llm_classify_line(
                        line=line, description=desc,
                        amount_signed=amount_signed, date_str=str(txn_date)
                    )
                    llm_calls += 1
                    parser_path = "llm_fallback"

                    # ✅ LLM can only override category freely
                    cat = (llm_out.get("category") or "").lower()
                    if cat in ALLOWED_CATEGORIES:
                        category_final = cat

                    # ✅ LLM can only override transaction_type if rules were UNCERTAIN
                    # Never let LLM downgrade a confident TRANSFER or INCOME to EXPENSE
                    lt = _safe_txn_type(llm_out.get("transaction_type"))
                    if txn_type_rules is None and lt:
                        # Rules had no opinion — trust LLM with evidence check
                        if lt == TransactionType.INCOME and _has_any(line + desc, INCOME_KEYWORDS):
                            txn_type_final = lt
                        elif lt == TransactionType.TRANSFER and _has_any(line + desc, TRANSFER_KEYWORDS):
                            txn_type_final = lt
                        elif lt == TransactionType.EXPENSE:
                            txn_type_final = lt
                    # else: rules were confident — keep txn_type_final as-is, don't let LLM override

                    mv = llm_out.get("merchant")
                    if isinstance(mv, str) and mv.strip():
                        merchant_value = mv.strip()[:30]

                    llm_conf = llm_out.get("confidence", "low")
                    parser_path = "llm_fallback"

            confidence_final = calculate_confidence(parser_path, cat_conf, llm_conf)

            raw_payload = {
                "raw_line": line,
                "parser": parser_path,
                "rules": {
                    "category": category_rules,
                    "category_conf": cat_conf,
                    "transaction_type": txn_type_rules.value if txn_type_rules else None,
                    "merchant_guess": merchant_value,
                },
                **({"llm": {"confidence": llm_conf, "used": True}} if parser_path == "llm_fallback" else {})
            }

            tx = Transaction(
                transaction_id=f"txn_{student_id}_{idx}_{txn_date.isoformat()}_{int(amount_abs*100)}",
                student_id=student_id,
                amount=amount_abs,
                transaction_type=txn_type_final,
                date=txn_date,
                description=desc,
                merchant=merchant_value,
                category=category_final,
                payment_method="other",
                source=source,
                confidence=confidence_final,
                raw_data=raw_payload,
                notes="",
                tags=[],
            )
            transactions.append(tx)

        except Exception as e:
            errors.append(f"Line {idx}: {type(e).__name__}: {e} :: {line}")

    return ParsedResult(transactions, skipped, errors, llm_calls)


# -------------------------
# Parsing helpers
# -------------------------

def _candidate_lines(raw_text: str) -> List[str]:
    """
    Heuristic: break into lines and keep those that look like statement rows.
    We keep lines containing an amount and a date-like pattern.
    """
    out: List[str]= []
    for ln in raw_text.splitlines():
        line = " ".join(ln.strip().split())
        if not line:
            continue
        if _find_date(line) is None:
            continue
        if _find_amount(line) is None:
            continue
        out.append(line)
    return out

def _parse_line(line: str) -> Optional[Tuple[date, float, str]]:
    """Returns (date, signed_amount, description) or None"""
    d = _find_date(line)
    if d is None:
        return None
    
    amt = _find_amount(line)
    if amt is None:
        return None
    
    # description: remove date and amount tokens crudely
    desc = line
    desc = _remove_date_from_text(desc)
    desc = _remove_amount_from_text(desc)
    desc = desc.strip("-|")

    return d, amt, desc

def _find_date(text: str) -> Optional[date]:
    for pat in DATA_PATTERNS:
        m = re.search(pat, text)
        if not m:
            continue
        gd = m.groupdict()
        try:
            yyyy = int(gd["yyyy"])
            mm = int(gd.get('mm') or MONTH_MAP.get((gd.get("mon") or "").lower(), 0))
            dd = int(gd["dd"])
            if mm<=0:
                return None
            return date(yyyy, mm, dd)
        except Exception:
            return None
    return None


def _find_amount(text: str) -> Optional[float]:
    """
    Extract the last amount-like token and return it as a signed float.

    Handles:
      - -500.00, $-500.00, -$500.00
      - (500.00), ($500.00)
      - 500.00-  (trailing minus)
      - 500.00 CR / 500.00 DR
      - 1,200.50
    """
    if not text:
        return None

    # normalize weird spaces often found in PDFs
    text = text.replace("\u202f", " ").replace("\xa0", " ")

    matches = list(AMOUNT_RE.finditer(text))
    if not matches:
        return None

    # pick the last match (most statements place amount at end of row)
    m = matches[-1]

    num = (m.group("number") or "").replace(",", "")
    dec = m.group("decimal") or ""
    if not num:
        return None

    try:
        val = float(f"{num}{dec}")
    except ValueError:
        return None

    # --- Determine sign ---
    is_negative = False

    # 1) Parentheses mean negative in most statements
    if m.group("paren_open") and m.group("paren_close"):
        is_negative = True

    # 2) Leading sign
    if (m.group("prefix") or "") == "-":
        is_negative = True
    elif (m.group("prefix") or "") == "+":
        is_negative = False

    # 3) Trailing sign (e.g. 500.00-)
    if (m.group("suffix") or "") == "-":
        is_negative = True
    elif (m.group("suffix") or "") == "+":
        is_negative = False

    # 4) CR/DR markers (if present, they usually override)
    crdr = (m.group("crdr") or "").upper()
    if crdr == "DR":
        is_negative = True
    elif crdr == "CR":
        is_negative = False

    return -val if is_negative else val

def _remove_date_from_text(text: str) -> str:
    for pat in DATA_PATTERNS:
        text = re.sub(pat, "", text)
    return " ".join(text.split())

def _remove_amount_from_text(text: str) -> str:
    # Remove the last amount occurrence only (usually statement column at end)
    matches = list(AMOUNT_RE.finditer(text))
    if not matches:
        return text
    m = matches[-1]
    start, end = m.span()
    return (text[:start] + text[end:]).strip()

def _normalize_text(s: str) -> str:
    """
    Normalize a statement line for keyword matching:
    - lowercase
    - replace punctuation with spaces
    - collapse whitespace
    """
    s = (s or "").lower()
    s = re.sub(r"[^a-z0-9]+", " ", s)   # punctuation -> space
    s = " ".join(s.split())            # collapse spaces
    return s

def _normalize_keywords(keywords: List[str]) -> List[str]:
    """Lowercase + strip + collapse spaces inside keywords too."""
    out = []
    for k in keywords:
        k2 = _normalize_text(k)
        if k2:
            out.append(k2)
    return out

# Pre-normalize keyword lists once (recommended)
_TRANSFER_KWS = None
_INCOME_KWS = None

def _infer_type(
    line: str,
    amount_signed: float,
    *,
    statement_mode: str = "bank_account"  # "credit_card" | "bank_account"
) -> TransactionType:
    """
    Rules-based inference for TransactionType with robust matching.

    credit_card mode:
      - positive = purchases (expense)
      - negative = payments/credits (transfer) unless refund/cashback/etc (income)

    bank_account mode:
      - positive = deposits (income)
      - negative = withdrawals (expense)
    """
    global _TRANSFER_KWS, _INCOME_KWS

    # Normalize line once
    lower = _normalize_text(line)
    lower_raw = line.lower()

    # Normalize keyword lists once
    if _TRANSFER_KWS is None:
        _TRANSFER_KWS = _normalize_keywords(TRANSFER_KEYWORDS)
    if _INCOME_KWS is None:
        _INCOME_KWS = _normalize_keywords(INCOME_KEYWORDS)

    # ------------------------------------------------------------------
    # 0) VERY HIGH PRIORITY: Card payments should ALWAYS be TRANSFER
    #    This fixes "PAYMENT THANK YOU" reliably (even with punctuation)
    # ------------------------------------------------------------------
    payment_patterns = [
        "payment thank you",
        "payment received",
        "autopay",
        "auto pay",
        "card payment",
        "bill payment",
        "online payment",
        "pmt rec",
        "payment rec",
    ]
    for p in payment_patterns:
        if p in lower_raw or _normalize_text(p) in lower:  # ← check both
            return TransactionType.TRANSFER

    # ------------------------------------------------------------------
    # 1) Transfers next (but avoid overly generic tokens like "paid")
    # ------------------------------------------------------------------
    # NOTE: if you keep "paid" in TRANSFER_KEYWORDS, it will match too much.
    # Better to remove "paid" or require context like "paid to" etc.
    for k in _TRANSFER_KWS:
        if k and k in lower:
            return TransactionType.TRANSFER

    # ------------------------------------------------------------------
    # 2) Income indicators (refunds, deposits, cashback, interest)
    # ------------------------------------------------------------------
    for k in _INCOME_KWS:
        if k and k in lower:
            return TransactionType.INCOME

    # ------------------------------------------------------------------
    # 3) Sign-based fallback depends on statement mode
    # ------------------------------------------------------------------
    if statement_mode == "credit_card":
        # For credit cards:
        # - positive amounts are typically purchases (expense)
        # - negative are typically payments/credits (transfer)
        return TransactionType.EXPENSE if amount_signed > 0 else TransactionType.TRANSFER

    # Bank account:
    return TransactionType.INCOME if amount_signed > 0 else TransactionType.EXPENSE

def _guess_category(description: str) -> Tuple[str, str]:
    """
    Returns (category, confidence: high|medium|low)
    """
    d = (description or "").lower()

    for key, cat in CATEGORY_KEYWORDS:
        if key in d:
            return cat, "high"

    # light heuristic
    if any(k in d for k in ["uber", "lyft"]):
        return "uber", "high"
    if any(k in d for k in ["rent", "lease"]):
        return "rent", "high"
    if any(k in d for k in ["grocery", "market"]):
        return "groceries", "medium"

    return "other", "low"



# -------------------------
# LLM fallback
# -------------------------

def _llm_classify_line(
        *,
        line: str,
        description: str,
        amount_signed: float,
        date_str: str
) -> Dict[str, Any]:
    """
    Ask Groq to classify a tricky statement line.
    Returns dict with keys: category, transaction_type, merchant, confidence
    """
    system_prompt = (
        "You are a bank statement line classifier.\n"
        "Return ONLY valid JSON with keys:\n"
        "category, transaction_type, merchant, confidence.\n"
        "category MUST be one of the allowed categories list.\n"
        "transaction_type MUST be one of: expense, income, transfer.\n"
        "confidence MUST be: high, medium, low.\n"
        "No extra keys, no explanations."
    )

    user_prompt = f"""
LINE: {line}
DESCRIPTION_CLEANED: {description}
DATE: {date_str}
AMOUNT_SIGNED: {amount_signed}
ALLOWED_CATEGORIES: {sorted(ALLOWED_CATEGORIES)}
"""
    
    res = llm_wrapper.generate_structured_response(system_prompt=system_prompt,
                                                   user_prompt=user_prompt,
                                                   response_format='{"category":"other","transaction_type":"expense","merchant":null,"confidence":"low"}'
    )

    data = res.get("data") or {}

    # enforce safety
    cat = data.get("category", "other")
    if cat not in ALLOWED_CATEGORIES:
        cat = "other"

    transaction_type = data.get("transaction_type", "expense")
    if transaction_type not in {"expense", "income", "transfer"}:
        transaction_type = "expense"

    conf = data.get("confidence", "low")
    if conf not in {"high", "medium", "low"}:
        conf = "low"
    
    merchant = data.get("merchant", None)

    return {"category": cat, "transaction_type": transaction_type, "merchant": merchant, "confidence": conf}

def _safe_txn_type(trans_type: Any) -> Optional[TransactionType]:
    """
    Convert str (expense|income|transfer) into TransactionType enum safely.
    """
    if isinstance(trans_type, TransactionType):
        return trans_type
    if isinstance(trans_type, str):
        t = trans_type.strip().lower()
        if t == "expense":
            return TransactionType.EXPENSE
        if t == "income":
            return TransactionType.INCOME
        if t == "transfer":
            return TransactionType.TRANSFER
    return None

def detect_bank_format(raw_text: str) -> str:
    """
    Guess the bank from raw statement text.
    Returns a slug like 'chase', 'bofa', 'zolve', etc.
    """
    text = (raw_text or "").lower()
    head = text[:2000]  
    # Ordered list: first match wins (most specific first)
    banks = [
        ("chase", ["chase", "jpmorgan", "chase.com"]),
        ("bofa", ["bank of america", "bofa", "bankamerica", "boa"]),
        ("wells_fargo", ["wells fargo", "wellsfargo"]),
        ("zolve", ["zolve", "zolve.com"]),
        ("dcu", ["digital federal", "dcu", "dcu.org"]),
        ("citi", ["citibank", "citi", "citi.com"]),
        ("capital_one", ["capital one", "capitalone"]),
        ("discover", ["discover bank", "discover"]),
        ("ally", ["ally bank", "ally"]),
        ("chime", ["chime"]),
        ("usbank", ["u.s. bank", "usbank", "us bank"]),
        ("pnc", ["pnc bank", "pnc"]),
        ("td", ["td bank", "tdbank"]),
    ]

    for slug, keywords in banks:
        if any(k in head for k in keywords):
            return slug
    return "unknown"

def calculate_confidence(parser: str, cat_conf: str, llm_conf: str) -> str:
    """Overall confidence based on parsing path"""
    if parser == "rules" and cat_conf == "high":
        return "high"
    if parser == "llm_fallback" and llm_conf == "high":
        return "high"
    if parser == "llm_fallback" and llm_conf == "medium":
        return "medium"
    return "low"

def deduplicate_transactions(transactions: List[Transaction]) -> List[Transaction]:
    """Remove duplicates from overlapping statements"""
    seen = set()
    unique = []
    for tx in transactions:
        key = (tx.date, tx.amount, tx.merchant)
        if key not in seen:
            seen.add(key)
            unique.append(tx)
    return unique

def extract_text_from_pdf_bytes(pdf_bytes: bytes) -> str:
    """
    Extract raw text from PDF bytes using PyMuPDF.
    """
    text_parts = []
    doc = fitz.open(stream=pdf_bytes, filetype="pdf")
    try:
        for page in doc:
            text_parts.append(page.get_text("text"))
    finally:
        doc.close()
    return "\n".join(text_parts).strip()