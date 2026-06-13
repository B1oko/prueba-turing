from fastapi import APIRouter, Request

router = APIRouter()


@router.get("/api/custom-cards")
async def get_custom_cards(req: Request):
    repository = req.app.state.card_repository
    cards = repository.find_all()
    return [card.model_dump() for card in cards]
