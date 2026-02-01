# yt-dlp-host API Specification

## Base URL
```
http://localhost:5000
```

## Authentication
All endpoints (except public ones) require an API key passed via the `X-API-Key` header.

```
X-API-Key: <your_api_key>
```

---

## Endpoints

### 1. Search YouTube Videos

**Endpoint:** `POST /search`

**Permission Required:** `search`

**Description:** Search YouTube for videos matching a query and return the first result with metadata.

**Request Body:**
```json
{
  "query": "eminem - lose yourself"
}
```

**Response (Success):**
```json
{
  "success": true,
  "url": "https://www.youtube.com/watch?v=xFYQQPAOz7Y",
  "title": "Eminem - Lose Yourself",
  "duration": 328,
  "id": "xFYQQPAOz7Y"
}
```

**Response (Error):**
```json
{
  "success": false,
  "message": "No videos found"
}
```

**Status Codes:**
- `200` - Success
- `400` - Missing query parameter
- `401` - Invalid or missing API key

**Example:**
```bash
curl -X POST \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  http://localhost:5000/search \
  -d '{"query": "the weeknd - blinding lights"}'
```

---

### 2. Download Video

**Endpoint:** `POST /get_video`

**Permission Required:** `get_video`

**Description:** Download a video with audio in the best available quality.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=xFYQQPAOz7Y",
  "filename": "eminem-lose-yourself",
  "video_format": "bestvideo",
  "audio_format": "bestaudio",
  "output_format": "mp4"
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | Yes | - | Valid YouTube URL |
| filename | string | No | auto | Custom filename (saves to /app/downloads/{filename}.{ext}) |
| video_format | string | No | bestvideo | Video format (bestvideo, 18, 22, etc.) |
| audio_format | string | No | bestaudio | Audio format (bestaudio, 140, 251, etc.) |
| output_format | string | No | - | Output format (mp4, mkv, webm, etc.) |

**Response:**
```json
{
  "status": "waiting",
  "task_id": "aB3cD4eF5gH6iJ7k"
}
```

**Status Codes:**
- `200` - Task created
- `400` - Missing URL
- `401` - Invalid or missing API key

---

### 3. Download Audio

**Endpoint:** `POST /get_audio`

**Permission Required:** `get_audio`

**Description:** Download audio only from a video.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=xFYQQPAOz7Y",
  "filename": "eminem-lose-yourself",
  "audio_format": "bestaudio",
  "output_format": "mp3"
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | Yes | - | Valid YouTube URL |
| filename | string | No | auto | Custom filename |
| audio_format | string | No | bestaudio | Audio format |
| output_format | string | No | - | Output format (mp3, m4a, wav, etc.) |

**Response:**
```json
{
  "status": "waiting",
  "task_id": "aB3cD4eF5gH6iJ7k"
}
```

---

### 4. Download Live Video

**Endpoint:** `POST /get_live_video`

**Permission Required:** `get_live_video`

**Description:** Download video from a live stream.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "filename": "live-stream",
  "duration": 3600,
  "start": 0
}
```

**Parameters:**
| Parameter | Type | Required | Default | Description |
|-----------|------|----------|---------|-------------|
| url | string | Yes | - | Valid YouTube live stream URL |
| filename | string | No | auto | Custom filename |
| duration | integer | No | - | Duration in seconds to record |
| start | integer | No | 0 | Start offset in seconds |
| video_format | string | No | bestvideo | Video format |
| audio_format | string | No | bestaudio | Audio format |

---

### 5. Download Live Audio

**Endpoint:** `POST /get_live_audio`

**Permission Required:** `get_live_audio`

**Description:** Download audio only from a live stream.

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=...",
  "filename": "live-audio",
  "duration": 3600
}
```

**Parameters:** Same as `get_live_video` but audio-focused

---

### 6. Get Video Info

**Endpoint:** `POST /get_info`

**Permission Required:** `get_info`

**Description:** Extract and save video metadata (title, duration, formats, etc.).

**Request Body:**
```json
{
  "url": "https://www.youtube.com/watch?v=xFYQQPAOz7Y",
  "filename": "video-info"
}
```

**Response:**
```json
{
  "status": "waiting",
  "task_id": "aB3cD4eF5gH6iJ7k"
}
```

**Note:** Returns a task ID. Check status to get the info.json file path.

---

### 7. Check Task Status

**Endpoint:** `GET /status/<task_id>`

**Description:** Get the status of a download task.

**Response (Processing):**
```json
{
  "key_name": "default",
  "status": "processing",
  "task_type": "get_audio",
  "url": "https://www.youtube.com/watch?v=xFYQQPAOz7Y",
  "audio_format": "bestaudio"
}
```

**Response (Completed):**
```json
{
  "key_name": "default",
  "status": "completed",
  "task_type": "get_audio",
  "url": "https://www.youtube.com/watch?v=xFYQQPAOz7Y",
  "audio_format": "bestaudio",
  "file": "/files/my-audio.mp3",
  "completed_time": "2026-02-01T14:22:45.123456"
}
```

**Response (Error):**
```json
{
  "key_name": "default",
  "status": "error",
  "task_type": "get_audio",
  "url": "https://www.youtube.com/watch?v=xFYQQPAOz7Y",
  "error": "Could not estimate file size",
  "completed_time": "2026-02-01T14:22:46.123456"
}
```

**Status Values:**
- `waiting` - Task queued, awaiting processing
- `processing` - Currently downloading
- `completed` - Download finished successfully
- `error` - Download failed

---

### 8. Download File

**Endpoint:** `GET /files/<path>`

**Description:** Download a completed file or get file info.

**Response:** Returns the file as binary data

