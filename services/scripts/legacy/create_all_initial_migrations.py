#!/usr/bin/env python3
"""
为所有微服务创建初始 Alembic 迁移脚本
"""

import os
import sys
from pathlib import Path

# 服务及其模型的映射
SERVICE_MODELS = {
    "user-service": {
        "db_name": "user_db",
        "models": ["user", "profile"],
        "imports": [
            "from app.models.user import User",
            "from app.models.profile import UserProfile, ProviderProfile",
        ],
    },
    "location-service": {
        "db_name": "location_db",
        "models": ["address", "saved_location"],
        "imports": [
            "from app.models.address import UserAddress",
            "from app.models.saved_location import SavedLocation",
        ],
        "needs_postgis": True,
    },
    "content-service": {
        "db_name": "content_db",
        "models": ["post", "comment", "media"],
        "imports": [],
    },
    "request-service": {
        "db_name": "request_db",
        "models": ["service_request"],
        "imports": [],
    },
    "notification-service": {
        "db_name": "notification_db",
        "models": ["notification"],
        "imports": [],
    },
    "payment-service": {
        "db_name": "payment_db",
        "models": ["payment", "payment_method"],
        "imports": [
            "from app.models.payment import Payment, PaymentHistory, Refund",
            "from app.models.payment_method import UserPaymentMethod, PaymentMethodUsage",
        ],
    },
    "safety-service": {
        "db_name": "safety_db",
        "models": ["report", "verification"],
        "imports": [],
    },
}


def create_migration_template(service_name, service_info):
    """为服务创建初始迁移模板"""

    migration_content = f'''"""Initial migration for {service_name}

Revision ID: 0001
Revises: 
Create Date: 2025-09-30 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '0001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    """
    此迁移将由 alembic revision --autogenerate 生成
    
    运行以下命令在开发环境生成实际的迁移内容:
    cd {service_name}
    export DATABASE_URL="postgresql://neighbor:password@localhost:5432/{service_info['db_name']}"
    alembic revision --autogenerate -m "Initial migration"
    
    或者手动填写表创建语句
    """
    pass


def downgrade() -> None:
    """Drop all tables"""
    pass
'''

    return migration_content


def main():
    services_dir = Path(__file__).parent

    for service_name, service_info in SERVICE_MODELS.items():
        service_path = services_dir / service_name
        versions_dir = service_path / "alembic" / "versions"

        if not versions_dir.exists():
            print(f"⚠️  {service_name}/alembic/versions 不存在，跳过")
            continue

        # 检查是否已有迁移文件
        existing_migrations = list(versions_dir.glob("*.py"))
        if existing_migrations:
            print(
                f"✓ {service_name} 已有迁移文件: {[m.name for m in existing_migrations]}"
            )
            continue

        # 创建初始迁移文件
        migration_file = versions_dir / "0001_initial_migration.py"
        content = create_migration_template(service_name, service_info)

        with open(migration_file, "w") as f:
            f.write(content)

        print(f"✓ 创建 {service_name}/alembic/versions/0001_initial_migration.py")

    print("\n" + "=" * 60)
    print("初始迁移模板已创建！")
    print("=" * 60)
    print("\n接下来的步骤:")
    print("1. 每个服务需要运行 'alembic revision --autogenerate' 生成完整迁移")
    print("2. 或者手动编辑迁移文件填写表创建语句")
    print("3. 部署时，服务将自动运行 'alembic upgrade head'")


if __name__ == "__main__":
    main()
