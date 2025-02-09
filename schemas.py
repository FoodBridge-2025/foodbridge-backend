from pydantic import BaseModel, EmailStr
from datetime import date
from typing import Optional, Literal
import uuid

class CommunityCentreCreate(BaseModel):
    name: str
    address: str
    latitude: float
    longitude: float
    contact: str
    email: EmailStr
    password: str


class CommunityCentreResponse(BaseModel):
    id: str
    name: str
    address: str
    latitude: float
    longitude: float
    contact: str
    email: EmailStr  # Expose email but not password

class UserBase(BaseModel):
    name: str
    address: str
    contact: str
    email: EmailStr

class UserCreate(BaseModel):
    name: str
    address: str
    contact: str
    email: EmailStr
    password: str  # Accepts plain text (will be hashed before storing)

class UserResponse(BaseModel):
    id: str
    name: str
    address: str
    contact: str
    email: EmailStr

    class Config:
        orm_mode = True # Ensures conversion from SQLAlchemy model



class RequirementBase(BaseModel):
    community_centre_id: str
    servings: int
    date: date
    meal_type: str
    status: str

class RequirementCreate(RequirementBase):
    pass

class RequirementResponse(BaseModel):
    id: str
    servings: int
    date: date
    meal_type: str
    status: str
    community_centre: CommunityCentreResponse  # ✅ Include full details

    class Config:
        orm_mode = True

from pydantic import BaseModel
from typing import Optional

class FoodItemCreate(BaseModel):
    image: str
    title: str
    description: str
    servings: int
    request_id: str
    user_id: str

class FoodItemResponse(FoodItemCreate):
    id: str
    status: str

    class Config:
        orm_mode = True

from pydantic import BaseModel

class UserResponse(BaseModel):
    id: str
    name: str
    address: str
    contact: str
    email: str
    token_count: int

class FoodItemResponseWithUser(BaseModel):
    id: str
    image: str
    title: str
    description: str
    servings: int
    status: str
    user: UserResponse  # Embed user details

class FoodItemStatusUpdate(BaseModel):
    status: Literal["Open", "Approved", "In Transit", "Received", "Not fulfilled"]




