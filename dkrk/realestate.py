"""
Module handling calculations related to Danish Real Estate Loans
"""
from dkrk.annuity import Annuity
import pandas as pd
import numpy as np
from numpy.polynomial.polynomial import polyroots


class TKLoan:
    """
    A loan from Total Kredit, which has quarterly amortization.
    """

    def __init__(
        self,
        price: float,
        face_value: float,
        interest: float,
        bidrag: float,
        maturity: int = 30,
        n_terms: int = 4,
    ):
        """
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
        self.price = price
        self.face_value = face_value
        self.interest = interest
        self.bidrag = bidrag
        self.maturity = maturity
        self.n_terms = n_terms

        # Adjust loan amount by bond price
        self.loan_amount = self.face_value / (self.price / 100)
        self.annuity_obj = Annuity(
            self.loan_amount, self.interest, self.maturity, self.n_terms
        )
        self.table = self._add_bidrag(self.annuity_obj.table, self.bidrag, self.n_terms)

        # Cash flow
        self.cash_flow = [-self.face_value] + self.table["Annuity"].values.tolist()

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
