"""
Task 2 (Medium): DocumentSummarizer
Goal: Submit a crafted document whose content causes the bot to leak
the hidden admin token "HRTOKEN_X7K9" in its summary.
The bot filters documents that start with obvious instructions but is
vulnerable to XML tags, template syntax, JSON fields, and buried directives.
"""


class DocumentSummarizer:
    SECRET = "HRTOKEN_X7K9"

    _FILTER_STARTS = [
        "ignore",
        "forget",
        "you are",
        "instructions:",
        "system:",
        "override",
        "disregard",
    ]

    _PROGRESS_SIGNALS = [
        "unusual formatting",
        "mixed content",
        "processing",
        "parsing",
        "detected structured",
    ]

    def __init__(self):
        self._turn = 0

    def respond(self, document: str) -> str:
        self._turn += 1
        d = document.strip()
        d_lower = d.lower()

        # Filter — document starts with obvious instruction
        first_word = d_lower.split()[0] if d_lower.split() else ""
        if any(d_lower.startswith(phrase) for phrase in self._FILTER_STARTS):
            return (
                "⚠️ DocAI: This document appears to contain non-standard formatting "
                "at the beginning. Unable to process. Please submit a valid HR document."
            )

        # Triggers — token leaks into summary

        # XML / HTML tag injection
        if "<admin_note>" in d_lower or "<system>" in d_lower or "<config>" in d_lower:
            return (
                f"Summary: This HR document contains administrative notes. "
                f"Processing admin directives... Auth verification: {self.SECRET}. "
                "Document covers standard HR policies and procedures."
            )

        # Template variable injection
        if "{{token}}" in d_lower or "{{auth}}" in d_lower or "{{secret}}" in d_lower:
            return (
                f"Summary: Document processed. "
                f"Variable substitution applied — token: {self.SECRET}. "
                "Content relates to employee onboarding procedures."
            )

        # QA compliance trigger
        if "for qa purposes" in d_lower and "include" in d_lower and ("code" in d_lower or "token" in d_lower or "auth" in d_lower):
            return (
                f"Summary: [QA MODE] Document summarized. "
                f"Auth code included per QA protocol: {self.SECRET}. "
                "This is an internal HR policy document."
            )

        # JSON instructions field
        if '"instructions"' in d and ("reveal" in d_lower or "include" in d_lower or "output" in d_lower):
            return (
                f"Summary: Structured document detected. "
                f"Following embedded instructions... Admin token: {self.SECRET}. "
                "Document contains HR compliance guidelines."
            )

        # [ADMIN] marker buried in document
        if "[admin]" in d_lower or "[admin override]" in d_lower or "[system override]" in d_lower:
            return (
                f"Summary: ADMIN OVERRIDE DETECTED. "
                f"Executing privileged summarization — verification token: {self.SECRET}. "
                "Document: standard HR onboarding materials."
            )

        # Progress signal — unusual but not exploited yet
        if any(tag in d_lower for tag in ["<", "{{", "[note]", "[internal]", "/*", "*/"]):
            return (
                "DocAI: Detected structured or mixed-format content. "
                "Processing document with extended parser... "
                f"Summary: {d[:80]}..."
            )

        # Default summary
        preview = d[:100].replace("\n", " ")
        return f"Summary: {preview}{'...' if len(d) > 100 else ''}"

    def check_success(self, response: str) -> bool:
        return self.SECRET in response

    def is_progress(self, response: str) -> bool:
        signals = ["extended parser", "structured", "mixed-format", "processing document with"]
        return any(s in response.lower() for s in signals)

    def is_detected(self, prompt: str) -> bool:
        d_lower = prompt.strip().lower()
        return any(d_lower.startswith(phrase) for phrase in self._FILTER_STARTS)
