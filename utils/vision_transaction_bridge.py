"""
🔄 VISION TRANSACTION BRIDGE - Convert vision LLM output to Transaction objects

Why this file exists
--------------------
vision_llm_wrapper.py returns structured JSON from images, for example:
- document_type
- merchant
- date
- totals
- possible_transactions

But the rest of the app works with List[Transaction] objects.

This bridge:
1. takes structured vision output
2. normalizes dates, amounts, merchants
3. infers transaction types
4. maps simple categories
5. creates Transaction objects
6. returns a clean result object

Design principles
-----------------
- Single responsibility: conversion only
- Forgiving: skips bad items, does not crash the pipeline
- Deterministic: same input gives same output
- Document-aware: receipt vs statement behavior differs
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
import re

from schemas.transaction import Transaction, TransactionType


# # =========================================================
# # RESULT MODEL
# # =========================================================

# @dataclass
# class VisionTransactionResult:
#     """
#     Result of converting vision output to Transaction objects.

#     Fields
#     ------
#     transactions:
#         Successfully converted Transaction objects

#     skipped_items:
#         Raw items that could not be converted, with skip reasons

#     errors:
#         Non-fatal bridge-level errors for debugging

#     source_document_type:
#         Original document type from vision wrapper
#     """
#     transactions: List[Transaction]
#     skipped_items: List[Dict[str, Any]]
#     errors: List[str]
#     source_document_type: str

#     def to_dict(self) -> Dict[str, Any]:
#         return {
#             "transactions": [t.model_dump() for t in self.transactions],
#             "skipped_items": self.skipped_items,
#             "errors": self.errors,
#             "source_document_type": self.source_document_type,
#             "transaction_count": len(self.transactions),
#         }


# # =========================================================
# # SIMPLE CATEGORY MAPPING
# # =========================================================

# """
# 📊 ULTIMATE CATEGORY MAPPING - Complete transaction categorization system
# Covers 500+ merchants and patterns across 50+ categories for perfect financial tracking
# """

# from typing import List, Tuple

# # =========================================================
# # 🏠 HOUSING & UTILITIES
# # =========================================================

# CATEGORY_KEYWORDS: List[Tuple[str, str]] = [

#     # === Rent / Housing ===
#     ("rent", "rent"),
#     ("rental", "rent"),
#     ("apartment", "rent"),
#     ("lease", "rent"),
#     ("landlord", "rent"),
#     ("property management", "rent"),
#     ("zillow", "rent"),
#     ("apartments.com", "rent"),
#     ("realpage", "rent"),
#     ("rentcafe", "rent"),
#     ("resident portal", "rent"),
    
#     # === Mortgage ===
#     ("mortgage", "mortgage"),
#     ("home loan", "mortgage"),
#     ("rocket mortgage", "mortgage"),
#     ("quicken loans", "mortgage"),
#     ("loan payment", "mortgage"),
#     ("wells fargo mortgage", "mortgage"),
#     ("chase mortgage", "mortgage"),
#     ("bank of america mortgage", "mortgage"),
    
#     # === Utilities ===
#     ("electric", "utilities"),
#     ("electricity", "utilities"),
#     ("power", "utilities"),
#     ("gas bill", "utilities"),
#     ("natural gas", "utilities"),
#     ("water", "utilities"),
#     ("sewer", "utilities"),
#     ("trash", "utilities"),
#     ("waste management", "utilities"),
#     ("republic services", "utilities"),
#     ("waste", "utilities"),
    
#     # === Internet ===
#     ("internet", "internet"),
#     ("xfinity", "internet"),
#     ("comcast", "internet"),
#     ("spectrum", "internet"),
#     ("charter", "internet"),
#     ("cox", "internet"),
#     ("verizon fios", "internet"),
#     ("att fiber", "internet"),
#     ("google fiber", "internet"),
#     ("centurylink", "internet"),
#     ("frontier", "internet"),
#     ("mediacom", "internet"),
#     ("optimum", "internet"),
#     ("suddenlink", "internet"),
#     ("wifi", "internet"),
#     ("broadband", "internet"),
    
#     # === Phone ===
#     ("phone", "phone"),
#     ("verizon wireless", "phone"),
#     ("att wireless", "phone"),
#     ("tmobile", "phone"),
#     ("sprint", "phone"),
#     ("cricket", "phone"),
#     ("metro pcs", "phone"),
#     ("boost mobile", "phone"),
#     ("mint mobile", "phone"),
#     ("google fi", "phone"),
#     ("visible", "phone"),
#     ("us cellular", "phone"),
#     ("straight talk", "phone"),
#     ("cell phone", "phone"),
#     ("mobile bill", "phone"),
    
#     # === Insurance ===
#     ("insurance", "insurance"),
#     ("geico", "insurance"),
#     ("progressive", "insurance"),
#     ("state farm", "insurance"),
#     ("allstate", "insurance"),
#     ("liberty mutual", "insurance"),
#     ("nationwide", "insurance"),
#     ("farmers", "insurance"),
#     ("travelers", "insurance"),
#     ("usaa", "insurance"),
#     ("aaa insurance", "insurance"),
#     ("aarp", "insurance"),
#     ("the general", "insurance"),
#     ("root insurance", "insurance"),
#     ("lemonade", "insurance"),
#     ("health insurance", "insurance"),
#     ("dental insurance", "insurance"),
#     ("vision insurance", "insurance"),
#     ("life insurance", "insurance"),
#     ("renters insurance", "insurance"),
#     ("homeowners insurance", "insurance"),
#     ("car insurance", "insurance"),
#     ("auto insurance", "insurance"),
# ]


# # =========================================================
# # 🛒 GROCERIES & SUPERMARKETS
# # =========================================================

# GROCERY_KEYWORDS = [
#     # National chains
#     ("walmart", "groceries"),
#     ("walmart supercenter", "groceries"),
#     ("walmart neighborhood market", "groceries"),
#     ("target", "groceries"),
#     ("costco", "groceries"),
#     ("sam's club", "groceries"),
#     ("bj's wholesale", "groceries"),
    
#     # Traditional supermarkets
#     ("kroger", "groceries"),
#     ("ralphs", "groceries"),
#     ("fred meyer", "groceries"),
#     ("frys", "groceries"),
#     ("king soopers", "groceries"),
#     ("smith's", "groceries"),
#     ("qfc", "groceries"),
#     ("food 4 less", "groceries"),
#     ("pick n save", "groceries"),
#     ("metro market", "groceries"),
#     ("dillons", "groceries"),
#     ("baker's", "groceries"),
#     ("jay c", "groceries"),
#     ("gerbes", "groceries"),
#     ("owens", "groceries"),
    
#     # Specialty & organic
#     ("whole foods", "groceries"),
#     ("whole foods market", "groceries"),
#     ("trader joe", "groceries"),
#     ("trader joes", "groceries"),
#     ("sprouts", "groceries"),
#     ("sprouts farmers market", "groceries"),
#     ("natural grocers", "groceries"),
#     ("fresh market", "groceries"),
#     ("earth fare", "groceries"),
#     ("moms organic", "groceries"),
    
#     # Regional chains
#     ("wegmans", "groceries"),
#     ("publix", "groceries"),
#     ("heb", "groceries"),
#     ("central market", "groceries"),
#     ("meijer", "groceries"),
#     ("hy-vee", "groceries"),
#     ("giant eagle", "groceries"),
#     ("shoprite", "groceries"),
#     ("stop & shop", "groceries"),
#     ("food lion", "groceries"),
#     ("harris teeter", "groceries"),
#     ("giant food", "groceries"),
#     ("martin's", "groceries"),
#     ("winn-dixie", "groceries"),
#     ("bi-lo", "groceries"),
#     ("ingles", "groceries"),
#     ("lowes foods", "groceries"),
#     ("stater bros", "groceries"),
#     ("raley's", "groceries"),
#     ("bel air", "groceries"),
#     ("nob hill", "groceries"),
#     ("safeway", "groceries"),
#     ("albertsons", "groceries"),
#     ("vons", "groceries"),
#     ("jewel-osco", "groceries"),
#     ("acme", "groceries"),
#     ("shaws", "groceries"),
#     ("star market", "groceries"),
#     ("carrs", "groceries"),
#     ("randalls", "groceries"),
#     ("tom thumb", "groceries"),
    
#     # Discount grocers
#     ("aldi", "groceries"),
#     ("lidl", "groceries"),
#     ("save-a-lot", "groceries"),
#     ("foodmaxx", "groceries"),
#     ("winco", "groceries"),
#     ("winco foods", "groceries"),
#     ("grocery outlet", "groceries"),
#     ("foods co", "groceries"),
    
#     # International grocers
#     ("hmart", "groceries"),
#     ("ranch 99", "groceries"),
#     ("99 ranch", "groceries"),
#     ("h-mart", "groceries"),
#     ("assi plaza", "groceries"),
#     ("patel brothers", "groceries"),
#     ("subzi mandi", "groceries"),
#     ("mi tienda", "groceries"),
#     ("cardenas", "groceries"),
#     ("northgate", "groceries"),
#     ("el super", "groceries"),
#     ("vallarta", "groceries"),
    
#     # Delivery services
#     ("instacart", "groceries"),
#     ("amazon fresh", "groceries"),
#     ("amazon grocery", "groceries"),
#     ("freshdirect", "groceries"),
#     ("shipt", "groceries"),
#     ("misfits market", "groceries"),
#     ("imperfect foods", "groceries"),
#     ("hungryroot", "groceries"),
#     ("thrive market", "groceries"),
# ]

# CATEGORY_KEYWORDS.extend(GROCERY_KEYWORDS)


# # =========================================================
# # ☕ COFFEE & CAFE
# # =========================================================

