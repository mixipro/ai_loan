# app/models/user.py

from pydantic import BaseModel, Field, model_validator
from typing import List
from enum import Enum


# ─────────────────────────────────────────
# 🌍 LOCATION
# ─────────────────────────────────────────

class Country(str, Enum):
    USA          = "US"
    GERMANY      = "DE"
    JAPAN        = "JP"
    INDIA        = "IN"
    UK           = "GB"
    FRANCE       = "FR"
    ITALY        = "IT"
    BRAZIL       = "BR"
    CANADA       = "CA"
    RUSSIA       = "RU"
    SOUTH_KOREA  = "KR"
    AUSTRALIA    = "AU"
    SPAIN        = "ES"
    MEXICO       = "MX"
    INDONESIA    = "ID"
    NETHERLANDS  = "NL"
    SAUDI_ARABIA = "SA"
    TURKEY       = "TR"
    SWITZERLAND  = "CH"
    SERBIA       = "RS"


CITIES_BY_COUNTRY: dict[str, list[str]] = {
    "US": [
        "New York", "Los Angeles", "Chicago", "Houston", "Phoenix",
        "Philadelphia", "San Antonio", "San Diego", "Dallas", "San Jose",
        "Austin", "Jacksonville", "Fort Worth", "Columbus", "Charlotte",
        "Indianapolis", "San Francisco", "Seattle", "Denver", "Nashville",
        "Oklahoma City", "El Paso", "Washington", "Boston", "Memphis",
        "Louisville", "Portland", "Las Vegas", "Baltimore", "Milwaukee",
        "Albuquerque", "Tucson", "Fresno", "Sacramento", "Kansas City",
        "Mesa", "Atlanta", "Omaha", "Colorado Springs", "Raleigh",
        "Long Beach", "Virginia Beach", "Minneapolis", "Tampa", "New Orleans",
        "Arlington", "Bakersfield", "Honolulu", "Anaheim", "Aurora", "Miami",
    ],
    "DE": [
        "Berlin", "Hamburg", "Munich", "Cologne", "Frankfurt",
        "Stuttgart", "Düsseldorf", "Leipzig", "Dortmund", "Essen",
        "Bremen", "Dresden", "Hanover", "Nuremberg", "Duisburg",
        "Bochum", "Wuppertal", "Bielefeld", "Bonn", "Münster",
        "Karlsruhe", "Mannheim", "Augsburg", "Wiesbaden", "Gelsenkirchen",
        "Mönchengladbach", "Braunschweig", "Kiel", "Chemnitz", "Aachen",
        "Halle", "Magdeburg", "Freiburg", "Krefeld", "Lübeck",
        "Oberhausen", "Erfurt", "Mainz", "Rostock", "Kassel",
        "Hagen", "Hamm", "Saarbrücken", "Mülheim", "Potsdam",
        "Ludwigshafen", "Oldenburg", "Leverkusen", "Osnabrück", "Solingen",
    ],
    "JP": [
        "Tokyo", "Yokohama", "Osaka", "Nagoya", "Sapporo",
        "Fukuoka", "Kobe", "Kawasaki", "Kyoto", "Saitama",
        "Hiroshima", "Sendai", "Kitakyushu", "Chiba", "Sakai",
        "Niigata", "Hamamatsu", "Shizuoka", "Sagamihara", "Okayama",
        "Kumamoto", "Kagoshima", "Funabashi", "Hachioji", "Higashiosaka",
        "Matsuyama", "Utsunomiya", "Matsudo", "Nishinomiya", "Kanazawa",
        "Oita", "Kurashiki", "Yokosuka", "Nagasaki", "Kawaguchi",
        "Himeji", "Ichikawa", "Amagasaki", "Nara", "Suita",
        "Toyama", "Toyonaka", "Wakayama", "Asahikawa", "Takatsuki",
        "Iwaki", "Koriyama", "Hakodate", "Nagano", "Akita",
    ],
    "IN": [
        "Mumbai", "Delhi", "Bangalore", "Hyderabad", "Ahmedabad",
        "Chennai", "Kolkata", "Surat", "Pune", "Jaipur",
        "Lucknow", "Kanpur", "Nagpur", "Indore", "Thane",
        "Bhopal", "Visakhapatnam", "Pimpri-Chinchwad", "Patna", "Vadodara",
        "Ghaziabad", "Ludhiana", "Agra", "Nashik", "Faridabad",
        "Meerut", "Rajkot", "Varanasi", "Srinagar", "Aurangabad",
        "Dhanbad", "Amritsar", "Navi Mumbai", "Allahabad", "Ranchi",
        "Howrah", "Coimbatore", "Jabalpur", "Gwalior", "Vijayawada",
        "Jodhpur", "Madurai", "Raipur", "Kota", "Chandigarh",
        "Guwahati", "Solapur", "Hubballi", "Tiruchirappalli", "Mysore",
    ],
    "GB": [
        "London", "Birmingham", "Manchester", "Leeds", "Glasgow",
        "Sheffield", "Bradford", "Edinburgh", "Liverpool", "Bristol",
        "Cardiff", "Coventry", "Nottingham", "Leicester", "Sunderland",
        "Belfast", "Newcastle", "Brighton", "Hull", "Plymouth",
        "Stoke-on-Trent", "Wolverhampton", "Derby", "Swansea", "Southampton",
        "Salford", "Aberdeen", "Westminster", "Portsmouth", "York",
        "Peterborough", "Dundee", "Lancaster", "Oxford", "Newport",
        "Preston", "St Albans", "Norwich", "Chester", "Cambridge",
        "Salisbury", "Exeter", "Gloucester", "Lincoln", "Bath",
        "Worcester", "Canterbury", "Hereford", "Truro", "Ripon",
    ],
    "FR": [
        "Paris", "Marseille", "Lyon", "Toulouse", "Nice",
        "Nantes", "Montpellier", "Strasbourg", "Bordeaux", "Lille",
        "Rennes", "Reims", "Saint-Étienne", "Toulon", "Le Havre",
        "Grenoble", "Dijon", "Angers", "Nîmes", "Villeurbanne",
        "Saint-Denis", "Le Mans", "Aix-en-Provence", "Clermont-Ferrand", "Brest",
        "Limoges", "Tours", "Amiens", "Perpignan", "Metz",
        "Besançon", "Boulogne-Billancourt", "Orléans", "Mulhouse", "Rouen",
        "Caen", "Nancy", "Saint-Paul", "Argenteuil", "Montreuil",
        "Roubaix", "Dunkirk", "Tourcoing", "Avignon", "Poitiers",
        "Versailles", "Pau", "La Rochelle", "Antibes", "Cannes",
    ],
    "IT": [
        "Rome", "Milan", "Naples", "Turin", "Palermo",
        "Genoa", "Bologna", "Florence", "Bari", "Catania",
        "Venice", "Verona", "Messina", "Padua", "Trieste",
        "Taranto", "Brescia", "Parma", "Prato", "Modena",
        "Reggio Calabria", "Reggio Emilia", "Perugia", "Livorno", "Ravenna",
        "Cagliari", "Foggia", "Rimini", "Salerno", "Ferrara",
        "Sassari", "Latina", "Giugliano", "Monza", "Syracuse",
        "Bergamo", "Pescara", "Trento", "Forlì", "Vicenza",
        "Terni", "Bolzano", "Novara", "Piacenza", "Andria",
        "Ancona", "Arezzo", "Udine", "Cesena", "Lecce",
    ],
    "BR": [
        "São Paulo", "Rio de Janeiro", "Brasília", "Salvador", "Fortaleza",
        "Belo Horizonte", "Manaus", "Curitiba", "Recife", "Goiânia",
        "Belém", "Porto Alegre", "Guarulhos", "Campinas", "São Luís",
        "São Gonçalo", "Maceió", "Duque de Caxias", "Natal", "Teresina",
        "Campo Grande", "Nova Iguaçu", "Santo André", "São Bernardo do Campo", "João Pessoa",
        "Osasco", "Jaboatão dos Guararapes", "Contagem", "Ribeirão Preto", "São José dos Campos",
        "Uberlândia", "Sorocaba", "Cuiabá", "Aracaju", "Feira de Santana",
        "Joinville", "Aparecida de Goiânia", "Londrina", "Ananindeua", "Porto Velho",
        "Serra", "Niterói", "Caxias do Sul", "Macapá", "Florianópolis",
        "Vila Velha", "Mogi das Cruzes", "Belford Roxo", "Santos", "Betim",
    ],
    "CA": [
        "Toronto", "Montreal", "Vancouver", "Calgary", "Edmonton",
        "Ottawa", "Winnipeg", "Quebec City", "Hamilton", "Kitchener",
        "London", "Victoria", "Halifax", "Oshawa", "Windsor",
        "Saskatoon", "Regina", "St. Catharines", "Barrie", "Kelowna",
        "Abbotsford", "Sherbrooke", "Saguenay", "Lévis", "Trois-Rivières",
        "Kingston", "Guelph", "Burnaby", "Delta", "Richmond",
        "Sudbury", "Moncton", "Red Deer", "Lethbridge", "Kamloops",
        "Nanaimo", "Brantford", "Saint John", "Thunder Bay", "Whitby",
        "Chatham", "Surrey", "Laval", "Longueuil", "Oakville",
        "Brampton", "Markham", "Vaughan", "Mississauga", "Richmond Hill",
    ],
    "RU": [
        "Moscow", "Saint Petersburg", "Novosibirsk", "Yekaterinburg", "Kazan",
        "Nizhny Novgorod", "Chelyabinsk", "Samara", "Ufa", "Rostov-on-Don",
        "Omsk", "Krasnoyarsk", "Voronezh", "Perm", "Volgograd",
        "Krasnodar", "Saratov", "Tyumen", "Tolyatti", "Izhevsk",
        "Barnaul", "Ulyanovsk", "Irkutsk", "Khabarovsk", "Yaroslavl",
        "Vladivostok", "Makhachkala", "Tomsk", "Orenburg", "Novokuznetsk",
        "Kemerovo", "Ryazan", "Astrakhan", "Naberezhnye Chelny", "Penza",
        "Lipetsk", "Kirov", "Tula", "Cheboksary", "Kaliningrad",
        "Balashikha", "Kursk", "Magnitogorsk", "Ulan-Ude", "Tver",
        "Stavropol", "Nizhny Tagil", "Bryansk", "Ivanovo", "Krasnoyarsk",
    ],
    "KR": [
        "Seoul", "Busan", "Incheon", "Daegu", "Daejeon",
        "Gwangju", "Suwon", "Ulsan", "Changwon", "Seongnam",
        "Goyang", "Yongin", "Bucheon", "Cheongju", "Ansan",
        "Anyang", "Namyangju", "Hwaseong", "Jeonju", "Pohang",
        "Uijeongbu", "Siheung", "Gimhae", "Cheonan", "Yangsan",
        "Jeju", "Asan", "Gwangmyeong", "Gimpo", "Hanam",
        "Pyeongtaek", "Gumi", "Iksan", "Wonju", "Andong",
        "Jinju", "Gunpo", "Mokpo", "Gangneung", "Suncheon",
        "Yeosu", "Geoje", "Chuncheon", "Gwangyang", "Tongyeong",
        "Gyeongju", "Jeongeup", "Gunsan", "Sokcho", "Donghae",
    ],
    "AU": [
        "Sydney", "Melbourne", "Brisbane", "Perth", "Adelaide",
        "Gold Coast", "Canberra", "Hobart", "Geelong", "Newcastle",
        "Wollongong", "Logan City", "Launceston", "Townsville", "Cairns",
        "Toowoomba", "Darwin", "Albury", "Ballarat", "Bendigo",
        "Mackay", "Rockhampton", "Bunbury", "Bundaberg", "Coffs Harbour",
        "Wagga Wagga", "Hervey Bay", "Shepparton", "Mildura", "Tamworth",
        "Gladstone", "Sunbury", "Traralgon", "Orange", "Dubbo",
        "Bowral", "Geraldton", "Busselton", "Nowra", "Bathurst",
        "Alice Springs", "Warrnambool", "Kalgoorlie", "Devonport", "Lismore",
        "Mandurah", "Caloundra", "Maroochydore", "Mount Gambier", "Whyalla",
    ],
    "ES": [
        "Madrid", "Barcelona", "Valencia", "Seville", "Zaragoza",
        "Málaga", "Murcia", "Palma", "Las Palmas", "Bilbao",
        "Alicante", "Córdoba", "Valladolid", "Vigo", "Gijón",
        "Hospitalet", "Vitoria-Gasteiz", "La Coruña", "Granada", "Elche",
        "Oviedo", "Badalona", "Cartagena", "Terrassa", "Jerez",
        "Sabadell", "Santander", "Pamplona", "Almería", "Fuenlabrada",
        "Leganés", "San Sebastián", "Burgos", "Castellón", "Alcalá de Henares",
        "Getafe", "Albacete", "Alcorcón", "Salamanca", "Logroño",
        "Huelva", "Badajoz", "Tarragona", "Lleida", "Marbella",
        "León", "Cádiz", "Dos Hermanas", "Tenerife", "Girona",
    ],
    "MX": [
        "Mexico City", "Guadalajara", "Monterrey", "Puebla", "Tijuana",
        "León", "Ciudad Juárez", "Torreón", "San Luis Potosí", "Mérida",
        "Mexicali", "Culiacán", "Aguascalientes", "Acapulco", "Hermosillo",
        "Saltillo", "Morelia", "Naucalpan", "Zapopan", "Chihuahua",
        "Centro", "Tlalnepantla", "Cancún", "Querétaro", "Chimalhuacán",
        "San Nicolás de los Garza", "Ecatepec", "Nezahualcóyotl", "Irapuato", "Veracruz",
        "Guadalupe", "Xalapa", "Oaxaca", "Durango", "Zacatecas",
        "Tepic", "Colima", "Campeche", "Ciudad Obregón", "Ensenada",
        "Matamoros", "Mazatlán", "Reynosa", "Cuernavaca", "Tuxtla Gutiérrez",
        "Toluca", "Villahermosa", "Pachuca", "Tlaxcala", "Chilpancingo",
    ],
    "ID": [
        "Jakarta", "Surabaya", "Bandung", "Bekasi", "Medan",
        "Tangerang", "Depok", "Semarang", "Palembang", "Makassar",
        "South Tangerang", "Batam", "Bogor", "Pekanbaru", "Bandar Lampung",
        "Padang", "Malang", "Samarinda", "Tasikmalaya", "Pontianak",
        "Banjarmasin", "Balikpapan", "Manado", "Mataram", "Serang",
        "Yogyakarta", "Jambi", "Kupang", "Denpasar", "Ambon",
        "Surakarta", "Cimahi", "Kediri", "Bengkulu", "Jayapura",
        "Palu", "Probolinggo", "Cilegon", "Bitung", "Kendari",
        "Madiun", "Tarakan", "Dumai", "Ternate", "Sorong",
        "Lhokseumawe", "Tegal", "Sukabumi", "Blitar", "Pasuruan",
    ],
    "NL": [
        "Amsterdam", "Rotterdam", "The Hague", "Utrecht", "Eindhoven",
        "Tilburg", "Groningen", "Almere", "Breda", "Nijmegen",
        "Enschede", "Apeldoorn", "Haarlem", "Arnhem", "Zaanstad",
        "Amersfoort", "Haarlemmermeer", "Dordrecht", "Zoetermeer", "Leiden",
        "Maastricht", "Westland", "Emmen", "Delft", "Venlo",
        "Alkmaar", "Deventer", "Midden-Groningen", "Helmond", "Ede",
        "Leeuwarden", "Zwolle", "Sittard-Geleen", "Lelystad", "Roosendaal",
        "Hengelo", "Oss", "Purmerend", "Gouda", "Almelo",
        "Nieuwegein", "Bergen op Zoom", "Hardenberg", "Middelburg", "Schiedam",
        "Spijkenisse", "Hoorn", "Vlaardingen", "Alphen aan den Rijn", "Zaandijk",
    ],
    "SA": [
        "Riyadh", "Jeddah", "Mecca", "Medina", "Dammam",
        "Khobar", "Tabuk", "Buraidah", "Khamis Mushait", "Abha",
        "Hofuf", "Jubail", "Taif", "Yanbu", "Al Kharj",
        "Hail", "Najran", "Dhahran", "Arar", "Sakaka",
        "Jizan", "Qatif", "Al Bahah", "Bisha", "Ar Rass",
        "Unayzah", "Rafha", "Turaif", "Al Ula", "Wadi ad-Dawasir",
        "Al Qunfudhah", "Dawadmi", "Zulfi", "Al Majmaah", "Sharurah",
        "Aflaj", "Muzahmiyya", "Al Khubar", "Muhayil", "Samtah",
        "Farasan", "Al Lith", "Rabigh", "Badr", "Khulais",
        "Turbah", "Al Wajh", "Duba", "Tayma", "Al Qurayat",
    ],
    "TR": [
        "Istanbul", "Ankara", "Izmir", "Bursa", "Antalya",
        "Adana", "Konya", "Gaziantep", "Şanlıurfa", "Kocaeli",
        "Mersin", "Diyarbakır", "Hatay", "Manisa", "Kayseri",
        "Samsun", "Balıkesir", "Tekirdağ", "Kahramanmaraş", "Van",
        "Denizli", "Sakarya", "Aydın", "Muğla", "Eskişehir",
        "Trabzon", "Mardin", "Erzurum", "Ordu", "Malatya",
        "Rize", "Elazığ", "Sivas", "Batman", "Afyonkarahisar",
        "Zonguldak", "Tokat", "Osmaniye", "Çorum", "Giresun",
        "Şırnak", "Aksaray", "Kütahya", "Kastamonu", "Uşak",
        "Bolu", "Burdur", "Isparta", "Nevşehir", "Niğde",
    ],
    "CH": [
        "Zurich", "Geneva", "Basel", "Bern", "Lausanne",
        "Winterthur", "Lucerne", "St. Gallen", "Lugano", "Biel/Bienne",
        "Thun", "Bellinzona", "Köniz", "La Chaux-de-Fonds", "Schaffhausen",
        "Fribourg", "Chur", "Vernier", "Neuchâtel", "Uster",
        "Sion", "Emmen", "Lancy", "Kriens", "Burgdorf",
        "Zug", "Riehen", "Aarau", "Dübendorf", "Davos",
        "Frauenfeld", "Dietikon", "Wettingen", "Frenkendorf", "Kreuzlingen",
        "Muttenz", "Rheinfelden", "Arlesheim", "Münsingen", "Bulle",
        "Lyss", "Grenchen", "Olten", "Solothurn", "Arbon",
        "Wil", "Rorschach", "Romanshorn", "Weinfelden", "Amriswil",
    ],
    "RS": [
        "Belgrade", "Novi Sad", "Niš", "Kragujevac", "Subotica",
        "Zrenjanin", "Pančevo", "Čačak", "Novi Pazar", "Kraljevo",
        "Smederevo", "Leskovac", "Valjevo", "Užice", "Vranje",
        "Šabac", "Zaječar", "Sombor", "Pirot", "Požarevac",
        "Bor", "Prokuplje", "Jagodina", "Kruševac", "Kikinda",
        "Ruma", "Sremska Mitrovica", "Vršac", "Loznica", "Aranđelovac",
        "Sokobanja", "Bačka Palanka", "Inđija", "Stara Pazova", "Ćuprija",
        "Paraćin", "Mladenovac", "Obrenovac", "Lazarevac", "Ivanjica",
        "Priboj", "Prijepolje", "Trstenik", "Aleksandrovac", "Vrnjačka Banja",
        "Knjaževac", "Negotin", "Majdanpek", "Kladovo", "Bela Palanka",
    ],
}


