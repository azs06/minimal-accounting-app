# README.md - Small Business Accounting Software

## Overview

This is a minimal accounting software designed for small businesses with 7-12 employees. The application helps track income, expenses, inventory, invoices, and employee salaries, providing essential financial reports.

## Features

- **Income Tracking**: Record and manage all income sources
- **Expense Tracking**: Track and categorize business expenses
- **Inventory Management**: Manage product inventory with stock levels
- **Invoice Management**: Create and manage customer invoices
- **Employee & Salary Management**: Track employee information and salary payments
- **Financial Reports**: Generate profit/loss statements and other financial reports

## Installation

1. Extract the accounting_app_deployment.zip file to a directory of your choice
2. Open a terminal/command prompt and navigate to the extracted directory
3. Create a virtual environment:
   ```
   python -m venv venv
   ```
4. Activate the virtual environment:
   - Windows: `venv\Scripts\activate`
   - macOS/Linux: `source venv/bin/activate`
5. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

## Running the Application

1. With the virtual environment activated, start the application:
   ```
   export FLASK_APP=src/main.py
   flask run --host=0.0.0.0 --port=8080
   ```
2. Open your web browser and navigate to:
   ```
   http://localhost:8080
   ```

## Documentation

For detailed instructions on using the software, please refer to the USER_GUIDE.md file included in this package.

## Support

If you encounter any issues or have questions, please contact the development team.

Thank you for using our Small Business Accounting Software!
