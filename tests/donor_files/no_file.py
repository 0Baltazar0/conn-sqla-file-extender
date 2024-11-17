from sqlalchemy import Column, Float, Integer, String
from sqlalchemy.orm import declarative_base

Base = declarative_base()


# Define a simple model
class TestClass(Base):
    __tablename__ = "example_table"

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String, nullable=False)
    age = Column(Integer, nullable=False)
    salary = Column(Float, default=0.0)
