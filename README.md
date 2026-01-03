# PDF Table Extractor API

A FastAPI service that extracts tables from PDF files using tabula-py and pdfplumber. Designed for easy deployment on Railway.

## 🚀 Features

- **Multiple Extraction Methods**: Uses tabula-py for structured tables with lattice detection and pdfplumber as fallback
- **RESTful API**: Simple POST endpoint for PDF file uploads
- **Structured JSON Output**: Returns clean, structured data ready for database insertion
- **Railway Ready**: Pre-configured for one-click Railway deployment
- **Health Checks**: Built-in health check endpoints for monitoring

## 📋 Prerequisites

### For Local Development
- Python 3.11+
- Java 17+ (required for tabula-py)

### For Railway Deployment
- GitHub account
- Railway account (free tier available)

## 🛠️ Local Setup

### 1. Clone the repository
```bash
git clone <your-repo-url>
cd python-pdf-extact-crime-report
```

### 2. Create virtual environment
```bash
python -m venv venv

# Windows
venv\Scripts\activate

# macOS/Linux
source venv/bin/activate
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Verify Java installation
```bash
java -version
```
If Java is not installed, download from [Oracle JDK](https://www.oracle.com/java/technologies/downloads/) or [OpenJDK](https://openjdk.org/).

### 5. Run the server
```bash
uvicorn main:app --reload
```

Server will start at `http://localhost:8000`

## 🌐 Railway Deployment

### Step 1: Push to GitHub
```bash
git init
git add .
git commit -m "Initial commit: PDF extractor API"
git branch -M main
git remote add origin <your-github-repo-url>
git push -u origin main
```

### Step 2: Deploy on Railway

