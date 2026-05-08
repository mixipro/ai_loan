# app/models/simulation.py

from pydantic import BaseModel, Field, model_validator
from app.models.user import UserInput


class SimulationChoice(BaseModel):
    """
    Korisnikov izbor parametara za simulaciju.
    Granice se validiraju u orchestrator-u (jer zavise od user-a).
    """
    loan_amount: float = Field(
        ...,
        ge=0,
        description="Koliko korisnik želi da uzme kredita (0 = bez kredita)"
    )
    loan_years: int = Field(
        ...,
        ge=1,
        le=15,
        description="Broj godina za otplatu kredita"
    )
    savings_to_invest: float = Field(
        ...,
        ge=0,
        description="Koliko od svojih ušteđevina korisnik želi da uloži"
    )


class SimulationRequest(BaseModel):
    """
    Kombinovan request za /simulate endpoint:
    - user: ceo originalni profil (kao u /analyze)
    - simulation: korisnikovi custom parametri
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