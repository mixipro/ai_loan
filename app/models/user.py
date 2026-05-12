# app/models/user.py

from pydantic import BaseModel, Field, model_validator
from typing import List, Optional
from enum import Enum
from app.core.california_config import (
    CaliforniaRegion, REGION_DATA,
    get_cities_for_region, find_region_for_city
)

# ─────────────────────────────────────────
# 🌴 CALIFORNIA LOCATION
# ─────────────────────────────────────────

# Cities by region (automatski iz california_config)
CITIES_BY_REGION: dict[str, list[str]] = {
    region.value: data["cities"]
    for region, data in REGION_DATA.items()
}


class LocationInfo(BaseModel):
    region: CaliforniaRegion
    city: str

    @model_validator(mode="after")
    def city_must_be_valid(self) -> "LocationInfo":
        valid_cities = get_cities_for_region(self.region)
        if self.city not in valid_cities:
            raise ValueError(
                f"'{self.city}' is not a valid city for {self.region.value}. "
                f"Available cities: {valid_cities}"
            )
        return self


# ─────────────────────────────────────────
# 💰 FINANCIAL (USD only)
# ─────────────────────────────────────────

class Currency(str, Enum):
    USD = "USD"  # California-only system = USD only


class FinancialInfo(BaseModel):
    income: int = Field(..., gt=0, description="Monthly income (USD)")
    expenses: int = Field(..., ge=0, description="Monthly expenses (USD)")
    monthly_debt: int = Field(..., ge=0, description="Monthly debt payment (USD)")
    savings: int = Field(..., ge=0, description="Total savings (USD)")
    currency: Currency = Field(default=Currency.USD)

    @model_validator(mode="after")
    def expenses_lt_income(self) -> "FinancialInfo":
        if self.expenses >= self.income:
            raise ValueError("Expenses cannot exceed or equal income.")
        return self


# ─────────────────────────────────────────
# 💼 PROFESSIONAL — CALIFORNIA-SPECIFIC
# ─────────────────────────────────────────

class CaliforniaSector(str, Enum):
    # California-flagship industries
    TECHNOLOGY = "Technology"
    BIOTECHNOLOGY = "Biotechnology"
    ENTERTAINMENT = "Entertainment & Media"
    AGRICULTURE = "Agriculture"
    TOURISM = "Tourism & Hospitality"

    # Major California industries
    AEROSPACE = "Aerospace & Defense"
    FINANCE = "Finance & Banking"
    HEALTHCARE = "Healthcare"
    REAL_ESTATE = "Real Estate"
    GOVERNMENT = "Government & Public Sector"
    EDUCATION = "Education"

    # Standard sectors (preserved from original)
    LAW_ADMIN = "Law & Administration"
    CONSTRUCTION_INDUSTRY = "Construction & Industry"
    TRADE_SERVICES = "Trade & Services"
    ARTS = "Arts & Crafts"
    TRANSPORTATION = "Transportation"
    ENERGY = "Energy"
    MEDIA_COMMUNICATIONS = "Media & Communications"
    SCIENCE_RESEARCH = "Science & Research"

    # Niche California
    WINE_INDUSTRY = "Wine & Spirits"
    CANNABIS = "Cannabis Industry"
    VENTURE_CAPITAL = "Venture Capital"

    OTHER = "Other"


