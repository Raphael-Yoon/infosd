import sqlite3
import os

SNOWBALL_DB = '/home/snowball/pythons/snowball/snowball.db'
INFOPD_DB = '/home/snowball/pythons/infopd/infopd.db'

def migrate_questions():
    if not os.path.exists(SNOWBALL_DB):
        print(f"Error: Source DB not found at {SNOWBALL_DB}")
        return
    if not os.path.exists(INFOPD_DB):
        print(f"Error: Target DB not found at {INFOPD_DB}")
        return

    # 연결
    conn_sb = sqlite3.connect(SNOWBALL_DB)
    cursor_sb = conn_sb.cursor()
    
    conn_ipd = sqlite3.connect(INFOPD_DB)
    cursor_ipd = conn_ipd.cursor()

    try:
        # 기존 InfoPD 질문 초기화
        cursor_ipd.execute("DELETE FROM ipd_questions")
        
        # 스노우볼에서 원본 데이터 추출
        cursor_sb.execute("""
            SELECT id, display_number, level, category_id, category, text, type, help_text, evidence_list, sort_order
            FROM sb_disclosure_questions
        """)
        rows = cursor_sb.fetchall()
        
        # InfoPD 규격에 맞춰 매핑 (is_active 필드 1로 추가)
        mapped_rows = []
        for row in rows:
            mapped_rows.append((
                row[0], # id
                row[1], # display_number
                row[2], # level
                row[3], # category_id
                row[4], # category
                row[5], # text
                row[6], # type
                row[7], # help_text
                row[8], # evidence_title (mapped from evidence_list)
                1,      # is_active
                row[9]  # sort_order
            ))

        # 데이터 주입
        cursor_ipd.executemany("""
            INSERT INTO ipd_questions 
            (id, display_number, level, category_id, category, text, type, help_text, evidence_title, is_active, sort_order)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, mapped_rows)
        
        conn_ipd.commit()
        print(f"Migration Complete: Successfully transferred {len(mapped_rows)} official questions from Snowball DB.")
        
    except sqlite3.Error as e:
        print(f"Database error during migration: {e}")
        conn_ipd.rollback()
    finally:
        conn_sb.close()
        conn_ipd.close()

if __name__ == "__main__":
    migrate_questions()
