from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse, HTMLResponse
import tabula
import pdfplumber
import pandas as pd
import tempfile
import os
from typing import Dict, Any, List
import mysql.connector
from mysql.connector import Error
from dotenv import load_dotenv
import json
from datetime import datetime

# Load environment variables
load_dotenv()

# MySQL Configuration
MYSQL_CONFIG = {
    'host': os.getenv('MYSQL_HOST', 'localhost'),
    'port': int(os.getenv('MYSQL_PORT', 3306)),
    'user': os.getenv('MYSQL_USER', 'root'),
    'password': os.getenv('MYSQL_PASSWORD', ''),
    'database': os.getenv('MYSQL_DATABASE', 'crime_reports')
}

# Database connection pool
def get_db_connection():
    """Create and return a database connection"""
    try:
        connection = mysql.connector.connect(**MYSQL_CONFIG)
        return connection
    except Error as e:
        print(f"Error connecting to MySQL: {e}")
        return None

def create_tables():
    """Create necessary database tables if they don't exist"""
    connection = get_db_connection()
    if not connection:
        return False
    
    try:
        cursor = connection.cursor()
        
        # Create extraction_logs table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extraction_logs (
                id INT AUTO_INCREMENT PRIMARY KEY,
                filename VARCHAR(255),
                extraction_method VARCHAR(50),
                rows_count INT,
                columns_count INT,
                extracted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status VARCHAR(50)
            )
        """)
        
        # Create extracted_data table
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS extracted_data (
                id INT AUTO_INCREMENT PRIMARY KEY,
                extraction_log_id INT,
                row_data JSON,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (extraction_log_id) REFERENCES extraction_logs(id)
            )
        """)
        
        connection.commit()
        cursor.close()
        connection.close()
        return True
    except Error as e:
        print(f"Error creating tables: {e}")
        return False

# Create tables on startup
create_tables()

app = FastAPI(
    title="PDF Table Extractor API",
    description="Extract tables from PDF files using tabula-py and pdfplumber",
    version="1.0.0"
)


@app.get("/")
async def root():
    """Health check endpoint"""
    return {
        "status": "active",
        "service": "PDF Table Extractor API",
        "version": "1.0.0"
    }


