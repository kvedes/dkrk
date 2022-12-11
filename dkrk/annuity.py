"""Module to perform annuity calculations"""

import pandas as pd
import numpy as np
import plotly.graph_objects as go

pd.set_option("display.max_rows", 1000)
pd.set_option("display.float_format", lambda x: "%.3f" % x)


class Annuity:
    """Class to handle calculation of annuities. It uses the annuity formula
    p*r*(1/(1-(1+r)**(-n)))
    where p is the loan principal, r is the interest rate as a decimal e.g. 5% is 0.05, and n
    is the time to maturity.

    Nomenclature:
    Principal: The total amount money loaned
    Annuity: Denotes the total amount of money paid each month including repayment
        of a part of the principal and interest
    Repayment: The part of the principal which is paid back each term
    Maturity: The time until the loan is fully paid back, given in some time unit
    Term: The period of time between payments. There can be multiple
        terms in period of time. E.g. a loan might have a maturity of 30 years
        but payments are made each quarter.
    """

    def __init__(
        self, principal: float, interest: float, maturity: int, n_payments: int
    ):
        """
        Parameters
        ----------
        principal : float
            The principal of the loan
        interest : float
            The interest rate of the loan, as a decimal. E.g. 5% would be 0.05
        maturity : int
            The time to maturity. E.g. 30 for 30 years
        n_payments : int
            The number of payments made for each term. E.g. if the loan is for 30 years
            and payments are made each quarter, then n_paymens should 4. NB: It is not
            the total number of payments made during the lifetime of the annuity!
        """
        self.principal = principal
        self.interest = interest
        self.maturity = maturity
        self.n_payments = n_payments
        self.table = Annuity.calc_annuity_table(
            self.principal, self.interest, self.maturity, self.n_payments
        )

    @staticmethod
    def repayment(principal: float, interest: float, maturity: int, term: int):
        """
        The size of the repayment for a given term (the annuity minus interest)

        Parameters
        ----------
        principal : float
            The principal of the loan
        interest : float
            The interest rate of the loan, as a decimal. E.g. 5% would be 0.05
        maturity : int
            The time to maturity. E.g. 30 for 30 years
        term : int
            The term under for which the repayment should be calculated. E.g.
            to determine how much is paid in year 3, term should be set to 3.
            NB: The first term of repayment is term=1, thus dont use term=0.
        """
        assert term > 0, "Cannot set term < 1"
        a1 = principal * interest / ((1 + interest) ** maturity - 1)
        return a1 * (1 + interest) ** (t - 1)

    @staticmethod
    def calc_annuity_table(
        principal: float, interest: float, maturity: int, n_payments: int
    ) -> pd.DataFrame:
        """
        Create an annuity table showing amortization, repayment and interest
        for each time period.

        Parameters
        ----------
        principal : float
            The principal of the loan
        interest : float
            The interest rate of the loan, as a decimal. E.g. 5% would be 0.05
        maturity : int
            The time to maturity. E.g. 30 for 30 years
        n_payments : int
            The number of payments made for each term. E.g. if the loan is for 30 years
            and payments are made each quarter, then n_paymens should 4. NB: It is not
            the total number of payments made during the lifetime of the annuity!

        Returns
        -------
        pd.DataFrame
            Table showing annuities and amortization
        """
        df = pd.DataFrame(
            np.zeros((maturity * n_payments, 4)),
            columns=["Time", "Annuity", "Repayment", "Interest"],
        )
        df["Time"] = np.arange(1, (maturity * n_payments) + 1)

        df["Annuity"] = Annuity.calc_annuity(
            principal, interest / n_payments, maturity * n_payments
        )

        df["Repayment"] = np.array(
            [
                Annuity.repayment(
                    principal, interest / n_payments, maturity * n_payments, term
                )
                for term in range(1, (maturity * n_payments) + 1)
            ]
        )
        df["Debt"] = principal - df["Repayment"].cumsum()
        df["Interest"] = df["Annuity"] - df["Repayment"]

        return df

    @property
    def annuity(self) -> float:
        """
        Annuity which should be repaid each term.
        """
        return self.annuity(
            self.principal,
            self.interest / self.n_payments,
            self.maturity * self.n_payments,
        )

    @staticmethod
    def calc_annuity(principal: float, interest: float, maturity: int) -> float:
        """
        Calculate the annuity which should be repaid each term.

        Parameters
        ----------
        principal : float
            The principal of the loan
        interest : float
            The interest rate of the loan, as a decimal. E.g. 5% would be 0.05
        maturity : int
            The time to maturity. E.g. 30 for 30 years

        Returns
        -------
        float
            Annuity
        """
        return principal * interest * (1 / (1 - (1 + interest) ** (-maturity)))

    def plot(self):
        """
        Create a plot visualizing the amortization of the loan
        """
        fig = go.Figure(
            data=[
                go.Bar(
                    name="Repayment", x=self.table["Time"], y=self.table["Repayment"]
                ),
                go.Bar(name="Interest", x=self.table["Time"], y=self.table["Interest"]),
            ]
        )
        # Change the bar mode
        fig.update_layout(
            title={
                "text": "Annuity Loan P={}, r={}, m={}, n_pay={}".format(
                    self.principal, self.interest, self.maturity, self.n_payments
                ),
                "xanchor": "center",
                "yanchor": "top",
                "y": 0.9,
                "x": 0.5,
            },
            xaxis_title="Time",
            yaxis_title="$",
            barmode="stack",
            font=dict(size=18),
        )
        fig.show()

    def total_cost(self) -> float:
        """
        The total cost of the loan, which is the sum of all annuities
        """
        return self.table["Annuity"].sum()

    def total_interest(self) -> float:
        """
        The total interest paid on the loan during the whole lifetime
        """
        return self.table["Interest"].sum()
