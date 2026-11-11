"""Drill: fails before grading anything, so the verdict is DID NOT RUN."""
import a_module_that_does_not_exist  # noqa: F401
print("ok    never reached")
