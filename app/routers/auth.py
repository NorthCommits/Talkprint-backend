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
    
@router.post("/forgot-password")
def forgot_password(body: dict):
    try:
        email = body.get("email")
        if not email:
            raise HTTPException(status_code=400, detail="Email required")
        supabase.auth.reset_password_email(email)
        logger.info(f"Password reset email sent to {email}")
        return {"message": "Password reset email sent"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
    

@router.post("/auth/refresh")
def refresh_token(request: Request):
    """
    Takes refresh token from Authorization header, returns new access token
    """
    try:
        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            raise HTTPException(status_code=401, detail="Invalid token format")
        
        refresh_token = auth_header.replace("Bearer ", "")
        
        # Verify refresh token with Supabase
        user = supabase.auth.refresh_session(refresh_token).session
        
        logger.info(f"Token refreshed for user {user.user.id}")
        
        return {
            "access_token": user.access_token,
            "refresh_token": user.refresh_token,
            "expires_in": 3600
        }
    except Exception as e:
        logger.error(f"Token refresh failed: {str(e)}")
        raise HTTPException(status_code=401, detail="Invalid refresh token")


@router.post("/logout")
def logout():
    try:
        supabase.auth.sign_out()
        return {"message": "Logged out successfully"}
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))