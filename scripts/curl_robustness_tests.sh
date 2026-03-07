#!/usr/bin/env bash
# Robustness / edge case tests for StackOverbid API
# Tests wrong inputs, authorization failures, and business rule violations.
#
# Run curl_main_flow.sh first because this script reuses the data it created.
# Usage: bash scripts/curl_robustness_tests.sh

BASE_URL="http://localhost:8000"

# helper to pull a value out of a JSON response
json_val() {
  echo "$1" | grep -o "\"$2\":[^,}]*" | head -1 | sed "s/\"$2\"://;s/\"//g"
}

# log in to get tokens (users were created by the main flow script)
RESP=$(curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"seller1","password":"password123"}')
SELLER_TOKEN=$(json_val "$RESP" access_token)

RESP=$(curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"bidder1","password":"password123"}')
BIDDER1_TOKEN=$(json_val "$RESP" access_token)

RESP=$(curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"bidder2","password":"password123"}')
BIDDER2_TOKEN=$(json_val "$RESP" access_token)

# create a fresh item for bid-guard tests
LONG_END=$(date -u -d "+1 hour" +"%Y-%m-%dT%H:%M:%SZ")
RESP=$(curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"Test Lamp\",\"description\":\"For robustness tests\",\"starting_price\":10,\"end_time\":\"$LONG_END\"}")
EDIT_ITEM_ID=$(json_val "$RESP" id)

# item 1 from main flow is already closed/paid
ITEM_ID=1

# grab the order id from main flow
RESP=$(curl -sS -X GET "$BASE_URL/payment/orders/1/receipt" \
  -H "Authorization: Bearer $BIDDER1_TOKEN")
ORDER_ID=$(json_val "$RESP" order_id)


# Auth errors

echo "Testing duplicate username (expect 400)"
curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"seller1","password":"password123","first_name":"Dup","last_name":"User","address":"X"}'
echo ""

echo "Testing short username (expect 422)"
curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"ab","password":"password123","first_name":"A","last_name":"B","address":"X"}'
echo ""

echo "Testing short password (expect 422)"
curl -sS -X POST "$BASE_URL/auth/signup" \
  -H "Content-Type: application/json" \
  -d '{"username":"newuser99","password":"short","first_name":"A","last_name":"B","address":"X"}'
echo ""

echo "Testing wrong password (expect 400)"
curl -sS -X POST "$BASE_URL/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username":"seller1","password":"wrongpassword"}'
echo ""

echo "Testing no auth token (expect 401)"
curl -sS -X GET "$BASE_URL/catalogue/items"
echo ""

echo "Testing invalid JWT (expect 401)"
curl -sS -X GET "$BASE_URL/catalogue/items/1" \
  -H "Authorization: Bearer invalidtoken123"
echo ""


# Item creation errors

echo "Testing empty title (expect 422)"
curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"   \",\"description\":\"Something\",\"starting_price\":10,\"end_time\":\"$(date -u -d '+1 hour' +'%Y-%m-%dT%H:%M:%SZ')\"}"
echo ""

echo "Testing negative price (expect 422)"
curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"Bad\",\"description\":\"Negative\",\"starting_price\":-5,\"end_time\":\"$(date -u -d '+1 hour' +'%Y-%m-%dT%H:%M:%SZ')\"}"
echo ""

echo "Testing past end_time (expect 422)"
curl -sS -X POST "$BASE_URL/auction/items" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d "{\"title\":\"Bad\",\"description\":\"Past\",\"starting_price\":10,\"end_time\":\"$(date -u -d '-1 hour' +'%Y-%m-%dT%H:%M:%SZ')\"}"
echo ""


# Bidding errors

echo "Testing bid on closed auction (expect 400)"
curl -sS -X POST "$BASE_URL/auction/items/$ITEM_ID/bid" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER2_TOKEN" \
  -d '{"amount":1000}'
echo ""

echo "Testing bid below starting price (expect 400)"
curl -sS -X POST "$BASE_URL/auction/items/$EDIT_ITEM_ID/bid" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"amount":5}'
echo ""

echo "Testing seller bids on own item (expect 403)"
curl -sS -X POST "$BASE_URL/auction/items/$EDIT_ITEM_ID/bid" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $SELLER_TOKEN" \
  -d '{"amount":100}'
echo ""


# Payment errors

echo "Testing non-winner tries to pay (expect 400/403)"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER2_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Carol Lee","expiration_date":"12/30","security_code":"123"}'
echo ""

echo "Testing double payment (expect 400)"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Bob Jones","expiration_date":"12/30","security_code":"123"}'
echo ""

echo "Testing card number too short (expect 422)"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"123456","name_on_card":"Bob Jones","expiration_date":"12/30","security_code":"123"}'
echo ""

echo "Testing expired card (expect 422)"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Bob Jones","expiration_date":"01/20","security_code":"123"}'
echo ""

echo "Testing CVV with letters (expect 422)"
curl -sS -X POST "$BASE_URL/payment/items/$ITEM_ID/pay" \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $BIDDER1_TOKEN" \
  -d '{"credit_card_number":"4111111111111111","name_on_card":"Bob Jones","expiration_date":"12/30","security_code":"12A"}'
echo ""


# Receipt errors

echo "Testing other user views receipt (expect 403)"
curl -sS -X GET "$BASE_URL/payment/orders/$ORDER_ID/receipt" \
  -H "Authorization: Bearer $BIDDER2_TOKEN"
echo ""

echo "Testing nonexistent order (expect 404)"
curl -sS -X GET "$BASE_URL/payment/orders/99999/receipt" \
  -H "Authorization: Bearer $BIDDER1_TOKEN"
echo ""

echo "All robustness tests done"
