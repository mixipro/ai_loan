# app/core/california_config.py

"""
California regions, cities, tax brackets, and baseline data.
Hardkodovano za stabilnost — live data dolazi preko web search tools.
"""

from enum import Enum


# ═══════════════════════════════════════════════════════════════
# 🗺️ CALIFORNIA REGIONS
# ═══════════════════════════════════════════════════════════════

class CaliforniaRegion(str, Enum):
    BAY_AREA = "BAY_AREA"
    LOS_ANGELES = "LOS_ANGELES"
    SAN_DIEGO = "SAN_DIEGO"
    SACRAMENTO = "SACRAMENTO"
    CENTRAL_VALLEY = "CENTRAL_VALLEY"
    INLAND_EMPIRE = "INLAND_EMPIRE"
    ORANGE_COUNTY = "ORANGE_COUNTY"
    CENTRAL_COAST = "CENTRAL_COAST"


# ═══════════════════════════════════════════════════════════════
# 🏙️ REGION DETAILED DATA
# ═══════════════════════════════════════════════════════════════

REGION_DATA = {
    CaliforniaRegion.BAY_AREA: {
        "display_name": "Bay Area",
        "description": "Tech-driven Northern California — SF, Silicon Valley, East Bay",
        "cities": [
            "San Francisco", "San Jose", "Oakland", "Berkeley",
            "Palo Alto", "Mountain View", "Cupertino", "Sunnyvale",
            "Santa Clara", "Fremont", "Redwood City", "San Mateo",
            "Daly City", "Hayward", "Walnut Creek", "Concord",
            "Richmond", "San Rafael",
        ],
        "median_household_income": 130000,
        "cost_of_living_index": 1.85,
        "median_home_price": 1400000,
        "avg_price_per_sqft": 1100,
        "median_2br_rent": 4200,
        "rental_yield_avg": 0.035,
        "appreciation_5yr_avg": 0.06,
        "property_tax_effective": 0.0085,
        "primary_industries": ["tech", "biotech", "venture_capital", "finance"],
        "risk_factors": {"earthquake": "high", "wildfire": "low", "flood": "low"},
        "vibe": "fast-paced, equity-rich, expensive",
    },

    CaliforniaRegion.LOS_ANGELES: {
        "display_name": "Los Angeles",
        "description": "Entertainment capital, diverse industries",
        "cities": [
            "Los Angeles", "Long Beach", "Pasadena", "Santa Monica",
            "Beverly Hills", "Burbank", "Glendale", "Torrance",
            "Inglewood", "Manhattan Beach", "Hermosa Beach", "Culver City",
            "West Hollywood", "Hollywood", "Venice", "Marina del Rey",
            "Studio City", "Sherman Oaks",
        ],
        "median_household_income": 75000,
        "cost_of_living_index": 1.50,
        "median_home_price": 900000,
        "avg_price_per_sqft": 750,
        "median_2br_rent": 3000,
        "rental_yield_avg": 0.040,
        "appreciation_5yr_avg": 0.055,
        "property_tax_effective": 0.0080,
        "primary_industries": ["entertainment", "tourism", "aerospace", "fashion"],
        "risk_factors": {"earthquake": "high", "wildfire": "high", "flood": "moderate"},
        "vibe": "creative, diverse, image-conscious",
    },

    CaliforniaRegion.SAN_DIEGO: {
        "display_name": "San Diego",
        "description": "Biotech hub, military, beach lifestyle",
        "cities": [
            "San Diego", "La Jolla", "Carlsbad", "Encinitas",
            "Del Mar", "Chula Vista", "Oceanside", "Escondido",
            "Coronado", "Pacific Beach", "Solana Beach", "Poway",
        ],
        "median_household_income": 88000,
        "cost_of_living_index": 1.45,
        "median_home_price": 850000,
        "avg_price_per_sqft": 700,
        "median_2br_rent": 2800,
        "rental_yield_avg": 0.042,
        "appreciation_5yr_avg": 0.058,
        "property_tax_effective": 0.0078,
        "primary_industries": ["biotech", "military_defense", "tourism", "tech"],
        "risk_factors": {"earthquake": "moderate", "wildfire": "high", "flood": "low"},
        "vibe": "relaxed, outdoorsy, military-influenced",
    },

    CaliforniaRegion.SACRAMENTO: {
        "display_name": "Sacramento Region",
        "description": "State government center, growing tech",
        "cities": [
            "Sacramento", "Davis", "Roseville", "Elk Grove",
            "Folsom", "Rancho Cordova", "Citrus Heights", "West Sacramento",
            "Woodland", "Rocklin", "Lincoln", "Auburn",
        ],
        "median_household_income": 72000,
        "cost_of_living_index": 1.15,
        "median_home_price": 520000,
        "avg_price_per_sqft": 380,
        "median_2br_rent": 2000,
        "rental_yield_avg": 0.052,
        "appreciation_5yr_avg": 0.065,
        "property_tax_effective": 0.0095,
        "primary_industries": ["government", "healthcare", "education", "agriculture"],
        "risk_factors": {"earthquake": "moderate", "wildfire": "moderate", "flood": "moderate"},
        "vibe": "government town, family-oriented",
    },

    CaliforniaRegion.CENTRAL_VALLEY: {
        "display_name": "Central Valley",
        "description": "Agricultural heartland, affordable",
        "cities": [
            "Fresno", "Bakersfield", "Stockton", "Modesto",
            "Visalia", "Merced", "Tulare", "Hanford",
            "Lodi", "Turlock", "Madera", "Porterville",
        ],
        "median_household_income": 58000,
        "cost_of_living_index": 0.95,
        "median_home_price": 380000,
        "avg_price_per_sqft": 250,
        "median_2br_rent": 1500,
        "rental_yield_avg": 0.060,
        "appreciation_5yr_avg": 0.070,
        "property_tax_effective": 0.0105,
        "primary_industries": ["agriculture", "food_processing", "logistics", "healthcare"],
        "risk_factors": {"earthquake": "low", "wildfire": "moderate", "drought": "high"},
        "vibe": "agricultural, family-oriented, affordable",
    },

    CaliforniaRegion.INLAND_EMPIRE: {
        "display_name": "Inland Empire",
        "description": "Affordable SoCal alternative, logistics hub",
        "cities": [
            "Riverside", "San Bernardino", "Ontario", "Fontana",
            "Rancho Cucamonga", "Moreno Valley", "Corona", "Murrieta",
            "Temecula", "Redlands", "Chino", "Upland",
            "Hemet", "Pomona", "Victorville",
        ],
        "median_household_income": 70000,
        "cost_of_living_index": 1.20,
        "median_home_price": 580000,
        "avg_price_per_sqft": 380,
        "median_2br_rent": 2100,
        "rental_yield_avg": 0.045,
        "appreciation_5yr_avg": 0.070,
        "property_tax_effective": 0.0110,
        "primary_industries": ["logistics", "warehousing", "manufacturing", "healthcare"],
        "risk_factors": {"earthquake": "moderate", "wildfire": "high", "heat": "high"},
        "vibe": "commuter-friendly, suburbs, warehouse jobs",
    },

    CaliforniaRegion.ORANGE_COUNTY: {
        "display_name": "Orange County",
        "description": "Affluent SoCal coast, corporate + beach",
        "cities": [
            "Irvine", "Anaheim", "Newport Beach", "Huntington Beach",
            "Costa Mesa", "Santa Ana", "Fullerton", "Mission Viejo",
            "Laguna Beach", "Dana Point", "San Clemente", "Tustin",
            "Yorba Linda", "Garden Grove", "Westminster", "Orange",
        ],
        "median_household_income": 100000,
        "cost_of_living_index": 1.55,
        "median_home_price": 1100000,
        "avg_price_per_sqft": 850,
        "median_2br_rent": 3200,
        "rental_yield_avg": 0.038,
        "appreciation_5yr_avg": 0.058,
        "property_tax_effective": 0.0085,
        "primary_industries": ["tech", "healthcare", "finance", "tourism"],
        "risk_factors": {"earthquake": "high", "wildfire": "moderate", "flood": "low"},
        "vibe": "affluent suburbs, beach communities",
    },

    CaliforniaRegion.CENTRAL_COAST: {
        "display_name": "Central Coast",
        "description": "Wine country, tourism, scenic",
        "cities": [
            "Santa Barbara", "San Luis Obispo", "Monterey", "Carmel",
            "Salinas", "Santa Cruz", "Paso Robles", "Pismo Beach",
            "Morro Bay", "Cambria", "Solvang", "Ventura",
        ],
        "median_household_income": 78000,
        "cost_of_living_index": 1.40,
        "median_home_price": 850000,
        "avg_price_per_sqft": 700,
        "median_2br_rent": 2700,
        "rental_yield_avg": 0.040,
        "appreciation_5yr_avg": 0.055,
        "property_tax_effective": 0.0090,
        "primary_industries": ["agriculture", "tourism", "education", "wine_industry"],
        "risk_factors": {"earthquake": "moderate", "wildfire": "high", "flood": "low"},
        "vibe": "wine country, slow-paced, scenic",
    },
}

