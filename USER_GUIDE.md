# Small Business Accounting Software - User Guide

## Introduction

Welcome to the Small Business Accounting Software, a comprehensive solution designed specifically for small businesses with 7-12 employees. This software helps you efficiently manage your company's finances by tracking income, expenses, inventory, invoices, and employee salaries.

## Table of Contents

1. [Getting Started](#getting-started)
2. [Dashboard Overview](#dashboard-overview)
3. [Income Management](#income-management)
4. [Expense Management](#expense-management)
5. [Inventory Management](#inventory-management)
6. [Invoice Management](#invoice-management)
7. [Employee & Salary Management](#employee--salary-management)
8. [Financial Reports](#financial-reports)
9. [Data Export](#data-export)
10. [Troubleshooting](#troubleshooting)

## Getting Started

### System Requirements

- Python 3.11 or higher
- Web browser (Chrome, Firefox, or Edge recommended)
- 2GB RAM minimum
- 500MB free disk space

### Installation

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

### Starting the Application

1. With the virtual environment activated, start the application:
   ```
   flask run --host=0.0.0.0 --port=5000
   ```
2. Open your web browser and navigate to:
   ```
   http://localhost:5000
   ```
3. Log in with the default credentials:
   - Username: admin
   - Password: admin123
   (Please change these credentials after first login)

## Dashboard Overview

The dashboard provides a quick overview of your business finances:

- **Summary Cards**: View total income, expenses, and profit for the current month
- **Recent Transactions**: Lists the most recent income and expense entries
- **Inventory Status**: Shows items with low stock levels
- **Outstanding Invoices**: Displays unpaid invoices
- **Quick Actions**: Buttons for common tasks like adding income or creating invoices

## Income Management

### Adding Income

1. Click "Income" in the main navigation menu
2. Click the "Add Income" button
3. Fill in the required fields:
   - Description: Brief description of the income source
   - Amount: The income amount
   - Date Received: When the payment was received
   - Category: Select or create a category for this income
4. Click "Save" to record the income

### Viewing Income Records

1. Navigate to the "Income" section
2. Use the filter options to narrow down records by date range or category
3. Click on any record to view its details

### Editing Income Records

1. Navigate to the "Income" section
2. Find the record you want to edit and click the "Edit" icon
3. Update the information as needed
4. Click "Save" to update the record

### Deleting Income Records

1. Navigate to the "Income" section
2. Find the record you want to delete and click the "Delete" icon
3. Confirm the deletion when prompted

## Expense Management

### Adding Expenses

1. Click "Expenses" in the main navigation menu
2. Click the "Add Expense" button
3. Fill in the required fields:
   - Description: Brief description of the expense
   - Amount: The expense amount
   - Date Incurred: When the expense occurred
   - Category: Select or create a category for this expense
4. Click "Save" to record the expense

### Viewing Expense Records

1. Navigate to the "Expenses" section
2. Use the filter options to narrow down records by date range or category
3. Click on any record to view its details

### Editing Expense Records

1. Navigate to the "Expenses" section
2. Find the record you want to edit and click the "Edit" icon
3. Update the information as needed
4. Click "Save" to update the record

### Deleting Expense Records

1. Navigate to the "Expenses" section
2. Find the record you want to delete and click the "Delete" icon
3. Confirm the deletion when prompted

## Inventory Management

### Adding Inventory Items

1. Click "Inventory" in the main navigation menu
2. Click the "Add Item" button
3. Fill in the required fields:
   - Name: Product name
   - SKU: Stock keeping unit (unique identifier)
   - Quantity on Hand: Current stock level
   - Sale Price: Retail price of the item
   - Description: Product description
4. Click "Save" to add the item

### Viewing Inventory

1. Navigate to the "Inventory" section
2. Use the search box to find specific items
3. Sort by columns by clicking on the column headers
4. Click on any item to view its details

### Updating Inventory

1. Navigate to the "Inventory" section
2. Find the item you want to update and click the "Edit" icon
3. Update the information as needed
4. Click "Save" to update the record

### Deleting Inventory Items

1. Navigate to the "Inventory" section
2. Find the item you want to delete and click the "Delete" icon
3. Confirm the deletion when prompted

## Invoice Management

### Creating Invoices

1. Click "Invoices" in the main navigation menu
2. Click the "Create Invoice" button
3. Fill in the customer information:
   - Customer Name
   - Invoice Date
   - Due Date
4. Add items to the invoice:
   - Click "Add Item"
   - Select an inventory item or enter a custom item
   - Enter quantity and unit price
   - Repeat for additional items
5. Add any notes or payment terms
6. Click "Save" to create the invoice

### Viewing Invoices

1. Navigate to the "Invoices" section
2. Use the filter options to narrow down by date range or status
3. Click on any invoice to view its details

### Editing Invoices

1. Navigate to the "Invoices" section
2. Find the invoice you want to edit and click the "Edit" icon
3. Update the information as needed
4. Click "Save" to update the invoice

### Deleting Invoices

1. Navigate to the "Invoices" section
2. Find the invoice you want to delete and click the "Delete" icon
3. Confirm the deletion when prompted

## Employee & Salary Management

### Adding Employees

1. Click "Employees" in the main navigation menu
2. Click the "Add Employee" button
3. Fill in the required fields:
   - First Name
   - Last Name
   - Email
   - Phone Number
   - Position
   - Hire Date
4. Click "Save" to add the employee

### Recording Salary Payments

1. Navigate to the "Employees" section
2. Click on the employee's name
3. Click the "Add Salary Payment" button
4. Fill in the payment details:
   - Payment Date
   - Gross Amount
   - Deductions
   - Payment Period (optional)
   - Notes (optional)
5. Click "Save" to record the payment

### Viewing Employee Information

1. Navigate to the "Employees" section
2. Click on any employee to view their details and salary history

### Editing Employee Information

1. Navigate to the "Employees" section
2. Find the employee you want to edit and click the "Edit" icon
3. Update the information as needed
4. Click "Save" to update the record

## Financial Reports

### Generating Reports

1. Click "Reports" in the main navigation menu
2. Select the type of report you want to generate:
   - Profit and Loss Statement
   - Expense Report
   - Income Report
   - Inventory Report
3. Set the date range for the report
4. Click "Generate Report"

### Interpreting Reports

- **Profit and Loss Statement**: Shows total income, expenses, and profit/loss for the selected period
- **Expense Report**: Breaks down expenses by category
- **Income Report**: Breaks down income by category
- **Inventory Report**: Shows current inventory levels and values

## Data Export

### Exporting Data

1. Navigate to the section containing the data you want to export
2. Click the "Export" button
3. Select the export format (CSV, PDF)
4. Click "Export" to download the file

## Troubleshooting

### Common Issues

- **Application won't start**: Ensure Python and all dependencies are installed correctly
- **Can't log in**: Verify username and password; reset if necessary
- **Data not saving**: Check disk space and permissions
- **Reports not generating**: Verify there is data for the selected date range

### Getting Help

If you encounter any issues not covered in this guide, please contact technical support.

---

Thank you for using the Small Business Accounting Software. We hope it helps streamline your financial management processes!
