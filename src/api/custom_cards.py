import logging

from fastapi import APIRouter, Request

logger = logging.getLogger(__name__)
router = APIRouter()


@router.get("/api/custom-cards")
async def get_custom_cards(req: Request):
    repository = req.app.state.card_repository
    cards = repository.find_all()
    logger.info("Returning %d custom cards.", len(cards))
    return [card.model_dump() for card in cards]
