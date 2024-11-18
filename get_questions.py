import sqlite3

con = sqlite3.connect("history_questions.db", check_same_thread=False)
cur = con.cursor()

def get_question(query, in_answer_line=True, in_question_line=False, minimum_difficulty=0, maximum_difficulty=10, outputs=["*"]):
    if not (in_answer_line or in_question_line):
        return []

    # Split query into terms and clean them
    terms = [term.strip() for term in query.split(',') if term.strip()]
    if not terms:
        return []

    # Build the SQL query with OR conditions for each term
    conditions = []
    for term in terms:
        term_conditions = []
        if in_answer_line:
            term_conditions.append(f"Answer LIKE '%{term}%'")
        if in_question_line:
            term_conditions.append(f"Question LIKE '%{term}%'")
        if term_conditions:
            conditions.append(f"({' OR '.join(term_conditions)})")

    locator = f"({' OR '.join(conditions)})"

    sql_query = f"""
        SELECT {", ".join(outputs)} FROM Questions 
        WHERE {locator}
        AND Difficulty >= {minimum_difficulty}
        AND Difficulty <= {maximum_difficulty}
    """

    res = cur.execute(sql_query)
    results = res.fetchall()
    return results