# Keep existing Profession enum (150+ professions - too valuable to lose)
class Profession(str, Enum):
    # TECHNOLOGY
    SOFTWARE_ENGINEER = "Software Engineer"
    BACKEND_DEVELOPER = "Backend Developer"
    FRONTEND_DEVELOPER = "Frontend Developer"
    FULLSTACK_DEVELOPER = "Full Stack Developer"
    DATA_SCIENTIST = "Data Scientist"
    MACHINE_LEARNING_ENGINEER = "Machine Learning Engineer"
    AI_ENGINEER = "AI Engineer"
    DEVOPS_ENGINEER = "DevOps Engineer"
    CLOUD_ENGINEER = "Cloud Engineer"
    CYBERSECURITY_ANALYST = "Cybersecurity Analyst"
    NETWORK_ENGINEER = "Network Engineer"
    QA_ENGINEER = "QA Engineer"
    MOBILE_APP_DEVELOPER = "Mobile App Developer"
    GAME_DEVELOPER = "Game Developer"
    EMBEDDED_SYSTEMS_ENGINEER = "Embedded Systems Engineer"

    # FINANCE
    ACCOUNTANT = "Accountant"
    FINANCIAL_ANALYST = "Financial Analyst"
    INVESTMENT_BANKER = "Investment Banker"
    AUDITOR = "Auditor"
    TAX_CONSULTANT = "Tax Consultant"
    RISK_MANAGER = "Risk Manager"
    PORTFOLIO_MANAGER = "Portfolio Manager"
    FINANCIAL_PLANNER = "Financial Planner"
    CREDIT_ANALYST = "Credit Analyst"
    INSURANCE_UNDERWRITER = "Insurance Underwriter"

    # HEALTHCARE
    GENERAL_PRACTITIONER = "General Practitioner"
    SURGEON = "Surgeon"
    NURSE = "Nurse"
    PHARMACIST = "Pharmacist"
    DENTIST = "Dentist"
    PHYSIOTHERAPIST = "Physiotherapist"
    RADIOLOGIST = "Radiologist"
    PSYCHOLOGIST = "Psychologist"
    PSYCHIATRIST = "Psychiatrist"
    MEDICAL_LAB_TECHNICIAN = "Medical Lab Technician"

    # EDUCATION
    TEACHER = "Teacher"
    UNIVERSITY_PROFESSOR = "University Professor"
    TEACHING_ASSISTANT = "Teaching Assistant"
    SCHOOL_COUNSELOR = "School Counselor"
    EDUCATIONAL_CONSULTANT = "Educational Consultant"
    INSTRUCTIONAL_DESIGNER = "Instructional Designer"
    ONLINE_TUTOR = "Online Tutor"
    CURRICULUM_DEVELOPER = "Curriculum Developer"

    # LAW & ADMIN
    LAWYER = "Lawyer"
    LEGAL_ADVISOR = "Legal Advisor"
    PARALEGAL = "Paralegal"
    JUDGE = "Judge"
    PUBLIC_ADMINISTRATOR = "Public Administrator"
    HR_MANAGER = "HR Manager"
    OFFICE_MANAGER = "Office Manager"
    COMPLIANCE_OFFICER = "Compliance Officer"

    # CONSTRUCTION & INDUSTRY
    CIVIL_ENGINEER = "Civil Engineer"
    ARCHITECT = "Architect"
    MECHANICAL_ENGINEER = "Mechanical Engineer"
    ELECTRICAL_ENGINEER = "Electrical Engineer"
    CONSTRUCTION_MANAGER = "Construction Manager"
    SURVEYOR = "Surveyor"
    WELDER = "Welder"
    INDUSTRIAL_ENGINEER = "Industrial Engineer"

    # TRADE & SERVICES
    SALES_MANAGER = "Sales Manager"
    RETAIL_WORKER = "Retail Worker"
    CUSTOMER_SUPPORT_SPECIALIST = "Customer Support Specialist"
    MARKETING_SPECIALIST = "Marketing Specialist"
    DIGITAL_MARKETER = "Digital Marketer"
    BUSINESS_ANALYST = "Business Analyst"
    PRODUCT_MANAGER = "Product Manager"
    ACCOUNT_MANAGER = "Account Manager"

    # ARTS & ENTERTAINMENT (heavy in California!)
    GRAPHIC_DESIGNER = "Graphic Designer"
    UX_UI_DESIGNER = "UX/UI Designer"
    PHOTOGRAPHER = "Photographer"
    VIDEO_EDITOR = "Video Editor"
    ANIMATOR = "Animator"
    MUSICIAN = "Musician"
    ACTOR = "Actor"
    FILM_DIRECTOR = "Film Director"
    SCREENWRITER = "Screenwriter"  # ⭐ ADDED for LA
    PRODUCER = "Producer"  # ⭐ ADDED for LA
    EDITOR = "Editor"  # ⭐ ADDED for LA

    # AGRICULTURE (Central Valley!)
    FARMER = "Farmer"
    AGRONOMIST = "Agronomist"
    VETERINARIAN = "Veterinarian"
    AGRICULTURAL_TECHNICIAN = "Agricultural Technician"
    GREENHOUSE_WORKER = "Greenhouse Worker"
    WINEMAKER = "Winemaker"  # ⭐ ADDED for Central Coast
    VINEYARD_MANAGER = "Vineyard Manager"  # ⭐ ADDED

    # TRANSPORTATION
    TRUCK_DRIVER = "Truck Driver"
    DELIVERY_DRIVER = "Delivery Driver"
    PILOT = "Pilot"
    FLIGHT_ATTENDANT = "Flight Attendant"
    LOGISTICS_COORDINATOR = "Logistics Coordinator"
    WAREHOUSE_MANAGER = "Warehouse Manager"
    SHIP_CAPTAIN = "Ship Captain"

    # ENERGY
    ENERGY_ENGINEER = "Energy Engineer"
    SOLAR_TECHNICIAN = "Solar Technician"
    WIND_TURBINE_TECHNICIAN = "Wind Turbine Technician"
    OIL_GAS_ENGINEER = "Oil & Gas Engineer"
    POWER_PLANT_OPERATOR = "Power Plant Operator"

    # REAL ESTATE
    REAL_ESTATE_AGENT = "Real Estate Agent"
    PROPERTY_MANAGER = "Property Manager"
    REAL_ESTATE_BROKER = "Real Estate Broker"
    REAL_ESTATE_INVESTOR = "Real Estate Investor"

    # MEDIA
    JOURNALIST = "Journalist"
    NEWS_ANCHOR = "News Anchor"
    CONTENT_CREATOR = "Content Creator"
    COPYWRITER = "Copywriter"
    SOCIAL_MEDIA_MANAGER = "Social Media Manager"

    # SCIENCE (biotech in San Diego!)
    RESEARCH_SCIENTIST = "Research Scientist"
    BIOLOGIST = "Biologist"
    CHEMIST = "Chemist"
    PHYSICIST = "Physicist"
    DATA_ANALYST = "Data Analyst"
    BIOTECH_RESEARCHER = "Biotech Researcher"  # ⭐ ADDED for San Diego
    CLINICAL_RESEARCHER = "Clinical Researcher"  # ⭐ ADDED

    # OTHER
    ELECTRICIAN = "Electrician"
    PLUMBER = "Plumber"
    CHEF = "Chef"
    FITNESS_TRAINER = "Fitness Trainer"
    HAIRDRESSER = "Hairdresser"

    # EXTRA
    SCRUM_MASTER = "Scrum Master"
    BLOCKCHAIN_DEVELOPER = "Blockchain Developer"
    ETHICAL_HACKER = "Ethical Hacker"
    QUANTITATIVE_ANALYST = "Quantitative Analyst"
    ACTUARY = "Actuary"
    OCCUPATIONAL_THERAPIST = "Occupational Therapist"
    SPEECH_THERAPIST = "Speech Therapist"
    SPECIAL_EDUCATION_TEACHER = "Special Education Teacher"
    PROSECUTOR = "Prosecutor"
    NOTARY = "Notary"
    URBAN_PLANNER = "Urban Planner"
    SAFETY_ENGINEER = "Safety Engineer"
    PROCUREMENT_MANAGER = "Procurement Manager"
    SUPPLY_CHAIN_ANALYST = "Supply Chain Analyst"
    EVENT_MANAGER = "Event Manager"
    INTERIOR_DESIGNER = "Interior Designer"
    FASHION_DESIGNER = "Fashion Designer"
    SOUND_ENGINEER = "Sound Engineer"
    GAME_DESIGNER = "Game Designer"
    FORESTRY_ENGINEER = "Forestry Engineer"
    FISHERIES_SPECIALIST = "Fisheries Specialist"
    TRAIN_OPERATOR = "Train Operator"
    AIR_TRAFFIC_CONTROLLER = "Air Traffic Controller"
    RENEWABLE_ENERGY_ANALYST = "Renewable Energy Analyst"
    FACILITY_MANAGER = "Facility Manager"
    PR_MANAGER = "PR Manager"
    TECHNICAL_WRITER = "Technical Writer"
    STATISTICIAN = "Statistician"
    ECONOMIST = "Economist"
    MATHEMATICIAN = "Mathematician"
    SECURITY_GUARD = "Security Guard"
    FIREFIGHTER = "Firefighter"
    POLICE_OFFICER = "Police Officer"
    TRANSLATOR = "Translator"
    INTERPRETER = "Interpreter"
    LIBRARIAN = "Librarian"
    ARCHIVIST = "Archivist"
    TOUR_GUIDE = "Tour Guide"
    BARTENDER = "Bartender"

    # ⭐ NEW California-specific
    STARTUP_FOUNDER = "Startup Founder"
    VC_ANALYST = "Venture Capital Analyst"
    BUDTENDER = "Budtender (Cannabis)"


