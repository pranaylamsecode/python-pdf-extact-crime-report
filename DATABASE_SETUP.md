# 🗄️ MySQL Database Setup Guide

## Step 1: Install MySQL

If you don't have MySQL installed:

**Windows:**
- Download from: https://dev.mysql.com/downloads/installer/
- Install MySQL Server
- Remember the root password you set!

**Or use XAMPP:**
- Download XAMPP: https://www.apachefriends.org/
- Includes MySQL (MariaDB)
- Start MySQL from XAMPP Control Panel

## Step 2: Configure Database

### Option A: Using MySQL Command Line

```sql
-- Login to MySQL
mysql -u root -p

-- Create database
CREATE DATABASE crime_reports;

-- Use the database
USE crime_reports;

-- Tables will be created automatically by the app!
```

### Option B: Using phpMyAdmin (if using XAMPP)

1. Open: http://localhost/phpmyadmin
2. Click "New" to create database
3. Name it: `crime_reports`
4. Click "Create"

## Step 3: Update .env File

Edit `.env` file with your MySQL credentials:

```env
# MySQL Database Configuration
MYSQL_HOST=localhost
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_actual_password_here
MYSQL_DATABASE=crime_reports

# API Configuration
PORT=8000
```

**Important:** Replace `your_actual_password_here` with your MySQL root password!

## Step 4: Install Python Dependencies

```bash
.\venv\Scripts\pip install mysql-connector-python python-dotenv
```

## Step 5: Restart the Server

The tables will be created automatically when the server starts!

```bash
.\venv\Scripts\uvicorn main:app --reload
```

## 📊 Database Schema

The app creates 2 tables automatically:

### `extraction_logs`
- `id` - Auto increment primary key
- `filename` - PDF filename
- `extraction_method` - tabula or pdfplumber
- `rows_count` - Number of rows extracted
- `columns_count` - Number of columns
- `extracted_at` - Timestamp
- `status` - success/failed

### `extracted_data`
- `id` - Auto increment primary key
- `extraction_log_id` - Foreign key to extraction_logs
- `row_data` - JSON data for each row
- `created_at` - Timestamp

## 🔗 New API Endpoints

### Check Database Status
```
GET http://127.0.0.1:8000/db-status
```

### Save Extraction to Database
```
POST http://127.0.0.1:8000/save-to-db
Body: {
  "filename": "report.pdf",
  "method": "tabula",
  "rows": 830,
  "columns": ["col1", "col2"],
  "data": [{"col1": "value1", "col2": "value2"}]
}
```

### View All Extractions (UI)
```
http://127.0.0.1:8000/view-extractions
```

### Get All Extractions (API)
```
GET http://127.0.0.1:8000/extractions
```

### Get Specific Extraction Data
```
GET http://127.0.0.1:8000/extraction/{id}
```

## 🧪 Testing

1. **Check DB Connection:**
   ```
   http://127.0.0.1:8000/db-status
   ```

2. **Extract PDF:**
   - Go to: http://127.0.0.1:8000/ui
   - Upload a PDF
   - Get the JSON response

3. **Save to Database:**
   - Use the `/save-to-db` endpoint with the extraction data
   - Or modify the UI to auto-save (we can do this next!)

4. **View Saved Data:**
   ```
   http://127.0.0.1:8000/view-extractions
   ```

## ❗ Troubleshooting

### "Access denied for user 'root'"
- Check your MySQL password in `.env`
- Make sure MySQL is running

### "Unknown database 'crime_reports'"
- Run: `CREATE DATABASE crime_reports;` in MySQL

### "Can't connect to MySQL server"
- Make sure MySQL/XAMPP is running
- Check port 3306 is not blocked

### Tables not created
- Check server console for errors
- Manually create database first
- Restart the server

## ✅ Quick Test

```bash
# 1. Check if DB is connected
curl http://127.0.0.1:8000/db-status

# 2. Should see: {"status": "connected", ...}
```

---

**Need help?** Let me know which error you're seeing!
