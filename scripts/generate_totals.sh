#!/bin/bash

# Script to generate .env.totals file with monthly and yearly totals from database
# Usage: ./scripts/generate_totals.sh [database_path]

set -e

# Default database path
DB_PATH="${1:-transactions.db}"
OUTPUT_FILE=".env.totals"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Generating totals from database: ${DB_PATH}${NC}"

# Check if database exists
if [ ! -f "$DB_PATH" ]; then
    echo -e "${RED}Error: Database file not found: ${DB_PATH}${NC}"
    echo "Please provide the correct path to your transactions.db file"
    echo "Usage: $0 [database_path]"
    exit 1
fi

# Check if sqlite3 is available
if ! command -v sqlite3 &> /dev/null; then
    echo -e "${RED}Error: sqlite3 command not found${NC}"
    echo "Please install sqlite3 to run this script"
    exit 1
fi

# Create temporary SQL file for complex queries
TEMP_SQL=$(mktemp)

cat > "$TEMP_SQL" << 'EOF'
-- Query to get monthly gross pay totals
SELECT
    strftime('%Y', statement_date) as year,
    strftime('%m', statement_date) as month,
    SUM(COALESCE(gross_pay, 0)) as total_gross
FROM transactions_adp
WHERE gross_pay IS NOT NULL AND gross_pay != 0
GROUP BY year, month
ORDER BY year, month;

-- Query to get monthly net pay totals
SELECT
    strftime('%Y', statement_date) as year,
    strftime('%m', statement_date) as month,
    SUM(COALESCE(net_pay, 0)) as total_net
FROM transactions_adp
WHERE net_pay IS NOT NULL AND net_pay != 0
GROUP BY year, month
ORDER BY year, month;

-- Query to get yearly transaction counts
SELECT
    strftime('%Y', statement_date) as year,
    COUNT(*) as transaction_count
FROM transactions_adp
GROUP BY year
ORDER BY year;
EOF

echo -e "${YELLOW}Querying database for totals...${NC}"

# Initialize output file
> "$OUTPUT_FILE"

# Query monthly gross pay totals
echo -e "${YELLOW}Processing monthly gross pay totals...${NC}"
sqlite3 "$DB_PATH" "SELECT strftime('%Y', statement_date) as year, strftime('%m', statement_date) as month, SUM(COALESCE(gross_pay, 0)) as total_gross FROM transactions_adp WHERE gross_pay IS NOT NULL AND gross_pay != 0 GROUP BY year, month ORDER BY year, month;" | while IFS='|' read -r year month total; do
    if [ -n "$year" ] && [ -n "$month" ] && [ -n "$total" ]; then
        # Remove leading zero from month
        month_num=$(echo "$month" | sed 's/^0*//')
        echo "G_${year}_${month_num}=${total}" >> "$OUTPUT_FILE"
        echo -e "  ${GREEN}G_${year}_${month_num}=${total}${NC}"
    fi
done

# Query monthly net pay totals
echo -e "${YELLOW}Processing monthly net pay totals...${NC}"
sqlite3 "$DB_PATH" "SELECT strftime('%Y', statement_date) as year, strftime('%m', statement_date) as month, SUM(COALESCE(net_pay, 0)) as total_net FROM transactions_adp WHERE net_pay IS NOT NULL AND net_pay != 0 GROUP BY year, month ORDER BY year, month;" | while IFS='|' read -r year month total; do
    if [ -n "$year" ] && [ -n "$month" ] && [ -n "$total" ]; then
        # Remove leading zero from month
        month_num=$(echo "$month" | sed 's/^0*//')
        echo "N_${year}_${month_num}=${total}" >> "$OUTPUT_FILE"
        echo -e "  ${GREEN}N_${year}_${month_num}=${total}${NC}"
    fi
done

# Query yearly transaction counts
echo -e "${YELLOW}Processing yearly transaction counts...${NC}"
sqlite3 "$DB_PATH" "SELECT strftime('%Y', statement_date) as year, COUNT(*) as transaction_count FROM transactions_adp GROUP BY year ORDER BY year;" | while IFS='|' read -r year count; do
    if [ -n "$year" ] && [ -n "$count" ]; then
        echo "T_${year}=${count}" >> "$OUTPUT_FILE"
        echo -e "  ${GREEN}T_${year}=${count}${NC}"
    fi
done

# Clean up temporary file
rm -f "$TEMP_SQL"

echo -e "${GREEN}✓ Generated ${OUTPUT_FILE} successfully!${NC}"
echo -e "${YELLOW}File contents:${NC}"
echo "----------------------------------------"
cat "$OUTPUT_FILE"
echo "----------------------------------------"

# Summary
echo -e "${GREEN}Summary:${NC}"
echo -e "  - Monthly gross pay totals: $(grep -c '^G_' "$OUTPUT_FILE") entries"
echo -e "  - Monthly net pay totals: $(grep -c '^N_' "$OUTPUT_FILE") entries"
echo -e "  - Yearly transaction counts: $(grep -c '^T_' "$OUTPUT_FILE") entries"
echo -e "  - Total entries: $(wc -l < "$OUTPUT_FILE")"

echo -e "${GREEN}Done!${NC}"