# COFFEE_KEYWORDS = [
#     ("starbucks", "coffee"),
#     ("dunkin", "coffee"),
#     ("dunkin donuts", "coffee"),
#     ("tim hortons", "coffee"),
#     ("peet's", "coffee"),
#     ("peets coffee", "coffee"),
#     ("caribou coffee", "coffee"),
#     ("coffee bean", "coffee"),
#     ("the coffee bean & tea leaf", "coffee"),
#     ("philz coffee", "coffee"),
#     ("blue bottle", "coffee"),
#     ("intelligentsia", "coffee"),
#     ("la colombe", "coffee"),
#     ("stumptown", "coffee"),
#     ("counter culture", "coffee"),
#     ("dutch bros", "coffee"),
#     ("scooter's coffee", "coffee"),
#     ("biggby", "coffee"),
#     ("seattle's best", "coffee"),
#     ("tully's", "coffee"),
#     ("coffee shop", "coffee"),
#     ("cafe", "coffee"),
#     ("espresso", "coffee"),
#     ("latte", "coffee"),
#     ("cappuccino", "coffee"),
# ]

# CATEGORY_KEYWORDS.extend(COFFEE_KEYWORDS)


# # =========================================================
# # 🍽️ DINING OUT & RESTAURANTS
# # =========================================================

# DINING_KEYWORDS = [
#     # Fast Food
#     ("mcdonald", "dining_out"),
#     ("mcdonald's", "dining_out"),
#     ("burger king", "dining_out"),
#     ("wendy's", "dining_out"),
#     ("taco bell", "dining_out"),
#     ("kfc", "dining_out"),
#     ("popeyes", "dining_out"),
#     ("chick-fil-a", "dining_out"),
#     ("chick fil a", "dining_out"),
#     ("chipotle", "dining_out"),
#     ("moe's", "dining_out"),
#     ("qdob", "dining_out"),
#     ("cava", "dining_out"),
#     ("sweetgreen", "dining_out"),
#     ("subway", "dining_out"),
#     ("jimmy john's", "dining_out"),
#     ("firehouse subs", "dining_out"),
#     ("potbelly", "dining_out"),
#     ("pizza hut", "dining_out"),
#     ("domino's", "dining_out"),
#     ("dominos", "dining_out"),
#     ("papa john's", "dining_out"),
#     ("little caesars", "dining_out"),
#     ("papa murphy's", "dining_out"),
#     ("california pizza kitchen", "dining_out"),
#     ("cpk", "dining_out"),
#     ("arbys", "dining_out"),
#     ("sonic", "dining_out"),
#     ("sonic drive-in", "dining_out"),
#     ("in-n-out", "dining_out"),
#     ("in n out", "dining_out"),
#     ("five guys", "dining_out"),
#     ("whataburger", "dining_out"),
#     ("culver's", "dining_out"),
#     ("white castle", "dining_out"),
#     ("checkers", "dining_out"),
#     ("rally's", "dining_out"),
#     ("jack in the box", "dining_out"),
#     ("del taco", "dining_out"),
#     ("carl's jr", "dining_out"),
#     ("hardee's", "dining_out"),
#     ("church's chicken", "dining_out"),
#     ("bojangles", "dining_out"),
#     ("zaxby's", "dining_out"),
#     ("raising cane's", "dining_out"),
    
#     # Casual Dining
#     ("applebee's", "dining_out"),
#     ("chili's", "dining_out"),
#     ("tgi fridays", "dining_out"),
#     ("outback", "dining_out"),
#     ("outback steakhouse", "dining_out"),
#     ("olive garden", "dining_out"),
#     ("red lobster", "dining_out"),
#     ("longhorn", "dining_out"),
#     ("longhorn steakhouse", "dining_out"),
#     ("texas roadhouse", "dining_out"),
#     ("cheesecake factory", "dining_out"),
#     ("cheesecake", "dining_out"),
#     ("red robin", "dining_out"),
#     ("buffalo wild wings", "dining_out"),
#     ("bww", "dining_out"),
#     ("wingstop", "dining_out"),
#     ("hooter's", "dining_out"),
#     ("hooters", "dining_out"),
#     ("dave & buster's", "dining_out"),
#     ("dave and busters", "dining_out"),
#     ("bjs restaurant", "dining_out"),
#     ("bj's restaurant", "dining_out"),
#     ("denny's", "dining_out"),
#     ("ihop", "dining_out"),
#     ("waffle house", "dining_out"),
#     ("cracker barrel", "dining_out"),
#     ("friendly's", "dining_out"),
#     ("perkins", "dining_out"),
#     ("village inn", "dining_out"),
#     ("first watch", "dining_out"),
#     ("snooze", "dining_out"),
    
#     # Pizza (independent)
#     ("pizza", "dining_out"),
#     ("pizzeria", "dining_out"),
#     ("pasta", "dining_out"),
#     ("italian", "dining_out"),
#     ("sushi", "dining_out"),
#     ("japanese", "dining_out"),
#     ("ramen", "dining_out"),
#     ("chinese", "dining_out"),
#     ("thai", "dining_out"),
#     ("vietnamese", "dining_out"),
#     ("pho", "dining_out"),
#     ("indian", "dining_out"),
#     ("curry", "dining_out"),
#     ("mexican", "dining_out"),
#     ("tacos", "dining_out"),
#     ("burrito", "dining_out"),
#     ("korean", "dining_out"),
#     ("bbq", "dining_out"),
#     ("steakhouse", "dining_out"),
#     ("seafood", "dining_out"),
#     ("breakfast", "dining_out"),
#     ("brunch", "dining_out"),
#     ("lunch", "dining_out"),
#     ("dinner", "dining_out"),
#     ("restaurant", "dining_out"),
#     ("cafe", "dining_out"),
#     ("diner", "dining_out"),
#     ("bistro", "dining_out"),
#     ("grill", "dining_out"),
#     ("bar & grill", "dining_out"),
#     ("pub", "dining_out"),
# ]

# CATEGORY_KEYWORDS.extend(DINING_KEYWORDS)


# # =========================================================
# # 🚗 TRANSPORTATION
# # =========================================================

# TRANSPORT_KEYWORDS = [
#     # Gas Stations
#     ("shell", "gas"),
#     ("chevron", "gas"),
#     ("exxon", "gas"),
#     ("mobil", "gas"),
#     ("bp", "gas"),
#     ("amoco", "gas"),
#     ("76", "gas"),
#     ("arco", "gas"),
#     ("ampm", "gas"),
#     ("circle k", "gas"),
#     ("speedway", "gas"),
#     ("marathon", "gas"),
#     ("sunoco", "gas"),
#     ("valero", "gas"),
#     ("phillips 66", "gas"),
#     ("conoco", "gas"),
#     ("7-eleven", "gas"),
#     ("gas station", "gas"),
#     ("fuel", "gas"),
#     ("gasoline", "gas"),
    
#     # Rideshare
#     ("uber", "uber"),
#     ("lyft", "uber"),
#     ("via", "uber"),
#     ("taxi", "uber"),
#     ("cab", "uber"),
#     ("ride share", "uber"),
    
#     # Public Transit
#     ("metro", "public_transit"),
#     ("subway", "public_transit"),
#     ("bus", "public_transit"),
#     ("train", "public_transit"),
#     ("rail", "public_transit"),
#     ("light rail", "public_transit"),
#     ("transit", "public_transit"),
#     ("amtrak", "public_transit"),
#     ("greyhound", "public_transit"),
#     ("megabus", "public_transit"),
    
#     # Parking & Tolls
#     ("parking", "transport"),
#     ("garage", "transport"),
#     ("parking lot", "transport"),
#     ("meter", "transport"),
#     ("toll", "transport"),
#     ("ezpass", "transport"),
#     ("sunpass", "transport"),
#     ("fastrak", "transport"),
#     ("toll road", "transport"),
    
#     # Car Maintenance
#     ("oil change", "transport"),
#     ("tire", "transport"),
#     ("repair", "transport"),
#     ("maintenance", "transport"),
#     ("auto repair", "transport"),
#     ("mechanic", "transport"),
#     ("car wash", "transport"),
#     ("detailing", "transport"),
#     ("alignment", "transport"),
#     ("brake", "transport"),
#     ("battery", "transport"),
#     ("muffler", "transport"),
#     ("transmission", "transport"),
#     ("jiffy lube", "transport"),
#     ("valvoline", "transport"),
#     ("pep boys", "transport"),
#     ("autozone", "transport"),
#     ("oreilly", "transport"),
#     ("advance auto", "transport"),
#     ("ntb", "transport"),
#     ("goodyear", "transport"),
#     ("firestone", "transport"),
#     ("discount tire", "transport"),
#     ("mavis", "transport"),
#     ("monro", "transport"),
# ]

# CATEGORY_KEYWORDS.extend(TRANSPORT_KEYWORDS)


# # =========================================================
# # 🛍️ SHOPPING & RETAIL
# # =========================================================

# SHOPPING_KEYWORDS = [
#     # Online Shopping
#     ("amazon", "amazon"),
#     ("amzn", "amazon"),
#     ("amzn.com", "amazon"),
#     ("amazon prime", "amazon"),
#     ("amazon web services", "amazon"),
#     ("aws", "amazon"),
#     ("ebay", "shopping"),
#     ("etsy", "shopping"),
#     ("wish", "shopping"),
#     ("alibaba", "shopping"),
#     ("aliexpress", "shopping"),
#     ("temu", "shopping"),
#     ("shein", "shopping"),
#     ("zara", "shopping"),
#     ("hm", "shopping"),
#     ("uniqlo", "shopping"),
#     ("gap", "shopping"),
#     ("old navy", "shopping"),
#     ("banana republic", "shopping"),
#     ("nike", "shopping"),
#     ("adidas", "shopping"),
#     ("under armour", "shopping"),
    
