from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
from sqlalchemy.orm import Session
import models
from database import engine, SessionLocal
from typing import List
from fastapi.templating import Jinja2Templates
from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse

app = FastAPI()

templates = Jinja2Templates(directory="templates")

@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Create all the database tables
models.Base.metadata.create_all(bind=engine)

# Pydantic model for input data
class EnrollmentBase(BaseModel):
    zip_code: int
    state: str
    county: str
    year: int
    health_enrollment: int
    dental_enrollment: int
    male: int
    female: int
    low_income: int
    mid_income: int
    high_income: int
    age_18_25: int
    age_25_35: int
    age_35_45: int
    age_45_55: int
    age_56_plus: int

    class Config:
        orm_mode = True

# Dependency to get the database session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

# Add data to the database
@app.post("/add/")
async def create_data(mapdata: EnrollmentBase, db: Session = Depends(get_db)):
    total_population = mapdata.male + mapdata.female
    total_income = mapdata.low_income + mapdata.mid_income + mapdata.high_income
    total_age = mapdata.age_18_25 + mapdata.age_25_35 + mapdata.age_35_45 + mapdata.age_45_55 + mapdata.age_56_plus

    male_percentage = (mapdata.male / total_population) * 100 if total_population > 0 else 0
    female_percentage = (mapdata.female / total_population) * 100 if total_population > 0 else 0

    low_income_percentage = (mapdata.low_income / total_income) * 100 if total_income > 0 else 0
    medium_income_percentage = (mapdata.mid_income / total_income) * 100 if total_income > 0 else 0
    high_income_percentage = (mapdata.high_income / total_income) * 100 if total_income > 0 else 0

    age_18_25_percentage = (mapdata.age_18_25 / total_age) * 100 if total_age > 0 else 0
    age_25_35_percentage = (mapdata.age_25_35 / total_age) * 100 if total_age > 0 else 0
    age_35_45_percentage = (mapdata.age_35_45 / total_age) * 100 if total_age > 0 else 0
    age_45_55_percentage = (mapdata.age_45_55 / total_age) * 100 if total_age > 0 else 0
    age_56_plus_percentage = (mapdata.age_56_plus / total_age) * 100 if total_age > 0 else 0

    db_instance = models.Enrollment(
        zip_code=mapdata.zip_code,
        state=mapdata.state,
        county=mapdata.county,
        year=mapdata.year,
        health_enrollment=mapdata.health_enrollment,
        dental_enrollment=mapdata.dental_enrollment,
        male_percentage=male_percentage,
        female_percentage=female_percentage,
        low_income_percentage=low_income_percentage,
        medium_income_percentage=medium_income_percentage,
        high_income_percentage=high_income_percentage,
        age_18_25_percentage=age_18_25_percentage,
        age_25_35_percentage=age_25_35_percentage,
        age_35_45_percentage=age_35_45_percentage,
        age_45_55_percentage=age_45_55_percentage,
        age_56_plus_percentage=age_56_plus_percentage
    )
    db.add(db_instance)
    db.commit()
    db.refresh(db_instance)
    return db_instance

