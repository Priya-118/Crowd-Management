
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

##Detection Data Interface
The Person Detection module produces detection data for the Tracking module.

Current Detection Output
CSV file: frame,x1,y1,x2,y2,confidence

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
