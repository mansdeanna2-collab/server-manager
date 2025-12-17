#!/bin/bash
# update_cookie.sh - Updates XSRF-TOKEN and jtti_session cookies in mm.py and id.py
#
# This script:
# 1. Sends POST request to https://user.jtti.cc/api/front/login
# 2. Extracts XSRF-TOKEN and jtti_session from response Set-Cookie headers
# 3. Updates mm.py and id.py with the new cookie values

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
MM_PY="$SCRIPT_DIR/mm.py"
ID_PY="$SCRIPT_DIR/id.py"

# Login request data (encrypted)
LOGIN_DATA='{"data":"y5wBR0U2o0CEb/8UFs4rMEjYLDl16utsB5TqjofHRYjV2WdLZxNv/0uLm9P7HIXx6491g3+UslgkgKRfr17nLI169L8BfytCehVJmGAg1nKeU/PvYe4JLbo9zjvKLp+iSWYVQkY1jQNpi1KnufeKpg=="}'

# Temporary file for response headers
TEMP_HEADERS=$(mktemp)
TEMP_RESPONSE=$(mktemp)

# Cleanup function
cleanup() {
    rm -f "$TEMP_HEADERS" "$TEMP_RESPONSE"
}
trap cleanup EXIT

echo "Sending login request to user.jtti.cc..."

# Send login request and capture response headers
HTTP_STATUS=$(curl -s -w "%{http_code}" \
    -X POST "https://user.jtti.cc/api/front/login" \
    -H "Host: user.jtti.cc" \
    -H "Content-Type: application/json" \
    -H "Accept: application/json, text/plain, */*" \
    -H "Origin: https://user.jtti.cc" \
    -H "Referer: https://user.jtti.cc/user/" \
    -H "User-Agent: Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/143.0.0.0 Safari/537.36" \
    -H "Cookie: locale=en" \
    -D "$TEMP_HEADERS" \
    -d "$LOGIN_DATA" \
    -o "$TEMP_RESPONSE")

echo "HTTP Status: $HTTP_STATUS"

if [ "$HTTP_STATUS" != "200" ]; then
    echo "Error: Login request failed with status $HTTP_STATUS"
    cat "$TEMP_RESPONSE"
    exit 1
fi

# Check response for success
RESPONSE_CODE=$(cat "$TEMP_RESPONSE" | grep -o '"code":[0-9]*' | head -1 | grep -o '[0-9]*')
if [ "$RESPONSE_CODE" != "0" ]; then
    echo "Error: Login failed"
    cat "$TEMP_RESPONSE"
    exit 1
fi

echo "Login successful!"
cat "$TEMP_RESPONSE"
echo ""

# Extract XSRF-TOKEN from Set-Cookie header
XSRF_TOKEN=$(grep -i "Set-Cookie:.*XSRF-TOKEN=" "$TEMP_HEADERS" | sed -n 's/.*XSRF-TOKEN=\([^;]*\).*/\1/p' | head -1)

# Extract jtti_session from Set-Cookie header
JTTI_SESSION=$(grep -i "Set-Cookie:.*jtti_session=" "$TEMP_HEADERS" | sed -n 's/.*jtti_session=\([^;]*\).*/\1/p' | head -1)

echo "Extracted cookies:"
echo "XSRF-TOKEN: ${XSRF_TOKEN:0:50}..."
echo "jtti_session: ${JTTI_SESSION:0:50}..."

if [ -z "$XSRF_TOKEN" ] || [ -z "$JTTI_SESSION" ]; then
    echo "Error: Failed to extract cookies from response"
    echo "Response headers:"
    cat "$TEMP_HEADERS"
    exit 1
fi

# Update mm.py if it exists
if [ -f "$MM_PY" ]; then
    echo "Updating mm.py..."
    # Use sed to replace XSRF-TOKEN value
    sed -i "s/\"XSRF-TOKEN\":[[:space:]]*\"[^\"]*\"/\"XSRF-TOKEN\": \"$XSRF_TOKEN\"/g" "$MM_PY"
    # Use sed to replace jtti_session value
    sed -i "s/\"jtti_session\":[[:space:]]*\"[^\"]*\"/\"jtti_session\": \"$JTTI_SESSION\"/g" "$MM_PY"
    echo "mm.py updated successfully"
else
    echo "Warning: mm.py not found at $MM_PY"
fi

# Update id.py if it exists
if [ -f "$ID_PY" ]; then
    echo "Updating id.py..."
    # Use sed to replace XSRF-TOKEN value
    sed -i "s/\"XSRF-TOKEN\":[[:space:]]*\"[^\"]*\"/\"XSRF-TOKEN\": \"$XSRF_TOKEN\"/g" "$ID_PY"
    # Use sed to replace jtti_session value
    sed -i "s/\"jtti_session\":[[:space:]]*\"[^\"]*\"/\"jtti_session\": \"$JTTI_SESSION\"/g" "$ID_PY"
    echo "id.py updated successfully"
else
    echo "Warning: id.py not found at $ID_PY"
fi

echo ""
echo "Cookie update completed successfully!"
echo "New XSRF-TOKEN: $XSRF_TOKEN"
echo "New jtti_session: $JTTI_SESSION"
