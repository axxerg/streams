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

    if not isinstance(config, list):
        print("Error: catcast-config.json must contain a list")
        return

    print(f"Loaded {len(config)} entries from catcast-config.json")

    if len(config) == 0:
        print("Warning: catcast-config.json is empty")
        return

    created_channels = []
    updated_channels = []
    unchanged_channels = []
    failed_channels = []
    deleted_channels = []

    valid_entries = 0

    for channel in config:
        if not isinstance(channel, dict):
            print(f"Skipping non-dict entry: {channel}")
            continue

        channel_id = channel.get("id")
        slug = channel.get("slug")

        if not channel_id or not slug:
            print(f"Skipping invalid channel entry: {channel}")
            continue

        valid_entries += 1
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

    print(f"\nValid entries processed: {valid_entries}")
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
