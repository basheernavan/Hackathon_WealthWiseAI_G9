"""Shared data contract between ingestion, analysis and the dashboard.

Change this file only through a PR that all three developers have seen: every
stream builds against it independently. Money is EUR as float, rounded to 2 dp
on output (ADR-0004).
"""

from datetime import date
from enum import StrEnum
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class DocumentType(StrEnum):
    BANK_STATEMENT = "bank_statement"
    PAYSLIP = "payslip"
    LOAN_STATEMENT = "loan_statement"


class Category(StrEnum):
    INCOME = "income"
    HOUSING = "housing"
    GROCERIES = "groceries"
    TAKEAWAY = "takeaway"
    TRANSPORT = "transport"
    UTILITIES = "utilities"
    SUBSCRIPTIONS = "subscriptions"
    SHOPPING = "shopping"
    ENTERTAINMENT = "entertainment"
    DEBT_REPAYMENT = "debt_repayment"
    OTHER = "other"


DISCRETIONARY_CATEGORIES = frozenset(
    {Category.TAKEAWAY, Category.SHOPPING, Category.ENTERTAINMENT, Category.SUBSCRIPTIONS}
)


# ---------- Ingestion input ----------


class UploadedDocument(BaseModel):
    filename: str
    content: bytes


# ---------- Ingestion output: FinancialProfile ----------


class Transaction(BaseModel):
    date: date
    description: str
    amount: float = Field(description="EUR. Negative = money out, positive = money in.")
    balance: float | None = Field(default=None, description="Account balance after this transaction.")
    category: Category | None = Field(default=None, description="None from ingestion; set by analysis.")


class Payslip(BaseModel):
    employee: str
    employer: str
    pay_date: date
    gross_pay: float
    deductions: dict[str, float] = Field(description="Label as printed on the payslip -> amount (positive).")
    net_pay: float

    @model_validator(mode="after")
    def _net_matches_gross_minus_deductions(self) -> "Payslip":
        if abs(self.gross_pay - sum(self.deductions.values()) - self.net_pay) > 0.01:
            raise ValueError("net_pay must equal gross_pay minus deductions")
        return self


class DebtKind(StrEnum):
    LOAN = "loan"
    CREDIT_CARD = "credit_card"


class Debt(BaseModel):
    name: str = Field(description='Lender + product, e.g. "Northwind Bank Car Loan".')
    kind: DebtKind
    balance: float = Field(ge=0)
    annual_interest_rate: float = Field(ge=0, description="APR in percent: 8.9 means 8.9%.")
    monthly_payment: float = Field(ge=0, description="Scheduled or minimum monthly payment.")
    remaining_term_months: int | None = None


class SourceDocument(BaseModel):
    filename: str
    document_type: DocumentType
    warnings: list[str] = Field(default_factory=list, description="Shown to the user, e.g. skipped rows.")


class FinancialProfile(BaseModel):
    transactions: list[Transaction] = Field(default_factory=list)
    payslips: list[Payslip] = Field(default_factory=list)
    debts: list[Debt] = Field(default_factory=list)
    sources: list[SourceDocument] = Field(default_factory=list)


# ---------- Analysis output: Report ----------


class Metrics(BaseModel):
    months_covered: int
    monthly_income: float
    monthly_spending: float = Field(description="Positive number; includes debt repayments.")
    monthly_surplus: float
    spending_by_category: dict[Category, float] = Field(description="Monthly average, positive numbers.")
    savings_rate: float = Field(description="Fraction: 0.05 means 5%.")
    debt_to_income: float = Field(description="Fraction: monthly debt payments / monthly income.")
    total_debt: float
    current_balance: float
    emergency_fund_months: float
    discretionary_share: float = Field(description="Fraction of monthly_spending.")


class Subscription(BaseModel):
    name: str
    monthly_amount: float
    months_seen: int


class ScoreComponent(BaseModel):
    name: Literal["savings_rate", "debt_to_income", "emergency_fund", "discretionary_share"]
    value: float
    points: float
    max_points: int


class HealthScore(BaseModel):
    score: int = Field(ge=0, le=100)
    band: Literal["good", "fair", "needs attention"]
    components: list[ScoreComponent]


class AgentName(StrEnum):
    SPENDING = "spending"
    DEBT = "debt"
    SAVINGS = "savings"


class Recommendation(BaseModel):
    agent: AgentName
    title: str
    detail: str
    monthly_impact: float | None = Field(default=None, description="EUR/month freed or redirected.")
    evidence: list[Transaction] = Field(default_factory=list)


class DebtPayoffPlan(BaseModel):
    strategy: Literal["avalanche"] = "avalanche"
    payoff_order: list[str]
    extra_monthly_payment: float
    months_to_debt_free_current: int
    months_to_debt_free_with_extra: int
    months_saved: int
    interest_saved: float


class SavingsPlan(BaseModel):
    monthly_amount: float
    target_amount: float
    months_to_target: int | None = Field(description="None when monthly_amount is 0.")


class Report(BaseModel):
    metrics: Metrics
    health_score: HealthScore
    subscriptions: list[Subscription]
    identified_cuts: float = Field(description="EUR/month the spending agent found to free up.")
    debt_plan: DebtPayoffPlan | None
    savings_plan: SavingsPlan
    recommendations: list[Recommendation]
    llm_used: bool = Field(description="False when explanations fell back to templates.")
