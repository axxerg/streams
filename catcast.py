import json
import os
from pathlib import Path

import requests


def load_config(config_file="catcast-config.json"):
    """Load configuration from JSON file."""
    with open(config_file, "r", encoding="utf-8") as f:
        return json.load(f)


def get_current_program(channel_id):
    """Send POST request to get current program information."""
    url = f"https://api.catcast.tv/api/channels/{channel_id}/getcurrentprogram"

    try:
        response = requests.post(url, timeout=60)
        print(f"Channel {channel_id}: HTTP {response.status_code}")
        response.raise_for_status()
        return response.json()
    except requests.exceptions.RequestException as e:
        print(f"Error fetching data for channel {channel_id}: {e}")
        return None


def build_m3u8_content(stream_url):
    return f"""#EXTM3U
#EXT-X-VERSION:3
#EXT-X-STREAM-INF:BANDWIDTH=2000000
{stream_url}
"""


def create_or_update_m3u8_file(slug, stream_url, output_dir="catcast"):
    """Create or update M3U8 playlist file only if content changed."""
    Path(output_dir).mkdir(parents=True, exist_ok=True)

    output_file = os.path.join(output_dir, f"{slug}.m3u8")
    new_content = build_m3u8_content(stream_url)

    old_content = None
    if os.path.exists(output_file):
        with open(output_file, "r", encoding="utf-8") as f:
            old_content = f.read()

    if old_content == new_content:
        print(f"= Unchanged: {output_file}")
        return "unchanged"

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(new_content)

    if old_content is None:
        print(f"✓ Created: {output_file}")
        return "created"

    print(f"✓ Updated: {output_file}")
    return "updated"


def delete_m3u8_file(slug, output_dir="catcast"):
    """Delete M3U8 playlist file if it exists."""
    output_file = os.path.join(output_dir, f"{slug}.m3u8")

    if os.path.exists(output_file):
        try:
            os.remove(output_file)
            print(f"✗ Deleted: {output_file}")
            return True
        except Exception as e:
            print(f"Error deleting file {output_file}: {e}")
            return False
    else:
        print(f"✗ File not found: {output_file}")
        return False


def main():
    """Main function to process all channels."""
    try:
        config = load_config()
    except FileNotFoundError:
        print("Error: catcast-config.json not found")
        return
    except json.JSONDecodeError:
        print("Error: Invalid JSON in catcast-config.json")
        return

    created_channels = []
    updated_channels = []
    unchanged_channels = []
    failed_channels = []
    deleted_channels = []

    for channel in config:
        channel_id = channel.get("id")
        slug = channel.get("slug")

        if not channel_id or not slug:
            print(f"Skipping invalid channel entry: {channel}")
            continue

        print(f"\nProcessing channel: {slug} (ID: {channel_id})")

        response_data = get_current_program(channel_id)

        if not response_data:
            print(f"Failed to get data for channel {channel_id}")
            if delete_m3u8_file(slug):
                deleted_channels.append(slug)
            failed_channels.append(slug)
            continue

        if response_data.get("status") == 1 and "data" in response_data:
            data = response_data["data"]
            full_mobile_url = data.get("full_mobile_url")

            if full_mobile_url:
                result = create_or_update_m3u8_file(slug, full_mobile_url)

                if result == "created":
                    created_channels.append(slug)
                elif result == "updated":
                    updated_channels.append(slug)
                else:
                    unchanged_channels.append(slug)

                print(f"Successfully processed {slug}")
            else:
                print(f"No full_mobile_url found for channel {channel_id}")
                if delete_m3u8_file(slug):
                    deleted_channels.append(slug)
                failed_channels.append(slug)
        else:
            print(f"Invalid response status for channel {channel_id}")
            if delete_m3u8_file(slug):
                deleted_channels.append(slug)
            failed_channels.append(slug)

    print("\n" + "=" * 50)
    print("Processing Summary:")
    print("=" * 50)

    print(f"✓ Created: {len(created_channels)}")
    for slug in created_channels:
        print(f"  - {slug}")

    print(f"\n✓ Updated: {len(updated_channels)}")
    for slug in updated_channels:
        print(f"  - {slug}")

    print(f"\n= Unchanged: {len(unchanged_channels)}")
    for slug in unchanged_channels:
        print(f"  - {slug}")

    print(f"\n✗ Failed: {len(failed_channels)}")
    for slug in failed_channels:
        print(f"  - {slug}")

    print(f"\n✗ Deleted: {len(deleted_channels)}")
    for slug in deleted_channels:
        print(f"  - {slug}")

    print("\nProcessing complete!")


if __name__ == "__main__":
    main()
