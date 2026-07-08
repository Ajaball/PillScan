"""
Leaflet Summarizer Schemas
Pydantic response model for the AI leaflet/prescription summary endpoint.
"""

from pydantic import BaseModel


class LeafletSummaryResponse(BaseModel):
    """Arabic summary of a scanned medication leaflet / prescription."""

    summary: str                 # Arabic summary text (may use markdown-style bullets)
    provider: str                # "gemini" | "openai"
    model: str                   # model id used to generate the summary
    is_configured: bool          # False when no API key is set (summary is a setup hint)
    disclaimer_ar: str           # safety note shown under the summary (Arabic)
    disclaimer_en: str           # safety note shown under the summary (English)
