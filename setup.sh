#!/bin/bash
# ZFlow 一键启动脚本
# 支持 macOS 和 Linux
# 可重复运行：首次安装 / 代码更新后重新配置

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

info() { echo -e "${GREEN}[INFO]${NC} $1"; }
warn() { echo -e "${YELLOW}[WARN]${NC} $1"; }
error() { echo -e "${RED}[ERROR]${NC} $1"; exit 1; }
step() { echo -e "${BLUE}==> ${NC}$1"; }

# 检查命令是否存在
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# 检测操作系统
detect_os() {
    if [[ "$OSTYPE" == "darwin"* ]]; then
        OS="macos"
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        OS="linux"
    else
        error "不支持的操作系统: $OSTYPE"
    fi
    info "检测到操作系统: $OS"
}

# 检查并安装依赖
check_dependencies() {
    info "检查系统依赖..."

    # Python 3
    if ! command_exists python3; then
        error "未找到 Python 3，请先安装 Python 3.10+"
    fi
    PYTHON_VERSION=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    info "Python 版本: $PYTHON_VERSION"

    # Node.js
    if ! command_exists node; then
        error "未找到 Node.js，请先安装 Node.js 18+
        exit 1
    fi
    NODE_VERSION=$(node --version)
    info "Node.js 版本: $NODE_VERSION"

    # npm
    if ! command_exists npm; then
        error "未找到 npm"
    fi

    # PostgreSQL
    if ! command_exists psql; then
        warn "未找到 PostgreSQL，正在尝试安装..."
        if [[ "$OS" == "macos" ]]; then
            if command_exists brew; then
                brew install postgresql@14
                brew link postgresql@14
            else
                error "请先安装 Homebrew: https://brew.sh/"
            fi
        else
            error "请先安装 PostgreSQL: sudo apt install postgresql"
        fi
    fi
}

# 安装 Python 依赖
install_python_deps() {
    step "安装/更新 Python 依赖..."

    # 检查是否有 venv，没有则创建
    if [ ! -d ".venv" ]; then
        info "创建 Python 虚拟环境..."
        python3 -m venv .venv
    else
        info "虚拟环境已存在，更新依赖..."
    fi

    source .venv/bin/activate

    info "安装后端依赖..."
    pip install -q -r backend/requirements.txt || error "后端依赖安装失败"

    info "安装 worker 依赖..."
    pip install -q -r worker/requirements.txt || error "worker 依赖安装失败"

    info "安装 python-dotenv（用于 init_db）..."
    pip install -q python-dotenv
}

# 安装前端依赖
install_frontend_deps() {
    step "安装/更新前端依赖..."
    cd frontend
    npm install || error "前端依赖安装失败"
    cd ..
}

# 配置环境变量
setup_env() {
    info "配置环境变量..."

    if [ ! -f "backend/.env" ]; then
        if [ -f ".env.example" ]; then
            cp .env.example backend/.env
            info "已创建 backend/.env，请手动填入你的 API Keys"
        else
            warn "未找到 .env.example，创建默认配置..."
            cat > backend/.env << 'EOF'
APP_ENV=local
LOG_LEVEL=info

# Backend
API_HOST=0.0.0.0
API_PORT=8000
DATABASE_URL=postgresql+psycopg2://$(whoami)@localhost:5432/zflow_dev

# Worker
WORKER_POLL_INTERVAL_SECONDS=2

# LLM Provider
LLM_PROVIDER=glm
GLM_MODEL=glm-4.7
GLM_API_KEY=your_api_key_here

# Image Provider
IMAGE_PROVIDER=seedream
SEEDREAM_MODEL=doubao-seedream-4.5
SEEDREAM_API_KEY=your_api_key_here
SEEDREAM_API_BASE=https://open.bigmodel.cn/api/paas/v4
SEEDREAM_IMAGE_ENDPOINT=https://open.bigmodel.cn/api/paas/v4/images/generations
SEEDREAM_DEFAULT_SIZE=960x1280

# Video Provider
VIDEO_PROVIDER=vidu
VIDU_API_KEY=your_api_key_here
VIDU_VIDEO_ENDPOINT=https://open.bigmodel.cn/api/paas/v4/videos/generations
VIDU_VIDEO_MODEL=viduq2-pro-img2video
VIDU_VIDEO_DEFAULT_SIZE=960x1280
EOF
            warn "已创建 backend/.env，请填入你的 API Keys！"
        fi
    else
        info "backend/.env 已存在，跳过"
    fi
}

