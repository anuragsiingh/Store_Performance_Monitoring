# Project Structure
*  FastAPI backend: Provides APIs to trigger and download reports.

* Background task: Generates the report asynchronously.

* SQLAlchemy ORM: Handles database operations.

* ReportTracker Table: Tracks report status (pending, completed, etc.).

* CSV Files: Final generated reports stored on server disk.


# How it Works
1. User triggers report generation (POST /trigger_report) and return report_id.
2. Create a new report_id.csv file in /reports.
3. Using that report_id hit (/get_report).
4. A new report entry is created in the database.
5. Finally by hitting (/download/{report_id}) we will get the report and download it with link.
<!-- 4. A background task is started to generate the report asynchronously. -->

<!-- The system polls the database until the report is ready (up to a timeout). -->

<!-- If ready: the report file is returned.

If not ready in time: API times out (HTTP 408). -->


# API Endpoints
### POST /trigger_report

* Trigger report generation and returns a unique report id
* Content-Type: application/json

### GET /get_report

* collects the info of the particular restaurant associated to that report_id.
* Creates a {report_id}.csv in report folder containing all the info.

### GET /download/{report_id}

* Creates a link to download the csv
<!-- Response (if report ready within timeout):

HTTP 200 OK with report CSV file download.

Response (if report not ready within timeout):

HTTP 408 Request Timeout.
 -->




# Setup Instructions
### 1. Clone the repo:
```bash
git clone https://github.com/Abhijeet002/Abhijeet_28Apr.git
cd Abhijeet_28Apr
```


### 2. Install dependencies:
```bash
pip install -r requirements.txt
```

### 3. Start FastAPI server:
```bash
uvicorn main:app --reload
```

### 4. Access API Docs: Open browser at:
http://127.0.0.1:8000/docs


#### Author: Abhijeet Sachan