from datetime import date, datetime

from sqlalchemy import Column, Integer, String, Boolean, Date, ForeignKey, DateTime
from sqlalchemy.orm import relationship

from database import Base


class Users(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, unique=True, index=True)
    username = Column(String, unique=True, index=True)
    first_name = Column(String)
    last_name = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)

    # navigation property
    tasks = relationship("Tasks", back_populates="owner")


class Tasks(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    task_name = Column(String)
    category = Column(String)
    date_taken = Column(DateTime, default=datetime.utcnow)
    # days_expired = Column(String)
    owner_id = Column(Integer, ForeignKey("users.id"))

    # Navigation Property
    owner = relationship("Users", back_populates="tasks")