#     # Department Stores
#     ("target", "shopping"),
#     ("walmart", "shopping"),
#     ("kohl's", "shopping"),
#     ("kohls", "shopping"),
#     ("jcpenney", "shopping"),
#     ("jc penney", "shopping"),
#     ("macy's", "shopping"),
#     ("macys", "shopping"),
#     ("nordstrom", "shopping"),
#     ("nordstrom rack", "shopping"),
#     ("saks", "shopping"),
#     ("saks fifth avenue", "shopping"),
#     ("bloomingdale's", "shopping"),
#     ("bloomingdales", "shopping"),
#     ("neiman marcus", "shopping"),
#     ("bergdorf", "shopping"),
#     ("barneys", "shopping"),
#     ("dillard's", "shopping"),
#     ("dillards", "shopping"),
#     ("belk", "shopping"),
#     ("boscov's", "shopping"),
    
#     # Discount & Outlet
#     ("tj maxx", "shopping"),
#     ("tjmaxx", "shopping"),
#     ("marshalls", "shopping"),
#     ("homegoods", "shopping"),
#     ("sierra", "shopping"),
#     ("ross", "shopping"),
#     ("ross dress for less", "shopping"),
#     ("burlington", "shopping"),
#     ("burlington coat factory", "shopping"),
#     ("dd's discounts", "shopping"),
#     ("gabriel's", "shopping"),
#     ("ollie's", "shopping"),
#     ("ollies", "shopping"),
#     ("big lots", "shopping"),
#     ("five below", "shopping"),
    
#     # Home Goods
#     ("ikea", "shopping"),
#     ("crate & barrel", "shopping"),
#     ("crate and barrel", "shopping"),
#     ("west elm", "shopping"),
#     ("pottery barn", "shopping"),
#     ("williams sonoma", "shopping"),
#     ("sur la table", "shopping"),
#     ("bed bath & beyond", "shopping"),
#     ("bed bath and beyond", "shopping"),
#     ("buy buy baby", "shopping"),
#     ("container store", "shopping"),
#     ("the container store", "shopping"),
#     ("at home", "shopping"),
#     ("home sense", "shopping"),
#     ("homesense", "shopping"),
#     ("furniture", "shopping"),
#     ("mattress", "shopping"),
    
#     # Electronics
#     ("best buy", "electronics"),
#     ("apple store", "electronics"),
#     ("apple.com", "electronics"),
#     ("micro center", "electronics"),
#     ("b&h photo", "electronics"),
#     ("bhphoto", "electronics"),
#     ("newegg", "electronics"),
#     ("newegg.com", "electronics"),
#     ("gamestop", "electronics"),
#     ("game stop", "electronics"),
#     ("radioshack", "electronics"),
#     ("fry's", "electronics"),
#     ("frys electronics", "electronics"),
#     ("dell", "electronics"),
#     ("hp", "electronics"),
#     ("lenovo", "electronics"),
#     ("asus", "electronics"),
#     ("samsung", "electronics"),
#     ("lg", "electronics"),
#     ("sony", "electronics"),
#     ("panasonic", "electronics"),
#     ("canon", "electronics"),
#     ("nikon", "electronics"),
#     ("gopro", "electronics"),
#     ("fitbit", "electronics"),
#     ("garmin", "electronics"),
#     ("logitech", "electronics"),
#     ("corsair", "electronics"),
#     ("razer", "electronics"),
    
#     # Office & Stationery
#     ("staples", "shopping"),
#     ("office depot", "shopping"),
#     ("office max", "shopping"),
#     ("office depot/office max", "shopping"),
#     ("paper", "shopping"),
#     ("pens", "shopping"),
#     ("stationery", "shopping"),
    
#     # Beauty & Cosmetics
#     ("ulta", "shopping"),
#     ("ulta beauty", "shopping"),
#     ("sephora", "shopping"),
#     ("bath & body works", "shopping"),
#     ("bath and body works", "shopping"),
#     ("the body shop", "shopping"),
#     ("lush", "shopping"),
#     ("aveda", "shopping"),
#     ("kiehl's", "shopping"),
#     ("kiehls", "shopping"),
#     ("clinique", "shopping"),
#     ("estee lauder", "shopping"),
#     ("lancome", "shopping"),
#     ("mac cosmetics", "shopping"),
#     ("nyx", "shopping"),
#     ("maybelline", "shopping"),
#     ("covergirl", "shopping"),
#     ("revlon", "shopping"),
#     ("olaplex", "shopping"),
#     ("dyson", "shopping"),
#     ("conair", "shopping"),
# ]

# CATEGORY_KEYWORDS.extend(SHOPPING_KEYWORDS)


# # =========================================================
# # 📺 STREAMING & ENTERTAINMENT
# # =========================================================

# ENTERTAINMENT_KEYWORDS = [
#     # Streaming Services
#     ("netflix", "streaming"),
#     ("netflix.com", "streaming"),
#     ("spotify", "streaming"),
#     ("spotify.com", "streaming"),
#     ("hulu", "streaming"),
#     ("hulu.com", "streaming"),
#     ("disney+", "streaming"),
#     ("disney plus", "streaming"),
#     ("disneyplus", "streaming"),
#     ("peacock", "streaming"),
#     ("peacocktv", "streaming"),
#     ("paramount+", "streaming"),
#     ("paramount plus", "streaming"),
#     ("apple tv", "streaming"),
#     ("appletv", "streaming"),
#     ("apple music", "streaming"),
#     ("amazon prime video", "streaming"),
#     ("prime video", "streaming"),
#     ("hbo max", "streaming"),
#     ("hbomax", "streaming"),
#     ("max", "streaming"),
#     ("hbo", "streaming"),
#     ("starz", "streaming"),
#     ("showtime", "streaming"),
#     ("youtube premium", "streaming"),
#     ("youtube music", "streaming"),
#     ("pandora", "streaming"),
#     ("tidal", "streaming"),
#     ("deezer", "streaming"),
#     ("soundcloud", "streaming"),
#     ("audible", "streaming"),
#     ("scribd", "streaming"),
    
#     # Movies & Cinema
#     ("amc", "entertainment"),
#     ("amc theatres", "entertainment"),
#     ("regal", "entertainment"),
#     ("regal cinemas", "entertainment"),
#     ("cinemark", "entertainment"),
#     ("movie", "entertainment"),
#     ("theatre", "entertainment"),
#     ("cinema", "entertainment"),
#     ("fandango", "entertainment"),
#     ("atom tickets", "entertainment"),
    
#     # Gaming
#     ("xbox", "games"),
#     ("playstation", "games"),
#     ("ps5", "games"),
#     ("ps4", "games"),
#     ("nintendo", "games"),
#     ("steam", "games"),
#     ("epic games", "games"),
#     ("blizzard", "games"),
#     ("battle.net", "games"),
#     ("riot games", "games"),
#     ("league of legends", "games"),
#     ("valorant", "games"),
#     ("fortnite", "games"),
#     ("minecraft", "games"),
#     ("roblox", "games"),
#     ("twitch", "games"),
#     ("discord", "games"),
#     ("game", "entertainment"),
#     ("gaming", "entertainment"),
    
#     # Live Events
#     ("ticketmaster", "entertainment"),
#     ("ticket", "entertainment"),
#     ("concert", "entertainment"),
#     ("festival", "entertainment"),
#     ("event", "entertainment"),
#     ("broadway", "entertainment"),
#     ("show", "entertainment"),
#     ("theater", "entertainment"),
# ]

# CATEGORY_KEYWORDS.extend(ENTERTAINMENT_KEYWORDS)


# # =========================================================
# # 💳 INCOME & REFUNDS
# # =========================================================

# INCOME_KEYWORDS = [
#     ("salary", "salary"),
#     ("payroll", "salary"),
#     ("direct deposit", "salary"),
#     ("paycheck", "salary"),
#     ("wages", "salary"),
#     ("bonus", "salary"),
#     ("commission", "salary"),
#     ("tips", "salary"),
#     ("gratuity", "salary"),
    
#     ("refund", "refund"),
#     ("reversal", "refund"),
#     ("return", "refund"),
#     ("cashback", "refund"),
#     ("cash back", "refund"),
#     ("rebate", "refund"),
#     ("credit adjustment", "refund"),
    
#     ("interest", "investment"),
#     ("dividend", "investment"),
#     ("capital gain", "investment"),
#     ("investment", "investment"),
#     ("robinhood", "investment"),
#     ("vanguard", "investment"),
#     ("fidelity", "investment"),
#     ("schwab", "investment"),
#     ("charles schwab", "investment"),
#     ("etrade", "investment"),
#     ("acorns", "investment"),
#     ("stash", "investment"),
#     ("betterment", "investment"),
#     ("wealthfront", "investment"),
#     ("m1 finance", "investment"),
#     ("webull", "investment"),
#     ("coinbase", "investment"),
#     ("crypto", "investment"),
#     ("bitcoin", "investment"),
#     ("ethereum", "investment"),
# ]

# CATEGORY_KEYWORDS.extend(INCOME_KEYWORDS)


# # =========================================================
# # 📚 EDUCATION & LEARNING
# # =========================================================

# EDUCATION_KEYWORDS = [
#     ("tuition", "education"),
#     ("university", "education"),
#     ("college", "education"),
#     ("school", "education"),
#     ("student", "education"),
#     ("course", "education"),
#     ("class", "education"),
#     ("workshop", "education"),
#     ("seminar", "education"),
#     ("training", "education"),
#     ("coursera", "education"),
#     ("udemy", "education"),
#     ("udacity", "education"),
#     ("edx", "education"),
#     ("khan academy", "education"),
#     ("skillshare", "education"),
#     ("masterclass", "education"),
#     ("linkedin learning", "education"),
#     ("books", "books"),
#     ("textbook", "books"),
#     ("kindle", "books"),
#     ("amazon books", "books"),
#     ("barnes & noble", "books"),
#     ("barnes and noble", "books"),
#     ("bookshop", "books"),
#     ("audiobook", "books"),
#     ("libro.fm", "books"),
#     ("supplies", "supplies"),
#     ("school supplies", "supplies"),
#     ("art supplies", "supplies"),
#     ("craft supplies", "supplies"),
#     ("office supplies", "supplies"),
# ]