# ═══════════════════════════════════════════════════════════════
# 🏠 CITY-LEVEL OVERRIDES (specifični gradovi sa drugačijim cenama)
# ═══════════════════════════════════════════════════════════════

CITY_OVERRIDES = {
    # Bay Area premium cities
    "Palo Alto": {"price_per_sqft": 1800, "rent_2br": 5800},
    "San Francisco": {"price_per_sqft": 1300, "rent_2br": 4500},
    "Mountain View": {"price_per_sqft": 1400, "rent_2br": 4000},
    "Cupertino": {"price_per_sqft": 1500, "rent_2br": 4200},
    "San Jose": {"price_per_sqft": 900, "rent_2br": 3200},
    "Oakland": {"price_per_sqft": 700, "rent_2br": 2800},
    "Berkeley": {"price_per_sqft": 1000, "rent_2br": 3500},

    # LA premium cities
    "Beverly Hills": {"price_per_sqft": 1500, "rent_2br": 5500},
    "Santa Monica": {"price_per_sqft": 1300, "rent_2br": 4500},
    "Manhattan Beach": {"price_per_sqft": 1400, "rent_2br": 4800},
    "Hollywood": {"price_per_sqft": 900, "rent_2br": 3200},
    "Long Beach": {"price_per_sqft": 550, "rent_2br": 2400},

    # San Diego premium
    "La Jolla": {"price_per_sqft": 1400, "rent_2br": 4500},
    "Del Mar": {"price_per_sqft": 1500, "rent_2br": 5000},
    "Coronado": {"price_per_sqft": 1300, "rent_2br": 4200},

    # Orange County premium
    "Newport Beach": {"price_per_sqft": 1500, "rent_2br": 4800},
    "Laguna Beach": {"price_per_sqft": 1400, "rent_2br": 4500},
    "Irvine": {"price_per_sqft": 900, "rent_2br": 3500},

    # Central Coast premium
    "Santa Barbara": {"price_per_sqft": 1200, "rent_2br": 4000},
    "Carmel": {"price_per_sqft": 1400, "rent_2br": 4500},
}