class EmploymentStatus(str, Enum):
    FULL_TIME = "full-time"
    PART_TIME = "part-time"
    FREELANCER = "freelancer"
    SELF_EMPLOYED = "self-employed"
    UNEMPLOYED = "unemployed"
    STUDENT = "student"
    RETIRED = "retired"


class RiskProfile(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"

    @property
    def goal(self) -> str:
        return {
            RiskProfile.LOW: "safety",
            RiskProfile.MEDIUM: "growth",
            RiskProfile.HIGH: "profit",
        }[self]


# ⭐ NEW: California-specific professional fields (all optional)

class TechRole(str, Enum):
    SOFTWARE_ENGINEER = "Software Engineer"
    PRODUCT_MANAGER = "Product Manager"
    DESIGNER = "Designer (UX/UI)"
    DATA_SCIENTIST = "Data Scientist"
    DEVOPS_SRE = "DevOps / SRE"
    SECURITY = "Security Engineer"
    HARDWARE = "Hardware Engineer"
    QA = "QA / Test Engineer"
    ENGINEERING_MANAGER = "Engineering Manager"
    EXECUTIVE = "Tech Executive (VP/CTO/CEO)"
    OTHER_TECH = "Other Tech Role"


class EquityCompensation(str, Enum):
    NONE = "None"
    ISO = "ISO (Incentive Stock Options)"
    NSO = "NSO (Non-qualified Stock Options)"
    RSU = "RSU (Restricted Stock Units)"
    ESPP = "ESPP (Employee Stock Purchase)"
    FOUNDER_STOCK = "Founder Stock"
    MIXED = "Mixed (RSUs + Options)"


class CompanyStage(str, Enum):
    PRE_SEED = "Pre-seed Startup"
    SEED = "Seed Stage Startup"
    SERIES_A_B = "Series A-B"
    SERIES_C_PLUS = "Series C+"
    PRE_IPO = "Pre-IPO / Late Stage"
    PUBLIC = "Public Company"
    FAANG = "Big Tech / FAANG"
    GOVERNMENT = "Government"
    NONPROFIT = "Nonprofit"
    SMALL_BUSINESS = "Small Business"
    NA = "Not Applicable"


class EntertainmentRole(str, Enum):
    ABOVE_LINE = "Above-the-line (Writer/Director/Producer)"
    BELOW_LINE = "Below-the-line (Crew)"
    PERFORMER = "Performer (Actor/Musician)"
    EXECUTIVE = "Studio Executive"
    INDEPENDENT_CONTRACTOR = "Independent Contractor"
    AGENT_MANAGER = "Agent / Manager"
    NA = "Not Applicable"


# ─────────────────────────────────────────
# ⚙️ PREFERENCES
# ─────────────────────────────────────────

class HorizonGroup(str, Enum):
    SHORT = "1-3"
    MEDIUM = "3-5"
    LONG = "5-8"
    VERY_LONG = "8+"


class Preferences(BaseModel):
    risk_profile: RiskProfile
    horizon: HorizonGroup


# ─────────────────────────
# ⏰ WEEKLY HOURS AVAILABLE
# ─────────────────────────

class WeeklyHours(str, Enum):
    MINIMAL = "0-5"
    LIGHT = "5-15"
    MODERATE = "15-30"
    HEAVY = "30+"


# 🎯 PREDEFINED INTERESTS (50)
PREDEFINED_INTERESTS = [
    # Sport & fitness
    "fitness", "yoga", "running", "cycling", "swimming",
    "team sports", "martial arts", "hiking", "rock climbing", "skiing",

    # Food & drink
    "cooking", "baking", "wine", "coffee", "barbecue",

    # Tech & gaming
    "programming", "ai/ml", "gaming", "blockchain", "robotics",

    # Creative
    "photography", "videography", "music", "writing", "drawing",
    "design", "fashion", "interior design", "crafts",

    # Business & finance
    "investing", "real estate", "startups", "crypto", "trading",

    # Travel & lifestyle
    "travel", "languages", "history", "cultures", "outdoor adventure",

    # Wellness & lifestyle
    "meditation", "psychology", "self-improvement", "minimalism", "sustainability",

    # Education & hobbies
    "reading", "podcasts", "online courses", "board games", "puzzles",
    "gardening",
]


class ProfessionalInfo(BaseModel):
    sector: CaliforniaSector
    profession: Profession
    employment_status: EmploymentStatus

    interests: List[str] = Field(
        default_factory=list,
        description=f"List of interests. Predefined: {len(PREDEFINED_INTERESTS)}, custom allowed.",
        max_length=4
    )
    prior_experience: str = Field(
        default="",
        description="Brief description of previous businesses/projects",
        max_length=500
    )
    weekly_hours: WeeklyHours = Field(
        default=WeeklyHours.LIGHT,
        description="Hours per week available for business"
    )

    # ⭐ NEW: California-specific optional fields
    tech_role: Optional[TechRole] = Field(
        default=None,
        description="Specific tech role (if applicable, Bay Area focus)"
    )
    equity_compensation: Optional[EquityCompensation] = Field(
        default=None,
        description="Type of equity compensation received"
    )
    company_stage: Optional[CompanyStage] = Field(
        default=None,
        description="Stage of current employer (especially for tech/biotech)"
    )
    qsbs_eligible: Optional[bool] = Field(
        default=None,
        description="Does your stock qualify for QSBS exclusion? (Section 1202)"
    )
    entertainment_role: Optional[EntertainmentRole] = Field(
        default=None,
        description="Entertainment industry role (LA-specific)"
    )


# ─────────────────────────────────────────
# 👤 PERSONAL
# ─────────────────────────────────────────

class PersonalInfo(BaseModel):
    age: int = Field(..., gt=17, lt=120)


# ─────────────────────────────────────────
# 🔥 FINAL USER INPUT
# ─────────────────────────────────────────

class UserInput(BaseModel):
    personal: PersonalInfo
    location: LocationInfo
    financial: FinancialInfo
    professional: ProfessionalInfo
    preferences: Preferences