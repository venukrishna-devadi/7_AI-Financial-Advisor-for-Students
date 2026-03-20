                    ┌─────────────────────────────────────┐
                    │         🎯 USER INTERFACE           │
                    │         (ui/ folder)                │
                    │    What the student sees/clicks     │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │         🎮 ORCHESTRATOR              │
                    │         (runners/ folder)            │
                    │    Manages the game flow             │
                    │    Handles "Start","Choice","Save"   │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │         🧠 BRAIN (The Graph)         │
                    │         (graph/ folder)              │
                    │    Decides WHICH agent runs next     │
                    │    "Planner → Executor → Verifier"   │
                    └─────────────────┬───────────────────┘
                    ┌─────────────────┼───────────────────┐
                    ▼                 ▼                   ▼
            ┌───────────────┐ ┌───────────────┐ ┌───────────────┐
            │  🤖 AGENT 1   │ │  🤖 AGENT 2   │ │  🤖 AGENT 3   │
            │  (planner.py) │ │ (executor.py) │ │ (verifier.py) │
            │  in agents/   │ │  in agents/   │ │  in agents/   │
            └───────┬───────┘ └───────┬───────┘ └───────┬───────┘
                    │                  │                  │
                    └──────────────────┼──────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │         📦 DATA MODELS               │
                    │         (schemas/ folder)            │
                    │    Defines WHAT data looks like      │
                    │    "Transaction","Student","Budget"  │
                    └─────────────────┬───────────────────┘
                                      │
                    ┌─────────────────▼───────────────────┐
                    │         🔧 UTILITIES                 │
                    │         (utils/ folder)              │
                    │    Helper functions all agents use   │
                    │    "Parse PDF","OCR","Calculate"     │
                    └──────────────────────────────────────┘

📁 FOLDER-BY-FOLDER BREAKDOWN

1. schemas/ - THE BLUEPRINT 📐

Purpose: Defines the SHAPE of all data in your system 

Think of this as:

🏗️ Architect's blueprint - Shows exactly what a "Transaction" looks like
📝 Contract between all files - Everyone agrees on data format
🛡️ Guard - Prevents invalid data from entering system
Connection to others:

# schemas/transaction.py
class Transaction(BaseModel):
    amount: float        # Must be number
    date: datetime       # Must be date
    category: str        # Must be text
    # If someone tries to set amount="twenty dollars" → ERROR!
✅ agents/ use these to know what data they receive
✅ graph/ uses these to update state
✅ ui/ uses these to display information

2. agents/ - THE WORKERS 👷

Purpose: Each agent does ONE specific job

Think of this as:

🏭 Factory workers - Each has a specialized skill
🤖 AI specialists - One plans, one executes, one verifies

# agents/planner.py
class PlannerAgent:
    def analyze(self, student_data):
        # ONLY job: Look at spending and make plan
        # Takes input → Returns plan
        # Doesn't care about UI or databases

Connection to others:

✅ Called by graph/ when it's their turn
✅ Use schemas/ to understand input/output format
✅ Use utils/ for helper functions (like calculate interest)

3. graph/ - THE BOSS 👔

Purpose: Decides WHICH agent runs WHEN

Think of this as:

🎯 Project manager - Knows the workflow
🚦 Traffic controller - Directs the flow
📋 Decision maker - "If this happens, do that"

What goes inside:
# graph/builder.py
if student_just_started:
    run(planner_agent)    # First, make a plan
elif new_transaction_added:
    run(tracker_agent)     # Then, track spending
elif budget_exceeded:
    run(alert_agent)       # Finally, warn student

Connection to others:

✅ Imports all agents from agents/
✅ Uses schemas/ to check state
✅ Called by runners/ when game starts

4. runners/ - THE CONDUCTOR 🎭

Purpose: Manages the ENTIRE experience from start to finish

Think of this as:

🎬 Movie director - "Action! Cut! Next scene!"
🎮 Game master - Handles save/load, player choices
What goes inside:
# runners/hitl_runner.py
def start_new_game():
    # 1. Create initial state
    # 2. Tell graph to start
    # 3. Wait for result
    # 4. Show to user
    
def save_game():
    # Take current state → Save to file

Connection to others:

✅ Creates the graph/ and tells it to run
✅ Talks to ui/ to show results
✅ Uses schemas/ to save/load state

5. ui/ - THE FACE 🎨

Purpose: What the student SEES and CLICKS

Think of this as:

🖥️ Storefront window - Displays everything nicely
🖱️ Remote control - User presses buttons here
What goes inside:
# ui/app.py
st.button("Add Expense")  # User clicks
st.write(transaction)      # User sees

Connection to others:

✅ Calls runners/ when user clicks buttons
✅ Gets data from runners/ to display
✅ Uses schemas/ to format data nicely


6. utils/ - THE TOOLBOX 🔧

Purpose: Helper functions ANY file can use

Think of this as:

🧰 Shared toolbox - Everyone can grab these tools
📚 Library - Reusable code