class LocationInfo(BaseModel):
    country: Country
    city: str

    @model_validator(mode="after")
    def city_must_be_valid(self) -> "LocationInfo":
        valid_cities = CITIES_BY_COUNTRY.get(self.country.value, [])
        if self.city not in valid_cities:
            raise ValueError(
                f"'{self.city}' nije validan grad za {self.country.value}. "
                f"Dostupni gradovi: {valid_cities}"
            )
        return self


# ─────────────────────────────────────────
# 💰 FINANCIAL
# ─────────────────────────────────────────

class Currency(str, Enum):
    EUR = "EUR"
    USD = "USD"


class FinancialInfo(BaseModel):
    income:   int = Field(..., gt=0, description="Mesečni prihod")
    expenses: int = Field(..., ge=0, description="Mesečni troškovi")
    debt:     int = Field(..., ge=0, description="Ukupan dug")
    savings:  int = Field(..., ge=0, description="Ukupna štednja")
    currency: Currency

    @model_validator(mode="after")
    def expenses_lt_income(self) -> "FinancialInfo":
        if self.expenses >= self.income:
            raise ValueError("Troškovi ne mogu biti veći ili jednaki prihodima.")
        return self


# ─────────────────────────────────────────
# 💼 PROFESSIONAL
# ─────────────────────────────────────────

