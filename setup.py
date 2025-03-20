from setuptools import setup, find_packages

setup(
    name="app_campze",
    version="0.1.0",
    packages=find_packages(),
    python_requires=">=3.11,<3.12",
    install_requires=[
        # Core Flask packages
        "Flask==2.2.5",
        "Flask-SQLAlchemy==3.0.2",
        "Flask-Login==0.6.2",
        "Flask-WTF==1.1.1",
        "Flask-Mail==0.9.1",
        "Flask-Migrate==4.0.4",
        "Flask-CORS==4.0.0",
        
        # Database and ORM
        "SQLAlchemy==2.0.19",
        "pyodbc==4.0.39",
        "mysqlclient==2.2.4",
        
        # Forms and Validation
        "WTForms==3.0.1",
        "email-validator==2.0.0",
        
        # Utils
        "python-dotenv==0.21.1",
        "python-dateutil==2.8.2",
        "pytz==2023.3",
        "itsdangerous==2.1.2",
        "Werkzeug==2.2.3",
        "cachetools==5.3.1",
        "alembic==1.11.1",
        "gunicorn==20.1.0",
        
        # Image Processing
        "Pillow==9.5.0",
        
        # PDF Generation
        "pdfkit==1.0.0",
        
        # Security
        "bcrypt==4.0.1",
        
        # Additional Dependencies
        "click==8.1.7",
        "Jinja2==3.1.2",
        "MarkupSafe==2.1.3"
    ],
    description="Camp Management System",
    author="Jack Mthembu",
    author_email="your.email@example.com",  # Update this with your email
    url="https://github.com/JackMthembu/app_campze",
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Developers",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3.11",
    ],
) 