# CATEGORY_KEYWORDS.extend(EDUCATION_KEYWORDS)


# # =========================================================
# # 🏥 HEALTH & WELLNESS
# # =========================================================

# HEALTH_KEYWORDS = [
#     # Medical
#     ("doctor", "medical"),
#     ("physician", "medical"),
#     ("clinic", "medical"),
#     ("hospital", "medical"),
#     ("urgent care", "medical"),
#     ("emergency", "medical"),
#     ("medical", "medical"),
#     ("dental", "medical"),
#     ("dentist", "medical"),
#     ("orthodontist", "medical"),
#     ("vision", "medical"),
#     ("eye exam", "medical"),
#     ("glasses", "medical"),
#     ("contacts", "medical"),
#     ("prescription", "pharmacy"),
#     ("pharmacy", "pharmacy"),
#     ("cvs", "pharmacy"),
#     ("cvs pharmacy", "pharmacy"),
#     ("walgreens", "pharmacy"),
#     ("rite aid", "pharmacy"),
#     ("duane reade", "pharmacy"),
#     ("walmart pharmacy", "pharmacy"),
#     ("target pharmacy", "pharmacy"),
#     ("kroger pharmacy", "pharmacy"),
    
#     # Fitness
#     ("gym", "gym"),
#     ("fitness", "gym"),
#     ("workout", "gym"),
#     ("planet fitness", "gym"),
#     ("24 hour fitness", "gym"),
#     ("gold's gym", "gym"),
#     ("la fitness", "gym"),
#     ("equinox", "gym"),
#     ("orange theory", "gym"),
#     ("f45", "gym"),
#     ("crossfit", "gym"),
#     ("yoga", "gym"),
#     ("pilates", "gym"),
#     ("barre", "gym"),
#     ("soulcycle", "gym"),
#     ("peloton", "gym"),
    
#     # Personal Care
#     ("salon", "personal_care"),
#     ("hair", "personal_care"),
#     ("barber", "personal_care"),
#     ("haircut", "personal_care"),
#     ("spa", "personal_care"),
#     ("massage", "personal_care"),
#     ("nail", "personal_care"),
#     ("manicure", "personal_care"),
#     ("pedicure", "personal_care"),
#     ("lashes", "personal_care"),
#     ("waxing", "personal_care"),
#     ("tanning", "personal_care"),
#     ("great clips", "personal_care"),
#     ("supercuts", "personal_care"),
#     ("sport clips", "personal_care"),
# ]

# CATEGORY_KEYWORDS.extend(HEALTH_KEYWORDS)


# # =========================================================
# # ✈️ TRAVEL
# # =========================================================

# TRAVEL_KEYWORDS = [
#     # Airlines
#     ("delta", "flights"),
#     ("united", "flights"),
#     ("american airlines", "flights"),
#     ("southwest", "flights"),
#     ("jetblue", "flights"),
#     ("spirit", "flights"),
#     ("frontier", "flights"),
#     ("alaska", "flights"),
#     ("hawaiian", "flights"),
#     ("air canada", "flights"),
#     ("british airways", "flights"),
#     ("lufthansa", "flights"),
#     ("emirates", "flights"),
#     ("qatar", "flights"),
#     ("singapore air", "flights"),
#     ("flight", "flights"),
#     ("airline", "flights"),
#     ("airplane", "flights"),
    
#     # Hotels
#     ("hotel", "hotels"),
#     ("marriott", "hotels"),
#     ("hilton", "hotels"),
#     ("hyatt", "hotels"),
#     ("ihg", "hotels"),
#     ("holiday inn", "hotels"),
#     ("best western", "hotels"),
#     ("wyndham", "hotels"),
#     ("choice hotels", "hotels"),
#     ("airbnb", "hotels"),
#     ("vrbo", "hotels"),
#     ("hostel", "hotels"),
#     ("motel", "hotels"),
#     ("resort", "hotels"),
#     ("lodging", "hotels"),
#     ("accommodation", "hotels"),
    
#     # Booking Sites
#     ("expedia", "travel"),
#     ("booking.com", "travel"),
#     ("priceline", "travel"),
#     ("kayak", "travel"),
#     ("orbitz", "travel"),
#     ("travelocity", "travel"),
#     ("hotwire", "travel"),
#     ("hotels.com", "travel"),
    
#     # Car Rental
#     ("hertz", "travel"),
#     ("avis", "travel"),
#     ("enterprise", "travel"),
#     ("budget", "travel"),
#     ("thrifty", "travel"),
#     ("dollar", "travel"),
#     ("national", "travel"),
#     ("car rental", "travel"),
    
#     # Cruise
#     ("carnival", "travel"),
#     ("royal caribbean", "travel"),
#     ("norwegian", "travel"),
#     ("princess", "travel"),
#     ("celebrity", "travel"),
#     ("cruise", "travel"),
    
#     # Other Travel
#     ("passport", "travel"),
#     ("visa", "travel"),
#     ("travel insurance", "travel"),
#     ("luggage", "travel"),
#     ("baggage", "travel"),
# ]

# CATEGORY_KEYWORDS.extend(TRAVEL_KEYWORDS)


# # =========================================================
# # 🎓 STUDENT-SPECIFIC
# # =========================================================

# STUDENT_KEYWORDS = [
#     # Student Loans
#     ("student loan", "student_loan"),
#     ("sallie mae", "student_loan"),
#     ("navient", "student_loan"),
#     ("nelnet", "student_loan"),
#     ("great lakes", "student_loan"),
#     ("fedloan", "student_loan"),
#     ("aidvantage", "student_loan"),
#     ("mohela", "student_loan"),
#     ("edfinancial", "student_loan"),
#     ("student aid", "student_loan"),
#     ("fasfa", "student_loan"),
#     ("pell grant", "education"),
    
#     # University Expenses
#     ("bookstore", "books"),
#     ("campus store", "books"),
#     ("university dining", "dining_out"),
#     ("campus food", "dining_out"),
#     ("meal plan", "dining_out"),
#     ("cafeteria", "dining_out"),
#     ("dorm", "housing"),
#     ("residence hall", "housing"),
#     ("housing", "housing"),
#     ("room and board", "housing"),
    
#     # Greek Life
#     ("sorority", "student_life"),
#     ("fraternity", "student_life"),
#     ("dues", "student_life"),
#     ("rush", "student_life"),
    
#     # Student Activities
#     ("student activities", "entertainment"),
#     ("student union", "entertainment"),
#     ("campus events", "entertainment"),
#     ("homecoming", "entertainment"),
#     ("tailgate", "entertainment"),
# ]

# CATEGORY_KEYWORDS.extend(STUDENT_KEYWORDS)


# # =========================================================
# # 💳 CREDIT CARDS & PAYMENTS
# # =========================================================

# CREDIT_KEYWORDS = [
#     ("credit card", "credit_card"),
#     ("amex", "credit_card"),
#     ("american express", "credit_card"),
#     ("visa", "credit_card"),
#     ("mastercard", "credit_card"),
#     ("discover", "credit_card"),
#     ("capital one", "credit_card"),
#     ("chase", "credit_card"),
#     ("citi", "credit_card"),
#     ("citibank", "credit_card"),
#     ("wells fargo", "credit_card"),
#     ("bank of america", "credit_card"),
#     ("us bank", "credit_card"),
#     ("td bank", "credit_card"),
#     ("pnc", "credit_card"),
#     ("credit card payment", "credit_card"),
#     ("minimum payment", "credit_card"),
#     ("balance transfer", "credit_card"),
# ]

# CATEGORY_KEYWORDS.extend(CREDIT_KEYWORDS)


# # =========================================================
# # 🚘 CAR PAYMENTS & LOANS
# # =========================================================

# CAR_KEYWORDS = [
#     ("car payment", "car_payment"),
#     ("auto payment", "car_payment"),
#     ("auto loan", "car_payment"),
#     ("car loan", "car_payment"),
#     ("vehicle payment", "car_payment"),
#     ("honda financial", "car_payment"),
#     ("toyota financial", "car_payment"),
#     ("ford credit", "car_payment"),
#     ("gm financial", "car_payment"),
#     ("nissan finance", "car_payment"),
#     ("bmw financial", "car_payment"),
#     ("mercedes benz financial", "car_payment"),
#     ("vw credit", "car_payment"),
#     ("hyundai motor finance", "car_payment"),
#     ("kia motors finance", "car_payment"),
#     ("subaru finance", "car_payment"),
#     ("mazda financial", "car_payment"),
#     ("tesla", "car_payment"),
#     ("rivian", "car_payment"),
#     ("lucid", "car_payment"),
# ]

# CATEGORY_KEYWORDS.extend(CAR_KEYWORDS)


# # =========================================================
# # 💼 BUSINESS & WORK
# # =========================================================

# BUSINESS_KEYWORDS = [
#     ("business expense", "business"),
#     ("office", "business"),
#     ("conference", "business"),
#     ("meeting", "business"),
#     ("client", "business"),
#     ("contractor", "business"),
#     ("freelance", "business"),
#     ("consulting", "business"),
#     ("professional services", "business"),
#     ("legal", "business"),
#     ("attorney", "business"),
#     ("lawyer", "business"),
#     ("accountant", "business"),
#     ("cpa", "business"),
#     ("tax", "business"),
#     ("tax preparation", "business"),
#     ("h&r block", "business"),
#     ("turbotax", "business"),
#     ("quickbooks", "business"),
#     ("invoice", "business"),
#     ("payment received", "business"),
# ]

