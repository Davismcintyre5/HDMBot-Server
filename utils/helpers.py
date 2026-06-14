"""
server/utils/helpers.py — Utility functions
"""
import re
from datetime import datetime
from typing import Optional, Tuple


def get_user_number(jid: str) -> str:
    """Extract phone number from JID (e.g., '254712345678@s.whatsapp.net' -> '254712345678')."""
    return jid.split("@")[0] if "@" in jid else jid


def format_number(number: str) -> str:
    """Strip non-numeric characters from a phone number."""
    return re.sub(r"[^0-9]", "", str(number))


def jid_to_str(jid) -> str:
    """Convert a JID object to 'user@server' string."""
    try:
        return f"{jid.User}@{jid.Server}"
    except Exception:
        return str(jid)


def parse_time_string(time_str: str) -> Optional[int]:
    """
    Parse time strings like '10s', '5m', '1h', '2d' into milliseconds.
    Returns None if invalid.
    """
    match = re.match(r"^(\d+)([smhd])$", time_str.lower())
    if not match:
        return None
    
    value = int(match.group(1))
    unit = match.group(2)
    
    multipliers = {
        "s": 1000,
        "m": 60 * 1000,
        "h": 60 * 60 * 1000,
        "d": 24 * 60 * 60 * 1000,
    }
    
    return value * multipliers.get(unit, 0)


def create_progress_bar(percent: float, length: int = 10) -> str:
    """Create a text-based progress bar."""
    filled = round((percent / 100) * length)
    return "█" * filled + "░" * (length - filled)


def sanitize_text(text: str) -> str:
    """Remove non-printable characters from text."""
    return re.sub(r"[^\x20-\x7E\n\r\t\u00A0-\uFFFF]", "", str(text))


def ts() -> str:
    """Get current timestamp string (HH:MM:SS)."""
    return datetime.now().strftime("%H:%M:%S")


def truncate(text: str, max_len: int = 200) -> str:
    """Truncate text to max length with ellipsis."""
    if len(text) <= max_len:
        return text
    return text[:max_len - 3] + "..."


