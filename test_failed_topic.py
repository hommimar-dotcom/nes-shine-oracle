import sys
sys.path.insert(0, '.')
from agents import OracleBrain

brain = OracleBrain.__new__(OracleBrain)

t1 = "Bedroom Secrets Psychic Reading | His Deepest Intimacy Desires & Kinks | Secret Fantasies Revealed | Brutally Honest Scan | Compatibility"

res1, changed1 = brain._sanitize_topic(t1)

print("IN :", t1)
print("OUT:", res1)
print("CHANGED:", changed1)
