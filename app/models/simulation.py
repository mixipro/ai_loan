# app/models/simulation.py

from pydantic import BaseModel, Field, model_validator
from app.models.user import UserInput


class SimulationChoice(BaseModel):
    """
    User selection of simulation parameters.
    Boundaries are validated in the orchestrator (because they depend on the user).
    """
    loan_amount: float = Field(
        ...,
        ge=0,
        description="How much credit the user wants to take (0 = no credit)"
    )
    loan_years: int = Field(
        ...,
        ge=1,
        le=15,
        description="Number of years for loan repayment"
    )
    savings_to_invest: float = Field(
        ...,
        ge=0,
        description="How much of their savings the user wants to invest"
    )


class SimulationRequest(BaseModel):
    """
    Combined request for /simulate endpoint:
    - user: entire original profile (as in /analyze)
    - simulation: user's custom parameters
    """
    user: UserInput
    simulation: SimulationChoice

    @model_validator(mode="after")
    def savings_within_total(self) -> "SimulationRequest":
        if self.simulation.savings_to_invest > self.user.financial.savings:
            raise ValueError(
                f"savings_to_invest ({self.simulation.savings_to_invest}) ne može biti veći "
                f"od total savings ({self.user.financial.savings})"
            )
        return self