# CATEGORY_KEYWORDS.extend(BUSINESS_KEYWORDS)


# # =========================================================
# # 💰 OTHER CATEGORIES
# # =========================================================

# OTHER_KEYWORDS = [
#     # Charity & Donations
#     ("donation", "charity"),
#     ("charity", "charity"),
#     ("nonprofit", "charity"),
#     ("non-profit", "charity"),
#     ("foundation", "charity"),
#     ("church", "charity"),
#     ("tithe", "charity"),
#     ("go fund me", "charity"),
#     ("gofundme", "charity"),
    
#     # Subscriptions
#     ("subscription", "subscription"),
#     ("monthly fee", "subscription"),
#     ("annual fee", "subscription"),
#     ("membership", "subscription"),
#     ("costco membership", "subscription"),
#     ("amazon prime", "subscription"),
#     ("walmart+", "subscription"),
#     ("walmart plus", "subscription"),
    
#     # Gifts
#     ("gift", "gift"),
#     ("present", "gift"),
#     ("gift card", "gift"),
#     ("gift certificate", "gift"),
    
#     # Pets
#     ("pet", "pets"),
#     ("dog", "pets"),
#     ("cat", "pets"),
#     ("veterinarian", "pets"),
#     ("vet", "pets"),
#     ("pet food", "pets"),
#     ("pet store", "pets"),
#     ("petco", "pets"),
#     ("petsmart", "pets"),
#     ("chewy", "pets"),
    
#     # Misc
#     ("cash", "cash"),
#     ("atm", "cash"),
#     ("withdrawal", "cash"),
#     ("deposit", "deposit"),
#     ("transfer", "transfer"),
#     ("wire", "transfer"),
#     ("venmo", "transfer"),
#     ("paypal", "transfer"),
#     ("zelle", "transfer"),
#     ("cash app", "transfer"),
#     ("apple cash", "transfer"),
#     ("google pay", "transfer"),
# ]

# CATEGORY_KEYWORDS.extend(OTHER_KEYWORDS)


# # =========================================================
# # DEFAULT FALLBACK CATEGORY
# # =========================================================

# # Always include this at the end for any unmatched transactions
# # ("other", "other") is handled by the parser's default logic



# # =========================================================
# # HELPER FUNCTIONS
# # =========================================================

# def _parse_amount(amount_str: Optional[str]) -> Optional[float]:
#     """
#     Convert a string amount to a signed float.

#     Handles examples like:
#     - "$4.95"        -> 4.95
#     - "-$29.99"      -> -29.99
#     - "+$2,800.00"   -> 2800.00
#     - "4.95"         -> 4.95
#     - "($4.95)"      -> -4.95
#     - " - $ 29.99 "  -> -29.99
#     """
#     if amount_str is None:
#         return None

#     text = str(amount_str).strip()
#     if not text:
#         return None

#     # Remove whitespace noise first.
#     text = re.sub(r"\s+", "", text)

#     # Parentheses often indicate negative values in finance.
#     is_negative = text.startswith("(") and text.endswith(")")
#     if is_negative:
#         text = text[1:-1]

#     # Remove common currency symbols and commas.
#     text = (
#         text.replace("$", "")
#         .replace("€", "")
#         .replace("£", "")
#         .replace("¥", "")
#         .replace(",", "")
#     )

#     # Track explicit sign after currency cleanup.
#     if text.startswith("-"):
#         is_negative = True
#         text = text[1:]
#     elif text.startswith("+"):
#         text = text[1:]

#     try:
#         value = float(text)
#         return -value if is_negative else value
#     except ValueError:
#         return None


# def _month_num(month_abbr: str) -> int:
#     """
#     Convert 3-letter month abbreviation into month number.
#     Defaults to 1 if unknown.
#     """
#     months = {
#         "jan": 1, "feb": 2, "mar": 3, "apr": 4,
#         "may": 5, "jun": 6, "jul": 7, "aug": 8,
#         "sep": 9, "oct": 10, "nov": 11, "dec": 12,
#     }
#     return months.get(month_abbr.lower(), 1)


# def _parse_date(
#     date_str: Optional[str],
#     document_date: Optional[str] = None,
#     today: Optional[date] = None,
#     *,
#     allow_document_fallback: bool = True,
# ) -> Optional[date]:
#     """
#     Parse a date string into a Python date object.

#     Supports:
#     - YYYY-MM-DD
#     - MM/DD/YYYY
#     - MM-DD-YYYY
#     - MM/DD/YY
#     - Dec 25, 2025
#     - 25 Dec 2025
#     - Today / Yesterday

#     Behavior:
#     - tries item date first
#     - then optionally tries document date once
#     - finally falls back to today

#     This keeps the pipeline moving even when the vision model gives a partial date.
#     """
#     if today is None:
#         today = date.today()

#     if not date_str:
#         if allow_document_fallback and document_date:
#             return _parse_date(
#                 document_date,
#                 document_date=None,
#                 today=today,
#                 allow_document_fallback=False,
#             )
#         return today

#     text = str(date_str).strip().lower()

#     # Relative date handling for screenshot-like extractions.
#     if text == "today":
#         return today
#     if text == "yesterday":
#         return today - timedelta(days=1)

#     patterns = [
#         # YYYY-MM-DD
#         (r"^(\d{4})-(\d{1,2})-(\d{1,2})$", lambda g: (int(g[0]), int(g[1]), int(g[2]))),

#         # MM/DD/YYYY
#         (r"^(\d{1,2})/(\d{1,2})/(\d{4})$", lambda g: (int(g[2]), int(g[0]), int(g[1]))),

#         # MM-DD-YYYY
#         (r"^(\d{1,2})-(\d{1,2})-(\d{4})$", lambda g: (int(g[2]), int(g[0]), int(g[1]))),

#         # MM/DD/YY
#         (r"^(\d{1,2})/(\d{1,2})/(\d{2})$", lambda g: (2000 + int(g[2]), int(g[0]), int(g[1]))),

#         # Dec 25, 2025
#         (r"^([a-z]{3})\s+(\d{1,2}),?\s+(\d{4})$", lambda g: (int(g[2]), _month_num(g[0]), int(g[1]))),

#         # 25 Dec 2025
#         (r"^(\d{1,2})\s+([a-z]{3})\s+(\d{4})$", lambda g: (int(g[2]), _month_num(g[1]), int(g[0]))),
#     ]

#     for pattern, handler in patterns:
#         match = re.match(pattern, text)
#         if match:
#             try:
#                 year, month, day = handler(match.groups())
#                 return date(year, month, day)
#             except (ValueError, TypeError):
#                 continue

#     # Try document-level date once, but avoid self-recursing endlessly.
#     if allow_document_fallback and document_date:
#         doc_text = str(document_date).strip().lower()
#         if doc_text and doc_text != text:
#             return _parse_date(
#                 document_date,
#                 document_date=None,
#                 today=today,
#                 allow_document_fallback=False,
#             )

#     # Final fallback keeps the app usable instead of failing hard.
#     return today


# def _infer_transaction_type(
#     amount: float,
#     description: str,
#     document_type: str,
#     merchant: Optional[str] = None,
# ) -> TransactionType:
#     """
#     Infer whether a transaction is expense, income, or transfer.

#     Rules:
#     - transfer keywords have highest priority
#     - positive amount + income keywords -> INCOME
#     - receipts are usually EXPENSE items
#     - otherwise sign-based fallback:
#         negative -> EXPENSE
#         positive -> INCOME

#     Note:
#     We store Transaction.amount as absolute later, but type is inferred from signed amount.
#     """
#     lower_desc = (description or "").lower()
#     lower_merchant = (merchant or "").lower()
#     combined = f"{lower_desc} {lower_merchant}"

#     transfer_keywords = [
#         "transfer", "zelle", "venmo", "paypal", "ach",
#         "wire", "autopay", "payment received", "payment thank you",
#     ]
#     if any(keyword in combined for keyword in transfer_keywords):
#         return TransactionType.TRANSFER

#     income_keywords = [
#         "payroll", "salary", "deposit", "refund",
#         "interest", "credit", "direct deposit", "cashback",
#     ]
#     if amount > 0 and any(keyword in combined for keyword in income_keywords):
#         return TransactionType.INCOME

#     if document_type == "receipt":
#         # Receipt line items are purchases by default.
#         return TransactionType.EXPENSE

#     return TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME


# def _guess_category(description: str, merchant: Optional[str] = None) -> str:
#     """
#     Guess a transaction category from description + merchant.
#     Falls back to 'other' if no keyword matches.
#     """
#     search_text = f"{description or ''} {merchant or ''}".lower()

#     for keyword, category in CATEGORY_KEYWORDS:
#         if keyword in search_text:
#             return category

#     if any(k in search_text for k in ["grocery", "market", "food"]):
#         return "groceries"
#     if any(k in search_text for k in ["coffee", "espresso", "latte"]):
#         return "coffee"
#     if any(k in search_text for k in ["rent", "lease"]):
#         return "rent"
#     if any(k in search_text for k in ["uber", "lyft"]):
#         return "uber"

#     return "other"


# def _normalize_confidence(value: Any) -> str:
#     """
#     Normalize incoming confidence values into the Transaction schema's allowed values.
#     """
#     if isinstance(value, str):
#         lowered = value.strip().lower()
#         if lowered in {"high", "medium", "low"}:
#             return lowered
#     return "medium"


# def _make_transaction_id(student_id: str, txn_date: date, amount: float, index: int) -> str:
#     """
#     Create a stable, deterministic transaction ID based on:
#     - student
#     - date
#     - amount
#     - loop index

#     This is useful for reproducibility in demos/tests.
#     """
#     date_str = txn_date.strftime("%Y%m%d")
#     amount_int = int(abs(amount) * 100)
#     return f"vision_{student_id}_{date_str}_{amount_int}_{index}"


