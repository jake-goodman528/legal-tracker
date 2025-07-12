# PostgreSQL Setup Guide for Short Term Rental Tracker

This guide will help you set up PostgreSQL for your Short Term Rental Tracker application.

## Prerequisites

1. PostgreSQL server installed on your system
2. Python virtual environment activated
3. Required dependencies installed

## Step 1: Install PostgreSQL

### macOS (using Homebrew)
```bash
brew install postgresql
brew services start postgresql
```

### Ubuntu/Debian
```bash
sudo apt update
sudo apt install postgresql postgresql-contrib
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

### Windows
Download and install PostgreSQL from: https://www.postgresql.org/download/windows/

## Step 2: Create Database and User

1. Access PostgreSQL as the postgres user:
```bash
sudo -u postgres psql
```

2. Create a database and user:
```sql
-- Create database
CREATE DATABASE str_compliance_db;

-- Create user with password
CREATE USER str_user WITH PASSWORD 'your_secure_password';

-- Grant privileges
GRANT ALL PRIVILEGES ON DATABASE str_compliance_db TO str_user;

-- Exit psql
\q
```

## Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

## Step 4: Configure Environment Variables

Create a `.env` file based on `env.example`:

```bash
cp env.example .env
```

Edit `.env` and update the database configuration:

```env
# Database - PostgreSQL
DATABASE_URL=postgresql://str_user:your_secure_password@localhost:5432/str_compliance_db

# Other required variables
SESSION_SECRET=your-secure-session-secret-key-here-minimum-32-chars
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-secure-admin-password-here
```

## Step 5: Initialize Database

Run the application to create tables and sample data:

```bash
python main.py
```

The application will automatically:
- Create all necessary tables
- Create an admin user with the credentials from your environment
- Populate with sample data (unless `SKIP_SAMPLE_DATA` is set)

## Step 6: Verify Setup

1. Check that the database was created:
```bash
psql -U str_user -d str_compliance_db -c "\dt"
```

2. Start the application:
```bash
python main.py
```

3. Visit `http://localhost:9000` to verify the application is running

## Migrating from SQLite (Optional)

If you have existing data in SQLite that you want to migrate:

1. Create a backup of your current SQLite database:
```bash
cp instance/str_compliance.db instance/str_compliance.db.backup
```

2. Use the migration script (create if needed) or manually export/import data

## Troubleshooting

### Connection Issues
- Ensure PostgreSQL is running: `brew services list | grep postgresql` (macOS) or `sudo systemctl status postgresql` (Linux)
- Check if the database exists: `psql -U str_user -l`
- Verify connection string format: `postgresql://username:password@host:port/database`

### Permission Issues
- Make sure the user has proper permissions on the database
- Check if you can connect manually: `psql -U str_user -d str_compliance_db`

### Dependencies
- If you get import errors, ensure all dependencies are installed: `pip install -r requirements.txt`
- On some systems, you might need to install additional packages: `sudo apt install libpq-dev python3-dev` (Ubuntu/Debian)

## Production Considerations

1. **Security**: Use strong passwords and consider SSL connections
2. **Performance**: Configure PostgreSQL settings for your expected load
3. **Backup**: Set up regular database backups
4. **Monitoring**: Consider monitoring tools for database performance

## Environment Variables Reference

- `DATABASE_URL`: PostgreSQL connection string
- `SESSION_SECRET`: Flask session secret (required, minimum 32 characters)
- `ADMIN_USERNAME`: Initial admin username
- `ADMIN_PASSWORD`: Initial admin password
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `FLASK_DEBUG`: Enable Flask debug mode (true/false)
- `SKIP_SAMPLE_DATA`: Skip inserting sample data on startup (true/false) 