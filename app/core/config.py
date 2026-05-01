# app/core/config.py

class Settings:
    # loan config
    LOAN_YEARS = 5
    BASE_INTEREST = 0.06
    MAX_DTI = 0.3  # debt-to-income ratio

    # investment config
    INFLATION = 0.03
    LOAN_MARGIN = 0.03

    # system config
    BASE_CURRENCY = "EUR"

    # scoring weights
    ROI_WEIGHT = 0.5
    STABILITY_WEIGHT = 0.3
    RISK_WEIGHT = 0.2


# singleton instance
settings = Settings()