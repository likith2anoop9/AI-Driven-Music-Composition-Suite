# AI-Driven-Music-Composition-Suite



<img width="505" alt="Screenshot 2024-12-15 at 5 06 46 PM" src="https://github.com/user-attachments/assets/29cda83e-f35a-48f0-8c3d-2e136540a3d3" />


## Overview
The **Advanced Music and Voice Generator** is a cutting-edge project that combines generative AI tools (GAITs) to create music, generate lyrics, and clone voices. This Flask-based application offers a user-friendly interface where users can input prompts and receive fully composed songs with lyrics and voice overlays.

## Features
- **Lyrics Generation**: Dynamic and theme-specific lyrics using GPT-4o Mini.
- **Music Generation**: Instrumental music creation leveraging Suno AI via Ace Data Cloud.
- **Voice Cloning**: Custom voice overlays generated using the ElevenLabs API.
- **Interactive Web Interface**: Simple and intuitive design with Bootstrap for styling.

## Technologies Used
- **Backend**: Python, Flask
- **Frontend**: HTML, CSS, JavaScript (Bootstrap for styling)
- **GAITs**:
  - GPT-4o Mini for lyrics generation
  - Suno AI (via Ace Data Cloud) for music generation
  - ElevenLabs for voice cloning
- **Libraries**: Pydub, ReportLab

## Workflow Diagram
1. User provides input prompt with details such as mood, genre, tempo, and instruments.
2. Lyrics are generated using GPT-4o Mini.
3. Music is composed based on the input using Suno AI via Ace Data Cloud.
4. Voice cloning is performed using ElevenLabs API to overlay vocals.
5. Final outputs are integrated and presented to the user for download or playback.

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/AI-Driven-Music-Composition-Suite.git
   ```
2. Navigate to the project directory:
   ```bash
   cd AI-Driven-Music-Composition-Suite
   ```
3. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Set up API keys:
   - Add your **OpenAI**, **Ace Data Cloud**, and **ElevenLabs** API keys in a `.env` file:
     ```
     OPENAI_API_KEY=your_openai_api_key
     ACE_DATA_API_KEY=your_ace_data_api_key
     ELEVENLABS_API_KEY=your_elevenlabs_api_key
     ```
5. Run the application:
   ```bash
   python main.py
   ```
6. Open your browser and navigate to `http://127.0.0.1:5000`.

## Usage
1. **Generate Lyrics**: Enter a theme or prompt to create custom song lyrics.
2. **Create Music**: Select mood, genre, and instruments to generate a matching track.
3. **Clone Voice**: Upload or use preloaded audio to add vocals to the track.
4. **Preview and Download**: Listen to the output and download the lyrics, music, or vocalized track.

## Example
![Workflow Screenshot]![image](https://github.com/user-attachments/assets/b8cf9879-bb02-47b9-a336-ba72eb9f134e)


## Challenges and Learnings
- **API Access**: Suno AI’s API required integration via Ace Data Cloud.
- **Audio Synchronization**: Aligning music and vocals needed precise timing adjustments using Pydub.
- **Ethical Considerations**: Ensuring the system adheres to fair use and copyright guidelines.

## Future Improvements
- Add real-time generation capabilities for enhanced user experience.
- Incorporate more GAITs for diverse musical styles and voices.
- Optimize performance for faster processing and rendering.

## Contributing
1. Fork the repository.
2. Create a new branch:
   ```bash
   git checkout -b feature-name
   ```
3. Commit your changes:
   ```bash
   git commit -m "Add a new feature"
   ```
4. Push the branch:
   ```bash
   git push origin feature-name
   ```
5. Open a pull request.


## Acknowledgments
- **GPT-4o Mini** for creative and dynamic lyrics generation.
- **Suno AI** for versatile music generation capabilities.
- **ElevenLabs** for realistic and customizable voice cloning.

---
**Author:** Likith Kadiyala  
Feel free to reach out for collaborations or feedback!

