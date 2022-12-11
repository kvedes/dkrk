from setuptools import setup, find_packages

setup(
    name="dkrk",
    version="0.1",
    description="Calculations for Danish Real Estate Loans",
    author="Mathias Kvist Aarup",
    author_email="kvistanalytics@gmail.com",
    packages=find_packages(),
    install_requires=["numpy", "pandas", "plotly"],
)