1. Go to [railway.app](https://railway.app)
2. Click **New Project**
3. Select **Deploy from GitHub repo**
4. Choose your repository
5. Railway will automatically detect the configuration and deploy

**Deployment time**: ~5-7 minutes

### Step 3: Access your API

After deployment, Railway will provide a URL like:
```
https://your-app.up.railway.app
```

## 📡 API Endpoints

### 1. Health Check
```bash
GET /health
```

**Response:**
```json
{
  "status": "healthy"
}
```

---

### 2. Extract Tables (Auto - Recommended)
```bash
POST /extract
```

Tries tabula-py first, falls back to pdfplumber if needed.

**Request:**
- Method: `POST`
- Content-Type: `multipart/form-data`
- Body: PDF file with key `file`

**Example using curl:**
```bash
curl -X POST https://your-app.up.railway.app/extract \
  -F "file=@nagpur_rural.pdf"
```

**Success Response:**
```json
{
  "status": "success",
  "method": "tabula",
  "rows": 998,
  "columns": ["Crime", "2023_Reg", "2023_Det", "2024_Reg", "2024_Det"],
  "data": [
    {
      "Crime": "Murder",
      "2023_Reg": "58",
      "2023_Det": "56",
      "2024_Reg": "62",
      "2024_Det": "58"
    },
    {
      "Crime": "Attempt to Murder",
      "2023_Reg": "45",
      "2023_Det": "42",
      "2024_Reg": "48",
      "2024_Det": "45"
    }
  ]
}
```

**No Tables Response:**
```json
{
  "status": "no_tables",
  "message": "No tables found in the PDF file"
}
```

---

### 3. Extract with Tabula Only
```bash
POST /extract-tabula
```

Uses only tabula-py (best for PDFs with clear table borders).

---

### 4. Extract with PDFPlumber Only
```bash
POST /extract-pdfplumber
```

Uses only pdfplumber (best for PDFs without clear borders).

## 🔗 Laravel Integration

### Laravel Example
```php
<?php

use Illuminate\Support\Facades\Http;
use Illuminate\Support\Facades\Storage;

class PdfExtractorService
{
    protected $apiUrl;

    public function __construct()
    {
        $this->apiUrl = env('PDF_EXTRACTOR_API_URL', 'https://your-app.up.railway.app');
    }

    public function extractTables($pdfPath)
    {
        $response = Http::attach(
            'file',
            fopen($pdfPath, 'r'),
            basename($pdfPath)
        )->post("{$this->apiUrl}/extract");

        if ($response->successful()) {
            return $response->json();
        }

        throw new \Exception('PDF extraction failed: ' . $response->body());
    }

    public function extractAndStore($pdfPath, $model)
    {
        $result = $this->extractTables($pdfPath);

        if ($result['status'] === 'success') {
            foreach ($result['data'] as $row) {
                $model::create($row);
            }
            
            return [
                'success' => true,
                'rows_imported' => $result['rows']
            ];
        }

        return [
            'success' => false,
            'message' => 'No tables found'
        ];
    }
}
```

### .env Configuration
```env
PDF_EXTRACTOR_API_URL=https://your-app.up.railway.app
```

### Controller Example
```php
<?php

namespace App\Http\Controllers;

use Illuminate\Http\Request;
use App\Services\PdfExtractorService;

class CrimeReportController extends Controller
{
    protected $extractor;

    public function __construct(PdfExtractorService $extractor)
    {
        $this->extractor = $extractor;
    }

    public function upload(Request $request)
    {
        $request->validate([
            'pdf_file' => 'required|file|mimes:pdf|max:10240'
        ]);

        $path = $request->file('pdf_file')->getRealPath();
        
        try {
            $result = $this->extractor->extractTables($path);
            
            return response()->json([
                'success' => true,
                'data' => $result
            ]);
            
        } catch (\Exception $e) {
            return response()->json([
                'success' => false,
                'message' => $e->getMessage()
            ], 500);
        }
    }
}
```

## 🧪 Testing

### Using Postman

1. Create new POST request
2. URL: `https://your-app.up.railway.app/extract`
3. Body → form-data
4. Key: `file` (type: File)
5. Value: Select your PDF file
6. Click **Send**

### Using Python
```python
import requests

url = "https://your-app.up.railway.app/extract"
files = {'file': open('nagpur_rural.pdf', 'rb')}

response = requests.post(url, files=files)
print(response.json())
```

## 🔧 Configuration

### Environment Variables (Railway)

Railway automatically sets:
- `PORT`: Application port (default: 8080)

No additional environment variables needed!

## 📊 Response Format

All successful extractions return:

```typescript
{
  status: "success" | "no_tables",
  method?: "tabula" | "pdfplumber",  // Only on success
  rows?: number,                      // Only on success
  columns?: string[],                 // Only on success
  data?: Array<Record<string, any>>,  // Only on success
  message?: string                    // Only on no_tables
}
```

## ❗ Troubleshooting

### Local Development

**Error: Java not found**
- Install Java 17+: [Download here](https://www.oracle.com/java/technologies/downloads/)
- Verify: `java -version`

**Error: Module not found**
- Ensure virtual environment is activated
- Run: `pip install -r requirements.txt`

### Railway Deployment

**Build fails**
- Check Railway build logs
- Ensure `nixpacks.toml` includes `openjdk17`

**Health check fails**
- Verify `/health` endpoint works locally
- Check Railway logs for startup errors

**No tables extracted**
- Try the specific endpoints: `/extract-tabula` or `/extract-pdfplumber`
- Verify your PDF has actual tables (not scanned images)

## 📈 Monitoring

Railway provides:
- Build logs
- Runtime logs
- Metrics dashboard
- Health check monitoring

Access via Railway dashboard → Your Project → Deployments

## 💰 Cost

**Railway Free Tier:**
- $5 monthly credit
- ~500 hours of runtime
- Sufficient for testing and small projects

Monitor usage in Railway dashboard.

## 📝 License

MIT License - Feel free to use for any project!

## 🤝 Contributing

Contributions welcome! Feel free to submit issues and pull requests.

---

**Built with ❤️ using FastAPI, tabula-py, and pdfplumber**