# Get all statistics based on zip_code, state, or county
@app.get("/getallstatistics/")
async def get_all_statistics(
    zip_code: Optional[int] = None,
    state: Optional[str] = None,
    county: Optional[str] = None,
    db: Session = Depends(get_db)
):
    if not zip_code and not state and not county:
        raise HTTPException(status_code=400, detail="At least one parameter (zip_code, state, or county) must be provided")

    query = db.query(models.Enrollment)

    if zip_code:
        query = query.filter(models.Enrollment.zip_code == zip_code)
    if state:
        query = query.filter(models.Enrollment.state == state)
    if county:
        query = query.filter(models.Enrollment.county == county)

    enrollments = query.all()

    # Initialize default structure with empty data
    response = {
        "gender_percentages": {
            "male_percentage": 0.0,
            "female_percentage": 0.0
        },
        "enrollment_percentages": {
            "health_enrollment_percentage": 0.0,
            "dental_enrollment_percentage": 0.0
        },
        "income_categories": {
            "low_income_percentage": 0.0,
            "medium_income_percentage": 0.0,
            "high_income_percentage": 0.0
        },
        "age_group_percentages": {
            "18-25": 0.0,
            "25-35": 0.0,
            "35-45": 0.0,
            "45-55": 0.0,
            "56+": 0.0
        },
        "enrollment_by_year": {}
    }

    # If no enrollments are found, return the default empty structure
    if not enrollments:
        return response

    # Gender Percentages Calculation
    total_count = len(enrollments)
    male_percentage = sum(e.male_percentage for e in enrollments) / total_count
    female_percentage = sum(e.female_percentage for e in enrollments) / total_count

    response["gender_percentages"]["male_percentage"] = male_percentage
    response["gender_percentages"]["female_percentage"] = female_percentage

    # Enrollment Percentages Calculation
    total_health_enrollment = sum(e.health_enrollment for e in enrollments)
    total_dental_enrollment = sum(e.dental_enrollment for e in enrollments)
    total_enrollments = total_health_enrollment + total_dental_enrollment

    response["enrollment_percentages"]["health_enrollment_percentage"] = (total_health_enrollment / total_enrollments) * 100 if total_enrollments > 0 else 0
    response["enrollment_percentages"]["dental_enrollment_percentage"] = (total_dental_enrollment / total_enrollments) * 100 if total_enrollments > 0 else 0

    # Income Categories Calculation
    low_income_percentage = sum(e.low_income_percentage for e in enrollments) / total_count
    medium_income_percentage = sum(e.medium_income_percentage for e in enrollments) / total_count
    high_income_percentage = sum(e.high_income_percentage for e in enrollments) / total_count

    response["income_categories"]["low_income_percentage"] = low_income_percentage
    response["income_categories"]["medium_income_percentage"] = medium_income_percentage
    response["income_categories"]["high_income_percentage"] = high_income_percentage

    # Age Group Percentages Calculation
    age_18_25_percentage = sum(e.age_18_25_percentage for e in enrollments) / total_count
    age_25_35_percentage = sum(e.age_25_35_percentage for e in enrollments) / total_count
    age_35_45_percentage = sum(e.age_35_45_percentage for e in enrollments) / total_count
    age_45_55_percentage = sum(e.age_45_55_percentage for e in enrollments) / total_count
    age_56_plus_percentage = sum(e.age_56_plus_percentage for e in enrollments) / total_count

    response["age_group_percentages"]["18-25"] = age_18_25_percentage
    response["age_group_percentages"]["25-35"] = age_25_35_percentage
    response["age_group_percentages"]["35-45"] = age_35_45_percentage
    response["age_group_percentages"]["45-55"] = age_45_55_percentage
    response["age_group_percentages"]["56+"] = age_56_plus_percentage

    # Enrollment by Year Calculation
    enrollment_by_year = {}
    for e in enrollments:
        year = e.year
        if year not in enrollment_by_year:
            enrollment_by_year[year] = {"health": 0, "dental": 0, "total": 0}
        enrollment_by_year[year]["health"] += e.health_enrollment
        enrollment_by_year[year]["dental"] += e.dental_enrollment
        enrollment_by_year[year]["total"] += (e.health_enrollment + e.dental_enrollment)

    response["enrollment_by_year"] = enrollment_by_year

    return response

@app.post("/add_bulk/")
async def create_data_bulk(mapdata: List[EnrollmentBase], db: Session = Depends(get_db)):
    for data in mapdata:
        # Calculate percentages
        total_population = data.male + data.female
        total_income = data.low_income + data.mid_income + data.high_income
        total_age = data.age_18_25 + data.age_25_35 + data.age_35_45 + data.age_45_55 + data.age_56_plus

        male_percentage = (data.male / total_population) * 100 if total_population > 0 else 0
        female_percentage = (data.female / total_population) * 100 if total_population > 0 else 0

        low_income_percentage = (data.low_income / total_income) * 100 if total_income > 0 else 0
        medium_income_percentage = (data.mid_income / total_income) * 100 if total_income > 0 else 0
        high_income_percentage = (data.high_income / total_income) * 100 if total_income > 0 else 0

        age_18_25_percentage = (data.age_18_25 / total_age) * 100 if total_age > 0 else 0
        age_25_35_percentage = (data.age_25_35 / total_age) * 100 if total_age > 0 else 0
        age_35_45_percentage = (data.age_35_45 / total_age) * 100 if total_age > 0 else 0
        age_45_55_percentage = (data.age_45_55 / total_age) * 100 if total_age > 0 else 0
        age_56_plus_percentage = (data.age_56_plus / total_age) * 100 if total_age > 0 else 0

        db_instance = models.Enrollment(
            zip_code=data.zip_code,
            state=data.state,
            county=data.county,
            year=data.year,
            health_enrollment=data.health_enrollment,
            dental_enrollment=data.dental_enrollment,
            male_percentage=male_percentage,
            female_percentage=female_percentage,
            low_income_percentage=low_income_percentage,
            medium_income_percentage=medium_income_percentage,
            high_income_percentage=high_income_percentage,
            age_18_25_percentage=age_18_25_percentage,
            age_25_35_percentage=age_25_35_percentage,
            age_35_45_percentage=age_35_45_percentage,
            age_45_55_percentage=age_45_55_percentage,
            age_56_plus_percentage=age_56_plus_percentage
        )
        db.add(db_instance)
    
    db.commit()
    return {"message": "Bulk data added successfully"}

