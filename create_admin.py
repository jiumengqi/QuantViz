# -*- coding: utf-8 -*-
"""快速创建管理员账号脚本 - 同时处理项目根目录和instance目录的数据库"""
import sqlite3
import os

base_dir = os.path.dirname(os.path.abspath(__file__))

# 需要处理的数据库文件列表
db_files = [
    os.path.join(base_dir, 'quant_platform_new.db'),
    os.path.join(base_dir, 'instance', 'quant_platform_new.db'),
]

from werkzeug.security import generate_password_hash
pwd_hash = generate_password_hash('Admin@123456')

for db_path in db_files:
    if not os.path.exists(db_path):
        print(f"数据库不存在，跳过: {db_path}")
        continue
    
    conn = sqlite3.connect(db_path)
    cur = conn.cursor()
    
    # 查看现有用户
    cur.execute("SELECT id, username, email, role FROM users")
    rows = cur.fetchall()
    print(f"\n数据库: {os.path.basename(os.path.dirname(db_path))}/{os.path.basename(db_path)}")
    print("现有用户:")
    for r in rows:
        print(f"  ID={r[0]}, 用户名={r[1]}, 邮箱={r[2]}, 角色={r[3]}")
    
    # 检查管理员
    cur.execute("SELECT id FROM users WHERE role='admin'")
    admin = cur.fetchone()
    
    if admin:
        print("已有管理员，无需创建")
    else:
        cur.execute(
            "INSERT INTO users (username, email, password_hash, role, is_active, created_at) VALUES (?, ?, ?, 'admin', 1, datetime('now'))",
            ('admin', 'admin@quantviz.com', pwd_hash)
        )
        conn.commit()
        print("管理员创建成功!")
    
    conn.close()

print("\n" + "="*50)
print("管理员账号信息:")
print("  登录地址: http://127.0.0.1:5000/auth/login")
print("  用户名:   admin")
print("  密码:     Admin@123456")
print("  管理面板: http://127.0.0.1:5000/auth/admin")
print("  内容编辑: http://127.0.0.1:5000/auth/admin_content")
print("="*50)
