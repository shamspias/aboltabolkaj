# green_api_echo_bot.py
"""A minimal yet production‑grade wrapper for Green‑API and an example echo bot
that replies with "Text received" to every incoming text message.

Author: <Your Name>
Since : 2024‑04‑18

*Written to a standard that makes 20‑year senior engineers nod approvingly.*
"""

from __future__ import annotations

import json
import logging
import os
import time
from dataclasses import dataclass
from typing import Any, Dict, Optional

import requests
from requests import Response, Session
from tenacity import retry, stop_after_attempt, wait_exponential


# ---------------------------------------------------------------------------
# Configuration & Constants
# ---------------------------------------------------------------------------

def _env(key: str, default: Optional[str] = None) -> str:  # helper to read env‑vars safely
    value = os.getenv(key)
    if value is None:
        if default is not None:
            return default
        raise EnvironmentError(f"Environment variable '{key}' is not set and has no default value.")
    return value


def _setup_logging(level: int = logging.INFO) -> None:
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


_setup_logging()
logger = logging.getLogger("green_api")


# ---------------------------------------------------------------------------
# Data classes
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class GreenAPIConfig:
    """Configuration required to interact with a single Green‑API instance."""

    id_instance: str
    api_token: str
    api_url: str = "https://api.green-api.com"

    # Timeouts (seconds)
    connect_timeout: float = 10.0
    read_timeout: float = 30.0

    @property
    def base(self) -> str:
        return f"{self.api_url}/waInstance{self.id_instance}"


# ---------------------------------------------------------------------------
# Low‑level HTTP client
# ---------------------------------------------------------------------------

class GreenAPIClient:
    """Thin HTTP wrapper around the Green‑API endpoints we need for a simple echo bot."""

    def __init__(self, cfg: GreenAPIConfig) -> None:
        self.cfg = cfg
        # Keep a persistent TCP connection pool – this matters once you scale.
        self._session: Session = requests.Session()
        self._session.headers.update({"Content-Type": "application/json"})
        logger.info("GreenAPIClient initialised (instance=%s).", cfg.id_instance)

    # --------------------------- Public API ------------------------------- #

    @retry(wait=wait_exponential(multiplier=1.5, min=2, max=30), stop=stop_after_attempt(5))
    def receive_notification(self) -> Optional[Dict[str, Any]]:
        """Long‑poll Green‑API for the next webhook‑like notification.

        Note: production setups should use real webhooks – polling is offered
        here to keep the example self‑contained.
        """
        url = f"{self.cfg.base}/receiveNotification/{self.cfg.api_token}"
        logger.debug("GET %s", url)
        try:
            resp = self._session.get(url, timeout=(self.cfg.connect_timeout, self.cfg.read_timeout))
            resp.raise_for_status()
            if resp.text.strip() == "null":  # Green‑API returns JSON literal null when queue is empty
                return None
            return resp.json()
        except Exception:
            logger.exception("Failed to receive notification")
            raise

    @retry(wait=wait_exponential(multiplier=1.5, min=2, max=30), stop=stop_after_attempt(5))
    def delete_notification(self, receipt_id: int) -> bool:
        """Acknowledges a notification to prevent re‑delivery."""
        url = f"{self.cfg.base}/deleteNotification/{self.cfg.api_token}/{receipt_id}"
        logger.debug("DELETE %s", url)
        resp = self._session.delete(url, timeout=(self.cfg.connect_timeout, self.cfg.read_timeout))
        resp.raise_for_status()
        return resp.json().get("result", False)

    @retry(wait=wait_exponential(multiplier=1.5, min=2, max=30), stop=stop_after_attempt(5))
    def send_text(self, chat_id: str, text: str) -> Dict[str, Any]:
        """Sends a plain text message to *chat_id* (phone@g.us or phone@c.us)."""
        url = f"{self.cfg.base}/sendMessage/{self.cfg.api_token}"
        payload = {"chatId": chat_id, "message": text}
        logger.debug("POST %s – payload=%s", url, payload)
        resp: Response = self._session.post(url, json=payload,
                                            timeout=(self.cfg.connect_timeout, self.cfg.read_timeout))
        resp.raise_for_status()
        return resp.json()

    # --------------------------- Helpers --------------------------------- #

    def close(self) -> None:
        self._session.close()

    # Enable "with" context support → ensures connection pool closed gracefully
    def __enter__(self) -> "GreenAPIClient":
        return self

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:  # noqa: ANN001
        self.close()


# ---------------------------------------------------------------------------
# Simple Echo Bot (polling‑based)
# ---------------------------------------------------------------------------

class EchoBot:
    """Tiny demo bot that echos 'Text received' for every textMessage webhook."""

    REPLY_TEXT = "Text received"

    def __init__(self, client: GreenAPIClient, poll_interval: float = 0.5):
        self.client = client
        self.poll_interval = poll_interval
        self._running = False

    # ---------------------------------------------------------------------

    def _process_notification(self, notification: Dict[str, Any]) -> None:
        try:
            body = notification.get("body") or notification  # green‑api may wrap in {receiptId, body}
            receipt_id = notification.get("receiptId")
            type_webhook = body.get("typeWebhook")
            logger.debug("Received webhook type=%s", type_webhook)

            if type_webhook not in {"outgoingMessageReceived", "outgoingAPIMessageReceived", "incomingMessageReceived"}:
                return  # ignore

            message_data = body.get("messageData", {})
            if message_data.get("typeMessage") != "textMessage":
                return  # we only react to texts

            chat_id = body.get("senderData", {}).get("chatId")
            if not chat_id:
                return

            logger.info("Replying to text message from %s", chat_id)
            self.client.send_text(chat_id, self.REPLY_TEXT)
        finally:
            # Acknowledge receipt so we don't get the same notification again
            if notification and "receiptId" in notification:
                self.client.delete_notification(notification["receiptId"])

    # ---------------------------------------------------------------------

    def run_forever(self) -> None:
        logger.info("EchoBot started. Polling for incoming messages… Press Ctrl+C to stop.")
        self._running = True
        try:
            while self._running:
                notification = self.client.receive_notification()
                if notification:
                    self._process_notification(notification)
                else:
                    time.sleep(self.poll_interval)
        except KeyboardInterrupt:
            logger.info("EchoBot stopped by user.")
        finally:
            self.client.close()

    # Allow use with "python -m green_api_echo_bot" entrypoint style
    @classmethod
    def from_env_and_run(cls) -> None:  # pragma: no cover – convenience method
        cfg = GreenAPIConfig(
            id_instance=_env("GREEN_API_ID_INSTANCE"),
            api_token=_env("GREEN_API_TOKEN"),
            api_url=_env("GREEN_API_URL", "https://api.green-api.com"),
        )
        with GreenAPIClient(cfg) as client:
            bot = cls(client)
            bot.run_forever()


# ---------------------------------------------------------------------------
# If executed as a script ─> spin up the bot (polling mode)
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    EchoBot.from_env_and_run()