# # =========================================================
# # MAIN BRIDGE FUNCTION
# # =========================================================

# def vision_result_to_transactions(
#     vision_output: Dict[str, Any],
#     student_id: str,
#     *,
#     default_currency: str = "USD",
#     today: Optional[date] = None,
# ) -> VisionTransactionResult:
#     """
#     Convert vision LLM output to Transaction objects.

#     Args
#     ----
#     vision_output:
#         Result from vision_llm_wrapper.extract_*()

#     student_id:
#         Student owner of the generated transactions

#     default_currency:
#         Kept for future extension / provenance. We store it in raw_data if vision output misses it.

#     today:
#         Optional override for deterministic tests

#     Returns
#     -------
#     VisionTransactionResult
#     """
#     if today is None:
#         today = date.today()

#     transactions: List[Transaction] = []
#     skipped_items: List[Dict[str, Any]] = []
#     errors: List[str] = []

#     # -----------------------------------------------------
#     # Validate top-level wrapper response
#     # -----------------------------------------------------
#     if not vision_output.get("success", False):
#         errors.append(f"Vision extraction failed: {vision_output.get('error', 'Unknown error')}")
#         return VisionTransactionResult(
#             transactions=[],
#             skipped_items=[],
#             errors=errors,
#             source_document_type="unknown",
#         )

#     data = vision_output.get("data", {})
#     if not isinstance(data, dict) or not data:
#         errors.append("No usable 'data' object found in vision output")
#         return VisionTransactionResult(
#             transactions=[],
#             skipped_items=[],
#             errors=errors,
#             source_document_type="unknown",
#         )

#     document_type = str(data.get("document_type", "unknown")).strip().lower()
#     document_merchant = data.get("merchant")
#     document_date = data.get("date")
#     document_currency = data.get("currency") or default_currency
#     document_confidence = _normalize_confidence(data.get("confidence"))

#     # -----------------------------------------------------
#     # Pull transaction-like items from vision output
#     # -----------------------------------------------------
#     possible_txns = data.get("possible_transactions", [])
#     if not isinstance(possible_txns, list):
#         possible_txns = []

#     # If no item-level transactions were extracted, try to build one from totals.
#     # This is especially useful for receipts where only the total is visible.
#     if not possible_txns:
#         totals = data.get("totals", {})
#         if isinstance(totals, dict) and totals.get("total"):
#             possible_txns = [
#                 {
#                     "date": document_date,
#                     "description": f"{document_type.capitalize()} total",
#                     "amount": totals.get("total"),
#                     "merchant": document_merchant,
#                     "confidence": document_confidence,
#                 }
#             ]

#     # -----------------------------------------------------
#     # Convert each possible transaction into Transaction
#     # -----------------------------------------------------
#     for idx, item in enumerate(possible_txns):
#         if not isinstance(item, dict):
#             skipped_items.append({"raw_item": item, "skip_reason": "Transaction item is not a dict"})
#             continue

#         try:
#             desc = str(item.get("description", "")).strip()
#             amount_str = item.get("amount")
#             item_merchant = item.get("merchant") or document_merchant
#             item_date_str = item.get("date")
#             item_confidence = _normalize_confidence(item.get("confidence", document_confidence))

#             # Description is the most important field for later UX/debugging.
#             if not desc:
#                 skipped_items.append({**item, "skip_reason": "Missing description"})
#                 continue

#             # Amount must be parseable to create a useful Transaction.
#             amount_signed = _parse_amount(amount_str)
#             if amount_signed is None:
#                 skipped_items.append({**item, "skip_reason": f"Could not parse amount: {amount_str}"})
#                 continue

#             # Date can fall back to document date, then to today.
#             txn_date = _parse_date(
#                 item_date_str,
#                 document_date=document_date,
#                 today=today,
#             )
#             if txn_date is None:
#                 skipped_items.append({**item, "skip_reason": f"Could not parse date: {item_date_str}"})
#                 continue

#             txn_type = _infer_transaction_type(
#                 amount=amount_signed,
#                 description=desc,
#                 document_type=document_type,
#                 merchant=item_merchant,
#             )

#             category = _guess_category(desc, item_merchant)
#             txn_id = _make_transaction_id(student_id, txn_date, amount_signed, idx)

#             # IMPORTANT:
#             # Transaction.amount in your schema is absolute and sign is represented by transaction_type.
#             tx = Transaction(
#                 transaction_id=txn_id,
#                 student_id=student_id,
#                 amount=abs(amount_signed),
#                 transaction_type=txn_type,
#                 date=txn_date,
#                 description=desc[:200],
#                 merchant=item_merchant[:30] if isinstance(item_merchant, str) and item_merchant.strip() else None,
#                 category=category,
#                 payment_method="other",
#                 # Must match currently allowed Transaction.source literal values.
#                 source="screenshot",
#                 confidence=item_confidence,
#                 raw_data={
#                     "vision_item": item,
#                     "vision_document_type": document_type,
#                     "vision_document_merchant": document_merchant,
#                     "vision_document_date": document_date,
#                     "vision_document_currency": document_currency,
#                     "vision_document_confidence": document_confidence,
#                 },
#                 notes=f"Extracted from {document_type}",
#                 tags=[],
#             )

#             transactions.append(tx)

#         except Exception as e:
#             errors.append(f"Error processing item {idx}: {e}")
#             skipped_items.append({**item, "skip_reason": str(e)})

#     return VisionTransactionResult(
#         transactions=transactions,
#         skipped_items=skipped_items,
#         errors=errors,
#         source_document_type=document_type,
#     )


# # =========================================================
# # DOCUMENT-TYPE SPECIFIC CONVENIENCE FUNCTIONS
# # =========================================================

# def receipt_to_transactions(vision_output: Dict[str, Any], student_id: str) -> VisionTransactionResult:
#     """
#     Convenience wrapper for receipt-like vision results.
#     """
#     return vision_result_to_transactions(vision_output, student_id)


# def bank_statement_to_transactions(vision_output: Dict[str, Any], student_id: str) -> VisionTransactionResult:
#     """
#     Convenience wrapper for bank-statement-like vision results.
#     """
#     return vision_result_to_transactions(vision_output, student_id)


# =========================================================
# EXAMPLE USAGE
# =========================================================



"""
🔄 VISION TRANSACTION BRIDGE - Convert vision LLM output to Transaction objects
"""

# from __future__ import annotations

# from datetime import date, timedelta
# from typing import List, Dict, Any, Optional, Tuple
# from dataclasses import dataclass
# import re

# from schemas.transaction import Transaction, TransactionType


# =========================================================
# RESULT MODEL
# =========================================================

@dataclass
class VisionTransactionResult:
    transactions: List[Transaction]
    skipped_items: List[Dict[str, Any]]
    errors: List[str]
    source_document_type: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "transactions": [t.model_dump(mode="json") for t in self.transactions],
            "skipped_items": self.skipped_items,
            "errors": self.errors,
            "source_document_type": self.source_document_type,
            "transaction_count": len(self.transactions),
        }


# =========================================================
# ALLOWED CATEGORY MAPPING
# Must match schemas.transaction.Category exactly
# =========================================================

ALLOWED_CATEGORIES = {
    "food", "groceries", "dining_out", "coffee",
    "housing", "rent", "utilities", "internet", "phone",
    "transport", "gas", "uber", "public_transit",
    "entertainment", "streaming", "games", "movies",
    "shopping", "clothing", "electronics", "amazon",
    "education", "tuition", "books", "supplies",
    "health", "medical", "gym", "pharmacy",
    "personal_care", "haircut", "cosmetics",
    "travel", "flights", "hotels",
    "income", "salary", "gift", "refund",
    "transfer", "savings", "investment",
    "other",
}

