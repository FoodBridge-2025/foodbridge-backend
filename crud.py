from fastapi import HTTPException
from models import User
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
import models, schemas
import uuid
from models import CommunityCentre
from schemas import CommunityCentreCreate
from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def hash_password(password: str) -> str:
    """Hashes a plain text password."""
    return pwd_context.hash(password)

def create_community_centre(db: Session, centre: CommunityCentreCreate):
    # Check if email or contact already exists
    existing_centre = db.query(CommunityCentre).filter(
        (CommunityCentre.email == centre.email) | (CommunityCentre.contact == centre.contact)
    ).first()
    if existing_centre:
        raise HTTPException(status_code=400, detail="Email or Contact already in use.")

    # Hash the password before storing
    hashed_password = hash_password(centre.password)
    print(hashed_password)
    new_centre = CommunityCentre(
        name=centre.name,
        address=centre.address,
        latitude=centre.latitude,
        longitude=centre.longitude,
        contact=centre.contact,
        email=centre.email,
        password=hashed_password,  # Store hashed password
    )

    db.add(new_centre)
    db.commit()
    db.refresh(new_centre)
    return new_centre



# ✅ Get all community centres
def get_community_centres(db: Session):
    return db.query(models.CommunityCentre).all()


# ✅ Get a community centre by ID
def get_community_centre_by_id(db: Session, centre_id: str):
    return db.query(models.CommunityCentre).filter(models.CommunityCentre.id == centre_id).first()

#End user endpoints
def create_user(db: Session, user: schemas.UserCreate):
    try:
        hashed_password = pwd_context.hash(user.password)
        db_user = User(
            name=user.name,
            address=user.address,
            contact=user.contact,
            email=user.email,
            password=hashed_password,
            token_count=0
        )
        db.add(db_user)
        db.commit()
        db.refresh(db_user)
        return db_user
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="Email or Contact already exists")

def get_user_by_id(db: Session, user_id: str):
    return db.query(User).filter(User.id == user_id).first()

def get_all_users(db: Session):
    return db.query(User).all()


def get_requirement_by_id(db: Session, requirement_id: str):
    return db.query(models.Requirement).filter(models.Requirement.id == requirement_id).first()

from sqlalchemy.orm import Session
from models import Requirement
from datetime import date

def get_requirements_by_date_and_meal_type(db: Session, today_date: date, meal_type: str):
    """Fetch all community centre requirements for the current date and meal type."""
    return db.query(Requirement).filter(
        Requirement.date == today_date,
        Requirement.meal_type == meal_type
    ).all()

def get_requirements(db: Session):
    return db.query(models.Requirement).join(models.CommunityCentre).all()

def create_or_update_requirement(db: Session, requirement: schemas.RequirementCreate):
    existing_requirement = (
        db.query(models.Requirement)
        .filter(
            models.Requirement.date == requirement.date,
            models.Requirement.community_centre_id == requirement.community_centre_id,
            models.Requirement.meal_type == requirement.meal_type
        )
        .first()
    )

    if existing_requirement:
        # Update existing record
        existing_requirement.servings = requirement.servings
        existing_requirement.status = requirement.status
        db.commit()
        db.refresh(existing_requirement)
        return existing_requirement
    else:
        # Create a new requirement
        new_requirement = models.Requirement(
            id=str(uuid.uuid4()),
            community_centre_id=requirement.community_centre_id,
            servings=requirement.servings,
            date=requirement.date,
            meal_type=requirement.meal_type,
            status=requirement.status
        )
        db.add(new_requirement)
        db.commit()
        db.refresh(new_requirement)
        return new_requirement

from datetime import datetime

def get_requests_by_community_centre(db: Session, community_centre_id: str):
    """
    Get requests for a given community centre, sorted by earliest date first.
    Determines the meal type automatically based on the current time.
    """
    meal_priority = {"breakfast": 1, "lunch": 2, "dinner": 3}

    # Determine the meal type based on the current time
    current_hour = datetime.now().hour

    if current_hour < 10:
        meal_type = "breakfast"
    elif current_hour < 16:
        meal_type = "lunch"
    else:
        meal_type = "dinner"
    print(f"Current meal type: {meal_type}")

    # Filter requests for the given community center
    query = db.query(models.Requirement).filter(models.Requirement.community_centre_id == community_centre_id)

    # Exclude earlier meal types based on time
    if meal_type == "lunch":
        query = query.filter(models.Requirement.meal_type != "breakfast")
    elif meal_type == "dinner":
        query = query.filter(models.Requirement.meal_type != "breakfast", models.Requirement.meal_type != "lunch")

    # Sort first by date (earliest first), then by meal type priority
    query = query.order_by(models.Requirement.date.asc()).all()

    # Sort results based on meal type priority
    sorted_results = sorted(query, key=lambda r: meal_priority[r.meal_type])

    return sorted_results


def update_food_item_status(db: Session, food_item_id: str, new_status: str):
    # Fetch the food item by ID
    food_item = db.query(models.FoodItem).filter(models.FoodItem.id == food_item_id).first()

    # Check if the food item exists
    if not food_item:
        raise HTTPException(status_code=404, detail="Food item not found")

    # Validate if the status is valid
    valid_statuses = ["Open", "Approved", "In Transit", "Received", "Not fulfilled"]
    if new_status not in valid_statuses:
        raise HTTPException(status_code=400, detail="Invalid status")

    # Update the status
    food_item.status = new_status
    db.commit()
    db.refresh(food_item)

    if new_status == "Received":
        requirement = db.query(Requirement).filter(Requirement.id == food_item.request_id).first()
        if requirement:
            # Adjust the servings
            requirement.servings -= food_item.servings
            if requirement.servings <= 0:
                requirement.servings = 0  # Ensure it does not go negative
                requirement.status = "Fulfilled"  # Optional: Mark requirement as fulfilled

            db.commit()
            db.refresh(requirement)

    return food_item