from enum import Enum


class Sector(str, Enum):
    TECHNOLOGY            = "Technology"
    FINANCE               = "Finance"
    HEALTHCARE            = "Healthcare"
    EDUCATION             = "Education"
    LAW_ADMIN             = "Law & Administration"
    CONSTRUCTION_INDUSTRY = "Construction & Industry"
    TRADE_SERVICES        = "Trade & Services"
    ARTS_ENTERTAINMENT    = "Arts & Entertainment"
    AGRICULTURE           = "Agriculture"
    TRANSPORTATION        = "Transportation"
    ENERGY                = "Energy"
    REAL_ESTATE           = "Real Estate"
    MEDIA_COMMUNICATIONS  = "Media & Communications"
    SCIENCE_RESEARCH      = "Science & Research"
    OTHER                 = "Other"


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

    # ARTS & ENTERTAINMENT
    GRAPHIC_DESIGNER = "Graphic Designer"
    UX_UI_DESIGNER = "UX/UI Designer"
    PHOTOGRAPHER = "Photographer"
    VIDEO_EDITOR = "Video Editor"
    ANIMATOR = "Animator"
    MUSICIAN = "Musician"
    ACTOR = "Actor"
    FILM_DIRECTOR = "Film Director"

    # AGRICULTURE
    FARMER = "Farmer"
    AGRONOMIST = "Agronomist"
    VETERINARIAN = "Veterinarian"
    AGRICULTURAL_TECHNICIAN = "Agricultural Technician"
    GREENHOUSE_WORKER = "Greenhouse Worker"

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

    # SCIENCE
    RESEARCH_SCIENTIST = "Research Scientist"
    BIOLOGIST = "Biologist"
    CHEMIST = "Chemist"
    PHYSICIST = "Physicist"
    DATA_ANALYST = "Data Analyst"

    # OTHER
    ELECTRICIAN = "Electrician"
    PLUMBER = "Plumber"
    CHEF = "Chef"
    FITNESS_TRAINER = "Fitness Trainer"
    HAIRDRESSER = "Hairdresser"

    # EXTRA (do 150)
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


