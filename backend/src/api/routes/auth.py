from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter()

class APIKeyRequest(BaseModel):
    email: str
    tier: str = "free"

@router.post("/register")
async def register():
    """Register new user"""
    return {"message": "Registration endpoint - coming soon"}

@router.post("/api-key")
async def create_api_key(request: APIKeyRequest):
    """Create new API key"""
    # TODO: Implement API key generation
    return {"message": "API key creation coming soon"}
