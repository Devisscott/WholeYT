# Social Media Downloader

A powerful, open-source, local-first web application that allows users to download videos, reels, and posts from major social media platforms including YouTube, Facebook, Instagram, Twitter, and more. Built with a modern Glassmorphism UI and dark mode support.

## Features

- **Home Downloader**: Download individual videos with real-time preview, format selection, and QR code generation for mobile downloads.
- **Bulk Downloader**: Queue and download multiple URLs simultaneously with individual progress tracking.
- **Link Grabber**: Extract media links from playlists, profiles, or any webpage and batch download selected items.
- **Cookie Authentication**: Support for uploading cookies.txt files to access restricted or private content.
- **Responsive Design**: Fully mobile-optimized interface with dark mode support.
- **Privacy Focused**: Local-first architecture with no external data tracking.

## Technology Stack

- **Frontend**: HTML5, CSS3, JavaScript, Tailwind CSS, Lucide Icons
- **Backend**: Python, Flask, yt-dlp
- **UI Design**: Glassmorphism with translucent cards, blur effects, and smooth animations

## Installation

1. **Clone the Repository** (if applicable) or ensure all files are in your working directory.

2. **Set up a Virtual Environment** (recommended):
   ```
   python -m venv venv
   venv\Scripts\activate  # On Windows
   # OR
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install Dependencies**:
   ```
   pip install -r requirements.txt
   ```

4. **Run the Application**:
   ```
   python app.py
   ```

5. **Access the Web Interface**:
   Open your browser and navigate to `http://localhost:5000`

## Usage

- **Home Downloader**: Paste a video URL to preview and download with customizable format options.
- **Bulk Downloader**: Add multiple URLs to a queue and manage simultaneous downloads.
- **Link Grabber**: Extract all media links from a page for selective or batch downloading.
- **Cookies**: Upload a cookies.txt file for accessing private content (exportable via browser extensions).

## Project Structure

- `app.py`: Main Flask application with API endpoints for video downloading and link extraction.
- `templates/`: HTML templates for the web interface.
  - `base.html`: Base template with shared layout and styles.
  - `index.html`: Home page for single video downloads.
  - `bulk_download.html`: Interface for bulk downloads.
  - `link_grabber.html`: Tool for extracting media links from pages.
- `downloads/`: Directory where downloaded files are saved.
- `cookies/`: Directory for uploaded cookies files.

## Contributing

This project is open-source and welcomes contributions. Please feel free to submit pull requests or open issues for bugs and feature requests.

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Disclaimer

This tool is for personal use and educational purposes only. Downloading copyrighted content may violate the terms of service of the respective platforms. Use responsibly and ensure you have the right to download and store any content.
