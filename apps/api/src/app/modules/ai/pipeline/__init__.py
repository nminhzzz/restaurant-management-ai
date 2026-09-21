"""Text-to-SQL pipeline steps, in execution order.

    normalize → prompt → generate → guard → execute → interpret

`guard` lives one level up in `app.modules.ai.guard` because it is a security
control rather than a generation step, and is unit-tested on its own.
"""