@app.get("/ui", response_class=HTMLResponse)
async def web_ui():
    """Web UI for testing PDF extraction"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>PDF Table Extractor - Test UI</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                display: flex;
                justify-content: center;
                align-items: center;
                padding: 20px;
            }
            
            .container {
                background: white;
                border-radius: 20px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
                max-width: 900px;
                width: 100%;
                padding: 40px;
            }
            
            h1 {
                color: #667eea;
                margin-bottom: 10px;
                font-size: 2em;
            }
            
            .subtitle {
                color: #666;
                margin-bottom: 30px;
                font-size: 0.95em;
            }
            
            .upload-area {
                border: 3px dashed #667eea;
                border-radius: 15px;
                padding: 40px;
                text-align: center;
                background: #f8f9ff;
                margin-bottom: 20px;
                transition: all 0.3s ease;
            }
            
            .upload-area:hover {
                background: #f0f2ff;
                border-color: #764ba2;
            }
            
            .upload-area.dragover {
                background: #e8ebff;
                border-color: #764ba2;
                transform: scale(1.02);
            }
            
            input[type="file"] {
                display: none;
            }
            
            .file-label {
                display: inline-block;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 15px 40px;
                border-radius: 50px;
                cursor: pointer;
                font-size: 1em;
                font-weight: 600;
                transition: transform 0.2s;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            
            .file-label:hover {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }
            
            .file-label:active {
                transform: translateY(0);
            }
            
            .file-name {
                margin-top: 15px;
                color: #667eea;
                font-weight: 600;
            }
            
            .upload-icon {
                font-size: 3em;
                margin-bottom: 15px;
            }
            
            button {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                border: none;
                padding: 15px 50px;
                border-radius: 50px;
                font-size: 1.1em;
                font-weight: 600;
                cursor: pointer;
                width: 100%;
                margin-top: 20px;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
            }
            
            button:hover:not(:disabled) {
                transform: translateY(-2px);
                box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
            }
            
            button:disabled {
                background: #ccc;
                cursor: not-allowed;
                box-shadow: none;
            }
            
            .loading {
                display: none;
                text-align: center;
                margin: 20px 0;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto 10px;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .result {
                display: none;
                margin-top: 30px;
                padding: 25px;
                background: #f8f9ff;
                border-radius: 15px;
                border-left: 5px solid #667eea;
            }
            
            .result h2 {
                color: #667eea;
                margin-bottom: 15px;
                font-size: 1.5em;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
                gap: 15px;
                margin-bottom: 20px;
            }
            
            .stat-card {
                background: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                box-shadow: 0 2px 10px rgba(0, 0, 0, 0.1);
            }
            
            .stat-value {
                font-size: 2em;
                font-weight: bold;
                color: #667eea;
            }
            
            .stat-label {
                color: #666;
                font-size: 0.9em;
                margin-top: 5px;
            }
            
            .badge {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 5px 15px;
                border-radius: 20px;
                font-size: 0.85em;
                font-weight: 600;
                margin-bottom: 15px;
            }
            
            .badge.success {
                background: #10b981;
            }
            
            .badge.warning {
                background: #f59e0b;
            }
            
            pre {
                background: #1e1e1e;
                color: #d4d4d4;
                padding: 20px;
                border-radius: 10px;
                overflow-x: auto;
                font-size: 0.9em;
                max-height: 400px;
                overflow-y: auto;
            }
            
            .error {
                background: #fee;
                border-left-color: #f00;
                color: #c00;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <h1>📄 PDF Table Extractor</h1>
            <p class="subtitle">Upload a PDF file to extract tables using AI-powered extraction</p>
            
            <form id="uploadForm" enctype="multipart/form-data">
                <div class="upload-area" id="uploadArea">
                    <div class="upload-icon">📁</div>
                    <label for="pdfFile" class="file-label">Choose PDF File</label>
                    <input type="file" id="pdfFile" name="file" accept=".pdf" required>
                    <div class="file-name" id="fileName"></div>
                </div>
                
                <button type="submit" id="extractBtn" disabled>Extract Tables</button>
            </form>
            
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>Extracting tables from PDF...</p>
            </div>
            
            <div class="result" id="result"></div>
        </div>
        
        <script>
            const uploadArea = document.getElementById('uploadArea');
            const pdfFile = document.getElementById('pdfFile');
            const fileName = document.getElementById('fileName');
            const extractBtn = document.getElementById('extractBtn');
            const uploadForm = document.getElementById('uploadForm');
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            
            // File input change
            pdfFile.addEventListener('change', function() {
                if (this.files.length > 0) {
                    fileName.textContent = '✓ ' + this.files[0].name;
                    extractBtn.disabled = false;
                } else {
                    fileName.textContent = '';
                    extractBtn.disabled = true;
                }
            });
            
            // Drag and drop
            uploadArea.addEventListener('dragover', (e) => {
                e.preventDefault();
                uploadArea.classList.add('dragover');
            });
            
            uploadArea.addEventListener('dragleave', () => {
                uploadArea.classList.remove('dragover');
            });
            
            uploadArea.addEventListener('drop', (e) => {
                e.preventDefault();
                uploadArea.classList.remove('dragover');
                
                const files = e.dataTransfer.files;
                if (files.length > 0 && files[0].type === 'application/pdf') {
                    pdfFile.files = files;
                    fileName.textContent = '✓ ' + files[0].name;
                    extractBtn.disabled = false;
                }
            });
            
            // Form submission
            uploadForm.addEventListener('submit', async (e) => {
                e.preventDefault();
                
                const formData = new FormData();
                formData.append('file', pdfFile.files[0]);
                
                loading.style.display = 'block';
                result.style.display = 'none';
                extractBtn.disabled = true;
                
                try {
                    const response = await fetch('/extract', {
                        method: 'POST',
                        body: formData
                    });
                    
                    const data = await response.json();
                    
                    loading.style.display = 'none';
                    result.style.display = 'block';
                    
                    if (data.status === 'success') {
                        result.className = 'result';
                        result.innerHTML = `
                            <span class="badge success">✓ SUCCESS</span>
                            <h2>Extraction Complete!</h2>
                            
                            <div class="stats">
                                <div class="stat-card">
                                    <div class="stat-value">${data.rows}</div>
                                    <div class="stat-label">Rows Extracted</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${data.columns.length}</div>
                                    <div class="stat-label">Columns Found</div>
                                </div>
                                <div class="stat-card">
                                    <div class="stat-value">${data.method}</div>
                                    <div class="stat-label">Method Used</div>
                                </div>
                            </div>
                            
                            <h3 style="margin-top: 20px; color: #667eea;">Columns:</h3>
                            <p style="margin-bottom: 15px;">${data.columns.join(', ')}</p>
                            
                            <h3 style="margin-top: 20px; color: #667eea;">JSON Response:</h3>
                            <pre>${JSON.stringify(data, null, 2)}</pre>
                        `;
                    } else {
                        result.className = 'result error';
                        result.innerHTML = `
                            <span class="badge warning">⚠ NO TABLES FOUND</span>
                            <h2>No tables detected in this PDF</h2>
                            <p style="margin-top: 15px;">The PDF might not contain structured tables, or they might be in image format.</p>
                        `;
                    }
                    
                    extractBtn.disabled = false;
                    
                } catch (error) {
                    loading.style.display = 'none';
                    result.style.display = 'block';
                    result.className = 'result error';
                    result.innerHTML = `
                        <span class="badge" style="background: #f00;">✗ ERROR</span>
                        <h2>Extraction Failed</h2>
                        <p style="margin-top: 15px;">${error.message}</p>
                    `;
                    extractBtn.disabled = false;
                }
            });
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


@app.get("/health")
async def health_check():
    """Health check for Railway"""
    return {"status": "healthy"}


@app.get("/test-extract")
async def test_extract_pdf(pdf_path: str) -> Dict[str, Any]:
    """
    Test endpoint: Extract tables from a local PDF file (for local testing only)
    
    Args:
        pdf_path: Full path to PDF file on your local system
        
    Example:
        http://127.0.0.1:8000/test-extract?pdf_path=C:/Users/YourName/Desktop/sample.pdf
        
    Returns:
        JSON object containing extracted table data
    """
    
    # Validate file exists
    if not os.path.exists(pdf_path):
        raise HTTPException(
            status_code=404,
            detail=f"File not found: {pdf_path}"
        )
    
    # Validate file type
    if not pdf_path.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please provide a PDF file."
        )
    
    try:
        # Try extraction with tabula-py first
        try:
            tables = tabula.read_pdf(
                pdf_path,
                pages="all",
                lattice=True,
                multiple_tables=True,
                silent=True
            )
            
            if tables and len(tables) > 0:
                df = pd.concat(tables, ignore_index=True)
                df = df.fillna("")
                
                return {
                    "status": "success",
                    "method": "tabula",
                    "file": pdf_path,
                    "rows": len(df),
                    "columns": df.columns.tolist(),
                    "data": df.to_dict(orient="records")
                }
        except Exception as tabula_error:
            print(f"Tabula extraction failed: {tabula_error}")
            
            # Fallback to pdfplumber
            try:
                all_tables = []
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        if tables:
                            for table in tables:
                                all_tables.extend(table)
                
                if all_tables:
                    df = pd.DataFrame(all_tables[1:], columns=all_tables[0])
                    df = df.fillna("")
                    
                    return {
                        "status": "success",
                        "method": "pdfplumber",
                        "file": pdf_path,
                        "rows": len(df),
                        "columns": df.columns.tolist(),
                        "data": df.to_dict(orient="records")
                    }
            except Exception as pdfplumber_error:
                print(f"PDFPlumber extraction failed: {pdfplumber_error}")
        
        return {
            "status": "no_tables",
            "file": pdf_path,
            "message": "No tables found in the PDF file"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )


@app.post("/extract")
async def extract_pdf(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Extract tables from uploaded PDF file
    
    Args:
        file: PDF file uploaded via multipart/form-data
        
    Returns:
        JSON object containing:
        - status: success or no_tables
        - rows: number of rows extracted
        - columns: list of column names
        - data: list of dictionaries with table data
    """
    
    # Validate file type
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. Please upload a PDF file."
        )
    
    # Create temporary file to save uploaded PDF
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            content = await file.read()
            tmp.write(content)
            pdf_path = tmp.name
        
        # Try extraction with tabula-py first (best for structured tables)
        try:
            tables = tabula.read_pdf(
                pdf_path,
                pages="all",
                lattice=True,
                multiple_tables=True,
                silent=True
            )
            
            if tables and len(tables) > 0:
                # Concatenate all tables
                df = pd.concat(tables, ignore_index=True)
                
                # Clean the data
                df = df.fillna("")
                
                return {
                    "status": "success",
                    "method": "tabula",
                    "rows": len(df),
                    "columns": df.columns.tolist(),
                    "data": df.to_dict(orient="records")
                }
        except Exception as tabula_error:
            print(f"Tabula extraction failed: {tabula_error}")
            
            # Fallback to pdfplumber
            try:
                all_tables = []
                with pdfplumber.open(pdf_path) as pdf:
                    for page in pdf.pages:
                        tables = page.extract_tables()
                        if tables:
                            for table in tables:
                                all_tables.extend(table)
                
                if all_tables:
                    # Convert to DataFrame
                    df = pd.DataFrame(all_tables[1:], columns=all_tables[0])
                    df = df.fillna("")
                    
                    return {
                        "status": "success",
                        "method": "pdfplumber",
                        "rows": len(df),
                        "columns": df.columns.tolist(),
                        "data": df.to_dict(orient="records")
                    }
            except Exception as pdfplumber_error:
                print(f"PDFPlumber extraction failed: {pdfplumber_error}")
        
        # If both methods fail, return no tables found
        return {
            "status": "no_tables",
            "message": "No tables found in the PDF file"
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error processing PDF: {str(e)}"
        )
    
    finally:
        # Clean up temporary file
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.unlink(pdf_path)


