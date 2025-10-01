#!/bin/bash
# 为所有微服务设置 Alembic 迁移

set -e

SERVICES=(
    "user-service:user_db"
    "location-service:location_db"
    "content-service:content_db"
    "request-service:request_db"
    "notification-service:notification_db"
    "payment-service:payment_db"
    "safety-service:safety_db"
    "investment-service:investment_db"
)

TEMPLATE_DIR="auth-service"

for SERVICE_INFO in "${SERVICES[@]}"; do
    IFS=':' read -r SERVICE DB_NAME <<< "$SERVICE_INFO"
    echo "=================================================="
    echo "设置 $SERVICE 的 Alembic 配置..."
    echo "=================================================="
    
    # 创建目录
    mkdir -p "$SERVICE/alembic/versions"
    
    # 复制 alembic.ini
    if [ ! -f "$SERVICE/alembic.ini" ]; then
        cp "$TEMPLATE_DIR/alembic.ini" "$SERVICE/alembic.ini"
        echo "✓ 创建 alembic.ini"
    fi
    
    # 复制 script.py.mako
    if [ ! -f "$SERVICE/alembic/script.py.mako" ]; then
        cp "$TEMPLATE_DIR/alembic/script.py.mako" "$SERVICE/alembic/script.py.mako"
        echo "✓ 创建 script.py.mako"
    fi
    
    # 创建 env.py（需要根据服务调整）
    if [ ! -f "$SERVICE/alembic/env.py" ]; then
        cat > "$SERVICE/alembic/env.py" <<'EOF'
from logging.config import fileConfig
from sqlalchemy import engine_from_config
from sqlalchemy import pool
from alembic import context
import os
import sys

# Add the app directory to the Python path
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from app.db.base import Base
# Import all models here
try:
    from app.models import *
except ImportError:
    pass

# this is the Alembic Config object, which provides
# access to the values within the .ini file in use.
config = context.config

# Interpret the config file for Python logging.
# This line sets up loggers basically.
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# add your model's MetaData object here
# for 'autogenerate' support
target_metadata = Base.metadata


def get_url():
    return os.getenv("DATABASE_URL")


def run_migrations_offline() -> None:
    """Run migrations in 'offline' mode."""
    url = get_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    """Run migrations in 'online' mode."""
    configuration = config.get_section(config.config_ini_section)
    configuration["sqlalchemy.url"] = get_url()
    connectable = engine_from_config(
        configuration,
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection, target_metadata=target_metadata
        )

        with context.begin_transaction():
            context.run_migrations()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
EOF
        echo "✓ 创建 env.py"
    fi
    
    echo "✓ $SERVICE Alembic 配置完成"
    echo ""
done

echo "=================================================="
echo "所有服务的 Alembic 配置已完成！"
echo "=================================================="
echo ""
echo "接下来需要："
echo "1. 为每个服务手动创建初始迁移脚本"
echo "2. 在 Dockerfile 或启动脚本中添加 'alembic upgrade head'"
echo "3. 从 main.py 中移除 Base.metadata.create_all()"
