"""
手动数据库迁移脚本 - 添加 split 字段到 data_files 表

使用方法:
    python migrate_add_split_column.py
"""

import sqlite3
from pathlib import Path

# 数据库路径
DB_PATH = Path(__file__).parent / "spatial_v2.db"

def migrate():
    """添加 split 字段到 data_files 表"""
    if not DB_PATH.exists():
        print(f"❌ 数据库不存在：{DB_PATH}")
        return False
    
    conn = sqlite3.connect(str(DB_PATH))
    cursor = conn.cursor()
    
    try:
        # 检查列是否已存在
        cursor.execute("PRAGMA table_info(data_files)")
        columns = [row[1] for row in cursor.fetchall()]
        
        if 'split' in columns:
            print("✅ split 字段已存在，无需迁移")
            return True
        
        # 添加 split 列
        print("📝 添加 split 列到 data_files 表...")
        cursor.execute("""
            ALTER TABLE data_files 
            ADD COLUMN split VARCHAR(50)
        """)
        
        conn.commit()
        print("✅ 迁移成功！已添加 split 字段")
        return True
        
    except sqlite3.OperationalError as e:
        print(f"❌ 迁移失败：{e}")
        conn.rollback()
        return False
    finally:
        conn.close()

if __name__ == "__main__":
    print(f"🔧 数据库路径：{DB_PATH}")
    success = migrate()
    exit(0 if success else 1)
