# app/core/country_config.py

# 🔹 COUNTRY RISK FACTOR
# smaller number = more stable economy,
# higher number = higher risk

COUNTRY_RISK = {
    "US": 0.9,
    "DE": 0.8,
    "JP": 0.75,
    "IN": 1.3,
    "GB": 0.85,
    "FR": 0.85,
    "IT": 0.95,
    "BR": 1.4,
    "CA": 0.85,
    "RU": 1.5,
    "KR": 0.9,
    "AU": 0.85,
    "ES": 0.95,
    "MX": 1.3,
    "ID": 1.35,
    "NL": 0.8,
    "SA": 1.1,
    "TR": 1.4,
    "CH": 0.7,
    "RS": 1.2
}


# 🔹 INTEREST RATE RANGE (min, max)
# will be used in interest_engine

COUNTRY_INTEREST = {
    "US": (0.04, 0.08),
    "DE": (0.03, 0.06),
    "JP": (0.02, 0.05),
    "IN": (0.07, 0.14),
    "GB": (0.04, 0.09),
    "FR": (0.035, 0.07),
    "IT": (0.05, 0.09),
    "BR": (0.08, 0.16),
    "CA": (0.04, 0.08),
    "RU": (0.09, 0.18),
    "KR": (0.04, 0.08),
    "AU": (0.04, 0.08),
    "ES": (0.045, 0.09),
    "MX": (0.08, 0.15),
    "ID": (0.09, 0.16),
    "NL": (0.03, 0.06),
    "SA": (0.05, 0.1),
    "TR": (0.1, 0.2),
    "CH": (0.02, 0.05),
    "RS": (0.06, 0.12)
}


# 🔹 MAX LOAN YEARS
COUNTRY_LOAN_YEARS = {
    "US": 7,
    "DE": 7,
    "JP": 7,
    "IN": 5,
    "GB": 7,
    "FR": 7,
    "IT": 6,
    "BR": 5,
    "CA": 7,
    "RU": 5,
    "KR": 6,
    "AU": 7,
    "ES": 6,
    "MX": 5,
    "ID": 5,
    "NL": 7,
    "SA": 6,
    "TR": 5,
    "CH": 7,
    "RS": 5
}