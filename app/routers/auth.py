from fastapi import APIRouter, Depends, Response
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import models
from app.schemas import schemas
from app.services import auth_service
from app.utils.auth import get_current_user

router = APIRouter(
    prefix="/auth",
    tags=["auth"]
)

@router.post("/signup", response_model=schemas.User)
def signup(user: schemas.UserCreate, db: Session = Depends(get_db)):
    result = auth_service.signup(db, user)
    result.links = [
        schemas.Link(rel="login", href="/auth/login", method="POST"),
    ]
    return result

@router.post("/login", response_model=schemas.Token)
def login(credentials: schemas.UserLogin, response: Response, db: Session = Depends(get_db)):
    result = auth_service.login(db, credentials)
    result.links = [
        schemas.Link(rel="catalogue", href="/catalogue/items", method="GET"),
        schemas.Link(rel="create_item", href="/auction/items", method="POST"),
        schemas.Link(rel="notifications", href="/notifications/", method="GET"),
    ]
    
    # Store token in HttpOnly cookie to mitigate Cross-Origin XSS
    response.set_cookie(
        key="access_token",
        value=result.access_token,
        httponly=True,
        samesite="none",
        secure=True,
        max_age=60*60*24 # 24 hours
    )
    
    return result

@router.get("/me", response_model=schemas.User)
def get_me(current_user: models.User = Depends(get_current_user)):
    return schemas.User.model_validate(current_user)


@router.patch("/me", response_model=schemas.User)
@router.put("/me", response_model=schemas.User)
def update_me(
    body: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """PATCH or PUT — same body. PUT avoids some proxies/CDNs that mishandle PATCH."""
    return auth_service.update_profile(db, current_user.id, body)


@router.post("/profile", response_model=schemas.User)
def update_profile_post(
    body: schemas.UserUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user),
):
    """POST fallback for environments that only allow GET/POST on cookie-auth APIs."""
    return auth_service.update_profile(db, current_user.id, body)


@router.post("/logout")
def logout(response: Response):
    response.delete_cookie(key="access_token", httponly=True, samesite="none", secure=True)
    return {"message": "Successfully logged out"}
