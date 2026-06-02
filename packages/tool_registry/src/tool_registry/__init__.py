"""Wright Tool Registry — dynamic loading of engineering tools via BaseTool pattern.

Every tool inherits from BaseTool and implements the Template Method Pattern
with online/offline fallback (write-through cache).
"""