class EmploymentStatus(str, Enum):
    FULL_TIME     = "full-time"
    PART_TIME     = "part-time"
    FREELANCER    = "freelancer"
    SELF_EMPLOYED = "self-employed"
    UNEMPLOYED    = "unemployed"
    STUDENT       = "student"
    RETIRED       = "retired"

class ProfessionalInfo(BaseModel):
    sector: Sector
    profession: Profession
    employment_status: EmploymentStatus



# ─────────────────────────────────────────
# ⚙️ PREFERENCES
# ─────────────────────────────────────────

class RiskProfile(str, Enum):
    LOW    = "low"     # → safety
    MEDIUM = "medium"  # → growth
    HIGH   = "high"    # → profit

    @property
    def goal(self) -> str:
        return {
            RiskProfile.LOW:    "safety",
            RiskProfile.MEDIUM: "growth",
            RiskProfile.HIGH:   "profit",
        }[self]

#
# class RiskLevel(str, Enum):
#     LOW = "low"
#     MEDIUM = "medium"
#     HIGH = "high"
#
#
# class InvestmentGoal(str, Enum):
#     SAFETY = "safety"
#     GROWTH = "growth"
#     PROFIT = "profit"
#

class HorizonGroup(str, Enum):
    SHORT     = "1-3"
    MEDIUM    = "3-5"
    LONG      = "5-8"
    VERY_LONG = "8+"


