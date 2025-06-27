#!/bin/bash

set -e

echo "Testing Monitoring Stack..."

GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

check_service() {
    local service=$1
    local url=$2
    local expected_status=${3:-200}
    
    echo -n "Checking $service... "
    
    response=$(curl -s -o /dev/null -w "%{http_code}" $url 2>/dev/null || echo "000")
    
    if [ "$response" = "$expected_status" ]; then
        echo -e "${GREEN}OK${NC}"
        return 0
    else
        echo -e "${RED}Failed (HTTP $response)${NC}"
        return 1
    fi
}

echo "Checking Service Health..."
echo "=========================="

check_service "Backend API" "http://localhost:8000/api/v1/health"
check_service "Prometheus" "http://localhost:9090/-/healthy"
check_service "Grafana" "http://localhost:3001/api/health"
check_service "AlertManager" "http://localhost:9093/-/healthy"

echo ""
echo "Generating Test Traffic..."
echo "========================="

for i in {1..5}; do
    curl -s -X POST http://localhost:8000/api/v1/search \
        -H "Content-Type: application/json" \
        -d '{"image_data": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg==", "top_k": 5}' > /dev/null
    echo -n "."
done
echo " Done!"

echo ""
echo -e "${GREEN}Monitoring stack is operational!${NC}"
echo ""
echo "Access Points:"
echo "  - Grafana: http://localhost:3001 (admin/admin)"
echo "  - Prometheus: http://localhost:9090"
echo "  - AlertManager: http://localhost:9093"
