# import sqlite3

# con = sqlite3.connect("history_questions.db")
# cur = con.cursor()

# cur.execute("""
#     UPDATE 
#         Questions
#     SET 
#         Question = REPLACE(Question, 
#             '[]',
#             '')
#     WHERE 
#         Question LIKE '%[*]%'
#     """)
# con.commit()