**Example:**
```bash
curl -H "X-API-Key: your_api_key" \
  http://localhost:5000/files/my-audio.mp3 \
  -o my-audio.mp3
```

**Query Parameters:**
- `raw=true` - Force download as attachment instead of inline display

---

### 9. Create API Key

**Endpoint:** `POST /create_key`

**Permission Required:** `create_key`

**Description:** Create a new API key with specified permissions.

**Request Body:**
```json
{
  "name": "mobile_app",
  "permissions": [
    "get_audio",
    "get_video",
    "search"
  ]
}
```

**Response:**
```json
{
  "message": "API key created",
  "name": "mobile_app",
  "key": "sk_live_1a2b3c4d5e6f7g8h9i0j"
}
```

---

### 10. Delete API Key

**Endpoint:** `DELETE /delete_key/<name>`

**Permission Required:** `delete_key`

**Description:** Delete an API key by name.

**Response:**
```json
{
  "message": "API key deleted",
  "name": "mobile_app"
}
```

---

### 11. Get API Key

**Endpoint:** `GET /get_key/<name>`

**Permission Required:** `get_key`

**Description:** Retrieve a specific API key.

**Response:**
```json
{
  "name": "mobile_app",
  "key": "sk_live_1a2b3c4d5e6f7g8h9i0j"
}
```

---

### 12. List All API Keys

**Endpoint:** `GET /get_keys`

**Permission Required:** `get_keys`

**Description:** Get all API keys and their permissions.

**Response:**
```json
{
  "default": {
    "key": "sk_live_...",
    "permissions": ["create_key", "delete_key", "get_key", "get_keys", "get_video", "get_audio", "get_live_video", "get_live_audio", "get_info", "search"],
    "memory_quota": 5368709120,
    "memory_usage": [],
    "last_access": "2026-02-01T14:22:45.123456"
  },
  "mobile_app": {
    "key": "sk_live_...",
    "permissions": ["get_audio", "get_video", "search"],
    "memory_quota": 5368709120,
    "memory_usage": [],
    "last_access": null
  }
}
```

---

### 13. Check Permissions

**Endpoint:** `POST /check_permissions`

**Description:** Verify if an API key has required permissions.

**Request Body:**
```json
{
  "permissions": ["get_audio", "search"]
}
```

**Response (Has Permissions):**
```json
{
  "message": "Permissions granted"
}
```

**Response (Missing Permissions):**
```json
{
  "message": "Insufficient permissions"
}
```

**Status Codes:**
- `200` - Has all required permissions
- `403` - Missing required permissions
- `401` - Invalid API key

---

## Common Parameters

### Format Specifications

**Video Formats:**
- `bestvideo` - Best quality video (default)
- `bestvideo[height<=1080]` - Best video ≤ 1080p
- `18` - 360p
- `22` - 720p
- `137` - 4K

**Audio Formats:**
- `bestaudio` - Best quality audio (default)
- `140` - M4A/AAC
- `251` - Opus
- `249`, `250` - WebM Opus variants

**Output Formats:**
- Video: `mp4`, `mkv`, `webm`, `avi`
- Audio: `mp3`, `m4a`, `wav`, `opus`, `vorbis`

### Time Formats

**start_time, end_time:**
```
"HH:MM:SS" → "01:30:45"
"MM:SS"    → "90:45"
"SS"       → "5445"
```

---

## Workflow Example

### 1. Search for a song
```bash
curl -X POST \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  http://localhost:5000/search \
  -d '{"query": "dua lipa - levitating"}' \
  | jq '.url'
```

### 2. Download the audio
```bash
curl -X POST \
  -H "X-API-Key: your_key" \
  -H "Content-Type: application/json" \
  http://localhost:5000/get_audio \
  -d '{
    "url": "https://www.youtube.com/watch?v=TUVcZfQe-Kw",
    "filename": "dua-lipa-levitating",
    "output_format": "mp3"
  }' \
  | jq '.task_id'
```

### 3. Check download status
```bash
curl -H "X-API-Key: your_key" \
  http://localhost:5000/status/aB3cD4eF5gH6iJ7k
```

### 4. Download the file
```bash
curl -H "X-API-Key: your_key" \
  http://localhost:5000/files/dua-lipa-levitating.mp3 \
  -o dua-lipa-levitating.mp3
```

---

## Error Responses

### 400 Bad Request
```json
{
  "status": "error",
  "message": "URL is required"
}
```

### 401 Unauthorized
```json
{
  "error": "No API key provided"
}
```

### 404 Not Found
```json
{
  "status": "error",
  "message": "Task not found"
}
```

### 403 Forbidden
```json
{
  "error": "Access denied"
}
```

---

## Permissions

Available permissions:
- `search` - Search YouTube videos
- `get_video` - Download videos
- `get_audio` - Download audio
- `get_live_video` - Download from live streams (video)
- `get_live_audio` - Download from live streams (audio)
- `get_info` - Extract video metadata
- `create_key` - Create new API keys
- `delete_key` - Delete API keys
- `get_key` - View specific API key
- `get_keys` - View all API keys

---

## Rate Limits & Quotas

- **Memory Quota:** 5GB per API key (default)
- **Cleanup Time:** 10 minutes (completed tasks auto-delete)
- **Max Workers:** 4 concurrent downloads

---

## File Paths

**With custom filename:**
```
/app/downloads/my-audio.mp3
/app/downloads/video.mp4
```

**Without custom filename:**
```
/app/downloads/{task_id}/audio.m4a
/app/downloads/{task_id}/video.mkv
```

**Info files:**
```
/app/downloads/my-info.json          (with custom filename)
/app/downloads/{task_id}/info.json   (without custom filename)
```
