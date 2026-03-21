#!/bin/bash

# Commit-Message abfragen
read -p "Commit message: " msg

# Falls leer → abbrechen
if [ -z "$msg" ]; then
  echo "❌ Kein Commit-Text eingegeben"
  exit 1
fi

# Git Befehle
git add .
git commit -m "$msg"
git push origin main