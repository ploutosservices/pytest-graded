"""Drill: grades two cases, one fails, exits non-zero, so the verdict is FAILED."""
import sys
print("ok    a case that holds")
print("FAIL  a case that does not")
print("      expected 3, got 4")
sys.exit(1)
