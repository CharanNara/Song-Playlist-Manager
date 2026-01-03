import pytest
import json
import os
from fastapi.testclient import TestClient
from main import app, init_db

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_db():
    """Setup test database before each test"""
    # Remove existing test db if any
    if os.path.exists('songs.db'):
        os.remove('songs.db')
    init_db()
    yield
    # Cleanup after test
    if os.path.exists('songs.db'):
        os.remove('songs.db')


class TestDataLoading:
    """Test JSON data loading and normalization"""
    
    def test_load_valid_json(self):
        """Test loading valid JSON file"""
        test_data = {
            "id": {"0": "song1", "1": "song2"},
            "title": {"0": "Test Song 1", "1": "Test Song 2"},
            "danceability": {"0": 0.5, "1": 0.8}
        }
        
        json_content = json.dumps(test_data).encode()
        response = client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["songs_loaded"] == 2
        assert "Data loaded" in data["message"]
    
    def test_load_json_with_special_characters(self):
        """Test loading JSON with commas, quotes, newlines in title"""
        test_data = {
            "id": {"0": "song1", "1": "song2", "2": "song3"},
            "title": {
                "0": "Song, with comma",
                "1": 'Song "with quotes"',
                "2": "Song\nwith\nnewline"
            },
            "danceability": {"0": 0.5, "1": 0.6, "2": 0.7}
        }
        
        json_content = json.dumps(test_data).encode()
        response = client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
        
        assert response.status_code == 200
        assert response.json()["songs_loaded"] == 3
        
        # Verify data was sanitized
        songs_response = client.get("/api/songs?page=1&limit=10")
        songs = songs_response.json()["songs"]
        
        # Newlines should be converted to spaces
        assert "\n" not in songs[2]["title"]
    
    def test_load_json_with_missing_fields(self):
        """Test loading JSON with missing/null values"""
        test_data = {
            "id": {"0": "song1"},
            "title": {"0": "Test Song"},
            "danceability": {"0": None}
        }
        
        json_content = json.dumps(test_data).encode()
        response = client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
        
        assert response.status_code == 200
        
        # Verify defaults applied
        songs_response = client.get("/api/songs")
        song = songs_response.json()["songs"][0]
        assert song["danceability"] == 0.0
    
    def test_load_json_with_integer_title(self):
        """Test loading JSON where title is an integer"""
        test_data = {
            "id": {"0": "song1"},
            "title": {"0": 123},  # Integer instead of string
            "danceability": {"0": 0.5}
        }
        
        json_content = json.dumps(test_data).encode()
        response = client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
        
        assert response.status_code == 200
        
        # Verify integer converted to string
        songs_response = client.get("/api/songs")
        song = songs_response.json()["songs"][0]
        assert song["title"] == "123"
        assert isinstance(song["title"], str)
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON"""
        response = client.post(
            "/api/load-data",
            files={"file": ("test.json", b"invalid json", "application/json")}
        )
        
        assert response.status_code == 500


class TestPagination:
    """Test pagination functionality"""
    
    def setup_method(self):
        """Load test data before each test"""
        test_data = {
            "id": {str(i): f"song{i}" for i in range(25)},
            "title": {str(i): f"Song {i}" for i in range(25)},
            "danceability": {str(i): 0.5 for i in range(25)}
        }
        
        json_content = json.dumps(test_data).encode()
        client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
    
    def test_get_first_page(self):
        """Test getting first page"""
        response = client.get("/api/songs?page=1&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["songs"]) == 10
        assert data["page"] == 1
        assert data["total"] == 25
        assert data["total_pages"] == 3
    
    def test_get_last_page(self):
        """Test getting last page with fewer items"""
        response = client.get("/api/songs?page=3&limit=10")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["songs"]) == 5  # Only 5 items on last page
        assert data["page"] == 3
    
    def test_custom_page_size(self):
        """Test custom page size"""
        response = client.get("/api/songs?page=1&limit=5")
        
        assert response.status_code == 200
        data = response.json()
        assert len(data["songs"]) == 5
        assert data["total_pages"] == 5


class TestSorting:
    """Test sorting functionality"""
    
    def setup_method(self):
        """Load test data"""
        test_data = {
            "id": {"0": "a", "1": "b", "2": "c"},
            "title": {"0": "Zebra", "1": "Apple", "2": "Mango"},
            "danceability": {"0": 0.3, "1": 0.9, "2": 0.5}
        }
        
        json_content = json.dumps(test_data).encode()
        client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
    
    def test_sort_by_title_asc(self):
        """Test sorting by title ascending"""
        response = client.get("/api/songs?sort_by=title&sort_order=asc")
        
        songs = response.json()["songs"]
        assert songs[0]["title"] == "Apple"
        assert songs[1]["title"] == "Mango"
        assert songs[2]["title"] == "Zebra"
    
    def test_sort_by_title_desc(self):
        """Test sorting by title descending"""
        response = client.get("/api/songs?sort_by=title&sort_order=desc")
        
        songs = response.json()["songs"]
        assert songs[0]["title"] == "Zebra"
        assert songs[2]["title"] == "Apple"
    
    def test_sort_by_danceability(self):
        """Test sorting by numeric field"""
        response = client.get("/api/songs?sort_by=danceability&sort_order=asc")
        
        songs = response.json()["songs"]
        assert songs[0]["danceability"] == 0.3
        assert songs[1]["danceability"] == 0.5
        assert songs[2]["danceability"] == 0.9


class TestSearch:
    """Test search functionality (LIKE match, multi-result response)"""

    def setup_method(self):
        """Load test data"""
        test_data = {
            "id": {"0": "1", "1": "2"},
            "title": {"0": "Unique Song", "1": "Another Song"},
            "danceability": {"0": 0.5, "1": 0.6}
        }

        json_content = json.dumps(test_data).encode()
        client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )

    def test_search_existing_song(self):
        """Search should return matches (case-insensitive LIKE)"""
        response = client.get("/api/songs/search?title=Unique Song&limit=10")

        assert response.status_code == 200
        data = response.json()

        assert "count" in data
        assert "songs" in data
        assert data["count"] >= 1
        assert any(song["title"] == "Unique Song" for song in data["songs"])

    def test_search_case_insensitive(self):
        """Search should be case-insensitive"""
        response = client.get("/api/songs/search?title=unique song&limit=10")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] >= 1
        assert any(song["title"] == "Unique Song" for song in data["songs"])

    def test_search_partial_match(self):
        """Search should support partial title (LIKE)"""
        response = client.get("/api/songs/search?title=Song&limit=10")

        assert response.status_code == 200
        data = response.json()

        # Both titles contain 'Song'
        assert data["count"] == 2
        titles = [s["title"] for s in data["songs"]]
        assert "Unique Song" in titles
        assert "Another Song" in titles

    def test_search_nonexistent_song(self):
        """Search should return count=0 and empty list when no matches"""
        response = client.get("/api/songs/search?title=Does Not Exist&limit=10")

        assert response.status_code == 200
        data = response.json()

        assert data["count"] == 0
        assert data["songs"] == []



class TestRating:
    """Test rating functionality"""
    
    def setup_method(self):
        """Load test data"""
        test_data = {
            "id": {"0": "song1"},
            "title": {"0": "Test Song"},
            "danceability": {"0": 0.5}
        }
        
        json_content = json.dumps(test_data).encode()
        client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
    
    def test_update_valid_rating(self):
        """Test updating rating with valid value"""
        response = client.put(
            "/api/songs/song1/rating",
            json={"rating": 5}
        )
        
        assert response.status_code == 200
        data = response.json()
        assert data["rating"] == 5
        
        # Verify rating persisted
        songs = client.get("/api/songs").json()["songs"]
        assert songs[0]["rating"] == 5
    
    def test_update_rating_invalid_value(self):
        """Test updating rating with invalid value (>5)"""
        response = client.put(
            "/api/songs/song1/rating",
            json={"rating": 6}
        )
        
        assert response.status_code == 422  # Validation error
    
    def test_update_rating_negative_value(self):
        """Test updating rating with negative value"""
        response = client.put(
            "/api/songs/song1/rating",
            json={"rating": -1}
        )
        
        assert response.status_code == 422
    
    def test_update_rating_nonexistent_song(self):
        """Test updating rating for non-existent song"""
        response = client.put(
            "/api/songs/fake_id/rating",
            json={"rating": 3}
        )
        
        assert response.status_code == 404


class TestCSVExport:
    """Test CSV export functionality"""
    
    def setup_method(self):
        """Load test data with edge cases"""
        test_data = {
            "id": {"0": "1", "1": "2", "2": "3"},
            "title": {
                "0": "Normal Song",
                "1": "Song, with comma",
                "2": 'Song "with quotes"'
            },
            "danceability": {"0": 0.5, "1": 0.6, "2": 0.7}
        }
        
        json_content = json.dumps(test_data).encode()
        client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
    
    def test_csv_export_success(self):
        """Test successful CSV export"""
        response = client.get("/api/songs/export")
        
        assert response.status_code == 200
        assert response.headers["content-type"] == "text/csv; charset=utf-8"
        assert "attachment" in response.headers["content-disposition"]
    
    def test_csv_export_special_characters(self):
        """Test CSV properly escapes special characters"""
        response = client.get("/api/songs/export")
        
        csv_content = response.content.decode('utf-8')
        
        # Check that commas are handled (title should be quoted)
        assert '"Song, with comma"' in csv_content
        
        # Check that quotes are escaped (doubled)
        assert 'Song ""with quotes""' in csv_content
    
    def test_csv_export_empty_database(self):
        """Test CSV export with no data"""
        # Clear database
        client.post(
            "/api/load-data",
            files={"file": ("test.json", b'{"id":{}}', "application/json")}
        )
        
        response = client.get("/api/songs/export")
        assert response.status_code == 404


class TestEdgeCases:
    """Test various edge cases"""
    
    def test_empty_json_file(self):
        """Test loading empty JSON"""
        test_data = {"id": {}, "title": {}}
        
        json_content = json.dumps(test_data).encode()
        response = client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
        
        assert response.status_code == 200
        assert response.json()["songs_loaded"] == 0
    
    def test_very_long_title(self):
        """Test handling very long title"""
        long_title = "A" * 1000
        test_data = {
            "id": {"0": "1"},
            "title": {"0": long_title},
            "danceability": {"0": 0.5}
        }
        
        json_content = json.dumps(test_data).encode()
        response = client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
        
        assert response.status_code == 200
        
        # Verify data stored correctly
        songs = client.get("/api/songs").json()["songs"]
        assert len(songs[0]["title"]) == 1000
    
    def test_unicode_characters(self):
        """Test handling Unicode characters"""
        test_data = {
            "id": {"0": "1"},
            "title": {"0": "Song 🎵 with émojis and ñ"},
            "danceability": {"0": 0.5}
        }
        
        json_content = json.dumps(test_data).encode()
        response = client.post(
            "/api/load-data",
            files={"file": ("test.json", json_content, "application/json")}
        )
        
        assert response.status_code == 200
        
        songs = client.get("/api/songs").json()["songs"]
        assert "🎵" in songs[0]["title"]
        assert "ñ" in songs[0]["title"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])