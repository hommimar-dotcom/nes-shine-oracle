import sys
sys.path.insert(0, '.')
from agents import OracleBrain

brain = OracleBrain.__new__(OracleBrain)

cases = [
    "Career Path Reading | Financial Stability",
    "Bedroom Secrets | His Deepest Intimacy Desires & Kinks",
    "Brutally Honest Scan | Compatibility",
    "Is he cheating on me?",
    "A completely normal reading about love"
]

for t in cases:
    res, changed = brain._sanitize_topic(t)
    print(f"IN: {t}")
    print(f"OUT: {res}")
    print(f"CHANGED: {changed}\n")
