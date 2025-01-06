from langchain_openai import ChatOpenAI
from langchain_groq import ChatGroq
from langchain_core.prompts import PromptTemplate, ChatPromptTemplate, MessagesPlaceholder
from langchain_core.output_parsers import StrOutputParser
import sqlparse
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import pyodbc
from pydantic import BaseModel

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],  # Update with your frontend's origin
    allow_credentials=True,
    allow_methods=["*"],  # Allow all HTTP methods
    allow_headers=["*"],  # Allow all headers
)

server = 'viavi-itsm-genai.database.windows.net'
database = 'ViaviItsm_genai'
username = 'cr-dev'
password = 'Genaiw0rd@12345'

connection_string = (
    f"DRIVER={{ODBC Driver 17 for SQL Server}};"
    f"SERVER={server};"
    f"DATABASE={database};"
    f"UID={username};"
    f"PWD={password}"
)

class Question(BaseModel):
    question: str

import os 
from dotenv import load_dotenv 
load_dotenv() 

groq_api_key = os.getenv("GROQ_API_KEY")

llm = ChatGroq(groq_api_key=groq_api_key,model="mixtral-8x7b-32768")

schema_description = """
Tables and Schema:
1.Table Name: IT_CSAT_Summary
  Columns:

    - TriggerID (nvarchar): Unique identifier for the incident or event that triggered the CSAT survey.
    - TakenOn (datetime): Date and time when the CSAT survey was taken.
    - State (nvarchar): The current state of the CSAT survey (e.g., "Complete," "Pending").
    - Metric (nvarchar): The question or metric being assessed in the CSAT survey.
    - Display (nvarchar): Display text summarizing the customer’s feedback.
    - StringValue (nvarchar): The raw text value of the customer’s response.
    - AssignmentGroup (nvarchar): The team or group responsible for resolving the incident.
    - Include_YN (nvarchar): Indicates whether the CSAT response should be included in the analysis ("Y" or "N").
    - Tier1 (nvarchar): High-level categorization of the issue (e.g., Infra, Apps).
    - Tier2 (nvarchar): Mid-level categorization for more specific classification of the issue.
    - Tier3 (nvarchar): Detailed categorization of the issue or incident.
    - Customer (nvarchar): Name of the customer providing the feedback.
    - Location (nvarchar): Location of the customer.
    - Business_Level_2 (nvarchar): Second-level categorization of the business unit impacted by the incident.
    - Assigned_To (nvarchar): Name of the person assigned to resolve the incident.
    - Region (nvarchar): Geographic region where the incident occurred (e.g., Americas, EMEA).
    - BU (nvarchar): Business unit related to the incident or feedback.
    - Office (nvarchar): The specific office location of the customer or the impacted team.
    - Name (nvarchar): Name or title of the incident or feedback request.
    - Description (nvarchar): Detailed description of the incident or the feedback provided.
    - Response (nvarchar): Customer’s response to the CSAT survey.
    - CSTAT_Rating (nvarchar): Overall customer satisfaction rating.
    - Configuration_Item (nvarchar): The affected configuration item, such as hardware, software, or network elements.
    - Subcategory (nvarchar): Subdivision of the main category related to the incident or feedback.
    - Category (nvarchar): High-level category of the incident or feedback.
    - Priority (nvarchar): Priority assigned to the incident (e.g., P1, P2).
    - Urgency (nvarchar): Level of urgency associated with resolving the incident.
    - Resolved_in_Days (int): Total number of days taken to resolve the incident.
    - Rsolved_in_HRs (int): Total number of hours taken to resolve the incident.
    - Opened (datetime): Date and time when the incident was opened.
    - Updated (datetime): Date and time of the most recent update to the incident.
    - Incident_state (nvarchar): Current state of the incident (e.g., Open, Closed).
    - RFC (nvarchar): Indicates if the incident is related to a request for change.
    - Caused_by_Change (nvarchar): Indicates if the incident was caused by a change request.
    - Resolution_Action (nvarchar): Actions taken to resolve the incident.
    - Explain_Resolution (nvarchar): Detailed explanation of how the incident was resolved.
    - Resolve_time (int): Time taken to resolve the incident, in hours.
    - Resolved (int): A flag indicating whether the incident has been resolved.
    - Resolved_by (nvarchar): Name of the individual who resolved the incident.
    - SLA_due (nvarchar): Indicates if the service level agreement (SLA) was breached or met.
    - Made_SLA (bit): Boolean indicating if the SLA was met (True/False).
    - Due_date (datetime): The deadline for resolving the incident.
    - Business_resolve_time (int): Total time taken for resolution by the business unit, in hours.
    - Actual_start_date (datetime): The actual start date and time for resolving the incident.
    - Actual_end_date (datetime): The actual completion date and time for resolving the incident.
    - Resolution_Code (nvarchar): A code indicating the resolution applied to the incident.
    - Contact_Type (nvarchar): How the incident was reported (e.g., email, phone).
    - Month (nvarchar): Month when the CSAT survey was completed or the incident was resolved.
    - Qtr (nvarchar): Quarter when the CSAT survey was completed or the incident was resolved.
    - Incident_URL (nvarchar): Link to the detailed incident record in the system.
    - MetricResult_URL (nvarchar): Link to the specific CSAT metric result in the system.
    - AssessmentTaken_URL (nvarchar): Link to the assessment taken by the customer in the system.

2. Table: cr_case  
   Columns:  
     - Number (nvarchar): The unique identifier for the incident.  
     - Opened (datetime): The timestamp when the incident was created.  
     - Priority (nvarchar): The priority level of the incident.  
     - Assigned to (nvarchar): The name of the individual assigned to resolve the incident.  
     - Customer (nvarchar): The individual or entity for whom the incident is being resolved.  
     - Name (nvarchar): A short description or title of the incident.  
     - Updated (datetime): The most recent timestamp when the ticket was updated.  
     - Incident state (nvarchar): The specific state tied to the incident occurrence.  
     - Assignment group (nvarchar): The group responsible for resolving the incident.  
     - Business resolve time (float): The duration allocated to resolve the issue, measured in seconds.  
     - Business duration (float): The total business time spent resolving the incident.  
     - Business impact (nvarchar): Description of the severity of the issue's impact on the business.  
     - Close notes (nvarchar): Notes provided upon closure of the incident.  
     - sys_id (nvarchar): A system-generated unique identifier for the incident ticket in the database.  
     - Item_Url (nvarchar): A hyperlink to the incident in the system (useful for navigation).  
     - Description (nvarchar): A more detailed explanation of the issue/request.  
     - Active (bit): Indicates whether the incident is active or resolved.  
     - Impact (nvarchar): Describes what action was taken or the impact on the system/business.  
     - u_aging_category (nvarchar): Categorizes incidents or tickets based on the duration since they were created.  
     - u_major_incident_flag (bit): Indicates if the incident is flagged as a major incident (True/False).  
     - u_fcr (bit): Indicates whether the ticket was resolved on the first call or interaction.  
     - sys_created_by (nvarchar): The name of the person or system that created the ticket.  
     - notify (int): A flag indicating notification preferences or status.  
     - u_high_level_bu (nvarchar): The high-level business unit impacted by the incident.  
     - contact_type (nvarchar): How the incident was reported.  
     - Breched_SLA (bit): Indicates whether the SLA was breached (True/False).  
     - u_tier_1 (nvarchar): The Tier 1 classification of the incident.  
     - u_tier_2 (nvarchar): The Tier 2 classification of the incident.  
     - u_tier_3 (nvarchar): The Tier 3 classification of the incident.  
     - ConfigurationItem (nvarchar): The affected configuration item.  
     - caused_by (nvarchar): Specifies the root cause or triggering event that led to the incident.  
     - upon_reject (nvarchar): Actions or statuses triggered when a request or ticket is rejected.  
     - origin_table (nvarchar): Indicates the originating table in the system for the incident.  
     - knowledge (nvarchar): A reference to knowledge articles related to the incident.  
     - u_subcategory (nvarchar): A more specific category for the incident.  
     - u_problem_open_by (nvarchar): The name of the person who opened the problem ticket associated with the incident.  
     - u_crisis_manager (nvarchar): The name of the crisis manager assigned to the incident.  
     - approval_set (nvarchar): A set of approval records or status associated with the ticket.  
     - u_exact_category (nvarchar): The exact category of the issue.  
     - universal_request (nvarchar): A universal identifier for a service request.  
     - correlation_display (nvarchar): A display field used to correlate related records.  
     - delivery_task (nvarchar): Reference to a specific delivery task related to the incident.  
     - work_start (datetime): The date and time when work on the incident began.  
     - service_offering (nvarchar): The specific service offering impacted by the incident.  
     - sys_class_name (nvarchar): The class name in the system that defines the type of record.  
     - closed_by (nvarchar): The name of the person who closed the ticket.  
     - follow_up (datetime): The scheduled date and time for a follow-up action on the incident.  
     - reopened_by (nvarchar): The name of the person who reopened the ticket.  
     - u_external_ticket (nvarchar): The identifier for an external ticket linked to this record.  
     - reassignment_count (nvarchar): The number of times the ticket was reassigned.  
     - u_category (nvarchar): The primary category of the incident.  
     - escalation (nvarchar): Indicates whether the incident was escalated.  
     - upon_approval (nvarchar): Specifies actions triggered upon approval of the ticket.  
     - correlation_id (nvarchar): A unique identifier used to correlate the ticket with related records.  
     - u_major_incident (nvarchar): Indicates whether the ticket is marked as a major incident.  
     - made_sla (nvarchar): A boolean field indicating whether the SLA was met.  
     - u_select_tag (nvarchar): Custom tags or labels applied to the ticket.  
     - u_business_unit_level_1 (nvarchar): The top-level business unit affected by the incident.  
     - u_business_unit_level_2 (nvarchar): The second-level business unit affected by the incident.  
     - resolved_by (nvarchar): The name of the person who resolved the ticket.  
     - opened_by (nvarchar): The name of the person who initially logged the ticket.  
     - user_input (nvarchar): Input or comments provided by the user during ticket creation.  
     - sys_domain (nvarchar): The domain within which the ticket resides.  
     - route_reason (nvarchar): The reason for routing the ticket to a specific team or individual.  
     - calendar_stc (nvarchar): Calendar time in a specific format, often used for SLA tracking.  
     - u_major_communication (nvarchar): Communication or updates related to a major incident.  
     - business_service (nvarchar): The service impacted.  
     - u_exact (nvarchar): Additional exact details or classification of the incident.  
     - rfc (nvarchar): Reference to a related Request for Change (RFC).  
     - expected_start (datetime): The expected start date and time for resolving the incident.  
     - opened_at (datetime): The date and time when the ticket was first opened.  
     - caller_id (nvarchar): The person who raised the issue.  
     - business_stc (nvarchar): Business service time clock details.  
     - cause (nvarchar): The identified cause of the incident.  
     - origin_id (nvarchar): The identifier for the source or origin of the ticket.  
     - calendar_duration (nvarchar): The total duration the ticket was active.  
     - incident_state (nvarchar): The current state of the incident.  
     - urgency (nvarchar): Indicates how critical or urgent the issue is.  
     - problem_id (nvarchar): A reference to the related problem record.  
     - company (nvarchar): The company associated with the incident.  
     - severity (nvarchar): Additional indicators of how critical or urgent the issue is.  
     - comments (nvarchar): Additional notes or updates logged during the incident lifecycle.  
     - approval (nvarchar): Approval records or status.  
     - due_date (datetime): The date and time by which the ticket is expected to be resolved.  
     - sys_mod_count (nvarchar): The number of modifications made to the ticket.  
     - u_peakpriority (nvarchar): A custom field for indicating peak priority incidents.  
     - u_explain (nvarchar): Additional explanations or details about the incident.  
     - u_resolution_action (nvarchar): Codes and descriptions of how the incident was resolved.  
     - u_resolution_code (nvarchar): Codes and descriptions of how the incident was resolved.  
     - u_close_code (nvarchar): A code specifying the reason for closing the ticket.  
     - location (nvarchar): The location where the issue occurred.  
     - u_org_level_1 (nvarchar): The first-level organizational unit affected by the incident.  
     - u_org_level_2 (nvarchar): The second-level organizational unit affected by the incident.  
     - IncCreatedOn	(datetime):	The timestamp for when the incident record was created.
     - IncUpdatedOn	(datetime)	The timestamp for the most recent update to the incident record.

Relationships:
- The "Number" column in the "cr_case" table is related to the "TriggerID" column in the "IT_CSAT_Summary" table, as incidents from the case table may trigger customer satisfaction surveys.
- The "Assigned_To" column in the "IT_CSAT_Summary" table is related to the "Assigned to" column in the "cr_case" table, capturing the person responsible for resolving incidents.
- The "Assignment group" column in the "IT_CSAT_Summary" table is related to the "Assignment group" column in the "cr_case" table, representing the teams managing incidents and their corresponding surveys.
- The "Configuration_Item" column in the "IT_CSAT_Summary" table is related to the "ConfigurationItem" column in the "cr_case" table, capturing the affected services or assets.
- The "Resolved_by" column in the "IT_CSAT_Summary" table is related to the "resolved_by" column in the "cr_case" table, ensuring traceability of resolutions to the corresponding cases.
- The "Location" column in the "IT_CSAT_Summary" table may map to the "location" column in the "cr_case" table, identifying where incidents occurred or were resolved.     
"""
prompt_template = PromptTemplate.from_template(
    template=f"""
You are an expert in converting English questions to SQL queries for Microsoft SQL Server (MS SQL). Please ensure that the SQL query is written according to MS SQL syntax.

Consider the following database schema:

{schema_description}

Question: {{question}}

Generate a valid MS SQL query in the following format:



The query should:
1. Use `TOP` for limiting rows, not `LIMIT` and dont use in each case `TOP` use it if it is necessary for the question asked.
2. Use MS SQL conventions like `INNER JOIN`, `LEFT JOIN`, and `RIGHT JOIN` where necessary.
3. Ensure proper usage of keywords like `GROUP BY`, `HAVING`, etc only use if it is necessary for the question asked
4.1 For priority column for p1 instead of 1 use 1 - High and p2 instead of 2 use 2 - Medium and for p3 instead of 3 use it as 3 - Low
4.2 Do not include any backticks or non-MS SQL conventions.
5. Do not include the word "SQL" or any formatting like backticks in the query.
6. Do not include the triple backticks (```) before or after the query.
7. Always give me SQL query wrapped in an alternative format like [].
8. Do not create any DML Queries (like DELETE, DROP,etc.). If a question requests such queries, respond with: "I am not allowed to perform DML operations like DELETE, DROP, etc."
9. Alias columns and aggregates properly (e.g., AVG(salary) AS AverageSalary).
11. When referring to column names in SQL queries, if the column name has spaces, always enclose it in brackets (e.g., [Assigned to], [Assignment group]) and avoid using underscores (e.g., Assigned_To should be written as [Assigned to]). Column names should be written as they appear, with brackets for spaces and no underscores.
 
10. For simpler queries, fetch the data from a single table without using joins. Use joins only when they are necessary to retrieve related data from multiple tables.
 
 

The generated SQL query should follow the above conventions and be written as a valid MS SQL query.
"""

)

