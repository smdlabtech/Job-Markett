#!/bin/bash

echo "🚀 Initialisation personnalisée..."

SQL_DIR="/src/sql"
FILES=("schema.sql" "indexes.sql" "triggers.sql")

for file in "${FILES[@]}"; do
  path="$SQL_DIR/$file"
  if [[ -f "$path" ]]; then
    echo "▶️ Exécution de $file..."
    psql -U "$JOBS_POSTGRES_USER" -d "$JOBS_POSTGRES_DB" -f "$path"
  else
    echo "⚠️ Fichier $path introuvable"
  fi
done

echo "✅ Tous les fichiers SQL ont été exécutés."