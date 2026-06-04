#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移脚本
用于安全更新数据库结构，添加新字段和表
"""
import os
import sys
import sqlite3
import shutil
from datetime import datetime

# 获取当前文件所在目录
current_dir = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, current_dir)

from db import db
from app import create_app
from config import DevelopmentConfig

# 数据库文件路径 - 使用 instance 文件夹下的数据库
DB_PATH = os.path.join(current_dir, 'instance', 'quant_platform_new.db')
BACKUP_PATH = os.path.join(current_dir, f'quant_platform_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.db')


def backup_database():
    """备份现有数据库"""
    if os.path.exists(DB_PATH):
        print(f"[1/6] 备份数据库到: {BACKUP_PATH}")
        shutil.copy2(DB_PATH, BACKUP_PATH)
        print("    ✓ 备份成功")
    else:
        print(f"[1/6] 数据库文件不存在，跳过备份")


def migrate_users_table():
    """迁移 users 表，添加新字段"""
    print("\n[2/6] 迁移 users 表...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # 获取现有列
        cursor.execute("PRAGMA table_info(users)")
        existing_columns = {col[1] for col in cursor.fetchall()}
        print(f"    现有列: {existing_columns}")
        
        # 需要添加的新列
        new_columns = [
            ('avatar', 'TEXT', "''"),
            ('phone', 'VARCHAR(20)', "''"),
            ('bio', 'TEXT', "''"),
            ('theme_preference', 'VARCHAR(10)', "'light'"),
            ('refresh_frequency', 'INTEGER', '5'),
            ('notification_email', 'BOOLEAN', '1'),
            ('notification_browser', 'BOOLEAN', '0'),
            ('backtest_default_capital', 'FLOAT', '100000.0'),
            ('backtest_default_fee', 'FLOAT', '0.0003'),
        ]
        
        for col_name, col_type, default_val in new_columns:
            if col_name not in existing_columns:
                try:
                    cursor.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_type} DEFAULT {default_val}")
                    print(f"    ✓ 添加列: {col_name}")
                except Exception as e:
                    print(f"    ⚠ 添加列 {col_name} 失败: {e}")
            else:
                print(f"    ✓ 列已存在: {col_name}")
        
        conn.commit()
        print("    ✓ users 表迁移完成")
    except Exception as e:
        print(f"    ✗ users 表迁移失败: {e}")
    finally:
        conn.close()


def create_notifications_table():
    """创建 notifications 表"""
    print("\n[3/6] 创建 notifications 表...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                type VARCHAR(50) NOT NULL DEFAULT 'system',
                is_read BOOLEAN NOT NULL DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        print("    ✓ notifications 表创建成功")
    except Exception as e:
        print(f"    ⚠ 表创建失败: {e}")
    finally:
        conn.close()


def create_feedback_table():
    """创建 feedback 表"""
    print("\n[4/6] 创建 feedback 表...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS feedback (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type VARCHAR(50) NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                status VARCHAR(50) NOT NULL DEFAULT 'pending',
                admin_reply TEXT,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        conn.commit()
        print("    ✓ feedback 表创建成功")
    except Exception as e:
        print(f"    ⚠ 表创建失败: {e}")
    finally:
        conn.close()


def create_strategy_and_backtest_tables():
    """创建策略和回测表"""
    print("\n[5/6] 创建策略和回测相关表...")
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    try:
        # ========== strategies 表：先检查再修复 ==========
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'")
        if cursor.fetchone():
            # 表已存在，检查缺失的列
            cursor.execute("PRAGMA table_info(strategies)")
            cols = {col[1] for col in cursor.fetchall()}
            missing = []
            if 'user_id' not in cols:
                try:
                    cursor.execute("ALTER TABLE strategies ADD COLUMN user_id INTEGER")
                    missing.append('user_id')
                except:
                    print(f"    [警告] 无法添加 strategies.user_id 列（可能已存在）")
            if 'type' not in cols:
                try:
                    cursor.execute("ALTER TABLE strategies ADD COLUMN type VARCHAR(50)")
                    missing.append('type')
                except:
                    print(f"    [警告] 无法添加 strategies.type 列（可能已存在）")
            if 'is_active' not in cols:
                try:
                    cursor.execute("ALTER TABLE strategies ADD COLUMN is_active BOOLEAN DEFAULT 1")
                    missing.append('is_active')
                except:
                    print(f"    [警告] 无法添加 strategies.is_active 列（可能已存在）")
            if 'code' not in cols:
                try:
                    cursor.execute("ALTER TABLE strategies ADD COLUMN code TEXT")
                    missing.append('code')
                except:
                    print(f"    [警告] 无法添加 strategies.code 列（可能已存在）")
            if missing:
                print(f"    ✓ 添加缺失列: {missing}")
            else:
                print("    ✓ strategies 表结构完整")
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS strategies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    name VARCHAR(255) NOT NULL,
                    description TEXT,
                    type VARCHAR(50),
                    parameters TEXT NOT NULL,
                    code TEXT,
                    is_active BOOLEAN DEFAULT 1,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            print("    ✓ strategies 表创建成功")
        
        # ========== backtest_results 表：先检查再修复 ==========
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='backtest_results'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(backtest_results)")
            cols = {col[1] for col in cursor.fetchall()}
            missing = []
            if 'user_id' not in cols:
                try:
                    cursor.execute("ALTER TABLE backtest_results ADD COLUMN user_id INTEGER")
                    missing.append('user_id')
                except:
                    print(f"    [警告] 无法添加 backtest_results.user_id 列（可能已存在）")
            if missing:
                print(f"    ✓ backtest_results 添加缺失列: {missing}")
            else:
                print("    ✓ backtest_results 表结构完整")
        else:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS backtest_results (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    strategy_id INTEGER,
                    stock_code VARCHAR(20) NOT NULL,
                    start_date DATE NOT NULL,
                    end_date DATE NOT NULL,
                    initial_capital FLOAT NOT NULL,
                    final_capital FLOAT NOT NULL,
                    total_return FLOAT NOT NULL,
                    annual_return FLOAT,
                    sharpe_ratio FLOAT,
                    max_drawdown FLOAT,
                    win_rate FLOAT,
                    profit_loss_ratio FLOAT,
                    trades_count INTEGER DEFAULT 0,
                    results_data TEXT,
                    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id),
                    FOREIGN KEY (strategy_id) REFERENCES strategies(id)
                )
            """)
            print("    ✓ backtest_results 表创建成功")
        
        # ========== 用户设置表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS user_settings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL UNIQUE,
                theme_preference VARCHAR(10) DEFAULT 'light',
                refresh_frequency INTEGER DEFAULT 5,
                notification_email BOOLEAN DEFAULT 1,
                notification_browser BOOLEAN DEFAULT 0,
                backtest_default_capital FLOAT DEFAULT 100000.0,
                backtest_default_fee FLOAT DEFAULT 0.0003,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 投资组合表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS portfolios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                name VARCHAR(255) NOT NULL,
                description TEXT,
                initial_capital FLOAT NOT NULL DEFAULT 100000.0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 观察列表 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS watchlist (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                stock_code VARCHAR(20) NOT NULL,
                stock_name VARCHAR(100),
                added_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, stock_code)
            )
        """)
        
        # ========== 新增表：策略版本 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS strategy_version (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                strategy_id INTEGER NOT NULL,
                version_number INTEGER NOT NULL,
                code TEXT,
                parameters TEXT,
                description TEXT,
                created_by INTEGER,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (strategy_id) REFERENCES strategies(id),
                FOREIGN KEY (created_by) REFERENCES users(id)
            )
        """)
        
        # ========== 新增表：社区帖子 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_posts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                title VARCHAR(255) NOT NULL,
                content TEXT NOT NULL,
                tags TEXT,
                views INTEGER DEFAULT 0,
                is_pinned BOOLEAN DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 新增表：社区评论 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_comments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER NOT NULL,
                user_id INTEGER NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (post_id) REFERENCES community_posts(id),
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 新增表：社区点赞 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS community_likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                post_id INTEGER,
                comment_id INTEGER,
                user_id INTEGER NOT NULL,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id),
                UNIQUE(user_id, post_id, comment_id)
            )
        """)
        
        # ========== 新增表：操作日志 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS operation_log (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action VARCHAR(100) NOT NULL,
                module VARCHAR(50),
                detail TEXT,
                ip_address VARCHAR(50),
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        # ========== 新增表：网站内容 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS site_contents (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                page VARCHAR(100) NOT NULL,
                section VARCHAR(100),
                content TEXT,
                updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
        """)
        
        # ========== 新增表：联系消息 ==========
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS contact_messages (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                name VARCHAR(100) NOT NULL,
                email VARCHAR(200) NOT NULL,
                subject VARCHAR(255),
                message TEXT NOT NULL,
                is_read BOOLEAN DEFAULT 0,
                created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        """)
        
        conn.commit()
        print("    ✓ 策略和回测表创建成功")
    except Exception as e:
        print(f"    ⚠ 表创建失败: {e}")
    finally:
        conn.close()


def verify_migration(db_path=None):
    """验证迁移"""
    path = db_path or DB_PATH
    print(f"\n[6/6] 验证迁移结果 ({os.path.basename(path)})...")
    conn = sqlite3.connect(path)
    cursor = conn.cursor()
    
    try:
        # 检查 users 表
        cursor.execute("PRAGMA table_info(users)")
        users_cols = [col[1] for col in cursor.fetchall()]
        print(f"    users 表包含 {len(users_cols)} 列")
        
        # 检查新增列
        required_new_cols = ['avatar', 'phone', 'bio', 'theme_preference', 'refresh_frequency']
        for col in required_new_cols:
            if col in users_cols:
                print(f"    ✓ 列存在: {col}")
            else:
                print(f"    ✗ 列缺失: {col}")
        
        # 检查 strategies 表列
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='strategies'")
        if cursor.fetchone():
            cursor.execute("PRAGMA table_info(strategies)")
            strat_cols = {col[1] for col in cursor.fetchall()}
            for col in ['user_id', 'type', 'is_active', 'code']:
                if col in strat_cols:
                    print(f"    ✓ strategies.{col} 存在")
                else:
                    print(f"    ✗ strategies.{col} 缺失")
        
        # 检查新表
        tables_to_check = ['notifications', 'feedback', 'strategies', 'backtest_results',
                          'user_settings', 'portfolios', 'watchlist', 'strategy_version',
                          'community_posts', 'community_comments', 'community_likes',
                          'operation_log', 'site_contents', 'contact_messages']
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        existing_tables = {row[0] for row in cursor.fetchall()}
        
        for table in tables_to_check:
            if table in existing_tables:
                print(f"    ✓ 表存在: {table}")
            else:
                print(f"    ⚠ 表缺失: {table}")
        
        print("    ✓ 迁移验证完成")
    except Exception as e:
        print(f"    ✗ 验证失败: {e}")
    finally:
        conn.close()


def migrate_database(db_path):
    """对单个数据库执行完整迁移"""
    global DB_PATH
    DB_PATH = db_path
    backup_database()
    migrate_users_table()
    create_notifications_table()
    create_feedback_table()
    create_strategy_and_backtest_tables()
    verify_migration(db_path)


if __name__ == '__main__':
    print("=" * 60)
    print("QuantViz 数据库迁移工具")
    print("=" * 60)
    
    try:
        # 1. 处理 instance 目录下的数据库
        instance_db = os.path.join(current_dir, 'instance', 'quant_platform_new.db')
        if os.path.exists(instance_db):
            print(f"\n>>> 处理 instance 数据库: {instance_db}")
            migrate_database(instance_db)
        else:
            print(f"\n>>> instance 数据库不存在，跳过: {instance_db}")
        
        # 2. 处理项目根目录下的数据库
        root_db = os.path.join(current_dir, 'quant_platform_new.db')
        if os.path.exists(root_db):
            print(f"\n>>> 处理根目录数据库: {root_db}")
            migrate_database(root_db)
        else:
            print(f"\n>>> 根目录数据库不存在，跳过: {root_db}")
        
        # 如果两个都没有
        if not os.path.exists(instance_db) and not os.path.exists(root_db):
            print("\n⚠ 未找到任何数据库文件，将创建 instance 目录下的数据库")
            migrate_database(instance_db)
        
        print("\n" + "=" * 60)
        print("✓ 数据库迁移完成！")
        print("=" * 60)
    except Exception as e:
        print(f"\n✗ 迁移失败: {e}")
        sys.exit(1)
