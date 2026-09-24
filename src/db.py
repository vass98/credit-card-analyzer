from sqlalchemy import Column, Date, Float, Integer, String, UniqueConstraint, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from config import DB_PATH

Base = declarative_base()


class Transaction(Base):
    __tablename__ = "transactions"

    id = Column(Integer, primary_key=True)
    bank = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    merchant = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # debit | credit
    category = Column(String, nullable=False)

    __table_args__ = (
        UniqueConstraint("bank", "date", "merchant", "amount", name="uix_transaction"),
    )


class Statement(Base):
    """One row per statement PDF -- the bank's own printed totals, not
    derived from summing transaction line items (which can't reproduce
    previous-balance carryover or multi-card consolidation)."""

    __tablename__ = "statements"

    id = Column(Integer, primary_key=True)
    bank = Column(String, nullable=False)
    period_start = Column(Date, nullable=False)
    period_end = Column(Date, nullable=False)
    due_date = Column(Date, nullable=False)
    total_due = Column(Float, nullable=False)
    min_due = Column(Float, nullable=False)

    __table_args__ = (
        UniqueConstraint("bank", "period_end", name="uix_statement"),
    )


class AccountTransaction(Base):
    """Savings/current account transactions -- kept separate from the credit
    card `transactions` table since it's a different kind of account
    (balance-bearing, salary/transfers rather than card spend)."""

    __tablename__ = "account_transactions"

    id = Column(Integer, primary_key=True)
    bank = Column(String, nullable=False)
    date = Column(Date, nullable=False)
    narration = Column(String, nullable=False)
    amount = Column(Float, nullable=False)
    type = Column(String, nullable=False)  # debit | credit
    category = Column(String, nullable=False)
    balance = Column(Float, nullable=True)

    __table_args__ = (
        UniqueConstraint("bank", "date", "narration", "amount", name="uix_account_transaction"),
    )


engine = create_engine(f"sqlite:///{DB_PATH}")
SessionLocal = sessionmaker(bind=engine)


def init_db():
    Base.metadata.create_all(engine)
