from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.exceptions import NotFoundError
from app.models.portfolio import Portfolio


class TenantAccess:
    def __init__(self, session: Session, tenant_id: str) -> None:
        self.session = session
        self.tenant_id = tenant_id

    def require_portfolio(self, portfolio_id: int) -> Portfolio:
        portfolio = self.session.scalar(
            select(Portfolio).where(
                Portfolio.id == portfolio_id,
                Portfolio.tenant_id == self.tenant_id,
            )
        )
        if portfolio is None:
            raise NotFoundError("Portfolio not found.")
        return portfolio
