from sqlalchemy import Column, Integer, String, Float
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()

class Enrollment(Base):
    __tablename__ = "enrollment_data"
    
    id = Column(Integer, primary_key=True, index=True)
    zip_code = Column(Integer, index=True)
    state = Column(String, index=True)
    county = Column(String, index=True)
    year = Column(Integer)
    health_enrollment = Column(Integer)
    dental_enrollment = Column(Integer)

    # New percentage columns
    male_percentage = Column(Float)
    female_percentage = Column(Float)
    low_income_percentage = Column(Float)
    medium_income_percentage = Column(Float)
    high_income_percentage = Column(Float)
    age_18_25_percentage = Column(Float)
    age_25_35_percentage = Column(Float)
    age_35_45_percentage = Column(Float)
    age_45_55_percentage = Column(Float)
    age_56_plus_percentage = Column(Float)
