import streamlit as st
import ollama
import sqlite3
import pandas as pd

# Function: NLP → SQL using Ollama
def get_sql_query_from_text(user_query):

    prompt = f"""
        You are an expert SQL generator for SQLite.

        You work ONLY with this table:

        TABLE: STUDENT
        Columns:
        - id (INTEGER PRIMARY KEY)
        - name (TEXT)
        - age (INTEGER)
        - course (TEXT)
        - marks (INTEGER)

        ---

        RULES:
        - Return ONLY valid SQLite SQL query
        - No explanations
        - If query is not related to the STUDENT table, return:
        SELECT "INVALID_QUERY" as error;
        - If user request is unclear or impossible, return:
        SELECT "NO_VALID_RESULT" as error;

        ---

        FEW SHOT EXAMPLES:

        User: Show all students
        SQL: SELECT * FROM STUDENT;

        User: Get students with marks greater than 80
        SQL: SELECT * FROM STUDENT WHERE marks > 80;

        User: Find students in Data Science course
        SQL: SELECT * FROM STUDENT WHERE course = 'Data Science';

        User: Students older than 20
        SQL: SELECT * FROM STUDENT WHERE age > 20;

        User: Average marks of students
        SQL: SELECT AVG(marks) FROM STUDENT;

        User: Delete all students
        SQL: SELECT "INVALID_QUERY" as error;

        User: Drop table
        SQL: SELECT "INVALID_QUERY" as error;

        ---

        NOW CONVERT THIS USER QUERY:
        User: {user_query}

        SQL:
        """

    response = ollama.chat(
        model="qwen2.5-coder:1.5b",
        messages=[{"role": "user", "content": prompt}]
    )

    sql_query = response["message"]["content"].strip()

    # clean markdown formatting if model adds it
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    return sql_query


# Function: execute SQL on SQLite DB
def run_sql_query(sql_query):
    connection = sqlite3.connect("student.db")
    cursor = connection.cursor()

    try:
        cursor.execute(sql_query)

        rows = cursor.fetchall()
        columns = [desc[0] for desc in cursor.description]

        connection.close()

        return columns, rows, None

    except Exception as e:
        connection.close()
        return None, None, str(e)


def main():
    st.set_page_config(page_title="NLP Text to SQL")
    st.header("LETS CHAT WITH SQL DATABASE")

    user_query = st.text_input("Enter your query - (Ask in detail for better results)")
    submit = st.button("Generate + Execute SQL")

    if submit and user_query:

        # STEP 1: Generate SQL
        sql_query = get_sql_query_from_text(user_query)

        st.subheader("GENERATED SQL QUERY")
        st.code(sql_query, language="sql")

        # STEP 2: Execute SQL
        columns, rows, error = run_sql_query(sql_query)

        if error:
            st.error(f"SQL Error: {error}")
            return

        # STEP 3: Convert to DataFrame (IMPORTANT FIX)
        st.subheader("QUERY RESULT")

        if rows:
            df = pd.DataFrame(rows, columns=columns)
            st.dataframe(df, use_container_width=True)
        else:
            st.warning("No data found")


if __name__ == "__main__":
    main()