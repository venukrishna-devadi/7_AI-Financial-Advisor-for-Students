import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from schemas.student import Student
from datetime import date

print("Test 1: Valid STudent")

try:
    krishna = Student(
        student_id="007",
        name= "Krishna Devadi",
        age="30",
        status="student",
        currency="USD",
        monthly_income= 1000,
        income_frequency="monthly",
        preferred_categories=["food", "FOOD", "RENt", "car emi", "miscellaneous"],
        fixed_monthly_expenses={"rent": 400, "car emi": 800, "miscellaneous": 100}
    )
    print("Created", krishna)
    print("Categories Noemalized:", krishna.preferred_categories)
    print("How much money is left to spend", krishna.estimated_disposable_income())
    print("Money left to spent", krishna.disposable_income_status())

except Exception as e:
    print("Failed", e)

try:
    student = Student(
        name="Jane Doe",
        email="not-an-email",  # Missing @
        university="State University",
        graduation_year=2026
    )
    print("❌ Should have failed but didn't!")
except Exception as e:
    print(f"✅ Correctly caught invalid email: {e}")