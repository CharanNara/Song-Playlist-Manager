from fastapi import FastAPI, HTTPException, UploadFile, File, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
import sqlite3
import json
import csv
import io
import math
import matplotlib
matplotlib.use('Agg')  # Use non-GUI backend
import matplotlib.pyplot as plt

app = FastAPI()

origin = ["http://localhost:5174", "http://localhost:5173"]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origin,
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
            title_str = str(title_val)
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
    conn = get_db()
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
def export_csv(
    title: str = Query(None),
    sort_by: str = Query("title"),
    sort_order: str = Query("asc")
):
    if sort_by not in ALLOWED_SORT_COLUMNS:
        raise HTTPException(status_code=400, detail="Invalid sort_by column")

    if sort_order not in {"asc", "desc"}:
        raise HTTPException(status_code=400, detail="Invalid sort_order")
    
    conn = get_db()
    
    # Build query based on whether we have a search filter
    if title and title.strip():
        pattern = f"%{title.strip().lower()}%"
        query = f'SELECT * FROM songs WHERE LOWER(title) LIKE ? ORDER BY {sort_by} {sort_order.upper()}'
        rows = conn.execute(query, (pattern,)).fetchall()
    else:
        query = f'SELECT * FROM songs ORDER BY {sort_by} {sort_order.upper()}'
        rows = conn.execute(query).fetchall()
    
    songs = [dict(row) for row in rows]
    conn.close()
    
    if not songs:
        raise HTTPException(status_code=404, detail="No songs to export")
    
    output = io.StringIO()
    writer = csv.DictWriter(
        output, 
        fieldnames=songs[0].keys(), 
        lineterminator='\n',
        quoting=csv.QUOTE_NONNUMERIC
    )
    writer.writeheader()
    writer.writerows(songs)
    
    return StreamingResponse(
        io.BytesIO(output.getvalue().encode('utf-8')),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=songs.csv"}
    )

# Chart Endpoints
@app.get("/api/charts/danceability-scatter")
def chart_danceability_scatter():
    """Generate scatter plot of danceability vs song index"""
    try:
        conn = get_db()
        rows = conn.execute('SELECT danceability FROM songs ORDER BY id').fetchall()
        conn.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No songs found")
        
        danceability = [row['danceability'] for row in rows]
        
        # Clear any existing plots
        # plt.clf()
        # plt.close('all')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.scatter(range(len(danceability)), danceability, alpha=0.6, c='#667eea', s=30)
        ax.set_xlabel('Song Index', fontsize=12)
        ax.set_ylabel('Danceability', fontsize=12)
        ax.set_title('Danceability Scatter Plot', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3)
        plt.tight_layout()
        
        # Save to bytes
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/charts/duration-histogram")
def chart_duration_histogram():
    """Generate histogram of song durations"""
    try:
        conn = get_db()
        rows = conn.execute('SELECT duration_ms FROM songs WHERE duration_ms > 0').fetchall()
        conn.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No songs found")
        
        durations_sec = [row['duration_ms'] / 1000 for row in rows]
        
        # Clear any existing plots
        # plt.clf()
        # plt.close('all')
        
        fig, ax = plt.subplots(figsize=(10, 6))
        ax.hist(durations_sec, bins=20, color='#764ba2', alpha=0.7, edgecolor='black')
        ax.set_xlabel('Duration (seconds)', fontsize=12)
        ax.set_ylabel('Number of Songs', fontsize=12)
        ax.set_title('Song Duration Histogram', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/charts/acousticness-tempo-bar")
def chart_acousticness_tempo_bar():
    """Generate bar chart of average acousticness and tempo"""
    try:
        conn = get_db()
        rows = conn.execute('SELECT acousticness, tempo FROM songs').fetchall()
        conn.close()
        
        if not rows:
            raise HTTPException(status_code=404, detail="No songs found")
        
        acousticness = [row['acousticness'] for row in rows]
        tempo = [row['tempo'] for row in rows]
        
        avg_acousticness = sum(acousticness) / len(acousticness)
        avg_tempo = sum(tempo) / len(tempo)
        
        # Clear any existing plots
        # plt.clf()
        # plt.close('all')
        
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.bar(['Acousticness', 'Tempo'], [avg_acousticness, avg_tempo], 
                      color=['#4facfe', '#f093fb'], alpha=0.8, edgecolor='black')
        ax.set_ylabel('Average Value', fontsize=12)
        ax.set_title('Average Acousticness vs Tempo', fontsize=14, fontweight='bold')
        ax.grid(True, alpha=0.3, axis='y')
        
        # Add value labels on bars
        for bar in bars:
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2., height,
                    f'{height:.2f}',
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
        
        plt.tight_layout()
        
        buf = io.BytesIO()
        fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
        buf.seek(0)
        plt.close(fig)
        
        return StreamingResponse(buf, media_type="image/png")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)