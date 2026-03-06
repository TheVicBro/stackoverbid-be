#!/usr/bin/env bash
# =============================================================================
# StackOverbid API – curl script
# =============================================================================
# Demonstrates the main use-case flow and robustness checks.
#
# PREREQUISITES
#   1. Server running:  uvicorn app.main:app --reload
#   2. Fresh database:  delete stackoverbid.db before running
#
# USAGE
#   bash scripts/curl_tests.sh
# =============================================================================

BASE_URL="http://localhost:8000"

# Helper: extract a JSON value by key (handles both "key":"str" and "key":num)
json_val() {
  echo "$1" | grep -o "\"$2\":[^,}]*" | head -1 | sed "s/\"$2\"://;s/\"//g"
}

echo ""
echo "=============================="
echo " PART 1: Main Use-Case Flow"
echo "=============================="

# ── UC1: Sign Up ─────────────────────────────────────────────────────────────
echo ""
echo "--- UC1: Sign Up (seller + 2 bidders) ---"

curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"seller1","password":"password123","first_name":"Alice","last_name":"Smith","address":"123 Main St"}'
echo ""

curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"bidder1","password":"password123","first_name":"Bob","last_name":"Jones","address":"456 Oak Ave"}'
echo ""

curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"bidder2","password":"password123","first_name":"Carol","last_name":"Lee","address":"789 Pine Rd"}'
echo ""

# ── UC1.5: Login ─────────────────────────────────────────────────────────────
echo ""
echo "--- UC1.5: Login ---"

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

# ── UC7: Create Auction Item ─────────────────────────────────────────────────
echo ""
echo "--- UC7: Seller Creates Auction Item ---"

END_TIME=$(date -u -d "+5 seconds" +"%Y-%m-%dT%H:%M:%SZ")

RESP=$(curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"Vintage Guitar\",\"description\":\"1965 Fender Stratocaster\",\"starting_price\":500,\"end_time\":\"$END_TIME\",\"shipping_time_days\":7,\"expedited_shipping_cost\":25}")
echo "$RESP"
ITEM_ID=$(json_val "$RESP" id)

# Create a second item for edit/bid-guard tests (expires in 1 hour)
LONG_END=$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ")
RESP=$(curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"Old Lamp\",\"description\":\"A dusty lamp\",\"starting_price\":10,\"end_time\":\"$LONG_END\"}")
echo "$RESP"
EDIT_ITEM_ID=$(json_val "$RESP" id)

# ── UC8: Edit Item ───────────────────────────────────────────────────────────
echo ""
echo "--- UC8: Seller Edits Item ---"

curl -sS -X PATCH "$BASE_URL/auction/items/$EDIT_ITEM_ID" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d '{"title":"Antique Lamp","description":"A beautifully restored antique lamp"}'
echo ""

# ── UC2: Browse / Search Catalogue ───────────────────────────────────────────
echo ""
echo "--- UC2: Browse Catalogue ---"

curl -sS -X GET "$BASE_URL/catalogue/items" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

echo ""
echo "--- UC2: Search by keyword ---"

curl -sS -X GET "$BASE_URL/catalogue/items?keyword=Guitar" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

# ── UC2.3: View Item Details ─────────────────────────────────────────────────
echo ""
echo "--- UC2.3: View Item Details ---"

curl -sS -X GET "$BASE_URL/catalogue/items/$ITEM_ID" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

# ── UC3: Place Bids ──────────────────────────────────────────────────────────
echo ""
echo "--- UC3: Place Bids (competitive bidding) ---"

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

# ── Auction End ──────────────────────────────────────────────────────────────
echo ""
echo "--- Waiting for auction to expire (6s)... ---"
sleep 6

echo "--- Seller Broadcasts Auction End ---"

curl -sS -X POST "$BASE_URL/notifications/items/$ITEM_ID/broadcast-end" \
  -H "Authorization: Bearer $SELLER_TOKEN"
echo ""

# ── Notifications ────────────────────────────────────────────────────────────
echo ""
echo "--- Notifications (winner) ---"

curl -sS -X GET "$BASE_URL/notifications/" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

echo ""
echo "--- Notifications (loser) ---"

curl -sS -X GET "$BASE_URL/notifications/" \
  -H "Authorization: Bearer $BIDDER2_TOKEN"
echo ""

# ── UC4/UC5: Payment ─────────────────────────────────────────────────────────
echo ""
echo "--- UC4/UC5: Winner Pays ---"

