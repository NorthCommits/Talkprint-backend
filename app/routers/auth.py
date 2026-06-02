from fastapi import APIRouter, HTTPException
from app.models.schemas import SignUpRequest, LoginRequest, AuthResponse
from app.database import supabase

router = APIRouter()


@router.post("/signup", response_model=AuthResponse)
def signup(body: SignUpRequest):
    try:
        response = supabase.auth.sign_up({
            "email": body.email,
            "password": body.password
        })
        if not response.user:
            raise HTTPException(status_code=400, detail="Signup failed")
        return AuthResponse(
            access_token=response.session.access_token,
            user_id=str(response.user.id),
            email=response.user.email
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/login", response_model=AuthResponse)
def login(body: LoginRequest):
    try:
        response = supabase.auth.sign_in_with_password({
            "email": body.email,
            "password": body.password
        })
        if not response.user:
            raise HTTPException(status_code=401, detail="Invalid credentials")
        return AuthResponse(
            access_token=response.session.access_token,
            user_id=str(response.user.id),
            email=response.user.email
        )
    except Exception as e:
        raise HTTPException(status_code=401, detail=str(e))


@router.post("/logout")
def logout():
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))