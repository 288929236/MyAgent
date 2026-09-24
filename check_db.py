import sqlite3
conn = sqlite3.connect('data/user-001/001.db')
cursor = conn.cursor()

# 查看有哪些表
cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
print('表:', cursor.fetchall())

# 查看 checkpoints 表的内容
cursor.execute('SELECT thread_id, checkpoint_id FROM checkpoints')
print('checkpoints:', cursor.fetchall())

conn.close()