RESP=$(curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Bob Jones","expiration_date":"12/30","security_code":"123","expedited_shipping":false}')
echo "$RESP"
ORDER_ID=$(json_val "$RESP" order_id)

# ── UC6: View Receipt ────────────────────────────────────────────────────────
echo ""
echo "--- UC6: View Receipt ---"

curl -sS -X GET "$BASE_URL/payment/orders/$ORDER_ID/receipt" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""


echo ""
echo "=============================="
echo " PART 2: Robustness Tests"
echo "=============================="

# ── Auth errors ──────────────────────────────────────────────────────────────
echo ""
echo "--- Duplicate username (expect 400) ---"
curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"seller1","password":"password123","first_name":"Dup","last_name":"User","address":"X"}'
echo ""

echo "--- Short username (expect 422) ---"
curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"ab","password":"password123","first_name":"A","last_name":"B","address":"X"}'
echo ""

echo "--- Short password (expect 422) ---"
curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser99","password":"short","first_name":"A","last_name":"B","address":"X"}'
echo ""

echo "--- Wrong password (expect 400) ---"
curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"seller1","password":"wrongpassword"}'
echo ""

echo "--- No auth token (expect 401) ---"
curl -sS -X GET "$BASE_URL/catalogue/items"
echo ""

echo "--- Invalid JWT (expect 401) ---"
curl -sS -X GET "$BASE_URL/catalogue/items/1" \
  -H "Authorization: Bearer invalidtoken123"
echo ""

# ── Item creation errors ─────────────────────────────────────────────────────
echo ""
echo "--- Empty title (expect 422) ---"
curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"   \",\"description\":\"Something\",\"starting_price\":10,\"end_time\":\"$(date -u -d '+1 hour' +'%Y-%m-%dT%H:%M:%SZ')\"}"
echo ""

echo "--- Negative price (expect 422) ---"
curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"Bad\",\"description\":\"Negative\",\"starting_price\":-5,\"end_time\":\"$(date -u -d '+1 hour' +'%Y-%m-%dT%H:%M:%SZ')\"}"
echo ""

echo "--- Past end_time (expect 422) ---"
curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"Bad\",\"description\":\"Past\",\"starting_price\":10,\"end_time\":\"$(date -u -d '-1 hour' +'%Y-%m-%dT%H:%M:%SZ')\"}"
echo ""

# ── Bidding errors ───────────────────────────────────────────────────────────
echo ""
echo "--- Bid on closed auction (expect 400) ---"
curl -sS -X POST "$BASE_URL/auction/items/$ITEM_ID/bid" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER2_TOKEN" \
  -d '{"amount":1000}'
echo ""

echo "--- Bid below starting price (expect 400) ---"
curl -sS -X POST "$BASE_URL/auction/items/$EDIT_ITEM_ID/bid" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"amount":5}'
echo ""

echo "--- Seller bids on own item (expect 403) ---"
curl -sS -X POST "$BASE_URL/auction/items/$EDIT_ITEM_ID/bid" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d '{"amount":100}'
echo ""

# ── Payment errors ───────────────────────────────────────────────────────────
echo ""
echo "--- Non-winner tries to pay (expect 400) ---"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER2_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Carol Lee","expiration_date":"12/30","security_code":"123"}'
echo ""

echo "--- Double payment (expect 400) ---"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Bob Jones","expiration_date":"12/30","security_code":"123"}'
echo ""

echo "--- Invalid card number / Luhn (expect 422) ---"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"1234567890123456","name_on_card":"Bob Jones","expiration_date":"12/30","security_code":"123"}'
echo ""

echo "--- Expired card (expect 422) ---"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Bob Jones","expiration_date":"01/20","security_code":"123"}'
echo ""

echo "--- CVV with letters (expect 422) ---"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Bob Jones","expiration_date":"12/30","security_code":"12A"}'
echo ""

# ── Receipt errors ───────────────────────────────────────────────────────────
echo ""
echo "--- Other user views receipt (expect 403) ---"
curl -sS -X GET "$BASE_URL/payment/orders/$ORDER_ID/receipt" \
  -H "Authorization: Bearer $BIDDER2_TOKEN"
echo ""

echo "--- Nonexistent order (expect 404) ---"
curl -sS -X GET "$BASE_URL/payment/orders/99999/receipt" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

echo ""
echo "=============================="
echo " Done."
echo "=============================="
