#!/bin/bash

# Konfiguracja
VOLUMES_DIR="/var/lib/docker/volumes"
BACKUP_DIR="/home/pawwlad/project/jhInDocker/backups"
DATE=$(date +%F)
TARGET_DIR="$BACKUP_DIR/$DATE"

# Tworzenie katalogu backupowego
mkdir -p "$TARGET_DIR"

# Funkcja sprawdzająca, czy nazwa należy do wykładowcy (nie ma 6 cyfr na początku)
is_teacher() {
    local username=$(basename "$1" | sed 's/jupyterhub-user-//;s/-my_public//;s/-work//')
    [[ ! $username =~ ^[0-9]{6} ]]
}

# Backup woluminów wykładowców (my_public i work)
for volume in "$VOLUMES_DIR"/jupyterhub-user-*; do
    if [ -d "$volume" ] && is_teacher "$volume"; then
        volume_type=$(basename "$volume" | awk -F'-' '{print $NF}')  # my_public lub work
        echo "Kopiowanie woluminu WYKŁADOWCY: $(basename "$volume") (typ: $volume_type)"
        cp -a "$volume" "$TARGET_DIR/"
    fi
done

# Backup woluminu publicznego (dla wszystkich)
if [ -d "$VOLUMES_DIR/jupyterhub-public" ]; then
    echo "Kopiowanie woluminu publicznego"
    cp -a "$VOLUMES_DIR/jupyterhub-public" "$TARGET_DIR/"
fi

# Ustawienie uprawnień dla pawwlad
setfacl -R -m u:pawwlad:r-x "$TARGET_DIR"
echo "Dodano prawa odczytu dla użytkownika pawwlad"

# Podsumowanie
echo "Backup zakończony. Zapisano w: $TARGET_DIR"
ls -lh "$TARGET_DIR"