#!/bin/bash
# install-trishul-snmp-docker.sh - Deploy Trishul SNMP Studio from GHCR
# Usage: ./install-trishul-snmp-docker.sh [up|down|restart|pull|logs|status|backup|restore]

set -e

# Config
GHCR_USER="tosumitdhaka"
BACKEND_IMAGE="ghcr.io/${GHCR_USER}/trishul-snmp-backend:latest"
FRONTEND_IMAGE="ghcr.io/${GHCR_USER}/trishul-snmp-frontend:latest"
VOLUME_NAME="trishul-snmp-data"

# Customizable ports
BACKEND_PORT="${BACKEND_PORT:-8000}"
FRONTEND_PORT="${FRONTEND_PORT:-8080}"

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

check_ghcr_login() {
    docker pull "$BACKEND_IMAGE" >/dev/null 2>&1
}

login_ghcr() {
    echo -e "${BLUE}🔐 Checking GHCR access...${NC}"
    
    if check_ghcr_login; then
        echo -e "${GREEN}✅ GHCR access OK${NC}"
        return 0
    fi
    
    echo -e "${YELLOW}⚠️  Authentication required${NC}"
    
    if [ -n "$GHCR_TOKEN" ]; then
        echo -e "${BLUE}Using GHCR_TOKEN from environment...${NC}"
        echo "$GHCR_TOKEN" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
    else
        echo ""
        echo -e "${BLUE}Enter GitHub PAT (or press Enter to skip):${NC}"
        read -s -p "Token: " token
        echo ""
        
        if [ -n "$token" ]; then
            echo "$token" | docker login ghcr.io -u "$GHCR_USER" --password-stdin
        else
            echo -e "${YELLOW}⚠️  Skipping login...${NC}"
        fi
    fi
    
    if check_ghcr_login; then
        echo -e "${GREEN}✅ GHCR login successful${NC}"
    else
        echo -e "${RED}❌ Failed to access images${NC}"
        exit 1
    fi
}

pull_images() {
    login_ghcr
    echo "📥 Pulling images..."
    docker pull "$BACKEND_IMAGE"
    docker pull "$FRONTEND_IMAGE"
    echo -e "${GREEN}✅ Images pulled${NC}"
}

setup_environment() {
    # Create Docker volume if not exists
    if ! docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1; then
        echo "📦 Creating Docker volume: $VOLUME_NAME"
        docker volume create "$VOLUME_NAME"
        echo -e "${GREEN}✅ Volume created${NC}"
    else
        echo -e "${GREEN}✅ Volume exists: $VOLUME_NAME${NC}"
    fi
}

run_containers() {
    pull_images
    setup_environment
    
    echo "🚀 Starting containers..."
    echo "   Backend port: $BACKEND_PORT"
    echo "   Frontend port: $FRONTEND_PORT"
    echo "   Data volume: $VOLUME_NAME"
    
    # Backend
    docker run -d \
        --name trishul-snmp-backend \
        --network host \
        -v "$VOLUME_NAME:/app/data" \
        -e APP_NAME="Trishul SNMP Studio" \
        -e APP_VERSION="1.1.5" \
        --restart unless-stopped \
        "$BACKEND_IMAGE" \
        uvicorn main:app --host 0.0.0.0 --port "$BACKEND_PORT"
    
    # Create nginx config
    cat > /tmp/trishul-nginx-$FRONTEND_PORT.conf << EOF
server {
    listen $FRONTEND_PORT;
    server_name localhost;
    client_max_body_size 50M;
    root /usr/share/nginx/html;
    index index.html;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        proxy_pass http://localhost:$BACKEND_PORT;
        proxy_http_version 1.1;
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
    }

    location ~* \.html$ {
        add_header Cache-Control "no-store, no-cache, must-revalidate";
        expires off;
    }
}
EOF
    
    # Frontend
    docker run -d \
        --name trishul-snmp-frontend \
        --network host \
        -v /tmp/trishul-nginx-$FRONTEND_PORT.conf:/etc/nginx/conf.d/default.conf:ro \
        --restart unless-stopped \
        "$FRONTEND_IMAGE"
    
    echo ""
    echo -e "${GREEN}✅ Trishul SNMP Studio is running!${NC}"
    echo ""
    echo "🌐 Frontend: http://localhost:$FRONTEND_PORT"
    echo "🔧 Backend: http://localhost:$BACKEND_PORT"
    echo "📦 Volume: $VOLUME_NAME"
    echo ""
    echo "Default login: admin / admin123"
    echo ""
}

