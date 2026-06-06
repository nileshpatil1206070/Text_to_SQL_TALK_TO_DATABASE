import streamlit as st
import ollama
import sqlite3

# Function: NLP → SQL using Ollama
def get_sql_query_from_text(user_query):

    prompt = f"""
You are an expert SQL generator.

Convert natural language into SQLite SQL.

Rules:
- Only return SQL query
- No explanation
- Use table: STUDENT (id, name, age, course, marks)

User Query:
{user_query}
"""

    response = ollama.chat(
        model="qwen2.5-coder:1.5b",
        messages=[{"role": "user", "content": prompt}]
    )

    sql_query = response["message"]["content"].strip()

    # remove accidental markdown formatting
    sql_query = sql_query.replace("```sql", "").replace("```", "").strip()

    return sql_query


# Function: execute SQL on SQLite DB
def run_sql_query(sql_query):
    connection = sqlite3.connect("student.db")
    cursor = connection.cursor()

    try:
        cursor.execute(sql_query)
        rows = cursor.fetchall()

        # column names
        columns = [desc[0] for desc in cursor.description] if cursor.description else []

        connection.close()
        return columns, rows, None

    except Exception as e:
        connection.close()
        return None, None, str(e)


def main():
    st.set_page_config(page_title="NLP Text to SQL")
    st.header("Ask your Student Database")

    user_query = st.text_input("Enter your query")
    submit = st.button("Generate + Execute SQL")

    if submit and user_query:

        # Step 1: Generate SQL
        sql_query = get_sql_query_from_text(user_query)

        st.subheader("Generated SQL Query")
        st.code(sql_query, language="sql")

        # Step 2: Execute SQL
        columns, rows, error = run_sql_query(sql_query)

        if error:
            st.error(f"SQL Error: {error}")
        else:
            st.subheader("Query Result")

            if rows:
                st.dataframe(rows, use_container_width=True)
            else:
                st.warning("No data found")


if __name__ == "__main__":
    main()