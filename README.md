# Danish Real Estate calculator

This projects lets you perform basic calculations on Danish Real Estate loans with fixed interest rate. It can create a simple table showing annuities, repayment, debt and bidrag (What is the english word for bidrag?). Currently only implemented for Total Kredit.

Small example:

```python
>>> from dkrk.realestate import TKLoan
>>> tk = TKLoan(
    price=99.47,
    face_value=1_000_000,
    interest=0.05,
    bidrag=0.0074,
    maturity=30,
    n_terms=4)
>>> tk.loan_amount
1005328.24
>>> tk.total_cost
2085604.07
>>> tk.total_interest
1080275.83
>>> tk.table
     Time   Annuity  Repayment  Interest        Debt   Bidrag
0       1 18079.316   3652.856 12566.603 1001675.384 1859.857
1       2 18072.558   3698.517 12520.942  997976.867 1853.099
2       3 18065.716   3744.748 12474.711  994232.119 1846.257
3       4 18058.788   3791.557 12427.901  990440.562 1839.329
4       5 18051.774   3838.952 12380.507  986601.610 1832.315
5       6 18044.672   3886.939 12332.520  982714.671 1825.213
...
```
