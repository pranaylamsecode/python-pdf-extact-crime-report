from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse
import tabula
import pdfplumber
import pandas as pd
import tempfile
import os
from typing import Dict, Any

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


@app.get("/health")
async def health_check():
    """Health check for Railway"""
    return {"status": "healthy"}


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


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 10000))
    uvicorn.run(app, host="0.0.0.0", port=port)
