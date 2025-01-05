# from fastapi import FastAPI
# from fastapi.middleware.cors import CORSMiddleware
# from pydantic import BaseModel
# from typing import List

# # Create FastAPI instance
# app = FastAPI()

# # Add CORS middleware to handle cross-origin requests
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allow all origins for simplicity (use more restrictive settings in production)
#     allow_credentials=True,
#     allow_methods=["*"],  # Allow all HTTP methods
#     allow_headers=["*"],  # Allow all headers
# )

# # Define the data model for the question
# class Question(BaseModel):
#     question: str

# # Sample data: predefined questions and answers
# # questions = [
# #     {"question": "What is the currency of Japan?", "answer": "Japanese Yen"},
# #     {"question": "What is the capital of France?", "answer": "Paris"},
# #     {"question": "What is the highest mountain in the world?", "answer": "Mount Everest"},
# # ]
# questions = [
#     {"question": "What is React", "answer": "React is a JavaScript library for building user interfaces."},
#     {"question": "What is JSX", "answer": "JSX is a syntax extension for JavaScript that looks similar to HTML and is used with React."},
#     {"question": "What is a component in React", "answer": "A component is a JavaScript function or class that optionally accepts inputs (props) and returns a React element that describes how a section of the UI should appear."},
#     {"question": "What is the virtual DOM", "answer": "The virtual DOM is a lightweight representation of the real DOM. React uses the virtual DOM to efficiently update the UI by minimizing direct manipulation of the real DOM."},
#     {"question": "What are props in React", "answer": "Props (short for properties) are used to pass data from a parent component to a child component in React."},
#     {"question": "What is state in React", "answer": "State is an object that holds information about a component's data and can change over time. Changes in state trigger re-renders of the component."},
#     {"question": "What is the useState hook", "answer": "The useState hook is a React hook that lets you add state to functional components."},
#     {"question": "What is the useEffect hook", "answer": "The useEffect hook is used to perform side effects in functional components, such as data fetching, manual DOM manipulation, or subscribing to external data sources."},
#     {"question": "What is a React hook", "answer": "React hooks are functions that let you use state and lifecycle features in functional components."},
#     {"question": "What is the difference between state and props", "answer": "State is local to a component and can be changed by the component, while props are passed to components by their parent and are immutable within the component."},
# ]

# # Endpoint to get all predefined questions
# @app.get("/questions")
# def get_questions():
#     return questions

# # Endpoint to ask a question and get an answer
# @app.post("/get-answer")
# def ask_question(question: Question):
#     # Find the question in the predefined list
#     for q in questions:
#         if q['question'].lower() == question.question.lower():
#             return {"answer": q['answer']}
#     return {"answer": "Sorry, I don't know the answer to that question."}









from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pyodbc
from pydantic import BaseModel

app = FastAPI()

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Update with your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

# Database connection parameters
server = 'viavi-itsm-genai.database.windows.net'
database = 'ViaviItsm_genai'
username = 'cr-dev'
password = 'Genaiw0rd@12345'

# Connection string
connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password}"
)

class QueryRequest(BaseModel):
    query: str

@app.post("/execute-query")
async def execute_query(request: QueryRequest):
    try:
        query = request.query
        if not query.strip().lower().startswith("select"):
            raise HTTPException(
                status_code=400,
                detail="Only SELECT queries are allowed"
            )

        with pyodbc.connect(connection_string) as conn:
            cursor = conn.cursor()
            cursor.execute(query)
            rows = cursor.fetchall()

            # Extract column names dynamically from the cursor
            columns = [column[0] for column in cursor.description]

            # Convert rows into a list of dictionaries
            results = [dict(zip(columns, row)) for row in rows]

            return {"query": query, "results": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

