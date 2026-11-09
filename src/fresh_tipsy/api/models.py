"""Pydantic request and response models for the HTTP API."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from fresh_tipsy.api.service import ServiceIssue, ServiceResponse
from fresh_tipsy.curves import CurveQuery


class _RequestModel(BaseModel):
    """Base request model with unknown-field protection."""

    model_config = ConfigDict(extra="forbid")


class CurveQueryRequest(_RequestModel):
    """Growth query request."""

    species_code: str = Field(min_length=1)
    site_index: float
    age: float
    pnc: str | None = None
    stock_height_m: float | None = None
    source_version: str | None = None
    scenario: str | None = None
    initial_density: int | None = None
    pct_density: int | None = None
    ct_density: int | None = None
    format: Literal["tab", "taf"] = "tab"

    def to_query(self) -> CurveQuery:
        """Convert to the core query model.

        Returns
        -------
        CurveQuery
            Typed growth query.
        """
        return CurveQuery(
            species_code=self.species_code,
            site_index=self.site_index,
            age=self.age,
            pnc=self.pnc,
            stock_height_m=self.stock_height_m,
            source_version=self.source_version,
            scenario=self.scenario,
            initial_density=self.initial_density,
            pct_density=self.pct_density,
            ct_density=self.ct_density,
            format=self.format,
        )


class ScenarioQueryRequest(_RequestModel):
    """Query inside an economics scenario."""

    species_code: str = Field(min_length=1)
    site_index: float
    age: float
    pnc: str | None = None
    stock_height_m: float | None = None
    source_version: str | None = None
    scenario: str | None = None
    initial_density: int | None = None
    pct_density: int | None = None
    ct_density: int | None = None
    format: Literal["tab", "taf"] = "taf"

    def as_dict(self) -> dict[str, object]:
        """Return a parser-compatible mapping.

        Returns
        -------
        dict of str to object
            Query fields.
        """
        return self.model_dump()


class PriceRequest(_RequestModel):
    """Explicit price entry."""

    species_code: str | None = None
    group: str
    period: str | None = None
    grade: str | None = None
    dimension: str | None = None
    detail: str | None = None
    price_per_unit: float = Field(ge=0)
    unit: str = Field(min_length=1)
    source: str = "scenario"
    citation: str = "Scenario input."


class CostRequest(_RequestModel):
    """Explicit cost entry."""

    category: str
    age: float = Field(ge=0)
    amount_per_ha: float = Field(ge=0)
    label: str = Field(min_length=1)
    source: str = "scenario"
    citation: str = "Scenario input."


class AssumptionsRequest(_RequestModel):
    """Discount assumptions request."""

    discount_rate: float = Field(ge=0)
    real_price_increase: float = 0.0
    real_cost_increase: float = 0.0
    real_increase_duration: float = Field(default=25.0, ge=0)
    base_age: float = Field(default=0.0, ge=0)
    include_sunk_costs: bool = False


class EconomicsScenarioRequest(_RequestModel):
    """Economics scenario request."""

    query: ScenarioQueryRequest
    period: str = "default"
    revenue_groups: list[str] = Field(min_length=1)
    prices: list[PriceRequest] = Field(default_factory=list)
    costs: list[CostRequest] = Field(default_factory=list)
    assumptions: AssumptionsRequest

    def as_dict(self) -> dict[str, object]:
        """Return a parser-compatible mapping.

        Returns
        -------
        dict of str to object
            Scenario fields.
        """
        return self.model_dump()


class ServiceIssueModel(BaseModel):
    """Structured issue in an API response."""

    code: str
    message: str


class ServiceEnvelopeModel(BaseModel):
    """Shared API response envelope."""

    status: Literal["ok", "error"]
    request: dict[str, object]
    result: dict[str, object] | None
    provenance: dict[str, object] | None
    evidence: str | None
    warnings: list[ServiceIssueModel]
    error: ServiceIssueModel | None

    @classmethod
    def from_response(cls, response: ServiceResponse) -> ServiceEnvelopeModel:
        """Convert a service response.

        Parameters
        ----------
        response : ServiceResponse
            Service envelope.

        Returns
        -------
        ServiceEnvelopeModel
            Pydantic envelope.
        """
        payload = response.as_dict()
        return cls.model_validate(payload)


class ServiceErrorEnvelope(BaseModel):
    """Error response returned by API handlers."""

    status: Literal["error"] = "error"
    request: dict[str, object]
    result: None = None
    provenance: None = None
    evidence: None = None
    warnings: list[ServiceIssueModel] = Field(default_factory=list)
    error: ServiceIssueModel

    @classmethod
    def from_issue(cls, request: dict[str, object], issue: ServiceIssue) -> ServiceErrorEnvelope:
        """Build an error envelope.

        Parameters
        ----------
        request : dict of str to object
            Original request.
        issue : ServiceIssue
            Structured issue.

        Returns
        -------
        ServiceErrorEnvelope
            Error envelope.
        """
        return cls(
            request=request,
            error=ServiceIssueModel(code=issue.code, message=issue.message),
        )