Connection to others:

✅ Imported by ANY file that needs help
✅ No knowledge of other files (pure functions)



🔄 HOW DATA FLOWS THROUGH YOUR APP

Example: Student adds a new expense

1. USER ACTION (ui/app.py)
   └── Student clicks "Add Expense" button
       └── Calls runners/hitl_runner.py

2. ROUTER (runners/hitl_runner.py)
   └── Gets current state from schemas/state.py
   └── Tells graph/builder.py to run with new data

3. ORCHESTRATOR (graph/builder.py)
   └── Checks: "What should happen next?"
   └── Decides: "Run the Analyzer agent"
   └── Calls agents/analyzer.py

4. AGENT (agents/analyzer.py)
   └── Takes student data (from schemas/)
   └── Uses utils/ocr.py to read receipt
   └── Returns analysis result

5. BACK TO ORCHESTRATOR
   └── Updates state using schemas/
   └── Decides next agent (maybe Tracker)

6. BACK TO ROUTER
   └── Gets final state
   └── Saves if needed

7. BACK TO UI
   └── Displays updated information


📊 FOLDER RESPONSIBILITIES CHEAT SHEET

Folder	Job	Input	Output	Knows About
schemas/	Define data shapes	Nothing	Data models	Nothing
agents/	Do one AI task	Student data	Analysis	schemas/, utils/
graph/	Orchestrate flow	Current state	Next action	agents/, schemas/
runners/	Manage game loop	User action	Updated state	graph/, schemas/
ui/	Show interface	User clicks	User action	runners/, schemas/
utils/	Helper functions	Raw data	Processed data	Nothing



For the Financial Advisor project, let's map it out:

┌─────────────────────────────────────────────────────────────────┐
│                      OUR FINANCIAL ADVISOR                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                   │
│  📁 schemas/                                                      │
│  ├── student.py      → What data do we store about a student?    │
│  ├── transaction.py  → What does one purchase look like?         │
│  ├── budget.py       → How do we represent a budget?             │
│  └── goal.py         → What is a savings goal?                   │
│                                                                   │
│  📁 agents/                                                        │
│  ├── analyzer.py     → Looks at spending, finds patterns         │
│  ├── planner.py      → Creates budget based on goals             │
│  ├── tracker.py      → Monitors actual vs planned                │
│  ├── advisor.py      → Gives suggestions                         │
│  └── alert.py        → Warns about problems                      │
│                                                                   │
│  📁 graph/                                                         │
│  └── builder.py      → Decides: "New data? Run analyzer first!"  │
│                                                                   │
│  📁 runners/                                                        │
│  └── financial_runner.py → Handles "Start","Add expense","Save"  │
│                                                                   │
│  📁 ui/                                                             │
│  ├── dashboard.py    → Main view with charts                      │
│  ├── input_forms.py  → Forms to add expenses                      │
│  └── uploaders.py    → PDF/image upload interface                │
│                                                                   │
│  📁 utils/                                                         │
│  ├── pdf_parser.py   → Extract text from bank statements         │
│  ├── #ocr_helper.py   → Read text from images                     │
│  ├── calculators.py  → Interest, projections, etc.               │
│  └── #validators.py   → Check if data makes sense                 │
└─────────────────────────────────────────────────────────────────┘


🚀 YOUR CODING ORDER (To Avoid Confusion)

Step 1: Build the Foundation (schemas/)

Start here because everything else depends on it
# Create these files FIRST
schemas/student.py
schemas/transaction.py
schemas/budget.py
schemas/goal.py


Step 2: Build the Tools (utils/)

Create helpers that agents will use
utils/pdf_parser.py
utils/ocr_helper.py
utils/calculators.py
utils/validators.py

Step 3: Build One Simple Agent (agents/)

Start with just the Analyzer
agents/analyzer.py  # Only this one first


Step 4: Build Simple Graph (graph/)

Connect just the Analyzer
graph/builder.py  # Only has analyzer node

Step 5: Build Simple Runner (runners/)

Test the flow
runners/simple_runner.py

Step 6: Build Simple UI (ui/)

See it work!
ui/simple_app.py

Step 7: Add More Agents

One by one, testing each
agents/planner.py
agents/tracker.py
agents/advisor.py
agents/alert.py


Step 8: Enhance Graph

Add conditional routing
graph/builder.py  # Add more nodes


Step 9: Build Full Runner

Add save/load, error handling
runners/financial_runner.py


Step 10: Build Beautiful UI

Make it look good
ui/dashboard.py
ui/input_forms.py
ui/uploaders.py


# For EACH file you create, answer:

FILE NAME: analyzer.py
LOCATION: agents/ folder
PURPOSE: Analyzes spending patterns
INPUT: Student object (from schemas/student.py)
OUTPUT: Analysis report with insights
DEPENDS ON: 
    - schemas/student.py
    - utils/calculators.py
CALLED BY: graph/builder.py when new data arrives
CALLS: Nothing (pure function)