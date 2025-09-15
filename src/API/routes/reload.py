from API.routes.recommend import load_recommendation_data, APIRouter

router = APIRouter()

@router.post("/reload", status_code=200)
def reload_offers():
    try:
        load_recommendation_data()
        return {"message": "🚀 API à jour !"}
    except Exception as e:
        return {"error": str(e)}