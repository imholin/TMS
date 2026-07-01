"""
backend/utils/helpers.py
Common utility functions for the TMS project.
"""
from __future__ import annotations

import math
import re
import random
import string
from datetime import datetime, timedelta, date
from typing import Any, Callable, TypeVar, Iterator

T = TypeVar("T")


# ---------------------------------------------------------------------------
# ID / Number Generation
# ---------------------------------------------------------------------------

def generate_no(prefix: str) -> str:
    """
    Generate a unique identifier string.

    Format: <PREFIX><YYYYMMDD><HHMMSS><4 random digits>

    Examples
    --------
    >>> generate_no("ORD")   # ORD202606301012305123
    >>> generate_no("SHP")   # SHP202606301012305123
    >>> generate_no("RT")    # RT202606301012305123
    >>> generate_no("EXP")   # EXP202606301012305123
    """
    now = datetime.now()
    date_part = now.strftime("%Y%m%d%H%M%S")
    rand_part = "".join(random.choices(string.digits, k=4))
    return f"{prefix}{date_part}{rand_part}"


def generate_route_no() -> str:
    """Alias for generate_no('RT')."""
    return generate_no("RT")


# ---------------------------------------------------------------------------
# Haversine Distance
# ---------------------------------------------------------------------------

def haversine(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Calculate the great-circle distance between two points on Earth
    using the Haversine formula.

    Parameters
    ----------
    lat1, lon1 : float
        Latitude and longitude of point 1 (in decimal degrees).
    lat2, lon2 : float
        Latitude and longitude of point 2 (in decimal degrees).

    Returns
    -------
    float
        Distance in kilometres (km).

    Example
    -------
    >>> round(haversine(31.2304, 121.4737, 39.9042, 116.4074), 2)
    1068.62
    """
    R = 6371.0088  # Earth mean radius in km

    lat1_rad = math.radians(lat1)
    lat2_rad = math.radians(lat2)
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2) ** 2
    )
    c = 2 * math.asin(math.sqrt(a))

    return round(R * c, 4)


# ---------------------------------------------------------------------------
# Chinese Validators
# ---------------------------------------------------------------------------

def validate_phone(phone: str) -> bool:
    """
    Validate a Chinese mobile phone number.

    Accepts formats: 13800138000, +86 13800138000, 08613800138000
    Strips leading +86 / 086 before checking.

    Returns
    -------
    bool
        True if the number is a valid 11-digit Chinese mobile.
    """
    if not phone:
        return False

    # Normalise: remove spaces, leading +86 or 086
    cleaned = re.sub(r"^(\+86|086)", "", phone.strip())

    # Must be exactly 11 digits starting with 1
    return bool(re.fullmatch(r"1[3-9]\d{9}", cleaned))


def validate_id_card(id_card: str) -> bool:
    """
    Validate a Chinese 18-digit resident identity card.

    The last character may be 'X' (uppercase).

    Returns
    -------
    bool
        True if the ID card format is valid.

    Note
    ----
    This only checks format; a full checksum validation would require
    the Wi coefficient / Yi sum lookup table.
    """
    if not id_card:
        return False

    pattern = r"^[1-9]\d{5}(19|20)\d{2}(0[1-9]|1[0-2])(0[1-9]|[12]\d|3[01])\d{3}[\dX]$"
    return bool(re.fullmatch(pattern, id_card.upper()))


def validate_plate_no(plate: str) -> bool:
    """
    Validate a Chinese vehicle plate number.

    Supports both civilian (e.g. 沪A12345) and new-energy (e.g. 沪AD12345)
    plate formats.

    Returns
    -------
    bool
        True if the plate format is valid.
    """
    if not plate:
        return False

    # Civilian plate: province letter + one letter + 5 digits/letters
    civilian = r"^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉闽贵粤青藏川宁琼使领][A-Z][A-HJ-NP-Z0-9]{5}$"
    # New-energy plate: province + 2 letters + 5 digits/letters
    new_energy = (
        r"^[京津沪渝冀豫云辽黑湘皖鲁新苏浙赣鄂桂甘晋蒙陕吉"
        r"闽贵粤青藏川宁琼使领]"
        r"[A-Z]{2}"
        r"[A-HJ-NP-Z0-9]{5}$"
    )

    return bool(re.fullmatch(civilian, plate.upper())) or bool(
        re.fullmatch(new_energy, plate.upper())
    )


# ---------------------------------------------------------------------------
# Formatting
# ---------------------------------------------------------------------------

def format_currency(amount: float) -> str:
    """
    Format a numeric amount as a Chinese ¥ currency string.

    Parameters
    ----------
    amount : float
        Monetary value.

    Returns
    -------
    str
        Formatted string, e.g. ¥1,234.56  /  ¥0.00  /  ¥-1,000.00

    Examples
    --------
    >>> format_currency(1234.567)
    '¥1,234.57'
    >>> format_currency(0)
    '¥0.00'
    >>> format_currency(-1000)
    '¥-1,000.00'
    """
    return f"¥{amount:,.2f}"


def format_weight(kg: float) -> str:
    """
    Format a weight in kilograms with unit.

    Returns
    -------
    str
        e.g. '5.50 kg'
    """
    return f"{kg:.2f} kg"


def format_distance(km: float) -> str:
    """
    Format a distance in kilometres with unit.

    Returns
    -------
    str
        e.g. '1,234.56 km'
    """
    return f"{km:,.2f} km"


# ---------------------------------------------------------------------------
# Date / Range Helpers
# ---------------------------------------------------------------------------

def date_range(start: str | date | datetime, end: str | date | datetime) -> list[date]:
    """
    Generate a list of dates from ``start`` (inclusive) to ``end`` (inclusive).

    Parameters
    ----------
    start : str | date | datetime
        Start date. ISO string format (YYYY-MM-DD) is accepted.
    end : str | date | datetime
        End date. ISO string format is accepted.

    Returns
    -------
    list[date]
        List of ``datetime.date`` objects.

    Examples
    --------
    >>> dr = date_range("2026-07-01", "2026-07-05")
    >>> len(dr)
    5

    >>> dr = date_range(date(2026, 7, 1), date(2026, 7, 3))
    >>> dr[0]
    datetime.date(2026, 7, 1)
    """
    if isinstance(start, str):
        start = datetime.fromisoformat(start.strip()).date()
    elif isinstance(start, datetime):
        start = start.date()

    if isinstance(end, str):
        end = datetime.fromisoformat(end.strip()).date()
    elif isinstance(end, datetime):
        end = end.date()

    result: list[date] = []
    current = start
    while current <= end:
        result.append(current)
        current += timedelta(days=1)
    return result


def parse_date(value: str | date | None) -> date | None:
    """
    Parse a date from various formats.

    Accepts: YYYY-MM-DD, YYYY/MM/DD, ISO datetime strings, ``date`` /
    ``datetime`` objects.

    Returns
    -------
    date | None
    """
    if value is None:
        return None
    if isinstance(value, date):
        return value if not isinstance(value, datetime) else value.date()
    value = value.strip()
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y%m%d"):
        try:
            return datetime.strptime(value, fmt).date()
        except ValueError:
            pass
    # Try ISO format (with time)
    try:
        return datetime.fromisoformat(value).date()
    except ValueError:
        return None


def format_datetime(dt: datetime | None, fmt: str = "%Y-%m-%d %H:%M:%S") -> str:
    """
    Format a datetime object to a string.

    Returns an empty string if ``dt`` is None.
    """
    if dt is None:
        return ""
    if isinstance(dt, datetime):
        return dt.strftime(fmt)
    return str(dt)


def today() -> date:
    """Return today's date (local time)."""
    return date.today()


def now() -> datetime:
    """Return current datetime (local time)."""
    return datetime.now()


# ---------------------------------------------------------------------------
# Pagination
# ---------------------------------------------------------------------------

def paginate_list(
    items: list[T],
    page: int | str = 1,
    per_page: int | str = 20,
) -> dict[str, Any]:
    """
    Paginate an in-memory list of items.

    Parameters
    ----------
    items : list
        Full list of items to paginate.
    page : int | str, default 1
        Current page number (1-indexed).
    per_page : int | str, default 20
        Number of items per page.

    Returns
    -------
    dict
        ``{'items': [...], 'total': N, 'page': P, 'per_page': PP,
        'pages': TOTAL_PAGES}``
        Returns empty ``items`` list when page is out of range.

    Examples
    --------
    >>> data = list(range(100))
    >>> p = paginate_list(data, page=2, per_page=10)
    >>> len(p['items'])
    10
    >>> p['total']
    100
    >>> p['page']
    2
    """
    try:
        page = max(1, int(page))
    except (TypeError, ValueError):
        page = 1

    try:
        per_page = max(1, int(per_page))
    except (TypeError, ValueError):
        per_page = 20

    total = len(items)
    total_pages = math.ceil(total / per_page) if per_page > 0 else 0

    start = (page - 1) * per_page
    end = start + per_page

    return {
        "items": items[start:end],
        "total": total,
        "page": page,
        "per_page": per_page,
        "pages": total_pages,
    }


# ---------------------------------------------------------------------------
# General Helpers
# ---------------------------------------------------------------------------

def chunked(iterable: list[T], size: int) -> Iterator[list[T]]:
    """
    Split an iterable into chunks of at most ``size`` elements.

    Yields
    ------
    list[T]
        Each chunk.

    Examples
    --------
    >>> list(chunked([1,2,3,4,5], 2))
    [[1, 2], [3, 4], [5]]
    """
    for i in range(0, len(iterable), size):
        yield iterable[i : i + size]


def clamp(value: float | int, minimum: float | int, maximum: float | int) -> float | int:
    """Clamp a value between minimum and maximum."""
    return max(minimum, min(value, maximum))


def safe_float(value: Any, default: float = 0.0) -> float:
    """Safely convert a value to float, returning ``default`` on failure."""
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def safe_int(value: Any, default: int = 0) -> int:
    """Safely convert a value to int, returning ``default`` on failure."""
    try:
        return int(float(value))
    except (TypeError, ValueError):
        return default


def truncate(text: str, length: int = 50, suffix: str = "…") -> str:
    """Truncate ``text`` to at most ``length`` characters."""
    if len(text) <= length:
        return text
    return text[: length - len(suffix)] + suffix
