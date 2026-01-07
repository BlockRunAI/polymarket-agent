#!/usr/bin/env python3
"""
Download Guidde video
"""
import subprocess
import sys
import os

VIDEO_URL = "https://app.guidde.com/share/playbooks/hVHZT7ZvzohGkYpZBkafDm?origin=dqrwj8QyFzOC0sssKUkPeOopKCh1"
OUTPUT_FILE = "polymarket_demo.mp4"

def try_ytdlp():
    """Try downloading with yt-dlp"""
    print("Trying yt-dlp...")
    try:
        subprocess.run([
            "yt-dlp",
            "--no-check-certificate",
            "-o", OUTPUT_FILE,
            VIDEO_URL
        ], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"yt-dlp failed: {e}")
        return False

def try_ytdlp_with_cookies():
    """Try with browser cookies"""
    print("Trying yt-dlp with browser cookies...")
    try:
        subprocess.run([
            "yt-dlp",
            "--cookies-from-browser", "chrome",
            "--no-check-certificate",
            "-o", OUTPUT_FILE,
            VIDEO_URL
        ], check=True)
        return True
    except (subprocess.CalledProcessError, FileNotFoundError) as e:
        print(f"yt-dlp with cookies failed: {e}")
        return False

def try_playwright():
    """Try with Playwright to get actual video URL and download it"""
    print("Trying Playwright (headless browser)...")
    try:
        from playwright.sync_api import sync_playwright
        import requests

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context()
            page = context.new_page()

            video_urls = []

            # Intercept network requests
            def handle_response(response):
                url = response.url
                content_type = response.headers.get('content-type', '')
                if '.mp4' in url or 'video' in content_type or 'storage.app.guidde.com' in url:
                    print(f"Found potential video: {url[:100]}...")
                    video_urls.append(url)

            page.on("response", handle_response)

            print(f"Loading page: {VIDEO_URL}")
            page.goto(VIDEO_URL, wait_until="networkidle", timeout=60000)

            # Wait for video to load and try to play it
            page.wait_for_timeout(3000)

            # Try clicking play button if exists
            try:
                play_btn = page.locator('button[aria-label*="play"], .play-button, [class*="play"]').first
                if play_btn.is_visible():
                    print("Clicking play button...")
                    play_btn.click()
                    page.wait_for_timeout(5000)
            except:
                pass

            # Also check for video element src
            try:
                video_src = page.eval_on_selector('video', 'el => el.src')
                if video_src:
                    print(f"Found video src: {video_src[:100]}...")
                    video_urls.append(video_src)
            except:
                pass

            browser.close()

            if video_urls:
                print(f"\nFound {len(video_urls)} potential video URLs")

                # Prioritize actual video files: uploads > previews > others
                # Look for URLs containing 'uploads' which contain the actual video
                priority_order = ['uploads%2F', 'previews%2F', '.mp4']

                for priority_term in priority_order:
                    for url in video_urls:
                        if priority_term not in url:
                            continue

                        print(f"\nTrying: {url[:80]}...")
                        try:
                            # First do a HEAD request to check content type
                            head = requests.head(url, timeout=10)
                            content_type = head.headers.get('content-type', '')
                            size = int(head.headers.get('content-length', 0))

                            print(f"  Content-Type: {content_type}")
                            print(f"  Size: {size / 1024 / 1024:.1f} MB")

                            # Skip if it's an image or too small (< 1MB)
                            if 'image' in content_type or size < 1000000:
                                print("  Skipping (image or too small)")
                                continue

                            # This looks like a video, download it
                            print(f"\nDownloading video...")
                            response = requests.get(url, stream=True, timeout=300)
                            if response.status_code == 200:
                                with open(OUTPUT_FILE, 'wb') as f:
                                    downloaded = 0
                                    for chunk in response.iter_content(chunk_size=8192):
                                        f.write(chunk)
                                        downloaded += len(chunk)
                                        if size:
                                            pct = (downloaded / size) * 100
                                            print(f"\rDownloading: {pct:.1f}%", end='', flush=True)

                                print(f"\n\nSaved to: {OUTPUT_FILE}")
                                return video_urls
                        except Exception as e:
                            print(f"  Failed: {e}")
                            continue

                return video_urls

    except ImportError:
        print("Playwright not installed. Run: pip install playwright && playwright install chromium")
    except Exception as e:
        print(f"Playwright failed: {e}")

    return None

def install_ytdlp():
    """Install yt-dlp if not present"""
    print("Installing yt-dlp...")
    subprocess.run([sys.executable, "-m", "pip", "install", "yt-dlp"], check=True)

def main():
    print("=" * 50)
    print("Guidde Video Downloader")
    print("=" * 50)
    print(f"URL: {VIDEO_URL}")
    print(f"Output: {OUTPUT_FILE}")
    print()

    # Check if yt-dlp is installed
    try:
        subprocess.run(["yt-dlp", "--version"], capture_output=True, check=True)
    except FileNotFoundError:
        install_ytdlp()

    # Try different methods
    if try_ytdlp():
        print(f"\nSuccess! Video saved to: {OUTPUT_FILE}")
        return

    if try_ytdlp_with_cookies():
        print(f"\nSuccess! Video saved to: {OUTPUT_FILE}")
        return

    # Try Playwright as last resort
    urls = try_playwright()
    if urls:
        print("\nManual download: Copy one of the URLs above and paste in browser")
        print("Or run: yt-dlp '<URL>'")
        return

    print("\n" + "=" * 50)
    print("MANUAL DOWNLOAD INSTRUCTIONS:")
    print("=" * 50)
    print("1. Open Chrome and go to:")
    print(f"   {VIDEO_URL}")
    print("2. Press F12 -> Network tab")
    print("3. Play the video")
    print("4. Filter by 'media' or '.mp4'")
    print("5. Right-click video request -> Copy URL")
    print("6. Download with: curl -o video.mp4 '<URL>'")

if __name__ == "__main__":
    main()
