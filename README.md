# 📄 PDF Table Extractor API

A powerful FastAPI application that extracts tables from PDF files using `tabula-py` (Javabased) and `pdfplumber`, with a built-in web UI and MySQL database integration.

## ✨ Features

- **Dual Extraction Methods**: Uses `tabula-py` for structure and `pdfplumber` for flexibility.
- **Web UI**: Beautiful drag-and-drop interface for testing.
- **Database Storage**: Save extracted data to MySQL for analysis.
- **REST API**: Clean JSON endpoints for integration.

## 🚀 How to Run Locally

Follow these commands to set up the project on Windows.

### 1. Prerequisites
- **Python 3.9+** installed
- **Java 17+** installed (Required for `tabula-py`)
- **MySQL Server** installed and running

### 2. Clone & Setup
```powershell
# Clone the repository (if you haven't)
git clone <your-repo-url>
cd python-pdf-extact-crime-report

# Create a virtual environment
python -m venv venv

# Activate the virtual environment
.\venv\Scripts\activate
```

### 3. Install Dependencies
```powershell
pip install -r requirements.txt
```

### 4. Database Setup
1. Create a MySQL database named `crime_reports`.
2. Rename `.env.example` to `.env` (or create it) with your credentials:
   ```env
   MYSQL_HOST=localhost
   MYSQL_PORT=3306
   MYSQL_USER=root
   MYSQL_PASSWORD=your_password
   MYSQL_DATABASE=crime_reports
   ```

### 5. Run the Server
```powershell
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```
.\venv\Scripts\uvicorn main:app --reload --host 127.0.0.1 --port 8000
---

## 🔗 Endpoints

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | **/ui** | **Open this in browser** - Web Interface |
| `GET` | **/docs** | Swagger API Documentation |
| `POST` | **/extract** | Extract tables (Auto-detect method) |
| `POST` | **/save-to-db** | Save extracted JSON to MySQL |
| `GET` | **/view-extractions** | View saved data in UI |
| `GET` | **/db-status** | Check database connection |

## 🛠️ Deployment (Docker/Render/Railway)

The project includes `Dockerfile` and `render.yaml` for easy deployment.

**Note:** For cloud deployment, ensure you verify the Java installation in the Dockerfile as `tabula-py` requires it.