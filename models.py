import uuid
from database import Base
from sqlalchemy import Column, String, Float, Integer, Date, ForeignKey, Enum
from sqlalchemy.orm import relationship
from passlib.context import CryptContext

# Initialize password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

class CommunityCentre(Base):
    __tablename__ = "community_centres"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(255), nullable=False)
    address = Column(String(255), nullable=False)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    contact = Column(String(20), unique=True, nullable=False)
    email = Column(String(100), unique=True, nullable=False)  # New Email field
    password = Column(String(255), nullable=False)  # Hashed Password field

    requirements = relationship("Requirement", back_populates="community_centre")

class User(Base):
    __tablename__ = "users"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(100), nullable=False)
    address = Column(String(255), nullable=False)
    contact = Column(String(20), nullable=False, unique=True)
    email = Column(String(100), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    token_count = Column(Integer, default=0)

    @staticmethod
    def hash_password(plain_password: str) -> str:
        """Hashes the password before storing it."""
        return pwd_context.hash(plain_password)

    def verify_password(self, plain_password: str) -> bool:
        """Verifies the password during login."""
        return pwd_context.verify(plain_password, self.password)

    # ✅ Add relationship to FoodItem
    food_items = relationship("FoodItem", back_populates="user")


class Requirement(Base):
    __tablename__ = "requirements"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    community_centre_id = Column(String(36), ForeignKey("community_centres.id"), nullable=False)
    servings = Column(Integer, nullable=False)
    date = Column(Date, nullable=False)
    meal_type = Column(String(50), nullable=False)
    status = Column(String(50), nullable=False)

    community_centre = relationship("CommunityCentre", back_populates="requirements")

    # ✅ Fix relationship name to match `FoodItem`
    food_items = relationship("FoodItem", back_populates="requirement")


class FoodItem(Base):
    __tablename__ = "food_items"

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    image = Column(String, nullable=False)
    title = Column(String, nullable=False)
    description = Column(String, nullable=False)
    servings = Column(Integer, nullable=False)
    request_id = Column(String(36), ForeignKey("requirements.id"), nullable=False)
    user_id = Column(String(36), ForeignKey("users.id"), nullable=False)
    status = Column(Enum("Open", "Approved", "In Transit", "Received", "Not fulfilled"), default="Open")

    # ✅ Fix relationship name to match `Requirement`
    requirement = relationship("Requirement", back_populates="food_items")
    user = relationship("User", back_populates="food_items")


