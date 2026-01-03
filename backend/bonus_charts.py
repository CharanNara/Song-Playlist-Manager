"""
Bonus visualizations for Song Playlist Manager
- Scatter plot: danceability vs song index
- Histogram: song duration (seconds)
- Bar charts: average acousticness and tempo

Run:
    python bonus_charts.py
"""

import sqlite3
import matplotlib.pyplot as plt

DB_PATH = "songs.db"


def fetch_songs():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    rows = conn.execute(
        """
        SELECT
            danceability,
            duration_ms,
            acousticness,
            tempo
        FROM songs
        """
    ).fetchall()
    conn.close()
    return rows


def scatter_danceability(songs):
    danceability = [row["danceability"] for row in songs]

    plt.figure()
    plt.scatter(range(len(danceability)), danceability)
    plt.xlabel("Song Index")
    plt.ylabel("Danceability")
    plt.title("Danceability Scatter Plot")
    plt.show()


def histogram_duration(songs):
    durations_sec = [
        row["duration_ms"] / 1000 for row in songs if row["duration_ms"] > 0
    ]

    plt.figure()
    plt.hist(durations_sec, bins=20)
    plt.xlabel("Duration (seconds)")
    plt.ylabel("Number of Songs")
    plt.title("Song Duration Histogram")
    plt.show()


def bar_acousticness_tempo(songs):
    acousticness = [row["acousticness"] for row in songs]
    tempo = [row["tempo"] for row in songs]

    avg_acousticness = sum(acousticness) / len(acousticness)
    avg_tempo = sum(tempo) / len(tempo)

    plt.figure()
    plt.bar(["Acousticness", "Tempo"], [avg_acousticness, avg_tempo])
    plt.ylabel("Average Value")
    plt.title("Average Acousticness vs Tempo")
    plt.show()


if __name__ == "__main__":
    songs = fetch_songs()

    if not songs:
        print("No songs found in database. Load data first.")
        exit(0)

    scatter_danceability(songs)
    histogram_duration(songs)
    bar_acousticness_tempo(songs)