# ═══════════════════════════════════════════════════════════════
# 🏛️ CALIFORNIA TAX BRACKETS (2024-2025)
# ═══════════════════════════════════════════════════════════════

CALIFORNIA_STATE_TAX_SINGLE = [
    # (max_income, rate)
    (10412, 0.01),
    (24684, 0.02),
    (38959, 0.04),
    (54081, 0.06),
    (68350, 0.08),
    (349137, 0.093),
    (418961, 0.103),
    (698271, 0.113),
    (float('inf'), 0.123),
]

CALIFORNIA_STATE_TAX_MARRIED = [
    (20824, 0.01),
    (49368, 0.02),
    (77918, 0.04),
    (108162, 0.06),
    (136700, 0.08),
    (698274, 0.093),
    (837922, 0.103),
    (1396542, 0.113),
    (float('inf'), 0.123),
]

# Federal tax brackets (2024)
FEDERAL_TAX_SINGLE = [
    (11600, 0.10),
    (47150, 0.12),
    (100525, 0.22),
    (191950, 0.24),
    (243725, 0.32),
    (609350, 0.35),
    (float('inf'), 0.37),
]

# Mental health tax — additional 1% on income > $1M in California
MENTAL_HEALTH_TAX_THRESHOLD = 1_000_000
MENTAL_HEALTH_TAX_RATE = 0.01

# ═══════════════════════════════════════════════════════════════
# 🏠 PROPERTY & SPECIAL TAXES
# ═══════════════════════════════════════════════════════════════

PROP_13_BASE_RATE = 0.01  # 1% of assessed value
PROP_13_ANNUAL_INCREASE_CAP = 0.02  # 2% max yearly increase

# LLC franchise tax (California minimum)
LLC_FRANCHISE_TAX_MIN = 800  # USD per year

# QSBS exclusion limit (Federal IRS Section 1202)
QSBS_EXCLUSION_MAX = 10_000_000  # Up to $10M tax-free


# ═══════════════════════════════════════════════════════════════
# 🔍 HELPER FUNCTIONS
# ═══════════════════════════════════════════════════════════════

def get_region_data(region: CaliforniaRegion) -> dict:
    """Returns full data dict for a California region."""
    return REGION_DATA[region]


def get_cities_for_region(region: CaliforniaRegion) -> list[str]:
    """Returns list of cities in a region."""
    return REGION_DATA[region]["cities"]


def get_all_california_cities() -> list[str]:
    """Returns flat list of all California cities across all regions."""
    cities = []
    for region_data in REGION_DATA.values():
        cities.extend(region_data["cities"])
    return cities


def find_region_for_city(city: str) -> CaliforniaRegion | None:
    """Returns the region containing a given city, or None."""
    for region, data in REGION_DATA.items():
        if city in data["cities"]:
            return region
    return None


def get_city_real_estate_data(city: str, region: CaliforniaRegion) -> dict:
    """
    Returns real estate data for a city.
    Uses CITY_OVERRIDES if specific, falls back to region average.
    """
    region_data = REGION_DATA[region]

    if city in CITY_OVERRIDES:
        return {
            "price_per_sqft": CITY_OVERRIDES[city]["price_per_sqft"],
            "rent_2br": CITY_OVERRIDES[city]["rent_2br"],
            "property_tax_effective": region_data["property_tax_effective"],
            "rental_yield_avg": region_data["rental_yield_avg"],
            "source": "city_specific",
        }

    # Fall back to region average
    return {
        "price_per_sqft": region_data["avg_price_per_sqft"],
        "rent_2br": region_data["median_2br_rent"],
        "property_tax_effective": region_data["property_tax_effective"],
        "rental_yield_avg": region_data["rental_yield_avg"],
        "source": "region_average",
    }