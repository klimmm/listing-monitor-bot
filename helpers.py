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


def are_duplicate_offers(offer1, offer2):
    """Check if two offers are duplicates based on key attributes"""
    # Required fields for comparison
    required_fields = ["building_id", "price_numeric", "floor", "rooms"]

    # Check if both offers have all required fields
    for field in required_fields:
        if field not in offer1 or field not in offer2:
            return False

    # Compare all required fields
    return (
        offer1["building_id"] == offer2["building_id"]
        and offer1["price_numeric"] == offer2["price_numeric"]
        and offer1["floor"] == offer2["floor"]
        and offer1["rooms"] == offer2["rooms"]
    )


def filter_duplicate_changes(new_changes, removed_changes):
    """Filter out duplicate changes where new and removed offers are the same property"""
    filtered_new = []
    filtered_removed = []

    # Track which removed offers are duplicates of new offers
    removed_duplicates = set()

    for new_change in new_changes:
        new_offer = new_change["current_offer"]
        is_duplicate = False

        for i, removed_change in enumerate(removed_changes):
            if i in removed_duplicates:
                continue

            removed_offer = removed_change["previous_offer"]

            if are_duplicate_offers(new_offer, removed_offer):
                print(
                    f"🔄 Filtering duplicate: New {new_offer['offer_id']} = Removed {removed_offer['offer_id']} "
                    f"({new_offer.get('building_id', 'N/A')}, {new_offer.get('price_numeric', 'N/A')}₽, "
                    f"Floor {new_offer.get('floor', 'N/A')}, {new_offer.get('rooms', 'N/A')} rooms)"
                )
                removed_duplicates.add(i)
                is_duplicate = True
                break

        if not is_duplicate:
            filtered_new.append(new_change)

    # Add non-duplicate removed changes
    for i, removed_change in enumerate(removed_changes):
        if i not in removed_duplicates:
            filtered_removed.append(removed_change)

    return filtered_new, filtered_removed


def track_changes(current_data, previous_data):
    """Compare current data with previous run to detect changes"""
    previous_offers = {item["offer_id"]: item for item in previous_data}
    current_offers = {item["offer_id"]: item for item in current_data}

    new_changes = []
    price_changes = []
    removed_changes = []

    # Track new offers and price changes
    for offer_id, current_offer in current_offers.items():
        if offer_id not in previous_offers:
            new_changes.append({"current_offer": current_offer})
        else:
            previous_offer = previous_offers[offer_id]
            if current_offer["price_numeric"] != previous_offer["price_numeric"]:
                price_changes.append(
                    {"current_offer": current_offer, "previous_offer": previous_offer}
                )

    # Track removed offers
    for offer_id, previous_offer in previous_offers.items():
        if offer_id not in current_offers:
            removed_changes.append({"previous_offer": previous_offer})

    # Filter out duplicates between new and removed
    filtered_new, filtered_removed = filter_duplicate_changes(
        new_changes, removed_changes
    )

    # Print changes for the filtered results
    for change in filtered_new:
        print_change(change["current_offer"])

    for change in price_changes:
        print_change(change["current_offer"], change["previous_offer"])

    for change in filtered_removed:
        print_change(previous_offer=change["previous_offer"])

    # Combine all changes for return
    all_changes = filtered_new + price_changes + filtered_removed

    print(f"\n🆕 NEW OFFERS: {len(filtered_new)}")
    print(f"💰 PRICE CHANGES: {len(price_changes)}")
    print(f"❌ REMOVED OFFERS: {len(filtered_removed)}")
    if len(new_changes) - len(filtered_new) > 0:
        print(f"🔄 FILTERED DUPLICATES: {len(new_changes) - len(filtered_new)}")

    return all_changes


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


def extract_floor_and_rooms(title):
    """Extract floor and room information from title string"""
    result = {}

    if not title:
        return result

    # Extract room count (e.g., "1-комн.", "2-комн.", "Студия")
    room_match = re.search(r"(\d+)-комн\.", title)
    if room_match:
        result["rooms"] = int(room_match.group(1))
    elif "студия" in title.lower():
        result["rooms"] = 0  # Studio = 0 rooms

    # Extract floor information (e.g., "3/9 этаж")
    floor_match = re.search(r"(\d+)/(\d+)\s*этаж", title)
    if floor_match:
        result["floor"] = int(floor_match.group(1))
        result["total_floors"] = int(floor_match.group(2))

    return result


def normalize_offer_data(offers):
    """Normalize offer data after parsing (modifies in-place)"""
    for offer in offers:
        # Parse Russian dates
        if "time_label" in offer and offer["time_label"]:
            offer["time_label_parsed"] = parse_russian_date(offer["time_label"])

        # Extract floor and room number from title
        if "title" in offer and offer["title"]:
            floor_info = extract_floor_and_rooms(offer["title"])
            offer.update(floor_info)
    return offers
