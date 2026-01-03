from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import sqlite3
import json
import csv
import io
import math

app = FastAPI()


app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)



# Database setup
def get_db():
    conn = sqlite3.connect('songs.db', check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS songs (
            id TEXT PRIMARY KEY,
            title TEXT NOT NULL,
            danceability REAL,
            energy REAL,
            key INTEGER,
            loudness REAL,
            mode INTEGER,
            acousticness REAL,
            instrumentalness REAL,
            liveness REAL,
            valence REAL,
            tempo REAL,
            duration_ms INTEGER,
            time_signature INTEGER,
            num_bars INTEGER,
            num_sections INTEGER,
            num_segments INTEGER,
            class INTEGER,
            rating INTEGER DEFAULT 0
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# Models
class UpdateRating(BaseModel):
    rating: int = Field(ge=0, le=5)

# Endpoints
@app.post("/api/load-data")
async def load_data(file: UploadFile = File(...)):
    try:
        contents = await file.read()
        data = json.loads(contents)
        
        # Normalize JSON
        first_key = list(data.keys())[0]
        num_records = len(data[first_key])
        
        records = []
        for i in range(num_records):
            record = []
            
            # Handle 'id' - ensure it's a string
            id_val = data.get('id', {}).get(str(i))
            record.append(str(id_val) if id_val is not None else f"song_{i}")
            
            # Handle 'title' - clean and ensure it's a string
            title_val = data.get('title', {}).get(str(i))
            if title_val is None:
                title_val = f"Untitled {i}"
            # Convert to string and handle special characters
            title_str = str(title_val)
            # Replace multiple whitespace/newlines with single space
            title_str = ' '.join(title_str.split())
            record.append(title_str)
            
            # Handle numeric fields with proper type conversion
            numeric_fields = [
                'danceability', 'energy', 'loudness', 'acousticness',
                'instrumentalness', 'liveness', 'valence', 'tempo'
            ]
            for field in numeric_fields:
                val = data.get(field, {}).get(str(i))
                try:
                    record.append(float(val) if val is not None else 0.0)
                except (ValueError, TypeError):
                    record.append(0.0)
            
            # Handle integer fields
            integer_fields = [
                'key', 'mode', 'duration_ms', 'time_signature',
                'num_bars', 'num_sections', 'num_segments', 'class'
            ]
            for field in integer_fields:
                val = data.get(field, {}).get(str(i))
                try:
                    record.append(int(val) if val is not None else 0)
                except (ValueError, TypeError):
                    record.append(0)
            
            record.append(0)  # rating
            records.append(tuple(record))
        
        # Insert into DB
        conn = get_db()
        conn.execute('DELETE FROM songs')
        conn.executemany('''
            INSERT INTO songs VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
        ''', records)
        conn.commit()
        conn.close()
        
        return {"message": "Data loaded", "songs_loaded": len(records)}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


ALLOWED_SORT_COLUMNS = {
    "id", "title", "danceability", "energy", "key", "loudness", "mode",
    "acousticness", "instrumentalness", "liveness", "valence", "tempo",
    "duration_ms", "time_signature", "num_bars", "num_sections",
    "num_segments", "class", "rating",
}


@app.get("/api/songs")
def get_songs(
    page: int = 1,
    limit: int = 10,
    sort_by: str = "title",
    sort_order: str = "asc"
):
    
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise HTTPException(status_code=400, detail="Invalid sort_by column")

    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid sort_order")
    
    conn = get_db()
    
    # Get total
    total = conn.execute('SELECT COUNT(*) FROM songs').fetchone()[0]
    
    # Get paginated data
    offset = (page - 1) * limit
    query = f'SELECT * FROM songs ORDER BY {sort_by} {sort_order.upper()} LIMIT ? OFFSET ?'
    rows = conn.execute(query, (limit, offset)).fetchall()
    
    songs = [dict(row) for row in rows]
    conn.close()
    
    return {
        "songs": songs,
        "total": total,
        "page": page,
        "limit": limit,
        "total_pages": math.ceil(total / limit) if total > 0 else 0
    }

@app.get("/api/songs/search")
def search_song(
    title: str = Query(..., min_length=1),
    limit: int = Query(10, ge=1, le=100)
):
    conn = get_db()  # must have row_factory = sqlite3.Row
    pattern = f"%{title.strip().lower()}%"

    rows = conn.execute(
        """
        SELECT *
        FROM songs
        WHERE LOWER(title) LIKE ?
        ORDER BY title
        LIMIT ?
        """,
        (pattern, limit)
    ).fetchall()

    conn.close()

    # rows is a list of sqlite3.Row objects -> dict(row) works
    songs = [dict(r) for r in rows]

    return {"count": len(songs), "songs": songs}


@app.put("/api/songs/{song_id}/rating")
def update_rating(song_id: str, request: UpdateRating):
    conn = get_db()
    conn.execute('UPDATE songs SET rating = ? WHERE id = ?', (request.rating, song_id))
    conn.commit()
    changed = conn.total_changes
    conn.close()
    
    if changed > 0:
        return {"message": "Rating updated", "song_id": song_id, "rating": request.rating}
    raise HTTPException(status_code=404, detail="Song not found")

@app.get("/api/songs/export")
def export_csv():
    conn = get_db()
    rows = conn.execute('SELECT * FROM songs ORDER BY title').fetchall()
    songs = [dict(row) for row in rows]
    conn.close()
    
    if not songs:
        raise HTTPException(status_code=404, detail="No songs to export")
    
    output = io.StringIO()
    # Use QUOTE_NONNUMERIC to properly escape strings with commas, quotes, newlines
    writer = csv.DictWriter(
        output, 
        fieldnames=songs[0].keys(), 
        lineterminator='\n',
        quoting=csv.QUOTE_NONNUMERIC  # This handles all special characters
    )
    writer.writeheader()
    writer.writerows(songs)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=songs.csv"}
    )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)