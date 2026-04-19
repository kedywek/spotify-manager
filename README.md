# Spotify Manager

Spotify Manager is an intelligent playlist organization tool that leverages machine learning to group your Spotify tracks based on their "vibe" and musical genre. By analyzing track tags, it automates the creation of cohesive listening experiences.

## 🚀 Features

* **Spotify OAuth2 Authentication**: Securely connect and authenticate with your Spotify account.
* **Playlist Management**: Fetch and view your personal playlists and their detailed track information.
* **Last.fm Integration**: Automatically retrieves genre and descriptive tags for tracks to enrich musical metadata.
* **Intelligent Clustering**: Groups tracks using the **K-Means** algorithm based on **TF-IDF** vectorization of musical tags.
* **Local Caching**: Stores retrieved tags in a local SQLite database (via SQLAlchemy) to minimize API calls and improve performance.
* **Spotify Export**: Seamlessly creates new categorized playlists directly on your Spotify account from the generated clusters.

## 🛠 Tech Stack

* **Language**: Python (>= 3.14)
* **Web Framework**: FastAPI
* **Machine Learning/Data**: Scikit-learn (K-Means, TfidfVectorizer), Pandas
* **Database**: SQLAlchemy, aiosqlite
* **APIs**: Spotipy (Spotify SDK), Last.fm API
* **Dependency Management**: uv

## 📋 Requirements & Configuration

1. **Install dependencies** (using `uv` is recommended):
   ```bash
   uv sync
   ```
2. **Configure Environment Variables**: Create a `.env` file based on `.env.example`:
   ```env
   SPOTIPY_CLIENT_ID=your_spotify_client_id
   SPOTIPY_CLIENT_SECRET=your_spotify_client_secret
   SPOTIPY_REDIRECT_URI=http://127.0.0.1:8000/callback
   LASTFM_API_KEY=your_lastfm_api_key
   ```

## 🏁 Getting Started

To launch the development server, run:

```bash
fastapi dev main.py
```

The application will be available at: `http://127.0.0.1:8000`.

## 📂 Project Structure

* `main.py`: Core API endpoints including authentication, playlist fetching, and clustering logic.
* `spotify_service.py`: Internal service for interacting with Spotify and Last.fm APIs.
* `clusterer.py`: Machine learning logic for processing track tags and generating clusters.
* `models.py` & `database.py`: Database schema definitions and SQLAlchemy session configuration.
* `config.py`: Configuration management using Pydantic Settings.

## 🗺 Roadmap

The project is under active development. Current status and future plans:

- [x] **Tag Collection** – Integration with Last.fm API and local caching of metadata.
- [x] **K-Means Clustering** – Implementation of K-Means algorithm for grouping tracks by genre tags.
- [ ] **GMM (Gaussian Mixture Model) Integration** – Implementing a more flexible, probabilistic clustering model.
- [ ] **Graphical User Interface (GUI)** – Developing a modern web frontend for easier interaction.
- [ ] **Audio Sample Analysis** – Moving beyond text-based tags to direct audio feature extraction from track samples for higher clustering precision.
