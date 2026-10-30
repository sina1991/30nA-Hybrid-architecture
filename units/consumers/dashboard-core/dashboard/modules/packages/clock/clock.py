"""Shared clock implementation for the Dashboard and command line."""
import argparse
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

PERSIAN_DIGITS = str.maketrans('0123456789', '۰۱۲۳۴۵۶۷۸۹')


def current_time(timezone=None):
    now = datetime.now(ZoneInfo(timezone)) if timezone else datetime.now().astimezone()
    return now.strftime('%H:%M:%S').translate(PERSIAN_DIGITS)


def run(data):
    return {"time": current_time(data.get("timezone"))}


def main():
    parser = argparse.ArgumentParser(description='Display the Dashboard clock')
    parser.add_argument('--timezone', help='IANA time zone, for example Asia/Tehran')
    args = parser.parse_args()
    try:
        print(current_time(args.timezone))
    except (ValueError, ZoneInfoNotFoundError):
        parser.error('Unknown time zone')


if __name__ == '__main__':
    main()
