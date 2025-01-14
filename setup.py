from setuptools import setup, find_packages

setup(
    name='proftpd_flask',
    version='1.0.0',
    packages=find_packages(),
    include_package_data=True,
    install_requires=[
        'Flask',
        'Flask-Session',
        'Flask-Migrate',
        'Flask-LDAP3-Login',
        'Flask-Login',
        'Flask-SQLAlchemy',
        'mysql-connector-python',
        'typing_extensions',
        'python-dotenv',
        'flake8'
    ],
    entry_points={
        'console_scripts': [
            'run_proftpd_flask=app:main',
        ],
    },
)