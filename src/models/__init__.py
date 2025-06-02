# This file makes the 'models' directory a Python package

from .company import Company, company_users # Added Company model and association table
from .user import User
from .income import Income
from .expense import Expense
from .inventory_item import InventoryItem
from .invoice import Invoice, InvoiceItem
from .employee import Employee, Salary