@app.post("/extract-tabula")
async def extract_with_tabula(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Extract tables using tabula-py only (for structured PDFs with clear table borders)
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            pdf_path = tmp.name
        
        tables = tabula.read_pdf(
            pdf_path,
            pages="all",
            lattice=True,
            multiple_tables=True,
            silent=True
        )
        
        if not tables:
            return {"status": "no_tables"}
        
        df = pd.concat(tables, ignore_index=True)
        df = df.fillna("")
        
        return {
            "status": "success",
            "rows": len(df),
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records")
        }
        
    finally:
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.unlink(pdf_path)


@app.post("/extract-pdfplumber")
async def extract_with_pdfplumber(file: UploadFile = File(...)) -> Dict[str, Any]:
    """
    Extract tables using pdfplumber only (for PDFs without clear borders)
    """
    if not file.filename.lower().endswith('.pdf'):
        raise HTTPException(status_code=400, detail="Invalid file type")
    
    try:
        with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp:
            tmp.write(await file.read())
            pdf_path = tmp.name
        
        all_tables = []
        with pdfplumber.open(pdf_path) as pdf:
            for page in pdf.pages:
                tables = page.extract_tables()
                if tables:
                    for table in tables:
                        all_tables.extend(table)
        
        if not all_tables:
            return {"status": "no_tables"}
        
        df = pd.DataFrame(all_tables[1:], columns=all_tables[0])
        df = df.fillna("")
        
        return {
            "status": "success",
            "rows": len(df),
            "columns": df.columns.tolist(),
            "data": df.to_dict(orient="records")
        }
        
    finally:
        if 'pdf_path' in locals() and os.path.exists(pdf_path):
            os.unlink(pdf_path)


@app.get("/db-status")
async def check_database_status():
    """Check MySQL database connection status"""
    connection = get_db_connection()
    if connection:
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT VERSION()")
            version = cursor.fetchone()
            cursor.close()
            connection.close()
            return {
                "status": "connected",
                "database": MYSQL_CONFIG['database'],
                "host": MYSQL_CONFIG['host'],
                "mysql_version": version[0] if version else "Unknown"
            }
        except Error as e:
            return {
                "status": "error",
                "message": str(e)
            }
    else:
        return {
            "status": "disconnected",
            "message": "Could not connect to MySQL. Please check your .env configuration."
        }


@app.post("/save-to-db")
async def save_extraction_to_db(
    filename: str,
    method: str,
    rows: int,
    columns: List[str],
    data: List[Dict[str, Any]]
):
    """
    Save extracted PDF data to MySQL database
    
    Args:
        filename: Name of the PDF file
        method: Extraction method used (tabula/pdfplumber)
        rows: Number of rows extracted
        columns: Column names
        data: Extracted data rows
    """
    connection = get_db_connection()
    if not connection:
        raise HTTPException(
            status_code=500,
            detail="Database connection failed. Please check MySQL configuration."
        )
    
    try:
        cursor = connection.cursor()
        
        # Insert into extraction_logs
        cursor.execute("""
            INSERT INTO extraction_logs 
            (filename, extraction_method, rows_count, columns_count, status)
            VALUES (%s, %s, %s, %s, %s)
        """, (filename, method, rows, len(columns), 'success'))
        
        log_id = cursor.lastrowid
        
        # Insert each row into extracted_data
        for row in data:
            cursor.execute("""
                INSERT INTO extracted_data (extraction_log_id, row_data)
                VALUES (%s, %s)
            """, (log_id, json.dumps(row)))
        
        connection.commit()
        cursor.close()
        connection.close()
        
        return {
            "status": "success",
            "message": f"Saved {rows} rows to database",
            "extraction_id": log_id
        }
        
    except Error as e:
        raise HTTPException(
            status_code=500,
            detail=f"Database error: {str(e)}"
        )


@app.get("/extractions")
async def get_all_extractions():
    """Get all extraction logs from database"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        cursor.execute("""
            SELECT id, filename, extraction_method, rows_count, 
                   columns_count, extracted_at, status
            FROM extraction_logs
            ORDER BY extracted_at DESC
        """)
        
        extractions = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # Convert datetime to string for JSON serialization
        for extraction in extractions:
            if extraction.get('extracted_at'):
                extraction['extracted_at'] = extraction['extracted_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return {"extractions": extractions}
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/extraction/{extraction_id}")
async def get_extraction_data(extraction_id: int):
    """Get specific extraction data by ID"""
    connection = get_db_connection()
    if not connection:
        raise HTTPException(status_code=500, detail="Database connection failed")
    
    try:
        cursor = connection.cursor(dictionary=True)
        
        # Get extraction log
        cursor.execute("""
            SELECT * FROM extraction_logs WHERE id = %s
        """, (extraction_id,))
        log = cursor.fetchone()
        
        if not log:
            raise HTTPException(status_code=404, detail="Extraction not found")
        
        # Get extraction data
        cursor.execute("""
            SELECT row_data FROM extracted_data 
            WHERE extraction_log_id = %s
        """, (extraction_id,))
        
        rows = cursor.fetchall()
        cursor.close()
        connection.close()
        
        # Parse JSON data
        data = [json.loads(row['row_data']) for row in rows]
        
        # Convert datetime
        if log.get('extracted_at'):
            log['extracted_at'] = log['extracted_at'].strftime('%Y-%m-%d %H:%M:%S')
        
        return {
            "log": log,
            "data": data
        }
        
    except Error as e:
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@app.get("/view-extractions", response_class=HTMLResponse)
async def view_extractions_ui():
    """UI to view all saved extractions"""
    html_content = """
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>View Saved Extractions</title>
        <style>
            * {
                margin: 0;
                padding: 0;
                box-sizing: border-box;
            }
            
            body {
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                min-height: 100vh;
                padding: 20px;
            }
            
            .container {
                max-width: 1400px;
                margin: 0 auto;
                background: white;
                border-radius: 20px;
                padding: 40px;
                box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
            }
            
            h1 {
                color: #667eea;
                margin-bottom: 30px;
                font-size: 2em;
            }
            
            .nav {
                margin-bottom: 30px;
            }
            
            .nav a {
                display: inline-block;
                background: #667eea;
                color: white;
                padding: 10px 20px;
                border-radius: 8px;
                text-decoration: none;
                margin-right: 10px;
                transition: transform 0.2s;
            }
            
            .nav a:hover {
                transform: translateY(-2px);
                background: #764ba2;
            }
            
            .extractions-list {
                margin-bottom: 30px;
            }
            
            .extraction-card {
                background: #f8f9ff;
                border-radius: 10px;
                padding: 20px;
                margin-bottom: 15px;
                cursor: pointer;
                transition: all 0.3s;
                border-left: 5px solid #667eea;
            }
            
            .extraction-card:hover {
                transform: translateX(5px);
                box-shadow: 0 4px 15px rgba(102, 126, 234, 0.3);
            }
            
            .extraction-card h3 {
                color: #667eea;
                margin-bottom: 10px;
            }
            
            .extraction-meta {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 10px;
                color: #666;
                font-size: 0.9em;
            }
            
            .data-view {
                display: none;
                margin-top: 20px;
            }
            
            .table-container {
                overflow-x: auto;
                margin-top: 20px;
            }
            
            table {
                width: 100%;
                border-collapse: collapse;
                background: white;
                border-radius: 8px;
                overflow: hidden;
            }
            
            th {
                background: #667eea;
                color: white;
                padding: 12px;
                text-align: left;
                font-weight: 600;
            }
            
            td {
                padding: 10px 12px;
                border-bottom: 1px solid #eee;
            }
            
            tr:hover {
                background: #f8f9ff;
            }
            
            .badge {
                display: inline-block;
                background: #10b981;
                color: white;
                padding: 4px 12px;
                border-radius: 12px;
                font-size: 0.8em;
                font-weight: 600;
                }
            
            .loading {
                text-align: center;
                padding: 40px;
            }
            
            .spinner {
                border: 4px solid #f3f3f3;
                border-top: 4px solid #667eea;
                border-radius: 50%;
                width: 40px;
                height: 40px;
                animation: spin 1s linear infinite;
                margin: 0 auto;
            }
            
            @keyframes spin {
                0% { transform: rotate(0deg); }
                100% { transform: rotate(360deg); }
            }
            
            .empty {
                text-align: center;
                padding: 60px;
                color: #999;
            }
            
            .stats {
                display: grid;
                grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
                gap: 20px;
                margin-bottom: 30px;
            }
            
            .stat-card {
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 25px;
                border-radius: 15px;
                text-align: center;
            }
            
            .stat-value {
                font-size: 2.5em;
                font-weight: bold;
                margin-bottom: 5px;
            }
            
            .stat-label {
                font-size: 0.9em;
                opacity: 0.9;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="nav">
                <a href="/ui">← Upload PDF</a>
                <a href="/db-status">Database Status</a>
            </div>
            
            <h1>📊 Saved PDF Extractions</h1>
            
            <div class="stats" id="stats"></div>
            
            <div class="extractions-list" id="extractionsList">
                <div class="loading">
                    <div class="spinner"></div>
                    <p>Loading extractions...</p>
                </div>
            </div>
            
            <div class="data-view" id="dataView"></div>
        </div>
        
        <script>
            async function loadExtractions() {
                try {
                    const response = await fetch('/extractions');
                    const result = await response.json();
                    
                    const listContainer = document.getElementById('extractionsList');
                    const statsContainer = document.getElementById('stats');
                    
                    if (result.extractions.length === 0) {
                        listContainer.innerHTML = '<div class="empty">No extractions found. Upload a PDF to get started!</div>';
                        return;
                    }
                    
                    // Show stats
                    const totalRows = result.extractions.reduce((sum, e) => sum + e.rows_count, 0);
                    statsContainer.innerHTML = `
                        <div class="stat-card">
                            <div class="stat-value">${result.extractions.length}</div>
                            <div class="stat-label">Total Extractions</div>
                        </div>
                        <div class="stat-card">
                            <div class="stat-value">${totalRows}</div>
                            <div class="stat-label">Total Rows Extracted</div>
                        </div>
                    `;
                    
                    // Show extractions
                    listContainer.innerHTML = result.extractions.map(ext => `
                        <div class="extraction-card" onclick="viewExtraction(${ext.id})">
                            <h3>📄 ${ext.filename}</h3>
                            <div class="extraction-meta">
                                <div><strong>Method:</strong> ${ext.extraction_method}</div>
                                <div><strong>Rows:</strong> ${ext.rows_count}</div>
                                <div><strong>Columns:</strong> ${ext.columns_count}</div>
                                <div><strong>Date:</strong> ${ext.extracted_at}</div>
                                <div><span class="badge">${ext.status}</span></div>
                            </div>
                        </div>
                    `).join('');
                    
                } catch (error) {
                    document.getElementById('extractionsList').innerHTML = 
                        '<div class="empty">Error loading extractions: ' + error.message + '</div>';
                }
            }
            
            async function viewExtraction(id) {
                const dataView = document.getElementById('dataView');
                dataView.innerHTML = '<div class="loading"><div class="spinner"></div><p>Loading data...</p></div>';
                dataView.style.display = 'block';
                
                try {
                    const response = await fetch(`/extraction/${id}`);
                    const result = await response.json();
                    
                    if (result.data.length === 0) {
                        dataView.innerHTML = '<div class="empty">No data found</div>';
                        return;
                    }
                    
                    // Get column names
                    const columns = Object.keys(result.data[0]);
                    
                    // Build table
                    const tableHTML = `
                        <h2>Extraction Details  for: ${result.log.filename}</h2>
                        <p style="margin: 10px 0; color: #666;">
                            Extracted on: ${result.log.extracted_at} | 
                            Method: ${result.log.extraction_method} | 
                            Rows: ${result.log.rows_count}
                        </p>
                        <div class="table-container">
                            <table>
                                <thead>
                                    <tr>
                                        ${columns.map(col => `<th>${col}</th>`).join('')}
                                    </tr>
                                </thead>
                                <tbody>
                                    ${result.data.map(row => `
                                        <tr>
                                            ${columns.map(col => `<td>${row[col] || ''}</td>`).join('')}
                                        </tr>
                                    `).join('')}
                                </tbody>
                            </table>
                        </div>
                    `;
                    
                    dataView.innerHTML = tableHTML;
                    dataView.scrollIntoView({ behavior: 'smooth' });
                    
                } catch (error) {
                    dataView.innerHTML = '<div class="empty">Error loading data: ' + error.message + '</div>';
                }
            }
            
            // Load on page load
            loadExtractions();
        </script>
    </body>
    </html>
    """
    return HTMLResponse(content=html_content)


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
