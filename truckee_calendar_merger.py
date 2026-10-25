#!/usr/bin/env python3
"""
Truckee Calendar Merger - Auto-updating unified calendar
Fetches multiple .ics calendar feeds and merges them into a single unified calendar.
"""

import requests
from icalendar import Calendar
from datetime import datetime
import sys
import os
import time

# ==============================================================================
# CONFIGURATION - Add your calendar URLs here
# ==============================================================================
ICS_URLS = [
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=25&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=26&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=44&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=27&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=29&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=24&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=30&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=31&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=32&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=28&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=33&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=47&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=14&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=34&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=35&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=36&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=37&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=38&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=46&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=39&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=40&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=41&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=45&feed=calendar",
    "https://www.townoftruckee.gov/common/modules/iCalendar/iCalendar.aspx?catID=42&feed=calendar"
    # Example format:
    # "https://www.townoftruckee.gov/calendar.ics?CatID=1",
    # "https://www.townoftruckee.gov/calendar.ics?CatID=2",
    # etc.
]

OUTPUT_FILE = "truckee_unified.ics"

# Safety checks: refuse to overwrite the existing file with a bad result
MIN_SUCCESSFUL_FRACTION = 0.5   # at least half the feeds must load
MIN_EVENTS = 1                  # and the merged result must contain events

# Be polite and look like a normal browser; some sites block the default
# "python-requests" user agent and GitHub's datacenter IPs.
HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/124.0 Safari/537.36"
    ),
    "Accept": "text/calendar, text/plain, */*",
}
MAX_ATTEMPTS = 4
DELAY_BETWEEN_FEEDS = 1.5  # seconds
# ==============================================================================

def fetch_ics(url):
    """Fetch an .ics file from a URL, retrying with backoff on failure."""
    for attempt in range(1, MAX_ATTEMPTS + 1):
        try:
            print(f"  Fetching: {url} (attempt {attempt}/{MAX_ATTEMPTS})")
            response = requests.get(url, headers=HEADERS, timeout=30)
            response.raise_for_status()
            return Calendar.from_ical(response.content)
        except Exception as e:
            print(f"  ❌ Error fetching {url}: {e}", file=sys.stderr)
            if attempt < MAX_ATTEMPTS:
                time.sleep(2 ** attempt)  # 2s, 4s, 8s
    return None

def merge_calendars(ics_urls, output_file):
    """Merge multiple .ics calendars into one."""
    print(f"\n🔄 Starting calendar merge at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"📋 Processing {len(ics_urls)} calendars...\n")
    
    # Create a new calendar
    merged_cal = Calendar()
    merged_cal.add('prodid', '-//Truckee Unified Calendar//EN')
    merged_cal.add('version', '2.0')
    merged_cal.add('x-wr-calname', 'Town of Truckee - All Events')
    merged_cal.add('x-wr-timezone', 'America/Los_Angeles')
    merged_cal.add('x-wr-caldesc', f'Unified calendar from {len(ics_urls)} Town of Truckee calendars')
    
    event_count = 0
    successful_calendars = 0
    
    # Fetch and merge each calendar
    for i, url in enumerate(ics_urls, 1):
        print(f"[{i}/{len(ics_urls)}]")
        if i > 1:
            time.sleep(DELAY_BETWEEN_FEEDS)
        cal = fetch_ics(url)
        
        if cal is None:
            continue
        
        successful_calendars += 1
        calendar_events = 0
        
        # Copy all events from this calendar
        for component in cal.walk():
            if component.name == "VEVENT":
                merged_cal.add_component(component)
                event_count += 1
                calendar_events += 1
        
        print(f"  ✅ Added {calendar_events} events\n")
    
    # Safety check: don't clobber a good calendar with a failed run
    if (successful_calendars < len(ics_urls) * MIN_SUCCESSFUL_FRACTION
            or event_count < MIN_EVENTS):
        print(
            f"\n❌ ABORTING: only {successful_calendars}/{len(ics_urls)} calendars "
            f"loaded and {event_count} events found. "
            f"Leaving existing {output_file} untouched.",
            file=sys.stderr,
        )
        sys.exit(1)

    # Write the merged calendar
    with open(output_file, 'wb') as f:
        f.write(merged_cal.to_ical())
    
    print(f"✨ SUCCESS!")
    print(f"📊 Merged {event_count} events from {successful_calendars}/{len(ics_urls)} calendars")
    print(f"💾 Output saved to: {output_file}")
    print(f"📏 File size: {os.path.getsize(output_file):,} bytes")
    
    return output_file

if __name__ == "__main__":
    # Validate configuration
    if not ICS_URLS or all(url.strip().startswith("#") or not url.strip() for url in ICS_URLS):
        print("❌ ERROR: No calendar URLs configured!")
        print("\n📝 Please edit this script and add your calendar URLs to the ICS_URLS list.")
        print("\nTo get the URLs:")
        print("1. Go to https://www.townoftruckee.gov/Calendar.aspx")
        print("2. Right-click each calendar subscription link")
        print("3. Select 'Copy Link Address'")
        print("4. Add each URL to the ICS_URLS list at the top of this script")
        sys.exit(1)
    
    # Clean up URLs (remove empty lines and comments)
    clean_urls = [url.strip() for url in ICS_URLS if url.strip() and not url.strip().startswith("#")]
    
    try:
        merge_calendars(clean_urls, OUTPUT_FILE)
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ FATAL ERROR: {e}", file=sys.stderr)
        sys.exit(1)
