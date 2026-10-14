import os
import unittest
from unittest.mock import patch


for setting in (
    "OPENROUTER_API_KEY",
    "SHOPWARE_URL",
    "SHOPWARE_ACCESS_ID",
    "SHOPWARE_SECRET_ACCESS_KEY",
):
    os.environ.setdefault(setting, "test")

from backend.agent import SYSTEM_PROMPT
from backend.main import ChatRequest, chat, conversation_last_used, conversations


class OrderResponseRuleTests(unittest.TestCase):
    def test_item_question_lists_only_product_names_and_quantities(self):
        self.assertIn(
            "ausschließlich jeden Produktnamen und die jeweilige Menge",
            SYSTEM_PROMPT,
        )
        self.assertIn("Verwende keine Markdown-Tabelle.", SYSTEM_PROMPT)
        self.assertIn("keine Preise, Produktnummern, Gesamtsumme", SYSTEM_PROMPT)

    def test_status_is_only_included_when_customer_asks(self):
        self.assertIn("Beantworte ausschließlich die konkrete Frage", SYSTEM_PROMPT)
        self.assertIn("Status, Zahlung, Versand oder Tracking nur, wenn", SYSTEM_PROMPT)

    def test_tracking_number_is_only_included_when_customer_asks(self):
        self.assertIn(
            "Nenne eine Trackingnummer nur, wenn der Kunde nach dem Versand",
            SYSTEM_PROMPT,
        )
        self.assertIn("oder der Sendungsverfolgung fragt", SYSTEM_PROMPT)

    def test_verification_failure_returns_fixed_customer_message(self):
        conversation_id = "verification-failed-test"
        expected_reply = (
            "Die Kombination aus Bestellnummer und Postleitzahl konnte nicht "
            "verifiziert werden. Bitte überprüfen Sie Ihre Angaben."
        )
        try:
            with patch(
                "backend.main.ask_agent",
                return_value={"error": "verification_failed"},
            ):
                response = chat(
                    ChatRequest(
                        message="Was ist in meiner Bestellung 10001? PLZ 12345",
                        conversation_id=conversation_id,
                    )
                )

            self.assertEqual(response["reply"], expected_reply)
            self.assertEqual(response["conversation_id"], conversation_id)
            self.assertNotIn("10001", response["reply"])
        finally:
            conversations.pop(conversation_id, None)
            conversation_last_used.pop(conversation_id, None)


if __name__ == "__main__":
    unittest.main()