@app.get("/getstatisticsbycountry/")
async def get_statistics_by_country(
    country: Optional[str] = None,  # Optional country parameter
    db: Session = Depends(get_db)
):
    # Check if the country is USA or America
    if country and country.lower() in ["usa", "america"]:
        # Fetch all data from the database
        enrollments = db.query(models.Enrollment).all()

        # If no enrollments are found, return default structure
        if not enrollments:
            return {
                "gender_percentages": {"male_percentage": 0.0, "female_percentage": 0.0},
                "enrollment_percentages": {"health_enrollment_percentage": 0.0, "dental_enrollment_percentage": 0.0},
                "income_categories": {
                    "low_income_percentage": 0.0,
                    "medium_income_percentage": 0.0,
                    "high_income_percentage": 0.0
                },
                "age_group_percentages": {
                    "18-25": 0.0,
                    "25-35": 0.0,
                    "35-45": 0.0,
                    "45-55": 0.0,
                    "56+": 0.0
                },
                "enrollment_by_year": {}
            }

        # Calculate total count of enrollments
        total_count = len(enrollments)

        # Calculate gender percentages
        male_percentage = sum(e.male_percentage for e in enrollments) / total_count
        female_percentage = sum(e.female_percentage for e in enrollments) / total_count

        # Enrollment Percentages
        total_health_enrollment = sum(e.health_enrollment for e in enrollments)
        total_dental_enrollment = sum(e.dental_enrollment for e in enrollments)
        total_enrollments = total_health_enrollment + total_dental_enrollment

        enrollment_percentages = {
            "health_enrollment_percentage": (total_health_enrollment / total_enrollments) * 100 if total_enrollments > 0 else 0.0,
            "dental_enrollment_percentage": (total_dental_enrollment / total_enrollments) * 100 if total_enrollments > 0 else 0.0,
        }

        # Income Categories
        income_categories = {
            "low_income_percentage": sum(e.low_income_percentage for e in enrollments) / total_count,
            "medium_income_percentage": sum(e.medium_income_percentage for e in enrollments) / total_count,
            "high_income_percentage": sum(e.high_income_percentage for e in enrollments) / total_count,
        }

        # Age Group Percentages
        age_group_percentages = {
            "18-25": sum(e.age_18_25_percentage for e in enrollments) / total_count,
            "25-35": sum(e.age_25_35_percentage for e in enrollments) / total_count,
            "35-45": sum(e.age_35_45_percentage for e in enrollments) / total_count,
            "45-55": sum(e.age_45_55_percentage for e in enrollments) / total_count,
            "56+": sum(e.age_56_plus_percentage for e in enrollments) / total_count,
        }

        # Enrollment by Year
        enrollment_by_year = {}
        for e in enrollments:
            year = e.year
            if year not in enrollment_by_year:
                enrollment_by_year[year] = {"health": 0, "dental": 0, "total": 0}
            enrollment_by_year[year]["health"] += e.health_enrollment
            enrollment_by_year[year]["dental"] += e.dental_enrollment
            enrollment_by_year[year]["total"] += (e.health_enrollment + e.dental_enrollment)

        # Return the response
        return {
            "gender_percentages": {
                "male_percentage": male_percentage,
                "female_percentage": female_percentage,
            },
            "enrollment_percentages": enrollment_percentages,
            "income_categories": income_categories,
            "age_group_percentages": age_group_percentages,
            "enrollment_by_year": enrollment_by_year,
        }

    # If the country is not USA or America, return an error
    raise HTTPException(status_code=400, detail="Country must be 'USA' or 'America'")

