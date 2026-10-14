from openai import OpenAI, RateLimitError
import json
import requests

SYSTEM_PROMPT = """
1. Du bist ein Shopware-Kundenservice-Assistent.
2. Beantworte Fragen zu Bestellungen ausschließlich mit Informationen,
die ausdrücklich von den verfügbaren Tools zurückgegeben wurden.
3. Füge keine Annahmen, Vorhersagen oder allgemeinen Shop-Abläufe hinzu.
4. Wenn eine Information nicht in den Tool-Daten enthalten ist, sage,
dass dazu keine Information vorliegt.
5. Ziehe aus Statuswerten keine zusätzlichen Schlussfolgerungen.
6. Erwähne frühere Bestellungen nur, wenn der Kunde ausdrücklich danach fragt.
7. Sprich direkt mit dem Kunden und verwende "Ihre Bestellung" bzw. "Ihre Bestellnummer".
8. Erfinde keine zukünftigen Schritte oder Prozesse wie E-Mails, Tracking-Informationen,
Liefertermine oder Versandabläufe, wenn diese nicht ausdrücklich in den Tool-Daten stehen.
9. Nenne eine Trackingnummer nur, wenn der Kunde nach dem Versand oder der Sendungsverfolgung fragt und die Nummer in den Tool-Daten vorhanden ist.
10. Wenn der Kunde nach dem Lieferzeitpunkt fragt und shippingDateEarliest und
shippingDateLatest vorhanden sind, nenne diesen Zeitraum als voraussichtlichen
Lieferzeitraum. Stelle ihn nicht als garantierten Liefertermin dar.
11. Wenn das Tool den Fehler "shopware_unavailable" zurückgibt, teile dem Kunden
kurz mit, dass die Bestelldaten momentan nicht abgerufen werden können und er
es später erneut versuchen soll.
12. Antworte kurz, natürlich und in einfachem, korrektem Deutsch. Verwende keine unnötigen Wiederholungen oder komplizierten Formulierungen.
13. shippingDateEarliest und shippingDateLatest beschreiben
den voraussichtlichen Lieferzeitraum, nicht den Versandzeitraum.
Diese Daten sind Schätzungen und keine garantierten Liefertermine.
14. Wenn der Kunde nach mehreren konkreten Bestellinformationen fragt, stelle genau diese Informationen übersichtlich dar.
15. Gib technische Statuswerte nicht einfach wörtlich wieder, sondern formuliere sie als natürliche Kundenservice-Sätze in korrektem Deutsch. Vermeide dabei redundante Formulierungen wie "Die Zahlung ist bezahlt".
16. Wenn der Kunde nach bestellten Produkten oder Artikeln fragt, nenne ausschließlich jeden Produktnamen und die jeweilige Menge als eigenen Aufzählungspunkt. Ergänze keine Preise, Produktnummern, Gesamtsumme, Zahlungs-, Status-, Versand- oder Trackinginformationen, außer der Kunde fragt ausdrücklich danach. Verwende keine Markdown-Tabelle.
17. Wenn das Tool den Fehler "verification_failed" zurückgibt, sage dem Kunden, dass die Kombination aus Bestellnummer und Postleitzahl nicht verifiziert werden konnte, und bitte ihn, seine Angaben zu prüfen. Sage nicht, ob die Bestellnummer existiert.
18. Beantworte ausschließlich die konkrete Frage des Kunden. Füge keine weiteren Bestellinformationen hinzu, nur weil sie in den Tool-Daten enthalten sind. Nenne Preise, Status, Zahlung, Versand oder Tracking nur, wenn der Kunde genau danach fragt.
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": (
                "Liest den Status und die enthaltenen Artikel einer Shopware-Bestellung. "
                "Wenn Bestellnummer und Postleitzahl im Gespräch vorhanden sind, "
                "muss dieses Tool aufgerufen werden."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "order_number": {
                        "type": "string",
                        "description": "Die Bestellnummer des Kunden",
                    },
                    "zipcode": {
                        "type": "string",
                        "description": "Die Postleitzahl der Lieferadresse",
                    },
                },
                "required": ["order_number", "zipcode"],
            },
        },
    }
]


def get_shopware_token(shopware_url, shopware_access_id, shopware_secret):
    response = requests.post(
        f"{shopware_url}/api/oauth/token",
        json={
            "grant_type": "client_credentials",
            "client_id": shopware_access_id,
            "client_secret": shopware_secret,
        },
    )

    response.raise_for_status()

    return response.json()["access_token"]


def test_shopware_connection(
    shopware_url,
    shopware_access_id,
    shopware_secret,
):
    try:
        get_shopware_token(
            shopware_url,
            shopware_access_id,
            shopware_secret,
        )

        return {"success": True}

    except requests.RequestException:
        return {"success": False}


def get_shopware_order(order_number, shopware_url, shopware_access_id, shopware_secret):
    token = get_shopware_token(shopware_url, shopware_access_id, shopware_secret)

    response = requests.post(
        f"{shopware_url}/api/search/order",
        headers={
            "Authorization": f"Bearer {token}",
            "Content-Type": "application/json",
        },
        json={
            "filter": [
                {
                    "type": "equals",
                    "field": "orderNumber",
                    "value": order_number,
                }
            ],
            "associations": {
                "stateMachineState": {},
                "primaryOrderTransaction": {"associations": {"stateMachineState": {}}},
                "primaryOrderDelivery": {
                    "associations": {
                        "stateMachineState": {},
                        "shippingOrderAddress": {},
                    }
                },
                "lineItems": {},
            },
            "limit": 1,
        },
    )

    response.raise_for_status()

    data = response.json()

    if not data["data"]:
        return None

    order = data["data"][0]
    attributes = order["attributes"]
    order_state_id = attributes["stateId"]
    tracking_codes = []

    status = None
    delivery_status = None
    delivery_state_id = None
    payment_status = None
    payment_state_id = None
    shipping_zipcode = None
    shipping_address_id = None
    shipping_date_earliest = None
    shipping_date_latest = None
    line_items = []

    # First: collect the IDs and basic order data
    for item in data.get("included", []):
        if item["type"] == "order_line_item":
            item_attributes = item["attributes"]
            line_item = {
                "label": item_attributes.get("label"),
                "quantity": item_attributes.get("quantity"),
            }
            for field in ("productNumber", "unitPrice", "totalPrice"):
                value = item_attributes.get(field)
                if value is not None:
                    line_item[field] = value
            line_items.append(line_item)

        if item["type"] == "order_delivery":
            delivery_state_id = item["attributes"]["stateId"]
            shipping_address_id = item["attributes"]["shippingOrderAddressId"]
            tracking_codes = item["attributes"].get("trackingCodes", [])
            shipping_date_earliest = item["attributes"].get("shippingDateEarliest")
            shipping_date_latest = item["attributes"].get("shippingDateLatest")

        if item["type"] == "order_transaction":
            payment_state_id = item["attributes"]["stateId"]

        if item["type"] == "state_machine_state" and item["id"] == order_state_id:
            status = item["attributes"]["name"]

    # Second: find the shipping ZIP code
    for item in data.get("included", []):
        if item["type"] == "order_address" and item["id"] == shipping_address_id:
            shipping_zipcode = item["attributes"]["zipcode"]
            break

    # Third: find the delivery status
    for item in data.get("included", []):
        if item["type"] == "state_machine_state" and item["id"] == delivery_state_id:
            delivery_status = item["attributes"]["name"]
            break

    # Fourth: find the payment status
    for item in data.get("included", []):
        if item["type"] == "state_machine_state" and item["id"] == payment_state_id:
            payment_status = item["attributes"]["name"]
            break

    return {
        "orderNumber": attributes["orderNumber"],
        "status": status,
        "deliveryStatus": delivery_status,
        "paymentStatus": payment_status,
        "shippingZipcode": shipping_zipcode,
        "trackingCodes": tracking_codes,
        "shippingDateEarliest": shipping_date_earliest,
        "shippingDateLatest": shipping_date_latest,
        "orderDate": attributes["orderDate"],
        "amountTotal": attributes["amountTotal"],
        "lineItems": line_items,
    }


def get_order_status(
    order_number, zipcode, shopware_url, shopware_access_id, shopware_secret
):
    try:
        order = get_shopware_order(
            order_number, shopware_url, shopware_access_id, shopware_secret
        )
    except requests.RequestException:
        return {"error": "shopware_unavailable"}

    if order is None:
        return None

    if order["shippingZipcode"] != zipcode:
        return {"error": "verification_failed"}

    order.pop("shippingZipcode", None)

    return order


def ask_agent(
    user_message,
    messages,
    openrouter_api_key,
    shopware_url,
    shopware_access_id,
    shopware_secret,
):
    client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=openrouter_api_key)

    messages.append({"role": "user", "content": user_message})

    try:
        response = client.chat.completions.create(
            model="openrouter/free", messages=messages, tools=tools, tool_choice="auto"
        )
    except RateLimitError:
        return {"error": "llm_rate_limit"}

    message = response.choices[0].message
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)

        if tool_call.function.name == "get_order_status":
            result = get_order_status(
                arguments["order_number"],
                arguments["zipcode"],
                shopware_url,
                shopware_access_id,
                shopware_secret,
            )

            messages.append(message)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

            if result == {"error": "verification_failed"}:
                return {"error": "verification_failed"}

            try:
                final_response = client.chat.completions.create(
                    model="openrouter/free", messages=messages
                )
            except RateLimitError:
                return {"error": "llm_rate_limit"}

            final_message = final_response.choices[0].message
            messages.append(final_message)

            return final_message

    messages.append(message)
    return message
