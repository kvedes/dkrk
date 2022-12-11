from distutils.core import setup

setup(
    name="dkrk",
    version="0.1",
    description="Calculations for Danish Real Estate Loans",
    author="Mathias Kvist Aarup",
    author_email="kvistanalytics@gmail.com",
    packages=["distutils", "distutils.command"],
    install_requires=["numpy", "pandas", "plotly"],
)
