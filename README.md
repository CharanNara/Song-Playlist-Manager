# Song Playlist Manager (Full Stack Take-Home)

A minimal full-stack application that ingests a **column-oriented JSON playlist dataset**, normalizes it into row-based song records, stores it in **SQLite**, and exposes a **FastAPI** backend consumed by a **React (Vite)** frontend dashboard.

This project implements the required features from the take-home prompt: data normalization, backend APIs (with pagination + sorting), frontend table view with pagination/sorting/search, CSV export, and star ratings. 

---

## What I Built

### Backend (FastAPI + SQLite)
- Accepts an uploaded JSON playlist file (column-oriented maps)
- Normalizes it into a row-based structure (one row per song)
- Stores records in a SQLite table `songs` (`songs.db`)
- Provides REST APIs for:
  - Fetch all songs **with pagination**
  - Search songs by **partial title match (case-insensitive LIKE search)** with bounded results
  - Update a song’s **star rating (1–5)**
  - Export all songs to **CSV** (handles commas/quotes/newlines safely)

### Frontend (React + Vite)
- Upload JSON file to load dataset
- Table renders songs with:
  - Pagination (10 rows per page)
  - Sortable columns (toggle asc/desc)
  - Search by title (Get Song)
  - Star rating UI (1–5 stars)
  - Download CSV button

### Testing
- **Backend tests (pytest)** cover:
  - JSON loading & normalization edge cases
  - Pagination and sorting
  - Search behavior (case-insensitive, partial match, multi-result responses)
  - Rating validation
  - CSV export + special character handling
- **Frontend tests (Vitest + Testing Library)** cover:
  - Basic UI rendering
  - Search interactions + messages
  - Rendering loaded songs
  - Export flow (mocked)

---

## Tech Stack

**Backend**
- FastAPI
- SQLite (via `sqlite3`)
- Pytest (unit tests)

**Frontend**
- React (Vite)
- Vitest + @testing-library/react

---

## Project Structure

VIVPRO_ASSIGNMENT_TAKEHOME/
- backend/
    - main.py
    - requirements.txt
    - test_main.py
    - songs.db # created at runtime
- frontend/
    - src/
        - App.jsx
        - App.css
        - App.test.jsx
        - main.jsx


---

## Features Implemented (Mapped to Requirements)


### ✅ 1.1 Data Processing
- Input JSON is **column-oriented** (each field is a map of `"index" -> value`)
- Backend normalizes it into rows and stores in SQLite

### ✅ 1.2 Backend APIs
- **GET all items**: `/api/songs` (with pagination + sorting)
- **GET by title**: `/api/songs/search?title=...` (case-insensitive partial match (LIKE) returns multiple results with configurable limit)
- **Rate a song**: `/api/songs/{song_id}/rating` (1–5)
- **Bonus**: Unit tests included (pytest)

### ✅ 1.3 Frontend Dashboard
- On load: fetches `/api/songs`
- Table view with:
  - Pagination (10 rows/page)
  - Sort columns (asc/desc toggle)
  - Search by title (Get Song)
  - Star rating column
  - CSV download button
- **Bonus**: Frontend unit tests included (Vitest)

---

# How to Run (Local)

## 1) Backend Setup & Run
cd backend

### create venv (optional but recommended)
python -m venv venv
source venv/bin/activate   # mac/linux
pip install -r requirements.txt

### run server
python main.py

OR 

uvicorn main:app --reload --host 0.0.0.0 --port 8000 

**Backend runs at:**
http://localhost:8000


## 2) Frontend Setup & Run
cd frontend
npm install
npm run dev

**Frontend runs at:**
http://localhost:5173


## Using the App
1. Start backend + frontend
2. Upload the provided playlist JSON file via the file input
3. Browse songs in the table (10 rows at a time)
4. Click column headers to sort
5. Search by title and click Search (or press Enter)
6. Click stars to rate a song
7. Click Download CSV to export all songs


## API Reference (Backend)

Base URL: http://localhost:8000/api

### Load Dataset
POST /load-data
-   form-data: file=<playlist.json>

### Get Songs (Paginated + Sortable)
GET /songs?page=1&limit=10&sort_by=title&sort_order=asc

**Params:**
- page (default 1)
- limit (default 10)
- sort_by (default title)
- sort_order (asc or desc)

### Search By Title (Partial Match, Case-Insensitive)
GET /songs/search?title=3AM&limit=10

Returns:
{
  "count": <number_of_matches>,
  "songs": [ { ...song }, ... ]
}

### Update Rating
PUT /songs/{song_id}/rating

### Export CSV
GET /songs/export
Downloads songs.csv


## Running Tests

### Backend Tests (pytest)
cd backend
pytest -v

### Frontend Tests (Vitest)
cd frontend
npm run test


## Notes / Design Choices
- SQLite is used for simplicity and portability (no external DB required).
- CSV export uses safe quoting to correctly handle commas, quotes, and newline characters in song titles.
- Sorting is supported through query parameters and applied at the DB query level.
- Rating is validated using Pydantic (0–5, UI uses 1–5).


## BONUS GRAPHS
1.3.8 Build a scatter chart for the songs using danceability value.
![alt text](https://github.com/CharanNara/Song-Playlist-Manager/blob/main/backend/graphs/scatter_danceable.png)

1.3.9 Build a histogram using song duration values (in seconds).
![alt text](https://github.com/CharanNara/Song-Playlist-Manager/blob/main/backend/graphs/histogram_duration.png)

1.3.10 Build bar charts for the acoustics and tempo value
![alt text](https://github.com/CharanNara/Song-Playlist-Manager/blob/main/backend/graphs/bar_acoust_tempo.png)



