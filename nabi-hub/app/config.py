"""نقطهٔ دسترسی یکپارچه به تنظیمات / Unified config access point.

از بیرونِ لایهٔ core، همه از همین ماژول `cfg` را ایمپورت می‌کنند.
"""
from app.core.settings import Config, cfg

__all__ = ["Config", "cfg"]
