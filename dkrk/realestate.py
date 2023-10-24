"""
Module handling calculations related to Danish Real Estate Loans
"""
from abc import ABC, abstractmethod
from enum import Enum
from dkrk.annuity import Annuity
import pandas as pd
import numpy as np
from numpy.polynomial.polynomial import polyroots
import plotly.express as px
from datetime import datetime
from dateutil.relativedelta import relativedelta


class Term(ABC):
    def __init__(self, start: datetime, end: datetime):
        self.start = start
        self.end = end

    @abstractmethod
    def next_term(self, **kwargs):
        raise NotImplementedError()


class Month(Term):
    def next_term(self):
        return Month(
            self.start + relativedelta(months=1), self.end + relativedelta(months=1)
        )


class Quarter(Term):
    def next_term(self):
        return Month(
            self.start + relativedelta(months=3), self.end + relativedelta(months=3)
        )

class TKDueDate(Enum):
    march = (3, 31)
    june = (6, 30)
    september = (9, 30)
    december = (12, 31)



class Maturity:

    def __init__(self, time_to_maturity: relativedelta, date: datetime):
        """Class containing information about current date and time to maturity.
        Current date doesnt have to be the day the bond is issued.

        Parameters
        ----------
        time_to_maturity : relativedelta
            The time until the final payment is made on the loan/bond (maturity)
        date : datetime
            The current date
        """
        self.time_to_maturity = time_to_maturity
        self.date = date

    @staticmethod
    def next_due_date(date: datetime) -> datetime:
        cur_year = date.year
        for due_month in TKDueMonth:
            loop_due = datetime(cur_year, due_month.value[0], due_month.value[1])
            if date < loop_due:
                break
        
        return loop_due 

    def due_dates(self) -> List[datetime]:
        res = []
        cur_date = self.date.copy()
        end_date = self.date + self.time_to_maturity
        while cur_date <= end_date:
            tmp_due = Maturity.next_due_date(cur_date)
            if tmp_due <= end_date:
                res.append(
                    tmp_due
                )
            else:
                break
        
        return res

