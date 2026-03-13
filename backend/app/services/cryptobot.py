import hashlib
import hmac
import httpx
from datetime import datetime
from app.config import settings


class CryptoBotService:
    BASE_URL = "https://pay.crypt.bot/api"

    def __init__(self) -> None:
        self.headers = {"Crypto-Pay-Api-Token": settings.CRYPTOBOT_TOKEN}

    async def create_invoice(self, amount: float, payload: str, description: str) -> dict:
        async with httpx.AsyncClient(timeout=20) as client:
            r = await client.post(
                f"{self.BASE_URL}/createInvoice",
                headers=self.headers,
                json={
                    "asset": "USDT",
                    "amount": str(amount),
                    "payload": payload,
                    "description": description,
                    "paid_btn_name": "openBot",
                    "paid_btn_url": "https://t.me/SafeBypass_bot",
                },
            )
            return r.json()

    def verify_signature(self, body: bytes, signature: str) -> bool:
        # CryptoBot signature scheme: HMAC_SHA256(body, SHA256(token))
        token_hash = hashlib.sha256(settings.CRYPTOBOT_TOKEN.encode()).digest()
        expected = hmac.new(token_hash, body, hashlib.sha256).hexdigest()
        return hmac.compare_digest(expected, signature)

    async def transfer(
        self,
        wallet: str,
        amount: float,
        asset: str = "TON",
        comment: str = "",
    ) -> bool:
        """Перевод средств на TON кошелёк через CryptoBot transfer API."""
        async with httpx.AsyncClient(timeout=30) as client:
            response = await client.post(
                f"{self.BASE_URL}/transfer",
                headers=self.headers,
                json={
                    "user_id": wallet,
                    "asset": asset,
                    "amount": str(round(amount, 6)),
                    "spend_id": f"safenet_{int(datetime.utcnow().timestamp())}",
                    "comment": comment,
                    "disable_send_notification": False,
                },
            )
            data = response.json()
            return data.get("ok", False)


cryptobot = CryptoBotService()