# 启动 PostgreSQL
start_postgres() {
    info "检查 PostgreSQL 服务..."

    # 尝试连接
    if psql -h localhost -U "$(whoami)" -c '\q' >/dev/null 2>&1; then
        info "PostgreSQL 已运行"
        return
    fi

    info "尝试启动 PostgreSQL..."
    if [[ "$OS" == "macos" ]]; then
        # macOS with Homebrew
        brew services start postgresql@14 2>/dev/null || \
        brew services start postgresql@15 2>/dev/null || \
        brew services start postgresql@16 2>/dev/null || \
        pg_ctl -D /usr/local/var/postgres start 2>/dev/null || \
        warn "无法自动启动 PostgreSQL，请手动启动"
    else
        # Linux
        sudo service postgresql start 2>/dev/null || \
        sudo systemctl start postgresql 2>/dev/null || \
        warn "无法自动启动 PostgreSQL，请手动启动"
    fi

    # 等待启动
    sleep 2
}

# 创建数据库
create_database() {
    info "检查数据库..."

    # 检测数据库用户
    DB_USER=$(whoami)
    if ! psql -h localhost -U "$DB_USER" -c '\q' >/dev/null 2>&1; then
        DB_USER="postgres"
        if ! psql -h localhost -U "$DB_USER" -c '\q' >/dev/null 2>&1; then
            warn "无法连接到 PostgreSQL，请手动创建数据库 zflow_dev"
            return
        fi
    fi

    # 检查数据库是否存在
    if psql -h localhost -U "$DB_USER" -lqt | cut -d \| -f 1 | grep -qw zflow_dev; then
        info "数据库 zflow_dev 已存在"
    else
        info "创建数据库 zflow_dev..."
        createdb -h localhost -U "$DB_USER" zflow_dev || \
        error "数据库创建失败，请手动创建: createdb zflow_dev"
    fi

    # 更新 .env 中的 DATABASE_URL
    sed -i.bak "s|DATABASE_URL=.*|DATABASE_URL=postgresql+psycopg2://$DB_USER@localhost:5432/zflow_dev|" backend/.env
    rm -f backend/.env.bak
}

# 初始化数据库表
init_database() {
    step "更新数据库表结构..."
    source .venv/bin/activate
    cd backend
    python -m app.db.init_db || error "数据库初始化失败"
    info "数据库表结构已更新（SQLAlchemy create_all 会自动处理新增表）"
    cd ..
}

# 启动服务
start_services() {
    echo ""
    echo "===================="
    echo "✅ 环境配置完成！"
    echo "===================="
    echo ""
    echo "执行以下命令启动服务："
    echo ""
    echo "  # 终端 1 - 后端"
    echo "  cd $(pwd)"
    echo "  source .venv/bin/activate"
    echo "  cd backend && source .env && uvicorn app.main:app --reload"
    echo ""
    echo "  # 终端 2 - 前端"
    echo "  cd $(pwd)/frontend"
    echo "  npm run dev"
    echo ""
    echo "访问: http://localhost:5173"
    echo ""
    echo "提示: 代码更新后，重新运行 ./setup.sh 即可更新依赖和数据库表结构"
    echo ""
}

# 主流程
main() {
    echo ""
    echo "🚀 ZFlow 环境配置"
    echo "===================="
    echo ""

    detect_os
    check_dependencies
    install_python_deps
    install_frontend_deps
    setup_env
    start_postgres
    create_database
    init_database
    start_services
}

main