CATEGORY_KEYWORDS: List[Tuple[str, str]] = [
    # groceries
    ("whole foods", "groceries"),
    ("trader joe", "groceries"),
    ("costco", "groceries"),
    ("kroger", "groceries"),
    ("heb", "groceries"),
    ("publix", "groceries"),
    ("aldi", "groceries"),
    ("lidl", "groceries"),
    ("instacart", "groceries"),
    ("amazon fresh", "groceries"),
    ("grocery", "groceries"),
    ("supermarket", "groceries"),
    ("market", "groceries"),

    # coffee
    ("starbucks", "coffee"),
    ("dunkin", "coffee"),
    ("peet", "coffee"),
    ("coffee bean", "coffee"),
    ("philz", "coffee"),
    ("latte", "coffee"),
    ("espresso", "coffee"),
    ("cappuccino", "coffee"),

    # dining out
    ("mcdonald", "dining_out"),
    ("burger king", "dining_out"),
    ("wendy's", "dining_out"),
    ("taco bell", "dining_out"),
    ("chipotle", "dining_out"),
    ("sweetgreen", "dining_out"),
    ("subway", "dining_out"),
    ("domino", "dining_out"),
    ("pizza hut", "dining_out"),
    ("papa john", "dining_out"),
    ("chick-fil-a", "dining_out"),
    ("chick fil a", "dining_out"),
    ("restaurant", "dining_out"),
    ("diner", "dining_out"),
    ("bistro", "dining_out"),
    ("grill", "dining_out"),
    ("sushi", "dining_out"),
    ("ramen", "dining_out"),
    ("thai", "dining_out"),
    ("indian", "dining_out"),
    ("mexican", "dining_out"),
    ("bbq", "dining_out"),
    ("breakfast", "dining_out"),
    ("brunch", "dining_out"),
    ("lunch", "dining_out"),
    ("dinner", "dining_out"),

    # housing & bills
    ("rent", "rent"),
    ("lease", "rent"),
    ("apartment", "rent"),
    ("property management", "rent"),
    ("mortgage", "housing"),
    ("electric", "utilities"),
    ("electricity", "utilities"),
    ("water", "utilities"),
    ("sewer", "utilities"),
    ("trash", "utilities"),
    ("waste management", "utilities"),
    ("internet", "internet"),
    ("xfinity", "internet"),
    ("comcast", "internet"),
    ("spectrum", "internet"),
    ("cox", "internet"),
    ("verizon fios", "internet"),
    ("fiber", "internet"),
    ("phone", "phone"),
    ("verizon wireless", "phone"),
    ("att wireless", "phone"),
    ("tmobile", "phone"),
    ("mint mobile", "phone"),
    ("cricket", "phone"),
    ("metro pcs", "phone"),

    # gas / transport
    ("shell", "gas"),
    ("chevron", "gas"),
    ("exxon", "gas"),
    ("mobil", "gas"),
    ("amoco", "gas"),
    ("arco", "gas"),
    ("sunoco", "gas"),
    ("valero", "gas"),
    ("phillips 66", "gas"),
    ("circle k", "gas"),
    ("circlek", "gas"),
    ("speedway", "gas"),
    ("marathon", "gas"),
    ("fuel", "gas"),
    ("gas station", "gas"),
    ("uber", "uber"),
    ("lyft", "uber"),
    ("metro", "public_transit"),
    ("amtrak", "public_transit"),
    ("greyhound", "public_transit"),
    ("megabus", "public_transit"),
    ("parking", "transport"),
    ("garage", "transport"),
    ("toll", "transport"),
    ("ezpass", "transport"),
    ("fastrak", "transport"),
    ("ntta", "transport"),
    ("ntta online", "transport"),
    ("ntta autocharge", "transport"),
    ("oil change", "transport"),
    ("jiffy lube", "transport"),
    ("autozone", "transport"),
    ("pep boys", "transport"),
    ("discount tire", "transport"),

    # shopping / electronics / amazon
    ("amazon", "amazon"),
    ("amzn", "amazon"),
    ("ebay", "shopping"),
    ("etsy", "shopping"),
    ("target", "shopping"),
    ("kohl", "shopping"),
    ("macy", "shopping"),
    ("nordstrom", "shopping"),
    ("tj maxx", "shopping"),
    ("marshalls", "shopping"),
    ("ross", "shopping"),
    ("burlington", "shopping"),
    ("ikea", "shopping"),
    ("ulta", "shopping"),
    ("sephora", "shopping"),
    ("best buy", "electronics"),
    ("apple.com", "electronics"),
    ("apple store", "electronics"),
    ("micro center", "electronics"),
    ("newegg", "electronics"),
    ("dell", "electronics"),
    ("lenovo", "electronics"),
    ("samsung", "electronics"),
    ("sony", "electronics"),

    # streaming / entertainment / games
    ("netflix", "streaming"),
    ("spotify", "streaming"),
    ("hulu", "streaming"),
    ("disney+", "streaming"),
    ("disney plus", "streaming"),
    ("peacock", "streaming"),
    ("paramount+", "streaming"),
    ("paramount plus", "streaming"),
    ("apple tv", "streaming"),
    ("youtube premium", "streaming"),
    ("audible", "streaming"),
    ("amc", "movies"),
    ("regal", "movies"),
    ("cinemark", "movies"),
    ("movie", "movies"),
    ("cinema", "movies"),
    ("xbox", "games"),
    ("playstation", "games"),
    ("nintendo", "games"),
    ("steam", "games"),
    ("epic games", "games"),
    ("gamestop", "games"),
    ("ticketmaster", "entertainment"),
    ("concert", "entertainment"),
    ("festival", "entertainment"),

    # education
    ("tuition", "tuition"),
    ("university", "education"),
    ("college", "education"),
    ("school", "education"),
    ("coursera", "education"),
    ("udemy", "education"),
    ("udacity", "education"),
    ("edx", "education"),
    ("textbook", "books"),
    ("barnes & noble", "books"),
    ("barnes and noble", "books"),
    ("kindle", "books"),
    ("bookstore", "books"),
    ("supplies", "supplies"),
    ("office supplies", "supplies"),

    # health
    ("doctor", "medical"),
    ("physician", "medical"),
    ("clinic", "medical"),
    ("hospital", "medical"),
    ("urgent care", "medical"),
    ("dentist", "medical"),
    ("dental", "medical"),
    ("pharmacy", "pharmacy"),
    ("walgreens", "pharmacy"),
    ("cvs pharmacy", "pharmacy"),
    ("rite aid", "pharmacy"),
    ("prescription", "pharmacy"),
    ("gym", "gym"),
    ("planet fitness", "gym"),
    ("24 hour fitness", "gym"),
    ("equinox", "gym"),
    ("orange theory", "gym"),
    ("crossfit", "gym"),
    ("haircut", "haircut"),
    ("barber", "haircut"),
    ("salon", "personal_care"),
    ("spa", "personal_care"),
    ("massage", "personal_care"),
    ("nail", "personal_care"),
    ("manicure", "personal_care"),
    ("pedicure", "personal_care"),
    ("cosmetic", "cosmetics"),
    ("ulta beauty", "cosmetics"),

    # travel
    ("delta", "flights"),
    ("united", "flights"),
    ("american airlines", "flights"),
    ("southwest", "flights"),
    ("jetblue", "flights"),
    ("spirit", "flights"),
    ("frontier", "flights"),
    ("flight", "flights"),
    ("airline", "flights"),
    ("marriott", "hotels"),
    ("hilton", "hotels"),
    ("hyatt", "hotels"),
    ("holiday inn", "hotels"),
    ("airbnb", "hotels"),
    ("vrbo", "hotels"),
    ("hotel", "hotels"),
    ("motel", "hotels"),
    ("expedia", "travel"),
    ("booking.com", "travel"),
    ("priceline", "travel"),
    ("kayak", "travel"),

    # income / refund / investment / gift
    ("salary", "salary"),
    ("payroll", "salary"),
    ("direct deposit", "salary"),
    ("paycheck", "salary"),
    ("wages", "salary"),
    ("refund", "refund"),
    ("reversal", "refund"),
    ("return credit", "refund"),
    ("cashback", "refund"),
    ("cash back", "refund"),
    ("rebate", "refund"),
    ("interest", "investment"),
    ("dividend", "investment"),
    ("robinhood", "investment"),
    ("vanguard", "investment"),
    ("fidelity", "investment"),
    ("schwab", "investment"),
    ("etrade", "investment"),
    ("acorns", "investment"),
    ("gift", "gift"),

    # transfer / savings
    ("zelle", "transfer"),
    ("venmo", "transfer"),
    ("paypal", "transfer"),
    ("cash app", "transfer"),
    ("wire transfer", "transfer"),
    ("online transfer", "transfer"),
    ("transfer", "transfer"),
    ("to savings", "savings"),
    ("from savings", "savings"),
]

TRANSFER_KEYWORDS = [
    "zelle",
    "venmo",
    "paypal",
    "cash app",
    "transfer",
    "wire",
    "autopay to chase pay in 4",
    "payment to chase pay in 4",
    "payment thank you",
    "payment received",
    "capital one mobile pmt",
    "mobile pmt",
]

INCOME_KEYWORDS = [
    "salary",
    "payroll",
    "direct deposit",
    "paycheck",
    "wages",
    "refund",
    "cashback",
    "cash back",
    "rebate",
    "interest",
    "dividend",
    "credit adjustment",
]

EXPENSE_OVERRIDE_KEYWORDS = [
    "honda pmt",
    "honda payment",
    "ins prem",
    "monthly service fee",
    "service fee",
    "card purchase",
    "recurring card purchase",
    "purchase with pin",
]


# =========================================================
# HELPER FUNCTIONS
# =========================================================

def _parse_amount(amount_str: Optional[str]) -> Optional[float]:
    if amount_str is None:
        return None

    text = str(amount_str).strip()
    if not text:
        return None

    text = re.sub(r"\s+", "", text)

    is_negative = text.startswith("(") and text.endswith(")")
    if is_negative:
        text = text[1:-1]

    text = (
        text.replace("$", "")
        .replace("€", "")
        .replace("£", "")
        .replace("¥", "")
        .replace(",", "")
    )

    if text.startswith("-"):
        is_negative = True
        text = text[1:]
    elif text.startswith("+"):
        text = text[1:]

    try:
        value = float(text)
        return -value if is_negative else value
    except ValueError:
        return None


def _month_num(month_abbr: str) -> int:
    months = {
        "jan": 1, "feb": 2, "mar": 3, "apr": 4,
        "may": 5, "jun": 6, "jul": 7, "aug": 8,
        "sep": 9, "oct": 10, "nov": 11, "dec": 12,
    }
    return months.get(month_abbr.lower(), 1)


def _parse_date(
    date_str: Optional[str],
    document_date: Optional[str] = None,
    today: Optional[date] = None,
    *,
    allow_document_fallback: bool = True,
) -> Optional[date]:
    if today is None:
        today = date.today()

    if not date_str:
        if allow_document_fallback and document_date:
            return _parse_date(
                document_date,
                document_date=None,
                today=today,
                allow_document_fallback=False,
            )
        return today

    text = str(date_str).strip().lower()

    if text == "today":
        return today
    if text == "yesterday":
        return today - timedelta(days=1)

    patterns = [
        (r"^(\d{4})-(\d{1,2})-(\d{1,2})$", lambda g: (int(g[0]), int(g[1]), int(g[2]))),
        (r"^(\d{1,2})/(\d{1,2})/(\d{4})$", lambda g: (int(g[2]), int(g[0]), int(g[1]))),
        (r"^(\d{1,2})-(\d{1,2})-(\d{4})$", lambda g: (int(g[2]), int(g[0]), int(g[1]))),
        (r"^(\d{1,2})/(\d{1,2})/(\d{2})$", lambda g: (2000 + int(g[2]), int(g[0]), int(g[1]))),
        (r"^([a-z]{3})\s+(\d{1,2}),?\s+(\d{4})$", lambda g: (int(g[2]), _month_num(g[0]), int(g[1]))),
        (r"^(\d{1,2})\s+([a-z]{3})\s+(\d{4})$", lambda g: (int(g[2]), _month_num(g[1]), int(g[0]))),
    ]

    for pattern, handler in patterns:
        match = re.match(pattern, text)
        if match:
            try:
                year, month, day = handler(match.groups())
                return date(year, month, day)
            except (ValueError, TypeError):
                continue

    if allow_document_fallback and document_date:
        doc_text = str(document_date).strip().lower()
        if doc_text and doc_text != text:
            return _parse_date(
                document_date,
                document_date=None,
                today=today,
                allow_document_fallback=False,
            )

    return today


