import json
import random
import uuid
import psycopg2
from psycopg2 import extras
from datetime import datetime, timedelta

# --- CONFIGURATION ---
DB_DSN = "postgresql://postgres:jCDUOCWCaHvQJsecNgDwVLybzYUzWQAa@switchback.proxy.rlwy.net:37491/railway"
TOTAL_RECORDS = 3000
TABLE_NAME = "raw_payments_ingestion"

# Master Data
MERCHANTS = ["Shopito", "Rappi", "MercadoLibre",
             "CornerShop", "Falabella", "GameStore", "Netflix"]
PROVIDERS = ["Stripe", "dLocal", "PayU", "Adyen", "Kushki", "MercadoPago"]
COUNTRIES = ["MX", "CO", "PE", "CL", "AR", "BR", "US", "ES"]

# Scenario Weights
SCENARIO_WEIGHTS = [0.5, 0.15, 0.15, 0.1, 0.1]


def get_db_connection():
    return psycopg2.connect(DB_DSN)


def setup_database():
    print("🔧 Setting up the database...")
    conn = get_db_connection()
    cur = conn.cursor()
    # cur.execute(f"DROP TABLE IF EXISTS {TABLE_NAME};") # Uncomment if you want to clean the table
    cur.execute(f"""
        CREATE TABLE IF NOT EXISTS {TABLE_NAME} (
            id UUID PRIMARY KEY,
            payload JSONB NOT NULL,
            is_processed BOOLEAN DEFAULT FALSE,
            created_at TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    print("✅ Table ready.")


def generate_xml_string(data):
    # In XML, the message is placed in <RetMsg> or <AuthTxt>
    return f"""<Tx><MerchID>{data['merchant_id']}</MerchID><Org>{data['origin']}</Org><Val>{data['amount']}</Val><Stat>{data['status_cat']}</Stat><RetMsg>{data['message']}</RetMsg></Tx>"""


def create_chaos_record():
    scenario = random.choices([0, 1, 2, 3, 4], weights=SCENARIO_WEIGHTS)[0]

    # Base Values
    merchant_name = random.choice(MERCHANTS)
    merchant_uuid = str(uuid.uuid4())
    provider = random.choice(PROVIDERS)
    destination_country = random.choice(["MX", "CO", "PE", "AR"])
    origin_country = random.choice(COUNTRIES)

    amount = round(random.uniform(20.0, 500.0), 2)
    latency = random.randint(50, 800)

    # --- MESSAGE AND STATUS LOGIC ---
    http_code = 200
    status_category = "APPROVED"
    # Varied success messages
    message_text = random.choice(
        ["AUTHORIZED", "00_SUCCESS", "APPROVED_BY_ISSUER", "OK"])

    # Case 1: Stripe Mexico (Technical Failure)
    if scenario == 1:
        provider = "Stripe"
        destination_country = "MX"
        if random.random() < 0.85:
            http_code = 402
            status_category = "FAILED"
            # Stripe-specific messages
            message_text = random.choice(
                ["do_not_honor", "insufficient_funds", "card_velocity_exceeded"])

    # Case 2: Shopito Low Conversion (Risk)
    elif scenario == 2:
        merchant_name = "Shopito"
        if random.random() < 0.7:
            http_code = 422
            status_category = "FAILED"
            # Risk messages
            message_text = random.choice(
                ["risk_profile_high", "merchant_blacklist", "blocked_by_rules"])

    # Case 3: PSE Timeout (Infrastructure)
    elif scenario == 3:
        provider = "dLocal"
        destination_country = "CO"
        if random.random() < 0.9:
            latency = random.randint(15000, 60000)
            http_code = 504
            status_category = "ERROR"
            # Timeout messages
            message_text = "upstream_gateway_timeout_504"

    # Case 4: Fraud in Brazil
    elif scenario == 4:
        destination_country = "BR"
        origin_country = "RU"
        amount = round(random.uniform(1.0, 5.0), 2)
        http_code = 403
        status_category = "FAILED"
        message_text = "suspected_fraud_velocity_check"

    # --- DATA INJECTION (FORMATS) ---

    format_type = random.choice(['modern', 'legacy', 'nested', 'xml_hell'])
    transaction_id = str(uuid.uuid4())

    base_obj = {
        "id": str(uuid.uuid4()),
        "transactional_id": transaction_id,
        "merchant": {
            "name": merchant_name,
            "id": merchant_uuid,
            "country": destination_country
        },
        "data": {}
    }

    # Modern Format: The message is clear in 'response_message'
    if format_type == 'modern':
        base_obj['data'] = {
            "provider": provider,
            "origin_iso": origin_country,
            "amount_details": {"value": amount, "currency": "USD"},
            "status": status_category,
            "response_message": message_text,
            "meta": {"latency": latency, "code": http_code}
        }

    # Legacy Format: The message is in 'server_txt' or 'ret_msg'
    elif format_type == 'legacy':
        base_obj['data'] = {
            "p_id": provider,
            "card_country": origin_country,
            "amt": amount,
            "st_code": 1 if status_category == "APPROVED" else 0,
            "server_txt": message_text,
            "exec_ms": latency
        }

    # Nested Format: The message is deep in 'details.reason'
    elif format_type == 'nested':
        base_obj['data'] = {
            "audit": {
                "geo": {"m": destination_country, "u": origin_country},
                "gw": provider
            },
            "outcome": {
                "disposition": status_category,
                "details": {
                    "reason": message_text,
                    "http": http_code
                },
                "perf": latency
            }
        }

    # XML Format: The message is in <RetMsg>
    elif format_type == 'xml_hell':
        base_obj['data'] = {
            "type": "XML_BLOB",
            "content": generate_xml_string({
                "merchant_id": merchant_uuid,
                "origin": origin_country,
                "amount": amount,
                "status_cat": status_category,
                "message": message_text
            })
        }

    return (base_obj['id'], json.dumps(base_obj))


def main():
    setup_database()
    print(f"🚀 Generating {TOTAL_RECORDS} records...")

    data_batch = []
    for _ in range(TOTAL_RECORDS):
        data_batch.append(create_chaos_record())

    print("💾 Inserting into Railway...")
    conn = get_db_connection()
    cur = conn.cursor()
    query = f"INSERT INTO {TABLE_NAME} (id, payload) VALUES %s"

    try:
        extras.execute_values(cur, query, data_batch)
        conn.commit()
        print(f"✅ DONE. {TOTAL_RECORDS} records inserted.")
    except Exception as e:
        print(f"❌ ERROR: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()


if __name__ == "__main__":
    main()
