import os
from dotenv import load_dotenv
from openai import OpenAI
import json
import requests

load_dotenv()

api_key = os.getenv("OPENROUTER_API_KEY")
shopware_url = os.getenv("SHOPWARE_URL")
shopware_access_id = os.getenv("SHOPWARE_ACCESS_ID")
shopware_secret = os.getenv("SHOPWARE_SECRET_ACCESS_KEY")

client = OpenAI(base_url="https://openrouter.ai/api/v1", api_key=api_key)

SYSTEM_PROMPT = """
Du bist ein Shopware-Kundenservice-Assistent.
Beantworte Fragen zu Bestellungen ausschließlich mit Informationen,
die ausdrücklich von den verfügbaren Tools zurückgegeben wurden.
Füge keine Annahmen, Vorhersagen oder allgemeinen Shop-Abläufe hinzu.
Wenn eine Information nicht in den Tool-Daten enthalten ist, sage,
dass dazu keine Information vorliegt.
Ziehe aus Statuswerten keine zusätzlichen Schlussfolgerungen.
Erwähne frühere Bestellungen nur, wenn der Kunde ausdrücklich danach fragt.
Sprich direkt mit dem Kunden und verwende "Ihre Bestellung" bzw. "Ihre Bestellnummer".
Erfinde keine zukünftigen Schritte oder Prozesse wie E-Mails, Tracking-Informationen,
Liefertermine oder Versandabläufe, wenn diese nicht ausdrücklich in den Tool-Daten stehen.
Wenn Trackingnummern in den Tool-Daten vorhanden sind, nenne sie dem Kunden.
Wenn der Kunde nach dem Lieferzeitpunkt fragt und shippingDateEarliest und
shippingDateLatest vorhanden sind, nenne diesen Zeitraum als voraussichtlichen
Versandzeitraum.
Wenn das Tool den Fehler "shopware_unavailable" zurückgibt, teile dem Kunden
kurz mit, dass die Bestelldaten momentan nicht abgerufen werden können und er
es später erneut versuchen soll.
"""

tools = [
    {
        "type": "function",
        "function": {
            "name": "get_order_status",
            "description": (
                "Liest den aktuellen Status einer Shopware-Bestellung. "
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
                        "description": "Die Postleitzahl der Rechnungsadresse",
                    },
                },
                "required": ["order_number", "zipcode"],
            },
        },
    }
]


def get_shopware_token():
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


def get_shopware_order(order_number):
    token = get_shopware_token()

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
                "billingAddress": {},
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

    # First: collect the IDs and basic order data
    for item in data.get("included", []):
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
    }


def get_order_status(order_number, zipcode):
    try:
        order = get_shopware_order(order_number)
    except requests.RequestException:
        return {"error": "shopware_unavailable"}

    if order is None:
        return None

    if order["shippingZipcode"] != zipcode:
        return {"error": "verification_failed"}

    order.pop("shippingZipcode", None)
    return order


def ask_agent(user_message, messages):
    messages.append({"role": "user", "content": user_message})

    response = client.chat.completions.create(
        model="openrouter/free", messages=messages, tools=tools, tool_choice="auto"
    )

    message = response.choices[0].message
    if message.tool_calls:
        tool_call = message.tool_calls[0]
        arguments = json.loads(tool_call.function.arguments)

        if tool_call.function.name == "get_order_status":
            result = get_order_status(arguments["order_number"], arguments["zipcode"])

            messages.append(message)

            messages.append(
                {
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result),
                }
            )

            final_response = client.chat.completions.create(
                model="openrouter/free", messages=messages
            )

            final_message = final_response.choices[0].message
            messages.append(final_message)

            return final_message

    messages.append(message)
    return message
