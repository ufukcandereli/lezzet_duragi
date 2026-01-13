# Restaurant Automation System

A full-featured web-based restaurant management system built with Flask and SQLite. This application provides comprehensive tools for managing daily menus, table reservations, order processing, and payment handling.

## Table of Contents

- [Features](#features)
- [Technology Stack](#technology-stack)
- [Project Structure](#project-structure)
- [Installation](#installation)
- [Usage](#usage)
- [API Endpoints](#api-endpoints)
- [Database Schema](#database-schema)
- [Testing](#testing)
- [Default Credentials](#default-credentials)
- [License](#license)

## Features

### Customer-Facing Features
- **Daily Menu Display**: Automatically shows menu items scheduled for the current day
- **Weekly Menu Overview**: Browse the complete weekly menu organized by day
- **Quick Ordering**: Select items from the menu and submit orders to specific tables
- **Table Reservation**: Book tables in advance with party size and date/time selection

### Administrative Features
- **Real-time Table Status**: Visual dashboard showing occupied and available tables
- **Order Management**: View active orders with itemized details and total prices
- **Payment Processing**: Accept cash or credit card payments and automatically free tables
- **Menu Management**: Add and remove menu items with category, price, and image support
- **Reservation Management**: View, assign tables to, or delete reservations

## Technology Stack

| Component | Technology |
|-----------|------------|
| Backend | Python 3.x, Flask |
| Database | SQLite3 |
| Frontend | HTML5, CSS3, JavaScript |
| UI Framework | Bootstrap 5.3 |
| Templating | Jinja2 |
| Testing | pytest |

## Project Structure

```
restaurant-automation/
├── app.py                 # Main Flask application
├── database.db            # SQLite database file
├── db_tamir.py            # Database repair utility
├── test_app.py            # Unit test suite
├── run_tests.bat          # Test runner script (Windows)
├── requirements.txt       # Python dependencies
├── ReadMe.md              # Project documentation
├── static/
│   └── img/               # Menu item images (28 images)
└── templates/
    ├── base.html          # Base template with navigation
    ├── index.html         # Homepage with daily menu
    ├── general_menu.html  # Weekly menu display
    ├── reservation.html   # Reservation form
    ├── login.html         # Admin login page
    └── admin.html         # Admin dashboard
```

## Installation

### Prerequisites
- Python 3.8 or higher
- pip (Python package manager)

### Setup Instructions

1. Clone or download the repository:
   ```bash
   git clone <repository-url>
   cd restaurant-automation
   ```

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install flask pytest
   ```

4. Run the application:
   ```bash
   python app.py
   ```

5. Access the application at `http://127.0.0.1:5000`

## Usage

### For Customers

1. **View Today's Menu**: Visit the homepage to see available dishes for the current day
2. **Place an Order**: 
   - Click "Add" on desired menu items
   - Select your table number
   - Click "Send Order"
3. **Make a Reservation**: Navigate to the reservation page and fill in your details
4. **Browse Weekly Menu**: Click "All Dishes" to see the complete weekly menu

### For Staff/Admin

1. **Login**: Navigate to `/admin` and enter the password
2. **Manage Orders**: View active orders and process payments
3. **Handle Reservations**: Assign tables to reservations or remove completed ones
4. **Update Menu**: Add new items or remove existing ones from the menu

## API Endpoints

### Public Routes

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/` | Homepage with daily menu |
| GET | `/genel-menu` | Weekly menu overview |
| GET | `/rezervasyon` | Reservation form |
| POST | `/rezervasyon` | Submit reservation |
| POST | `/order` | Submit new order |

### Protected Routes (Require Authentication)

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/admin` | Admin dashboard |
| GET | `/login` | Login page |
| POST | `/login` | Process login |
| GET | `/logout` | Logout and redirect |
| POST | `/add_item` | Add menu item |
| POST | `/delete_item/<id>` | Remove menu item |
| POST | `/delete_reservation/<id>` | Remove reservation |
| POST | `/assign_table/<id>` | Assign table to reservation |
| POST | `/pay_bill` | Process payment |

## Database Schema

### Tables

**menu**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| name | TEXT | Item name |
| price | REAL | Item price |
| category | TEXT | Category (Main Course, Appetizer, Dessert, Beverage) |
| image | TEXT | Image filename |

**daily_menu**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| menu_item_id | INTEGER | Foreign key to menu |
| day_of_week | TEXT | Day name (Monday-Sunday) |

**reservations**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| customer_name | TEXT | Customer name |
| party_size | INTEGER | Number of guests |
| date_time | TEXT | Reservation date and time |
| status | TEXT | Status (Pending/Seated) |
| assigned_table | INTEGER | Assigned table number |

**orders**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Primary key |
| table_no | INTEGER | Table number |
| status | TEXT | Status (Active/Paid) |
| items | TEXT | Comma-separated item names |
| total_price | REAL | Total order amount |
| payment_type | TEXT | Payment method |

**tables**
| Column | Type | Description |
|--------|------|-------------|
| id | INTEGER | Table number |
| capacity | INTEGER | Seating capacity |
| status | TEXT | Status (Available/Occupied) |

## Testing

The project includes a comprehensive test suite with 27 unit tests covering all major functionality.

### Running Tests

**Windows:**
```bash
run_tests.bat
```

**Cross-platform:**
```bash
python -m pytest test_app.py -v
```

### Test Coverage

| Category | Tests | Description |
|----------|-------|-------------|
| Homepage | 2 | Page loading, daily menu display |
| Reservation | 3 | Form display, submission, redirect |
| Order | 3 | Creation, validation, price calculation |
| Authentication | 4 | Login, logout, access control |
| Admin Panel | 3 | Access control, data display |
| Payment | 3 | Authorization, cash/card processing |
| Menu Management | 2 | Add/delete items |
| Reservation Management | 2 | Delete, table assignment |
| General Menu | 2 | Page loading, weekly display |
| Helper Functions | 1 | Day translation |
| Integration | 2 | End-to-end workflows |

## Default Credentials

| Role | Password |
|------|----------|
| Admin | `admin123` |

**Important**: Change the default password and secret key before deploying to production.

## Configuration

Key configuration variables in `app.py`:

```python
app.secret_key = 'your_secret_key_here'  # Change in production
```

## License

This project is developed for educational purposes. All rights reserved.

---

**Author**: Restaurant Automation Project Team  
**Version**: 1.0.0  
**Last Updated**: January 2026