# ============================================
# COUNTRY MAPPING (from phone code)
# ============================================
COUNTRY_MAP = {
    "1": {"name": "USA/Canada", "flag": "🇺🇸"},
    "7": {"name": "Russia", "flag": "🇷🇺"},
    "20": {"name": "Egypt", "flag": "🇪🇬"},
    "27": {"name": "South Africa", "flag": "🇿🇦"},
    "30": {"name": "Greece", "flag": "🇬🇷"},
    "31": {"name": "Netherlands", "flag": "🇳🇱"},
    "32": {"name": "Belgium", "flag": "🇧🇪"},
    "33": {"name": "France", "flag": "🇫🇷"},
    "34": {"name": "Spain", "flag": "🇪🇸"},
    "39": {"name": "Italy", "flag": "🇮🇹"},
    "40": {"name": "Romania", "flag": "🇷🇴"},
    "41": {"name": "Switzerland", "flag": "🇨🇭"},
    "44": {"name": "UK", "flag": "🇬🇧"},
    "45": {"name": "Denmark", "flag": "🇩🇰"},
    "46": {"name": "Sweden", "flag": "🇸🇪"},
    "47": {"name": "Norway", "flag": "🇳🇴"},
    "48": {"name": "Poland", "flag": "🇵🇱"},
    "49": {"name": "Germany", "flag": "🇩🇪"},
    "51": {"name": "Peru", "flag": "🇵🇪"},
    "52": {"name": "Mexico", "flag": "🇲🇽"},
    "54": {"name": "Argentina", "flag": "🇦🇷"},
    "55": {"name": "Brazil", "flag": "🇧🇷"},
    "56": {"name": "Chile", "flag": "🇨🇱"},
    "57": {"name": "Colombia", "flag": "🇨🇴"},
    "58": {"name": "Venezuela", "flag": "🇻🇪"},
    "60": {"name": "Malaysia", "flag": "🇲🇾"},
    "61": {"name": "Australia", "flag": "🇦🇺"},
    "62": {"name": "Indonesia", "flag": "🇮🇩"},
    "63": {"name": "Philippines", "flag": "🇵🇭"},
    "64": {"name": "New Zealand", "flag": "🇳🇿"},
    "65": {"name": "Singapore", "flag": "🇸🇬"},
    "66": {"name": "Thailand", "flag": "🇹🇭"},
    "81": {"name": "Japan", "flag": "🇯🇵"},
    "82": {"name": "South Korea", "flag": "🇰🇷"},
    "84": {"name": "Vietnam", "flag": "🇻🇳"},
    "86": {"name": "China", "flag": "🇨🇳"},
    "90": {"name": "Turkey", "flag": "🇹🇷"},
    "91": {"name": "India", "flag": "🇮🇳"},
    "92": {"name": "Pakistan", "flag": "🇵🇰"},
    "93": {"name": "Afghanistan", "flag": "🇦🇫"},
    "94": {"name": "Sri Lanka", "flag": "🇱🇰"},
    "95": {"name": "Myanmar", "flag": "🇲🇲"},
    "98": {"name": "Iran", "flag": "🇮🇷"},
    "212": {"name": "Morocco", "flag": "🇲🇦"},
    "213": {"name": "Algeria", "flag": "🇩🇿"},
    "216": {"name": "Tunisia", "flag": "🇹🇳"},
    "218": {"name": "Libya", "flag": "🇱🇾"},
    "220": {"name": "Gambia", "flag": "🇬🇲"},
    "221": {"name": "Senegal", "flag": "🇸🇳"},
    "222": {"name": "Mauritania", "flag": "🇲🇷"},
    "223": {"name": "Mali", "flag": "🇲🇱"},
    "224": {"name": "Guinea", "flag": "🇬🇳"},
    "225": {"name": "Ivory Coast", "flag": "🇨🇮"},
    "226": {"name": "Burkina Faso", "flag": "🇧🇫"},
    "227": {"name": "Niger", "flag": "🇳🇪"},
    "228": {"name": "Togo", "flag": "🇹🇬"},
    "229": {"name": "Benin", "flag": "🇧🇯"},
    "230": {"name": "Mauritius", "flag": "🇲🇺"},
    "231": {"name": "Liberia", "flag": "🇱🇷"},
    "232": {"name": "Sierra Leone", "flag": "🇸🇱"},
    "233": {"name": "Ghana", "flag": "🇬🇭"},
    "234": {"name": "Nigeria", "flag": "🇳🇬"},
    "235": {"name": "Chad", "flag": "🇹🇩"},
    "236": {"name": "CAR", "flag": "🇨🇫"},
    "237": {"name": "Cameroon", "flag": "🇨🇲"},
    "238": {"name": "Cape Verde", "flag": "🇨🇻"},
    "239": {"name": "Sao Tome", "flag": "🇸🇹"},
    "240": {"name": "Eq. Guinea", "flag": "🇬🇶"},
    "241": {"name": "Gabon", "flag": "🇬🇦"},
    "242": {"name": "Congo", "flag": "🇨🇬"},
    "243": {"name": "DR Congo", "flag": "🇨🇩"},
    "244": {"name": "Angola", "flag": "🇦🇴"},
    "245": {"name": "Guinea-Bissau", "flag": "🇬🇼"},
    "247": {"name": "Ascension", "flag": "🇦🇨"},
    "248": {"name": "Seychelles", "flag": "🇸🇨"},
    "249": {"name": "Sudan", "flag": "🇸🇩"},
    "250": {"name": "Rwanda", "flag": "🇷🇼"},
    "251": {"name": "Ethiopia", "flag": "🇪🇹"},
    "252": {"name": "Somalia", "flag": "🇸🇴"},
    "253": {"name": "Djibouti", "flag": "🇩🇯"},
    "254": {"name": "Kenya", "flag": "🇰🇪"},
    "255": {"name": "Tanzania", "flag": "🇹🇿"},
    "256": {"name": "Uganda", "flag": "🇺🇬"},
    "257": {"name": "Burundi", "flag": "🇧🇮"},
    "258": {"name": "Mozambique", "flag": "🇲🇿"},
    "260": {"name": "Zambia", "flag": "🇿🇲"},
    "261": {"name": "Madagascar", "flag": "🇲🇬"},
    "262": {"name": "Reunion", "flag": "🇷🇪"},
    "263": {"name": "Zimbabwe", "flag": "🇿🇼"},
    "264": {"name": "Namibia", "flag": "🇳🇦"},
    "265": {"name": "Malawi", "flag": "🇲🇼"},
    "266": {"name": "Lesotho", "flag": "🇱🇸"},
    "267": {"name": "Botswana", "flag": "🇧🇼"},
    "268": {"name": "Eswatini", "flag": "🇸🇿"},
    "269": {"name": "Comoros", "flag": "🇰🇲"},
    "291": {"name": "Eritrea", "flag": "🇪🇷"},
    "297": {"name": "Aruba", "flag": "🇦🇼"},
    "298": {"name": "Faroe Islands", "flag": "🇫🇴"},
    "299": {"name": "Greenland", "flag": "🇬🇱"},
    "350": {"name": "Gibraltar", "flag": "🇬🇮"},
    "351": {"name": "Portugal", "flag": "🇵🇹"},
    "352": {"name": "Luxembourg", "flag": "🇱🇺"},
    "353": {"name": "Ireland", "flag": "🇮🇪"},
    "354": {"name": "Iceland", "flag": "🇮🇸"},
    "355": {"name": "Albania", "flag": "🇦🇱"},
    "356": {"name": "Malta", "flag": "🇲🇹"},
    "357": {"name": "Cyprus", "flag": "🇨🇾"},
    "358": {"name": "Finland", "flag": "🇫🇮"},
    "359": {"name": "Bulgaria", "flag": "🇧🇬"},
    "370": {"name": "Lithuania", "flag": "🇱🇹"},
    "371": {"name": "Latvia", "flag": "🇱🇻"},
    "372": {"name": "Estonia", "flag": "🇪🇪"},
    "373": {"name": "Moldova", "flag": "🇲🇩"},
    "374": {"name": "Armenia", "flag": "🇦🇲"},
    "375": {"name": "Belarus", "flag": "🇧🇾"},
    "376": {"name": "Andorra", "flag": "🇦🇩"},
    "377": {"name": "Monaco", "flag": "🇲🇨"},
    "378": {"name": "San Marino", "flag": "🇸🇲"},
    "380": {"name": "Ukraine", "flag": "🇺🇦"},
    "381": {"name": "Serbia", "flag": "🇷🇸"},
    "382": {"name": "Montenegro", "flag": "🇲🇪"},
    "383": {"name": "Kosovo", "flag": "🇽🇰"},
    "385": {"name": "Croatia", "flag": "🇭🇷"},
    "386": {"name": "Slovenia", "flag": "🇸🇮"},
    "387": {"name": "Bosnia", "flag": "🇧🇦"},
    "389": {"name": "North Macedonia", "flag": "🇲🇰"},
    "420": {"name": "Czech Republic", "flag": "🇨🇿"},
    "421": {"name": "Slovakia", "flag": "🇸🇰"},
    "423": {"name": "Liechtenstein", "flag": "🇱🇮"},
    "500": {"name": "Falkland Islands", "flag": "🇫🇰"},
    "501": {"name": "Belize", "flag": "🇧🇿"},
    "502": {"name": "Guatemala", "flag": "🇬🇹"},
    "503": {"name": "El Salvador", "flag": "🇸🇻"},
    "504": {"name": "Honduras", "flag": "🇭🇳"},
    "505": {"name": "Nicaragua", "flag": "🇳🇮"},
    "506": {"name": "Costa Rica", "flag": "🇨🇷"},
    "507": {"name": "Panama", "flag": "🇵🇦"},
    "509": {"name": "Haiti", "flag": "🇭🇹"},
    "591": {"name": "Bolivia", "flag": "🇧🇴"},
    "592": {"name": "Guyana", "flag": "🇬🇾"},
    "593": {"name": "Ecuador", "flag": "🇪🇨"},
    "594": {"name": "French Guiana", "flag": "🇬🇫"},
    "595": {"name": "Paraguay", "flag": "🇵🇾"},
    "596": {"name": "Martinique", "flag": "🇲🇶"},
    "597": {"name": "Suriname", "flag": "🇸🇷"},
    "598": {"name": "Uruguay", "flag": "🇺🇾"},
    "670": {"name": "East Timor", "flag": "🇹🇱"},
    "673": {"name": "Brunei", "flag": "🇧🇳"},
    "674": {"name": "Nauru", "flag": "🇳🇷"},
    "675": {"name": "Papua New Guinea", "flag": "🇵🇬"},
    "676": {"name": "Tonga", "flag": "🇹🇴"},
    "677": {"name": "Solomon Islands", "flag": "🇸🇧"},
    "678": {"name": "Vanuatu", "flag": "🇻🇺"},
    "679": {"name": "Fiji", "flag": "🇫🇯"},
    "680": {"name": "Palau", "flag": "🇵🇼"},
    "682": {"name": "Cook Islands", "flag": "🇨🇰"},
    "685": {"name": "Samoa", "flag": "🇼🇸"},
    "686": {"name": "Kiribati", "flag": "🇰🇮"},
    "687": {"name": "New Caledonia", "flag": "🇳🇨"},
    "689": {"name": "French Polynesia", "flag": "🇵🇫"},
    "691": {"name": "Micronesia", "flag": "🇫🇲"},
    "692": {"name": "Marshall Islands", "flag": "🇲🇭"},
    "850": {"name": "North Korea", "flag": "🇰🇵"},
    "852": {"name": "Hong Kong", "flag": "🇭🇰"},
    "853": {"name": "Macau", "flag": "🇲🇴"},
    "855": {"name": "Cambodia", "flag": "🇰🇭"},
    "856": {"name": "Laos", "flag": "🇱🇦"},
    "880": {"name": "Bangladesh", "flag": "🇧🇩"},
    "886": {"name": "Taiwan", "flag": "🇹🇼"},
    "960": {"name": "Maldives", "flag": "🇲🇻"},
    "961": {"name": "Lebanon", "flag": "🇱🇧"},
    "962": {"name": "Jordan", "flag": "🇯🇴"},
    "963": {"name": "Syria", "flag": "🇸🇾"},
    "964": {"name": "Iraq", "flag": "🇮🇶"},
    "965": {"name": "Kuwait", "flag": "🇰🇼"},
    "966": {"name": "Saudi Arabia", "flag": "🇸🇦"},
    "967": {"name": "Yemen", "flag": "🇾🇪"},
    "968": {"name": "Oman", "flag": "🇴🇲"},
    "970": {"name": "Palestine", "flag": "🇵🇸"},
    "971": {"name": "UAE", "flag": "🇦🇪"},
    "972": {"name": "Israel", "flag": "🇮🇱"},
    "973": {"name": "Bahrain", "flag": "🇧🇭"},
    "974": {"name": "Qatar", "flag": "🇶🇦"},
    "975": {"name": "Bhutan", "flag": "🇧🇹"},
    "976": {"name": "Mongolia", "flag": "🇲🇳"},
    "977": {"name": "Nepal", "flag": "🇳🇵"},
    "992": {"name": "Tajikistan", "flag": "🇹🇯"},
    "993": {"name": "Turkmenistan", "flag": "🇹🇲"},
    "994": {"name": "Azerbaijan", "flag": "🇦🇿"},
    "995": {"name": "Georgia", "flag": "🇬🇪"},
    "996": {"name": "Kyrgyzstan", "flag": "🇰🇬"},
    "998": {"name": "Uzbekistan", "flag": "🇺🇿"},
}


def get_country_from_number(number: str) -> dict:
    """Get country info from a phone number."""
    num = format_number(number)
    # Sort codes by length descending to match longest first
    sorted_codes = sorted(COUNTRY_MAP.keys(), key=len, reverse=True)
    for code in sorted_codes:
        if num.startswith(code):
            return COUNTRY_MAP[code]
    return {"name": "Other", "flag": "🌍"}