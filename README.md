# Khushu - Islamic Prayer Focus Enhancement System

WINNER OF MSAHACKS 2025 - SECOND PLACE PRIZE 🥈! 

## Overview
Khushu is an innovative application designed to help Muslims enhance their focus and mindfulness during prayer (salah), but is  particularly useful for people with ADHD, autism, anxiety, OCD, and sensory processing sensitivity. Using advanced EEG monitoring through the Muse headband, real-time analysis, and AI-powered guidance, the system provides actionable insights and personalized recommendations to improve prayer quality and spiritual connection.

## Features
- **Real-time EEG Monitoring**: Tracks brain activity during prayer using Muse headband
- **Khushu Index**: Proprietary algorithm measuring prayer focus using multiple brainwave bands:
  - Alpha (8-13 Hz): Relaxed focus
  - Theta (4-8 Hz): Deep meditation
  - Beta (13-30 Hz): Active thinking
  - Delta (0.5-4 Hz): Deep focus
  - Gamma (30-70 Hz): Higher cognitive processes
- **Live Visualization**: Dynamic display of brainwave patterns and focus metrics
- **AI Assistant**: GPT-4 powered guidance system with Islamic prayer expertise
- **Historical Analysis**: Detailed tracking of prayer sessions and progress
- **Condition-Specific Support**: Specialized guidance for users with ADHD, autism, anxiety, OCD, and sensory processing sensitivity

## Technology Stack
### Frontend
- HTML5/CSS3 with responsive design
- Vanilla JavaScript
- Chart.js for real-time data visualization
- Custom animations and transitions

### Backend
- Python 3.x
- Flask (REST API)
- OpenAI GPT-4 API
- Pylsl for EEG data streaming
- NumPy/Pandas for data processing
- Matplotlib for data visualization

## Prerequisites
1. Hardware Requirements:
   - Muse EEG Headband (2016 model or newer)
   - Computer with Bluetooth capability

2. Software Requirements:
   - Python 3.x
   - BlueMuse (Windows) or MuseLSL (macOS/Linux)
   - Modern web browser (Chrome/Firefox recommended)

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/khushu.git
   cd khushu
   ```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

3. Configure OpenAI API:
   - Update the API key in `backend/api/chatbot.py`
   - Or set as environment variable:
```bash
export OPENAI_API_KEY=your_api_key_here
```

## Running the Application

1. Start the Flask backend server:
```bash
cd backend
python server.py
```
The server will start on `http://localhost:5001`

2. Start the Khushu monitoring service:
```bash
python khushu_index.py
```

3. For motion detection via sensor logger on apple watch to detect which movements in prayer are done (as each movement has different focus levels i.e. bowing, standing, prostrating, etc.) (optional):
```bash
python handmotion.py
```

4. Access the frontend:
- Open `frontend/index.html` in your web browser
- Navigate through the available features:
  - Overall Results (khushu-level.html)
  - Ask AI (ai-page.html)
  - Live Demo (live.html)

## Project Structure
```
khushu/
├── backend/
│   ├── api/
│   │   └── chatbot.py          # AI assistant implementation
│   ├── server.py               # Main Flask server
│   ├── khushu_index.py         # EEG processing & analysis
│   ├── handmotion.py           # Prayer position detection
│   ├── khushu_results.csv      # Historical session data
│   └── detailed_session.csv    # Real-time session data
├── frontend/
│   ├── css/
│   │   ├── main-styles.css
│   │   ├── khushu-level.css
│   │   ├── ai-styles.css
│   │   └── live-styles.css
│   ├── index.html             # Landing page
│   ├── khushu-level.html      # Results dashboard
│   ├── ai-page.html           # AI assistant interface
│   └── live.html              # Real-time monitoring
└── requirements.txt
```

## Features in Detail

### Live Monitoring
- Real-time brainwave visualization with 5 frequency bands
- Dynamic Khushu Index calculation using weighted algorithm
- Instant feedback with focus level indicators
- Prayer position detection (optional)

### AI Assistant
- Personalized recommendations based on:
  - Current Khushu Index
  - Historical prayer data
  - Selected conditions/challenges
  - Islamic principles and teachings
- Support for multiple neurological conditions
- Context-aware spiritual guidance

### Analytics Dashboard
- Historical prayer session data
- Progress tracking with detailed metrics
- Focus level trends and patterns
- Exportable session data


## Acknowledgments
- Muse by InteraXon for EEG hardware
- OpenAI for GPT-4 integration
- Chart.js team for visualization library
- The Muslim developer community for feedback and support


## Note
This project is intended as a supplementary tool for prayer enhancement and should not be considered a replacement for traditional Islamic teachings or guidance from qualified religious scholars.