stop_containers() {
    echo "🛑 Stopping containers..."
    docker stop trishul-snmp-backend trishul-snmp-frontend 2>/dev/null || true
    docker rm trishul-snmp-backend trishul-snmp-frontend 2>/dev/null || true
    rm -f /tmp/trishul-nginx-*.conf
    echo -e "${GREEN}✅ Containers stopped${NC}"
}

restart_containers() {
    stop_containers
    run_containers
}

show_logs() {
    docker logs -f trishul-snmp-backend
}

show_status() {
    echo "📊 Container status:"
    docker ps --filter "name=trishul-snmp" --format "table {{.Names}}\t{{.Status}}"
    echo ""
    echo "⚙️  Configuration:"
    echo "   Backend port: $BACKEND_PORT"
    echo "   Frontend port: $FRONTEND_PORT"
    echo "   Data volume: $VOLUME_NAME"
    
    if docker volume inspect "$VOLUME_NAME" >/dev/null 2>&1; then
        local mount_point=$(docker volume inspect "$VOLUME_NAME" --format '{{.Mountpoint}}')
        echo "   Volume path: $mount_point"
        echo "   Volume size: $(docker system df -v | grep "$VOLUME_NAME" | awk '{print $3}')"
    fi
}

backup_data() {
    local backup_file="trishul-backup-$(date +%Y%m%d-%H%M%S).tar.gz"
    echo "💾 Creating backup: $backup_file"
    
    docker run --rm \
        -v "$VOLUME_NAME:/data" \
        -v "$(pwd):/backup" \
        alpine tar czf "/backup/$backup_file" -C /data .
    
    echo -e "${GREEN}✅ Backup created: $backup_file${NC}"
}

restore_data() {
    local backup_file="$1"
    
    if [ -z "$backup_file" ]; then
        echo -e "${RED}Error: Backup file not specified${NC}"
        echo "Usage: $0 restore <backup-file.tar.gz>"
        exit 1
    fi
    
    if [ ! -f "$backup_file" ]; then
        echo -e "${RED}Error: Backup file not found: $backup_file${NC}"
        exit 1
    fi
    
    echo "📥 Restoring from: $backup_file"
    
    docker run --rm \
        -v "$VOLUME_NAME:/data" \
        -v "$(pwd):/backup" \
        alpine sh -c "rm -rf /data/* && tar xzf /backup/$backup_file -C /data"
    
    echo -e "${GREEN}✅ Data restored${NC}"
}

case "${1:-up}" in
    up) run_containers ;;
    down) stop_containers ;;
    restart) restart_containers ;;
    pull) pull_images ;;
    logs) show_logs ;;
    status) show_status ;;
    backup) backup_data ;;
    restore) restore_data "$2" ;;
    *)
        echo "Usage: $0 {up|down|restart|pull|logs|status|backup|restore}"
        echo ""
        echo "Commands:"
        echo "  up       - Start containers"
        echo "  down     - Stop containers"
        echo "  restart  - Restart containers"
        echo "  pull     - Pull latest images"
        echo "  logs     - Show backend logs"
        echo "  status   - Show status"
        echo "  backup   - Backup data to tar.gz"
        echo "  restore  - Restore from backup"
        echo ""
        echo "Environment variables:"
        echo "  BACKEND_PORT   - Backend port (default: 8000)"
        echo "  FRONTEND_PORT  - Frontend port (default: 8080)"
        echo "  GHCR_TOKEN     - GitHub PAT (optional)"
        echo ""
        echo "Examples:"
        echo "  $0 up"
        echo "  $0 backup"
        echo "  $0 restore trishul-backup-20260203-123456.tar.gz"
        echo "  FRONTEND_PORT=3000 $0 up"
        exit 1
        ;;
esac