class TKLoan:
    """
    A loan from Total Kredit, which has quarterly amortization.
    """

    def __init__(
        self,
        face_value: float,
        interest: float,
        bidrag: float,
        maturity: int = 30,
        n_terms: int = 4,
    ):
        """
        Parameters
        ----------
        face_value : float
            The size of the loan
        interest : float
            The interest rate of the loan, as a decimal. E.g. 5% would be 0.05
        bidrag : float
            Bidrag is interest paid to the bank. Should be annual interest.
            #TODO: Find english word for bidrag
        maturity : int
            The time to maturity. E.g. 30 for 30 years
        n_terms : int
            The number of payments made for each term. E.g. if the loan is for 30 years
            and payments are made each quarter, then n_paymens should 4. NB: It is not
            the total number of payments made during the lifetime of the annuity!

        """
        self.face_value = face_value
        self.interest = interest
        self.bidrag = bidrag
        self.maturity = maturity
        self.n_terms = n_terms

        # Calc annuity
        self.annuity_obj = Annuity(
            self.face_value, self.interest, self.maturity, self.n_terms
        )
        self.table = self._add_bidrag(self.annuity_obj.table, self.bidrag, self.n_terms)

        # Cash flow
        self.cash_flow = [-self.face_value] + self.table["Annuity"].values.tolist()
    
    @classmethod
    def from_price(cls,
        price: float,
        face_value: float,
        interest: float,
        bidrag: float,
        maturity: int = 30,
        n_terms: int = 4,
    ):
        """
        Create a new loan with a desired size. E.g. you want to borrow 1000000
        and the bond is priced at 95. Thus you need a bond with face value
        1000000/0.95 = 1052631

        Parameters
        ----------
        price : float
            The price of the bond in the market in hundreds e.g. 99.4
        face_value : float
            The amount of money you want to borrow
        interest : float
            The interest rate of the loan, as a decimal. E.g. 5% would be 0.05
        bidrag : float
            Bidrag is interest paid to the bank. Should be annual interest.
            #TODO: Find english word for bidrag
        maturity : int
            The time to maturity. E.g. 30 for 30 years
        n_terms : int
            The number of payments made for each term. E.g. if the loan is for 30 years
            and payments are made each quarter, then n_paymens should 4. NB: It is not
            the total number of payments made during the lifetime of the annuity!

        """


        # Adjust loan amount by bond price
        loan_amount = face_value / (price / 100)

        return cls(
            loan_amount,
            interest,
            bidrag,
            maturity,
            n_terms
        )

    @staticmethod
    def _add_bidrag(table: pd.DataFrame, bidrag: float, n_terms: int) -> pd.DataFrame:
        """
        Adjust an amortization table by adding bidrag.

        Parameters
        ----------
        table : pd.DataFrame
            Table from dkrk.annuity.Annuity showing amortization
        bidrag : float
            Bidrag is interest paid to the bank. Should be annual interest.
        n_terms : int
            The number of payments made for each term. E.g. if the loan is for 30 years
            and payments are made each quarter, then n_paymens should 4. NB: It is not
            the total number of payments made during the lifetime of the annuity!

        Returns
        -------
        pd.DataFrame
            Adjusted amortization table with bidrag added
        """
        table["Bidrag"] = (table["Repayment"] + table["Debt"]) * bidrag / n_terms
        table["Annuity"] = table["Annuity"] + table["Bidrag"]
        return table

    @property
    def yield_to_maturity(self):
        """
        Calculate the yield to maturity
        """
        return TKLoan.irr_cashflow(self.cash_flow)

    @staticmethod
    def irr_cashflow(flow):
        roots = polyroots(flow)
        real_roots = np.real(roots[np.isreal(roots)])
        positive_roots = real_roots[real_roots > 0]
        assert len(positive_roots) == 1

        rate = 1 / positive_roots[0] - 1

        return rate

    @property
    def total_cost(self) -> float:
        """
        The total cost of the loan, which is the sum of all annuities
        """
        return self.table["Annuity"].sum()

    @property
    def total_interest(self) -> float:
        """
        The total interest paid on the loan during the whole lifetime
        """
        return self.table["Interest"].sum() + self.table["Bidrag"].sum()

    def table_after_tax(self, tax_rate: float) -> pd.DataFrame:
        """
        Add a tax rebate to the interest payments.

        Parameters
        ----------
        tax_rate : float
            The tax rate rebate for interest payments in decimal.
        """
        after_tax = self.table.copy()
        after_tax["Interest"] = after_tax["Interest"] * (1 - tax_rate)
        after_tax["Bidrag"] = after_tax["Bidrag"] * (1 - tax_rate)
        after_tax["Annuity"] = (
            after_tax["Repayment"] + after_tax["Interest"] + after_tax["Bidrag"]
        )
        return after_tax


class LoanPlotter:
    def __init__(self, *args: TKLoan):
        assert len(args) > 0, "No loans supplied!"
        self.loans = args

    def _concat_tables(self) -> pd.DataFrame:
        concat_list = []
        for loan in self.loans:
            cur_df = loan.table.copy()
            cur_df[
                "Loan"
            ] = f"{loan.interest*100:.2f}% {loan.maturity}Y {loan.bidrag*100:.2f}%"
            concat_list.append(cur_df)
        return pd.concat(concat_list)

    def plot(self, attribute: str):
        fig = px.line(
            self._concat_tables(), x="Time", y=attribute, color="Loan", title=attribute
        )
        fig.show()

    def plot_debt(self):
        self.plot("Debt")

    def plot_interest(self):
        self.plot("Interest")

    def plot_bidrag(self):
        self.plot("Bidrag")

    def plot_annuity(self):
        self.plot("Annuity")

    def plot_repayment(self):
        self.plot("Repayment")
