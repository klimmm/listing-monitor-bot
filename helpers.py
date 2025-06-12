import os
from datetime import datetime, timedelta
import re


def print_change(current_offer=None, previous_offer=None):
    if previous_offer is not None and current_offer is not None:
        print(f"\nPrice change: {current_offer['offer_id']}")
        print(f"{previous_offer['offer_id']}")
        print(f"{previous_offer['price']} → {current_offer['price']}")
    elif previous_offer is None:
        print(f"\nNew: {current_offer['offer_id']}")
        print(f"{current_offer['price']}, {current_offer['metro']}")
    elif current_offer is None:
        print(f"\nRemoved: {previous_offer['offer_id']}")
        print(f"{previous_offer['price']}, {previous_offer['metro']}")
    else:
        print("No change")


def track_changes(current_data, previous_data):
    """Compare current data with previous run to detect changes"""
    previous_offers = {item["offer_id"]: item for item in previous_data}
    current_offers = {item["offer_id"]: item for item in current_data}
    new = 0
    price_changes = 0
    removed = 0
    changes = []
    for offer_id, current_offer in current_offers.items():
        if offer_id not in previous_offers:
            changes.append({"current_offer": current_offer})
            print_change(current_offer)
            new += 1
        else:
            previous_offer = previous_offers[offer_id]
            if current_offer["price_numeric"] != previous_offer["price_numeric"]:
                changes.append(
                    {"current_offer": current_offer, "previous_offer": previous_offer}
                )
                print_change(current_offer, previous_offer)
                price_changes += 1
    for offer_id, previous_offer in previous_offers.items():
        if offer_id not in current_offers:
            changes.append({"previous_offer": previous_offer})
            print_change(previous_offer=previous_offer)
            removed += 1

    print(f"\n🆕 NEW OFFERS: {new}")
    print(f"💰 PRICE CHANGES: {price_changes}")
    print(f"❌ REMOVED OFFERS: {removed}")
    return changes


def construct_search_url(config):

    base_url = os.getenv("BASE_URL")

    url = f"{base_url}/cat.php?currency=2&engine_version=2&type=4&deal_type=rent&sort=creation_date_desc&"

    for key in config:
        if key == "district":
            for i, district in enumerate(config["district"]):
                url += f"district[{i}]={district}&"
        elif key == "street":
            for i, street in enumerate(config["street"]):
                url += f"street[{i}]={street}&"
        elif key == "rooms":
            if config["rooms"]:
                for room in config["rooms"]:
                    url += f"room{room}=1&"
        else:
            url += f"{key}={config[key]}&"

    return url.rstrip("&")


def construct_offer_url(offer_id):
    """Construct offer URL using environment variable"""

    base_url = os.getenv("BASE_URL")

    return f"{base_url}/rent/flat/{offer_id}/"


def format_offer(offer):
    """Format offer data for Telegram message"""
    offer_url = construct_offer_url(offer["offer_id"])
    fields = [
        (f"<b>{offer['time_label']}</b>",),
        (f"<b>{offer['sub_district']}, {offer['metro']}</b>",),
        (offer["price_info"],),
        (offer_url,),
    ]
    lines = [value[0] or "не указано" for value in fields]
    return "\n".join(lines)


def format_change(change):
    """Unified method to format any type of offer change"""
    has_current = "current_offer" in change
    has_previous = "previous_offer" in change

    if has_current and has_previous:
        # Price change
        header = "<b>ИЗМЕНЕНИЕ ЦЕНЫ</b>\n\n"
        current_offer = change["current_offer"]
        previous_offer = change["previous_offer"]
        price_info = (
            f"💵 <b>{previous_offer['price']} → {current_offer['price']}</b>\n\n"
        )
        offer_info = format_offer(current_offer)
        return header + price_info + offer_info

    elif has_current and not has_previous:
        # New offer
        header = "🆕 <b>НОВОЕ ПРЕДЛОЖЕНИЕ</b>\n\n"
        return header + format_offer(change["current_offer"])

    elif has_previous and not has_current:
        # Removed offer
        header = "❌ <b>ПРЕДЛОЖЕНИЕ СНЯТО</b>\n\n"
        return header + format_offer(change["previous_offer"])

    else:
        raise ValueError("Change must have either current_offer or previous_offer")


def parse_russian_date(time_label):
    """Parse Russian time labels to YYYY-MM-DD HH:MM:SS format"""
    if not time_label:
        return None

    now = datetime.now()
    months = {
        "янв": 1,
        "фев": 2,
        "мар": 3,
        "апр": 4,
        "май": 5,
        "мая": 5,
        "июн": 6,
        "июл": 7,
        "авг": 8,
        "сен": 9,
        "окт": 10,
        "ноя": 11,
        "дек": 12,
    }

    try:
        # Pattern 1: "сегодня, HH:MM"
        if "сегодня" in time_label:
            match = re.search(r"(\d{1,2}):(\d{2})", time_label)
            if match:
                hour, minute = int(match.group(1)), int(match.group(2))
                result = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                return result.strftime("%Y-%m-%d %H:%M:%S")

        # Pattern 2: "вчера, HH:MM"
        elif "вчера" in time_label:
            match = re.search(r"(\d{1,2}):(\d{2})", time_label)
            if match:
                hour, minute = int(match.group(1)), int(match.group(2))
                result = now - timedelta(days=1)
                result = result.replace(
                    hour=hour, minute=minute, second=0, microsecond=0
                )
                return result.strftime("%Y-%m-%d %H:%M:%S")

        # Pattern 3: "DD месяц, HH:MM"
        else:
            match = re.search(
                r"(\d{1,2})\s+([а-яА-Я]+),?\s+(\d{1,2}):(\d{2})", time_label
            )
            if match:
                day = int(match.group(1))
                month_name = match.group(2).lower()
                hour = int(match.group(3))
                minute = int(match.group(4))

                if month_name in months:
                    month = months[month_name]
                    year = now.year

                    result = datetime(year, month, day, hour, minute, 0)

                    # If date is in future, it's from last year
                    if result > now:
                        result = result.replace(year=year - 1)

                    return result.strftime("%Y-%m-%d %H:%M:%S")

    except Exception as e:
        print(f"Error parsing time label '{time_label}': {e}")

    return time_label  # Return original if parsing fails


def normalize_offer_data(offers):
    """Normalize offer data after parsing (modifies in-place)"""
    for offer in offers:
        # Parse Russian dates
        if "time_label" in offer and offer["time_label"]:
            offer["time_label_parsed"] = parse_russian_date(offer["time_label"])
    return offers