def _normalize_text(*parts: Optional[str]) -> str:
    joined = " ".join([p for p in parts if p])
    lowered = joined.lower()
    lowered = re.sub(r"[^a-z0-9*#&/\-\.\s]", " ", lowered)
    return " ".join(lowered.split())


def _infer_transaction_type(
    amount: float,
    description: str,
    document_type: str,
    merchant: Optional[str] = None,
) -> TransactionType:
    combined = _normalize_text(description, merchant)

    if any(k in combined for k in EXPENSE_OVERRIDE_KEYWORDS):
        return TransactionType.EXPENSE

    if any(k in combined for k in TRANSFER_KEYWORDS):
        return TransactionType.TRANSFER

    if amount > 0 and any(k in combined for k in INCOME_KEYWORDS):
        return TransactionType.INCOME

    if document_type == "receipt":
        return TransactionType.EXPENSE

    return TransactionType.EXPENSE if amount < 0 else TransactionType.INCOME


def _guess_category(description: str, merchant: Optional[str] = None) -> str:
    search_text = _normalize_text(description, merchant)

    if any(k in search_text for k in ["zelle", "venmo", "paypal", "cash app", "transfer"]):
        return "transfer"

    if "honda pmt" in search_text or "honda payment" in search_text:
        return "other"

    if "capital one mobile pmt" in search_text or "mobile pmt" in search_text:
        return "transfer"

    if "ins prem" in search_text:
        return "other"

    if "monthly service fee" in search_text:
        return "other"

    for keyword, category in CATEGORY_KEYWORDS:
        if keyword in search_text and category in ALLOWED_CATEGORIES:
            return category

    if any(k in search_text for k in ["grocery", "supermarket", "food market"]):
        return "groceries"
    if any(k in search_text for k in ["coffee", "espresso", "latte"]):
        return "coffee"
    if any(k in search_text for k in ["rent", "lease"]):
        return "rent"
    if any(k in search_text for k in ["uber", "lyft"]):
        return "uber"

    return "other"


def _normalize_confidence(value: Any) -> str:
    if isinstance(value, str):
        lowered = value.strip().lower()
        if lowered in {"high", "medium", "low"}:
            return lowered
    return "medium"


def _make_transaction_id(student_id: str, txn_date: date, amount: float, index: int) -> str:
    date_str = txn_date.strftime("%Y%m%d")
    amount_int = int(abs(amount) * 100)
    return f"vision_{student_id}_{date_str}_{amount_int}_{index}"


def _pick_source(document_type: str) -> str:
    doc = (document_type or "").lower()
    if doc in {"bank_statement", "statement", "pdf_statement"}:
        return "pdf"
    if doc == "screenshot":
        return "screenshot"
    return "screenshot"


# =========================================================
# MAIN BRIDGE FUNCTION
# =========================================================

def vision_result_to_transactions(
    vision_output: Dict[str, Any],
    student_id: str,
    *,
    default_currency: str = "USD",
    today: Optional[date] = None,
) -> VisionTransactionResult:
    if today is None:
        today = date.today()

    transactions: List[Transaction] = []
    skipped_items: List[Dict[str, Any]] = []
    errors: List[str] = []

    if not vision_output.get("success", False):
        errors.append(f"Vision extraction failed: {vision_output.get('error', 'Unknown error')}")
        return VisionTransactionResult(
            transactions=[],
            skipped_items=[],
            errors=errors,
            source_document_type="unknown",
        )

    data = vision_output.get("data", {})
    if not isinstance(data, dict) or not data:
        errors.append("No usable 'data' object found in vision output")
        return VisionTransactionResult(
            transactions=[],
            skipped_items=[],
            errors=errors,
            source_document_type="unknown",
        )

    document_type = str(data.get("document_type", "unknown")).strip().lower()
    document_merchant = data.get("merchant")
    document_date = data.get("date")
    document_currency = data.get("currency") or default_currency
    document_confidence = _normalize_confidence(data.get("confidence"))
    source_value = _pick_source(document_type)

    possible_txns = data.get("possible_transactions", [])
    if not isinstance(possible_txns, list):
        possible_txns = []

    if not possible_txns:
        totals = data.get("totals", {})
        if isinstance(totals, dict) and totals.get("total"):
            possible_txns = [
                {
                    "date": document_date,
                    "description": f"{document_type.capitalize()} total",
                    "amount": totals.get("total"),
                    "merchant": document_merchant,
                    "confidence": document_confidence,
                }
            ]

    for idx, item in enumerate(possible_txns):
        if not isinstance(item, dict):
            skipped_items.append({"raw_item": item, "skip_reason": "Transaction item is not a dict"})
            continue

        try:
            desc = str(item.get("description", "")).strip()
            amount_str = item.get("amount")
            item_merchant = item.get("merchant") or document_merchant
            item_date_str = item.get("date")
            item_confidence = _normalize_confidence(item.get("confidence", document_confidence))

            if not desc:
                skipped_items.append({**item, "skip_reason": "Missing description"})
                continue

            amount_signed = _parse_amount(amount_str)
            if amount_signed is None:
                skipped_items.append({**item, "skip_reason": f"Could not parse amount: {amount_str}"})
                continue

            txn_date = _parse_date(
                item_date_str,
                document_date=document_date,
                today=today,
            )
            if txn_date is None:
                skipped_items.append({**item, "skip_reason": f"Could not parse date: {item_date_str}"})
                continue

            txn_type = _infer_transaction_type(
                amount=amount_signed,
                description=desc,
                document_type=document_type,
                merchant=item_merchant,
            )

            category = _guess_category(desc, item_merchant)
            if category not in ALLOWED_CATEGORIES:
                category = "other"

            txn_id = _make_transaction_id(student_id, txn_date, amount_signed, idx)

            tx = Transaction(
                transaction_id=txn_id,
                student_id=student_id,
                amount=abs(amount_signed),
                transaction_type=txn_type,
                date=txn_date,
                description=desc[:200],
                merchant=item_merchant[:100] if isinstance(item_merchant, str) and item_merchant.strip() else None,
                category=category,
                payment_method="other",
                source=source_value,
                confidence=item_confidence,
                raw_data={
                    "vision_item": item,
                    "vision_document_type": document_type,
                    "vision_document_merchant": document_merchant,
                    "vision_document_date": document_date,
                    "vision_document_currency": document_currency,
                    "vision_document_confidence": document_confidence,
                },
                notes=f"Extracted from {document_type}",
                tags=[],
            )

            transactions.append(tx)

        except Exception as e:
            errors.append(f"Error processing item {idx}: {e}")
            skipped_items.append({**item, "skip_reason": str(e)})

    return VisionTransactionResult(
        transactions=transactions,
        skipped_items=skipped_items,
        errors=errors,
        source_document_type=document_type,
    )


# =========================================================
# CONVENIENCE FUNCTIONS
# =========================================================

def receipt_to_transactions(vision_output: Dict[str, Any], student_id: str) -> VisionTransactionResult:
    return vision_result_to_transactions(vision_output, student_id)


def bank_statement_to_transactions(vision_output: Dict[str, Any], student_id: str) -> VisionTransactionResult:
    return vision_result_to_transactions(vision_output, student_id)


if __name__ == "__main__":
    print("=" * 70)
    print("🧪 VISION TRANSACTION BRIDGE TEST")
    print("=" * 70)

    sample_vision_output = {
        "success": True,
        "data": {
            "document_type": "receipt",
            "merchant": "STARBUCKS COFFEE",
            "date": "2025-12-25",
            "currency": "USD",
            "confidence": "high",
            "totals": {
                "subtotal": "13.20",
                "tax": "1.12",
                "total": "14.32",
            },
            "possible_transactions": [
                {
                    "date": "2025-12-25",
                    "description": "Caffe Latte",
                    "amount": "$4.95",
                    "merchant": "STARBUCKS COFFEE",
                    "confidence": "high",
                },
                {
                    "date": "2025-12-25",
                    "description": "Cappuccino",
                    "amount": "$4.75",
                    "merchant": "STARBUCKS COFFEE",
                    "confidence": "high",
                },
                {
                    "date": "2025-12-25",
                    "description": "Blueberry Muffin",
                    "amount": "$3.50",
                    "merchant": "STARBUCKS COFFEE",
                    "confidence": "high",
                },
            ],
        },
    }

    result = vision_result_to_transactions(sample_vision_output, "STU001")

    print(f"\n📊 Converted {len(result.transactions)} transactions")
    print(f"   Skipped: {len(result.skipped_items)}")
    print(f"   Errors: {len(result.errors)}")
    print(f"   Source doc type: {result.source_document_type}")

    for i, tx in enumerate(result.transactions, start=1):
        print(f"\n{i}. {tx.merchant}: ${tx.amount:.2f}")
        print(f"   Description: {tx.description}")
        print(f"   Category: {tx.category}")
        print(f"   Type: {tx.transaction_type.value}")
        print(f"   Date: {tx.date}")