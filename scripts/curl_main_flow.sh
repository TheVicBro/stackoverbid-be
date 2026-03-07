#!/usr/bin/env bash
# Main flow script for StackOverbid API
# Walks through the full auction lifecycle: signup, login, create item,
# edit item, browse, bid, close auction, pay, and view receipt.
#
# Make sure the server is running and the DB is fresh before running.
# Usage: bash scripts/curl_main_flow.sh

BASE_URL="http://localhost:8000"

# helper to pull a value out of a JSON response
json_val() {
  echo "$1" | grep -o "\"$2\":[^,}]*" | head -1 | sed "s/\"$2\"://;s/\"//g"
}

# UC1.1 - Sign up three users (one seller, two bidders)
echo "Signing up seller"
curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"seller1","password":"password123","first_name":"Alice","last_name":"Smith","address":"123 Main St"}'
echo ""

echo "Signing up bidder1"
curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"bidder1","password":"password123","first_name":"Bob","last_name":"Jones","address":"456 Oak Ave"}'
echo ""

echo "Signing up bidder2"
curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"bidder2","password":"password123","first_name":"Carol","last_name":"Lee","address":"789 Pine Rd"}'
echo ""

# UC1.2 - Log in all three users
echo "Logging in"

RESP=$(curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"seller1","password":"password123"}')
echo "$RESP"
SELLER_TOKEN=$(json_val "$RESP" access_token)

RESP=$(curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"bidder1","password":"password123"}')
echo "$RESP"
BIDDER1_TOKEN=$(json_val "$RESP" access_token)

RESP=$(curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"bidder2","password":"password123"}')
echo "$RESP"
BIDDER2_TOKEN=$(json_val "$RESP" access_token)

# UC7 - Seller creates two auction items
echo "Creating auction item (Vintage Guitar, expires in 5s)"
END_TIME=$(date -u -d "+5 seconds" +"%Y-%m-%dT%H:%M:%SZ")

RESP=$(curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"Vintage Guitar\",\"description\":\"1965 Fender Stratocaster\",\"starting_price\":500,\"end_time\":\"$END_TIME\",\"shipping_time_days\":7,\"expedited_shipping_cost\":25}")
echo "$RESP"
ITEM_ID=$(json_val "$RESP" id)

# second item for editing (expires in 1 hour)
LONG_END=$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ")
RESP=$(curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"Old Lamp\",\"description\":\"A dusty lamp\",\"starting_price\":10,\"end_time\":\"$LONG_END\"}")
echo "$RESP"
EDIT_ITEM_ID=$(json_val "$RESP" id)

# UC8 - Edit item (no bids yet, so edit is allowed)
echo "Editing item"
curl -sS -X PATCH "$BASE_URL/auction/items/$EDIT_ITEM_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d '{"title":"Antique Lamp","description":"A beautifully restored antique lamp"}'
echo ""

# UC2 - Browse catalogue, search, view details
echo "Browsing catalogue"
curl -sS -X GET "$BASE_URL/catalogue/items" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

echo "Searching for 'Guitar'"
curl -sS -X GET "$BASE_URL/catalogue/items?keyword=Guitar" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

echo "Viewing item details"
curl -sS -X GET "$BASE_URL/catalogue/items/$ITEM_ID" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

# UC3 - Place bids (multiple bidders, increasing amounts)
echo "Placing bids"

curl -sS -X POST "$BASE_URL/auction/items/$ITEM_ID/bid" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"amount":550}'
echo ""

curl -sS -X POST "$BASE_URL/auction/items/$ITEM_ID/bid" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER2_TOKEN" \
  -d '{"amount":600}'
echo ""

curl -sS -X POST "$BASE_URL/auction/items/$ITEM_ID/bid" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"amount":750}'
echo ""

# UC4 - Wait for auction to expire, then seller closes it
echo "Waiting for auction to expire (6s)"
sleep 6

echo "Broadcasting auction end"
curl -sS -X POST "$BASE_URL/notifications/items/$ITEM_ID/broadcast-end" \
  -H "Authorization: Bearer $SELLER_TOKEN"
echo ""

echo "Checking winner notifications"
curl -sS -X GET "$BASE_URL/notifications/" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

echo "Checking loser notifications"
curl -sS -X GET "$BASE_URL/notifications/" \
  -H "Authorization: Bearer $BIDDER2_TOKEN"
echo ""

# UC5 - Winner pays
echo "Winner paying for item"
RESP=$(curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Bob Jones","expiration_date":"12/30","security_code":"123","expedited_shipping":false}')
echo "$RESP"
ORDER_ID=$(json_val "$RESP" order_id)

# UC6 - View receipt and shipment details
echo "Viewing receipt"
curl -sS -X GET "$BASE_URL/payment/orders/$ORDER_ID/receipt" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

echo "Done"
