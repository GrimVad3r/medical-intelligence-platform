from setuptools import find_packages, setup

setup(
    name="medical-intelligence-platform",
    version="0.1.0",
    packages=find_packages(where="."),
    package_dir={"": "."},
    python_requires=">=3.10",
    install_requires=[
        "fastapi>=0.109.0",
        "uvicorn[standard]>=0.27.0",
        "sqlalchemy>=2.0.0",
        "psycopg2-binary>=2.9.9",
        "pydantic>=2.5.0",
        "pydantic-settings>=2.1.0",
        "python-dotenv>=1.0.0",
        "httpx>=0.26.0",
        "streamlit>=1.29.0",
        "dagster>=1.6.0",
        "pytest>=7.4.0",
    ],
    extras_require={
        "nlp": ["spacy>=3.7.0", "transformers>=4.36.0", "shap>=0.44.0"],
        "yolo": ["ultralytics>=8.0.0", "torch>=2.0.0"],
        "dev": ["black", "isort", "flake8", "mypy", "pre-commit"],
    },
    entry_points={
        "console_scripts": [],
    },
)