class Preferences(BaseModel):
    risk_profile: RiskProfile
    horizon:      HorizonGroup



# ─────────────────────────────────────────
# 👤 PERSONAL
# ─────────────────────────────────────────

class PersonalInfo(BaseModel):
    age: int = Field(..., gt=0, lt=120)


# ─────────────────────────────────────────
# 🔥 FINAL USER INPUT
# ─────────────────────────────────────────

class UserInput(BaseModel):
    personal:     PersonalInfo
    location:     LocationInfo
    financial:    FinancialInfo
    professional: ProfessionalInfo
    preferences:  Preferences


# ─────────────────────────────────────────
# 🧪 PRIMER VALIDNOG UNOSA
# ─────────────────────────────────────────
#
# EXAMPLE = UserInput(
#     personal=PersonalInfo(age=32),
#     location=LocationInfo(country=Country.SERBIA, city="Belgrade"),
#     financial=FinancialInfo(
#         income=2500,
#         expenses=1800,
#         debt=5000,
#         savings=12000,
#         currency=Currency.EUR,
#     ),
#     professional=ProfessionalInfo(
#         sector=Sector.TECHNOLOGY,
#         onet_code="15-1252.00",
#         profession_title="Software Developers",
#         skills=["Python", "FastAPI", "PostgreSQL"],
#         employment_status=EmploymentStatus.FULL_TIME,
#         years_at_job=4,
#     ),
#     preferences=Preferences(
#         risk_profile=RiskProfile.MEDIUM,
#         horizon=HorizonGroup.MEDIUM,
#     ),
# )