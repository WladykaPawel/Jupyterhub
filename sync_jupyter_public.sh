#!/bin/bash

SOURCE_BASE="/var/lib/docker/volumes/jupyterhub-user-"
DEST_BASE="/var/lib/docker/volumes/jupyterhub-public/_data"

# Funkcja synchronizująca dane użytkownika
sync_user_data() {
    local username="$1"
    local source_path="${SOURCE_BASE}${username}-my_public/_data/"
    local dest_path="${DEST_BASE}/${username}/"

    if [ -d "$source_path" ]; then
        mkdir -p "$dest_path"
        rsync -av --delete "$source_path" "$dest_path" > /dev/null 2>&1
        echo "[$(date)] Zsynchronizowano dane użytkownika: $username"
    else
        echo "[$(date)] Brak folderu _data dla użytkownika: $username"
    fi
}

# Główna pętla monitorująca
while true; do
    # Znajdź wszystkie foldery użytkowników
    find "/var/lib/docker/volumes/" -maxdepth 1 -type d -name "jupyterhub-user-*-my_public" | while read -r user_folder; do
        username=$(basename "$user_folder" | sed 's/jupyterhub-user-\(.*\)-my_public/\1/')
        sync_user_data "$username"

        # Uruchom inotifywait w tle dla każdego folderu
        if ! pgrep -f "inotifywait.*${user_folder}/_data" > /dev/null; then
            inotifywait -r -m -e modify,create,delete --format "%w%f" "${user_folder}/_data/" | while read -r changed_file; do
                sync_user_data "$username"
            done &
        fi
    done
    sleep 5  # Odczekaj 5 sekund przed kolejnym skanem
done
