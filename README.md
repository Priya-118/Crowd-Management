
# Crowd Management

Crowd Detection, Prevention and Management Platform

## Project Overview

A computer-vision-based platform for detecting, tracking, predicting,
and managing crowd situations from video/CCTV input.

## Project Pipeline

Video Input
→ Person Detection
→ Person Tracking
→ Crowd Density Representation
→ Future Crowd Prediction
→ Risk Assessment
→ Prevention & Management

## Detection Data Interface

The Person Detection module produces detection data for the Tracking module.

### Current Detection Output

CSV file:
frame,x1,y1,x2,y2,confidence

## Module Responsibilities

### 1. Person Detection
- Detect people in each video frame using YOLOv5.
- Generate bounding boxes and confidence scores.
- Calculate the number of detected people per frame.
- Output detection data for the tracking module.

**Input:**
- CCTV/video footage

**Output:**
- Person bounding boxes
- Confidence scores
- Person count per frame
- Detection data for the tracking module

### 2. Person Tracking & Crowd Representation
- Take person detections from the detection module.
- Assign persistent IDs to detected people using ByteTrack.
- Track movement/trajectories across frames.
- Generate crowd counts and spatial density information.

**Input:**
- Person detections from Person Detection

**Output:**
- Persistent person IDs
- Trajectories
- Crowd counts
- Density representation/maps

### 3. Future Crowd Prediction
- Use historical crowd-density information.
- Train an Encoder–Decoder ConvLSTM model.
- Predict future crowd-density states/maps.

**Input:**
- Crowd-density sequences from the tracking/representation module

**Output:**
- Predicted future crowd density

### 4. Risk Assessment & Management
- Use current and predicted crowd information.
- Identify potentially risky crowd conditions.
- Provide alerts and management information through the platform.

**Input:**
- Current crowd information
- Predicted crowd information

**Output:**
- Risk assessment
- Alerts
- Management information

## Integration Flow

Person Detection
→ Person Tracking
→ Crowd Density Representation
→ Future Crowd Prediction
→ Risk Assessment
→ Management Platform

Each module should have a clearly defined input and output so that
the modules can be developed independently and integrated later.

## Development

Each team member should work on a separate Git branch.

Example:

- `priya-person-detection`
- `member2-tracking`
- `member3-crowd-prediction`
- `member4-management`

Changes should be merged into `main` after review.

## Data

Large video files, generated outputs, model weights, virtual
environments, and other large/generated files should not be committed
to the repository.

Use `.gitignore` for these files.

---

## Member 4 — Backend, Risk Assessment, Dashboard, and Integration

### Backend API Architecture (FastAPI & SQLite)

The backend provides REST APIs for video upload, CSV detection testing, ByteTrack tracking, 4-zone crowd distribution, movement & flow metrics, and 2D spatial density heatmaps.

### Directory Structure

```
backend/
  app/
    __init__.py
    main.py              # FastAPI app and middleware
    config.py            # Storage, CORS, and path security
    database.py          # SQLite engine and session management
    models.py            # SQLAlchemy models (Run, FrameMetric, ZoneMetric)
    schemas.py           # Pydantic validation schemas
    routes/
      health.py          # GET /api/health
      runs.py            # Runs, uploads, metrics, heatmap, video endpoints
    services/
      run_service.py     # Upload and run lifecycle management
      pipeline_service.py# Tracking & analytics adapter
      metrics_service.py # Aggregated & time-series crowd statistics
      heatmap_service.py # 2D Gaussian density estimation & heatmap PNG
  tests/                 # Automated test suite
```

### Exact Windows Commands

1. **Activate Environment & Install Dependencies**:
   ```powershell
   py -m pip install -r requirements.txt
   ```

2. **Start Backend Server**:
   ```powershell
   py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
   ```

3. **Open Interactive Swagger API Documentation**:
   Navigate in browser to:
   [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs)

4. **Run Automated Test Suite**:
   ```powershell
   py -m pytest backend/tests -v
   ```

### API Endpoints Reference

| Method | Endpoint | Description |
| :--- | :--- | :--- |
| `GET` | `/api/health` | API and database operational status |
| `POST` | `/api/runs/upload` | Upload recorded crowd video |
| `POST` | `/api/runs/test-csv` | Upload detection CSV or use repository sample |
| `POST` | `/api/runs/{run_id}/process` | Trigger ByteTrack tracking & analytics pipeline |
| `GET` | `/api/runs` | List processed video and CSV runs |
| `GET` | `/api/runs/{run_id}` | Retrieve specific run status & metadata |
| `GET` | `/api/runs/{run_id}/metrics` | Aggregated crowd counts, peak counts, zone distribution |
| `GET` | `/api/runs/{run_id}/timeseries` | Frame-by-frame time-series crowd & flow data |
| `GET` | `/api/runs/{run_id}/heatmap` | 2D Gaussian spatial crowd density grid & hotspots |
| `GET` | `/api/runs/{run_id}/heatmap/image` | Stream crowd density heatmap PNG image |
| `GET` | `/api/runs/{run_id}/video` | Stream annotated video |
| `DELETE` | `/api/runs/{run_id}` | Safely delete run, DB records, and stored files |

---

### Frontend Web Dashboard (React + Vite + Tailwind CSS)

The frontend provides an interactive single-page dashboard with a dark navy sidebar, responsive workspace, real-time KPI cards, Recharts time-series trends, 4-zone distribution, and 2D spatial density heatmaps.

#### Directory Structure

```
frontend/
  src/
    components/
      Sidebar.jsx          # Dark navy navigation with quick sample test action
      Topbar.jsx           # Top header with backend health status & active run badge
      StatCard.jsx         # KPI cards (crowd count, tracks, peak, movement %)
      ZoneDistribution.jsx # 4-Zone quadrant scene distribution (Zone A, B, C, D)
      CrowdTrendChart.jsx  # Recharts time-series chart (occupancy & zone breakdown)
      FlowMetricsChart.jsx # Recharts inflow vs outflow bar chart
      HeatmapPanel.jsx     # 2D Gaussian density image overlay & density matrix
      VideoUploader.jsx    # Drag-and-drop video/CSV uploader with progress
      RunHistory.jsx       # Run history table with status filters & actions
      VideoPlayerPanel.jsx # Media player & detection coordinate schema inspector
    services/
      api.js               # Axios API client configured for VITE_API_BASE_URL
    App.jsx                # Main dashboard application with view routing
    index.css              # Tailwind base & custom scrollbar styles
    main.jsx               # React DOM entry point
  tailwind.config.js       # Custom navy & teal brand color palette
  vite.config.js           # Vite build & development server config
  .env.example             # VITE_API_BASE_URL=http://127.0.0.1:8000
```

#### Running Frontend and Backend in Separate Terminals

**Terminal 1 — Backend API Server:**
```powershell
py -m uvicorn backend.app.main:app --host 127.0.0.1 --port 8000 --reload
```

**Terminal 2 — Frontend Dashboard:**
```powershell
cd frontend
npm install
npm run dev
```
Open **[http://localhost:5173](http://localhost:5173)** in your browser to access the dashboard.

