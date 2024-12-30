#!/bin/bash

# Check if an argument is supplied
if [ $# -ne 1 ]; then
  echo "Usage: $0 [local|prod]"
  exit 1
fi

# Set the replacement words based on the argument
if [ "$1" == "prod" ]; then
  search_word="settings.local"
  replace_word="settings.production"
  export GOOGLE_CLOUD_PROJECT=vault-446014
  export USE_CLOUD_SQL_AUTH_PROXY=true
  echo "Environment variables set for production."
elif [ "$1" == "local" ]; then
  search_word="settings.production"
  replace_word="settings.local"
  unset GOOGLE_CLOUD_PROJECT
  unset USE_CLOUD_SQL_AUTH_PROXY
  echo "Environment variables unset for local."
else
  echo "Invalid argument. Use 'local', 'prod' or 'heroku'."
  exit 1
fi

# Get the name of the script file
script_name=$(basename "$0")

# Find all files in the current directory and its subdirectories, excluding the script file itself
find . -type f -name "*.py" ! -name "$script_name" ! -path "./.env/*" -exec sed -i "s/\b$search_word\b/$replace_word/g" {} +

echo "Replaced all occurrences of '$search_word' with '$replace_word'."
