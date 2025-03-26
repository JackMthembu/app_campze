# Camp Management System

A Flask-based web application for managing camp bookings and operations.

## Features

- User authentication and authorization
- Camp package management
- Booking system
- Payment integration with Stripe
- Email notifications
- Admin dashboard
- Tour operator dashboard
- School dashboard

## Prerequisites

- Python 3.11+
- Poetry for dependency management
- Redis (for Celery tasks)
- PostgreSQL (recommended for production)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/JackMthembu/app_campze
cd app_campze
```

2. Install dependencies using Poetry:
```bash
poetry install
```

3. Create a `.env` file in the root directory with the following variables:
```env
FLASK_APP=app
FLASK_ENV=development
SECRET_KEY=your-secret-key
DATABASE_URL=postgresql://user:password@localhost/dbname
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=your-email@gmail.com
MAIL_PASSWORD=your-app-password
MAIL_DEFAULT_SENDER=your-email@gmail.com
STRIPE_PUBLIC_KEY=your-stripe-public-key
STRIPE_SECRET_KEY=your-stripe-secret-key
STRIPE_WEBHOOK_SECRET=your-stripe-webhook-secret
```

4. Initialize the database:
```bash
poetry run flask db upgrade
```

## Development

1. Activate the virtual environment:
```bash
poetry shell
```

2. Run the development server:
```bash
flask run
```

3. Run tests:
```bash
pytest
```

## Production Deployment

1. Set the environment to production:
```bash
export FLASK_ENV=production
```

2. Run with Gunicorn:
```bash
gunicorn "app:create_app('production')"
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.
