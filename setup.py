from setuptools import setup, find_packages

setup(
    name="agent_council",
    version="0.1.0",
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    install_requires=[
        "openai-agents",
        "openai",
        "python-dotenv",
        "rich",
        "pypdf",
        "python-docx",
    ],
)

