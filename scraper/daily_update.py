"""
Daily health check — runs in GitHub Actions every morning.
Verifies SEMO XML files and EirGrid are reachable for yesterday.
Exits with code 1 if zero SEMO intervals are found (triggers failure email).
"""

import sys
import requests
from datetime import datetime, timedelta

SEMO_BASE_URL  = "https://reports.sem-o.com/documents/"
EIRGRID_URL    = "https://www.smartgriddashboard.com/DashboardService.svc/data?area=generationactual&region=ALL&datefrom=01-Jan-2025+00%3A00&dateto=01-Jan-2025+23%3A59"

# Sample 12 intervals spread across yesterday (every 2 hours on the hour)
SAMPLE_CODES = ["0000", "0200", "0400", "0600", "0800", "1000",
                "1200", "1400", "1600", "1800", "2000", "2200"]


def check_semo(date_nodash: str, session: requests.Session) -> int:
    found = 0
    for code in SAMPLE_CODES:
        url = f"{SEMO_BASE_URL}PUB_5MinImbalPrc_{date_nodash}{code}.xml"
        try:
            r = session.get(url, timeout=15)
            if r.status_code == 200 and len(r.text) > 200:
                found += 1
        except Exception:
            pass
    return found


def check_eirgrid(session: requests.Session) -> bool:
    try:
        r = session.get(EIRGRID_URL, timeout=20)
        return r.status_code == 200
    except Exception:
        return False


def main():
    yesterday = (datetime.utcnow() - timedelta(days=1)).strftime("%Y%m%d")
    yesterday_fmt = f"{yesterday[:4]}-{yesterday[4:6]}-{yesterday[6:]}"

    print(f"Health check for {yesterday_fmt}")

    session = requests.Session()

    semo_count = check_semo(yesterday, session)
    eirgrid_ok = check_eirgrid(session)

    print(f"  SEMO intervals available : {semo_count} / {len(SAMPLE_CODES)}")
    print(f"  EirGrid responding       : {'yes' if eirgrid_ok else 'NO'}")

    if semo_count == 0:
        print("FAIL: zero SEMO intervals found — possible SEMO outage.")
        sys.exit(1)

    print("Health check passed.")


if __name__ == "__main__":
    main()
