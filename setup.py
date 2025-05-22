from setuptools import setup, find_packages

setup(
    name="tiktok_ad_analyzer",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        "pandas",
        "numpy",
        "plotly",
        "streamlit",
        "openpyxl",
    ],
    python_requires=">=3.8",
)