class QueryRequest(BaseModel):
    query: str

class CustomSQLParser(StrOutputParser):
    def parse(self, text: str) -> str:
        # If the question asks for DML operations, return the custom message
        if "DELETE" in text.upper() or "DROP" in text.upper():
            return "I am not allowed to perform DML operations like DELETE, DROP, etc."

        # Strip the response of unnecessary tags or introductory text.
        # Handle case where the output might contain square brackets or extra characters.
        
        # Check if the text is wrapped in square brackets, remove the brackets
        if text.startswith("[") and text.endswith("]"):
            sql_query = text[1:-1].strip()  # Remove leading and trailing square brackets
        else:
            sql_query = text.strip()

        # Return the cleaned SQL query
        return sql_query

output_parser = CustomSQLParser()


def generate_sql(question):
    prompt_value = prompt_template.invoke({"question": question})
    response = llm.invoke(prompt_value)
    
    # Use custom output parser to clean the response
    clean_response = output_parser.parse(response.content)
    return clean_response

# question = "What is the total number of incidents resolved by the Helpdesk Team?"
# # (need to get the question from react app)
# sql_query = generate_sql(question)
# #print("Generated SQL Query: \n")
# print(sql_query)


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


@app.post("/generate-sql")
async def generate_sql_endpoint(question: Question):
    try:
        sql_query = generate_sql(question.question)
        return {"sql_query": sql_query}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating SQL: {str(e)}")

