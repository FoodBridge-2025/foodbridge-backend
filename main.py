from datetime import datetime, time

from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware
from schemas import UserLogin
import models
import crud, schemas
import uuid
from models import FoodItem, Requirement, User
from schemas import FoodItemCreate, FoodItemResponse
from database import get_db
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from database import get_db
from schemas import CommunityCentreLogin
from models import CommunityCentre
from passlib.context import CryptContext

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all domains
    allow_credentials=True,
    allow_methods=["*"],   # Allow all HTTP methods
    allow_headers=["*"],   # Allow all headers
)

def hash_password(password: str) -> str:
    """Hashes a plain text password before storing it."""
    return pwd_context.hash(password)

def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a password against its hashed version."""
    return pwd_context.verify(plain_password, hashed_password)

# ✅ Endpoint to add a new community center
@app.post("/community-centres/", response_model=schemas.CommunityCentreResponse)
def add_community_centre(centre: schemas.CommunityCentreCreate, db: Session = Depends(get_db)):
    return crud.create_community_centre(db, centre)

# ✅ Endpoint to list all community centers
@app.get("/community-centres/", response_model=list[schemas.CommunityCentreResponse])
def list_community_centres(db: Session = Depends(get_db)):
    return crud.get_community_centres(db)

# ✅ NEW: Endpoint to fetch a community center by ID
@app.get("/community-centres/{centre_id}", response_model=schemas.CommunityCentreResponse)
def get_community_centre(centre_id: str, db: Session = Depends(get_db)):
    centre = crud.get_community_centre_by_id(db, centre_id)
    print(centre)
    if not centre:
        raise HTTPException(status_code=404, detail="Community centre not found")
    return centre

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

@app.post("/community-centres/login")
def login_community_centre(login_data: CommunityCentreLogin, db: Session = Depends(get_db)):
    """Logs in a community centre by verifying email and password."""

    centre = db.query(CommunityCentre).filter(CommunityCentre.email == login_data.email).first()

    if not centre:
        raise HTTPException(status_code=404, detail="Community centre not found")

    # Verify password
    if not pwd_context.verify(login_data.password, centre.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    return {"message": "Login successful", "community_centre_id": centre.id}


# End User Endpoints

@app.post("/users/", response_model=schemas.UserResponse)
def add_user(user: schemas.UserCreate, db: Session = Depends(get_db)):
    # Check if email already exists
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="Email already registered.")

    return crud.create_user(db, user)

@app.get("/users/{user_id}", response_model=schemas.UserResponse)
def get_user(user_id: str, db: Session = Depends(get_db)):
    user = crud.get_user_by_id(db, user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user

@app.get("/users/", response_model=list[schemas.UserResponse])
def list_users(db: Session = Depends(get_db)):
    return crud.get_all_users(db)

# Requirements Endpoints

@app.post("/requirements/", response_model=schemas.RequirementResponse)
def create_or_update(requirement: schemas.RequirementCreate, db: Session = Depends(get_db)):
    return crud.create_or_update_requirement(db, requirement)

@app.get("/requirements/", response_model=list[schemas.RequirementResponse])
def list_requirements(db: Session = Depends(get_db)):
    return crud.get_requirements(db)

@app.get("/requirements/{requirement_id}", response_model=schemas.RequirementResponse)
def get_requirement(requirement_id: str, db: Session = Depends(get_db)):
    requirement = crud.get_requirement_by_id(db, requirement_id)
    if not requirement:
        raise HTTPException(status_code=404, detail="Requirement not found")
    return requirement



def get_meal_type():
    """Determine the meal type based on the current time, extending dinner until 6 AM."""
    now = datetime.now().time()

    if time(6, 0) <= now < time(11, 0):
        return "breakfast"
    elif time(11, 0) <= now < time(16, 0):
        return "lunch"
    else:  # Dinner from 4 PM to 5:59 AM
        return "dinner"


@app.get("/requirements/today/", response_model=list[schemas.RequirementResponse])
def get_today_requirements(db: Session = Depends(get_db)):
    """Fetch all community centre requirements for the current date and meal type."""
    now = datetime.now()
    meal_type = get_meal_type()

    # If it's between 12 AM - 6 AM, fetch previous day's requirements for dinner
    if meal_type == "dinner" and now.hour < 6:
        today_date = (now.date()).replace(day=now.day - 1)  # Fetch yesterday's dinner
    else:
        today_date = now.date()

    return crud.get_requirements_by_date_and_meal_type(db, today_date, meal_type)


@app.get("/requirements/", response_model=list[schemas.RequirementResponse])
def get_requirements(db: Session = Depends(get_db)):
    """Fetch all requirements with full community centre details"""
    requirements = db.query(models.Requirement).join(models.CommunityCentre).all()

    for req in requirements:
        req.community_centre = db.query(models.CommunityCentre).filter_by(id=req.community_centre_id).first()

    return requirements


@app.get("/requests/{community_centre_id}", response_model=list[schemas.RequirementResponse])
def get_requests(community_centre_id: str, db: Session = Depends(get_db)):
    """Fetch earliest community centre requests, automatically determining meal type based on current time."""
    requests = crud.get_requests_by_community_centre(db, community_centre_id)

    if not requests:
        raise HTTPException(status_code=404, detail="No requests found")

    return requests

@app.post("/food_items", response_model=FoodItemResponse)
def create_food_item(food_item: FoodItemCreate, db: Session = Depends(get_db)):
    # Validate that the requirement (request_id) exists
    requirement = db.query(Requirement).filter(Requirement.id == food_item.request_id).first()
    if not requirement:
        raise HTTPException(status_code=400, detail="Invalid request_id: Requirement does not exist.")

    # Validate that the user exists
    user = db.query(User).filter(User.id == food_item.user_id).first()
    if not user:
        raise HTTPException(status_code=400, detail="Invalid user_id: User does not exist.")

    # Create the new FoodItem
    new_food_item = FoodItem(
        id=str(uuid.uuid4()),  # Generate a unique ID
        image=food_item.image,
        title=food_item.title,
        description=food_item.description,
        servings=food_item.servings,
        request_id=food_item.request_id,
        user_id=food_item.user_id,
        status="Open",  # Default status
    )

    db.add(new_food_item)
    db.commit()
    db.refresh(new_food_item)

    return new_food_item

@app.get("/food_items/{request_id}", response_model=list[schemas.FoodItemResponseWithUser])
def get_food_items_by_request_id(request_id: str, db: Session = Depends(get_db)):
    # Fetch all food items for the given request_id
    food_items = db.query(FoodItem).filter(FoodItem.request_id == request_id).all()

    if not food_items:
        raise HTTPException(status_code=404, detail="No food items found for the given request_id.")

    return food_items

@app.put("/food_items/{food_item_id}/status", response_model=schemas.FoodItemResponse)
def update_status(food_item_id: str, status_update: schemas.FoodItemStatusUpdate, db: Session = Depends(get_db)):
    return crud.update_food_item_status(db, food_item_id, status_update.status)


@app.get("/users/{user_id}/token_count", response_model=int)
def get_token_count(user_id: uuid.UUID, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    return user.token_count

@app.put("/users/{user_id}/token_count", response_model=schemas.UserResponse)
def update_token_count(user_id: uuid.UUID, token_count: int, db: Session = Depends(get_db)):
    user = db.query(models.User).filter(models.User.id == str(user_id)).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.token_count = token_count
    db.commit()
    db.refresh(user)
    return user

@app.post("/users/login")
def login_user(user_data: UserLogin, db: Session = Depends(get_db)):
    user = db.query(User).filter(User.email == user_data.email).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    if not verify_password(user_data.password, user.password):
        raise HTTPException(status_code=400, detail="Incorrect password")

    return {"message": "Login successful", "user_id": str(user.id)}



