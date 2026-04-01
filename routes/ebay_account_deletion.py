import hashlib
import logging
import os
from typing import Optional

from fastapi import APIRouter, Request, Response
from fastapi.responses import JSONResponse

router = APIRouter()
logger = logging.getLogger(__name__)

EBAY_ENDPOINT_URL = "https://web-production-78bf0.up.railway.app/ebay/account-deletion"


def _challenge_response(challenge_code: str, endpoint_url: str) -> str:
    """
    eBay challenge verification hash.
    SHA-256(challengeCode + verificationToken + endpointURL), hex-encoded.
    https://developer.ebay.com/marketplace-account-deletion
    """
    verification_token = os.environ.get("EBAY_VERIFICATION_TOKEN", "")
    payload = challenge_code + verification_token + endpoint_url
    return hashlib.sha256(payload.encode()).hexdigest()


@router.get("")
async def challenge_verification(request: Request):
    """
    eBay sends a GET with ?challengeCode=... to verify the endpoint.
    Also accepts ?challenge_code=... as a fallback.
    Respond with the SHA-256 hash so eBay confirms ownership.
    """
    params = request.query_params
    code = params.get("challengeCode") or params.get("challenge_code")
    if not code:
        return Response(status_code=400)

    return JSONResponse({"challengeResponse": _challenge_response(code, EBAY_ENDPOINT_URL)})


@router.post("")
async def account_deletion_notification(request: Request):
    """
    Receives eBay marketplace account deletion notifications.
    Acknowledge with 200; log the event for audit purposes.
    """
    try:
        body = await request.json()
        logger.info("[eBay] account deletion notification received: %s", body)
    except Exception:
        logger.warning("[eBay] account deletion notification: could not parse body")

    return Response(status_code=200)
