# This file must be sourced, not run
DOTENV_FILE="$( dirname "${BASH_SOURCE[0]}" )/.env.docker-compose-native"
while read -r VAR; do
  export "${VAR?}"
done < "${DOTENV_FILE}"
