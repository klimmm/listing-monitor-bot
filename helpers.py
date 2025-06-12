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


def construct_cian_url(config):

    url = "https://www.cian.ru/cat.php?currency=2&engine_version=2&type=4&deal_type=rent&sort=creation_date_desc&"

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


def format_offer(offer):
    """Format offer data for Telegram message"""
    fields = [
        (f"<b>{offer['time_label']}</b>",),
        (f"<b>{offer['sub_district']}, {offer['metro']}</b>",),
        (offer["price_info"],),
        (offer["offer_url"],),
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
