Documentation for all endpoints of the HR Sentiment Analysis Flask API.

Base URL: http://127.0.0.1:5000

1. Endpoint: Health Status
Route: GET /status
Description: This endpoint provides a health check to verify that the API server is operational and to report the status of the in-memory dataset.
Method: GET
Request
Parameters: None
Body: None
Responses
200 OK (Success)
Condition: Returned when the API server is running.
Body Structure:
status (string): Indicates the server is "online".
data_loaded (boolean): true if employee data has been loaded from the database, otherwise false.
total_employees (integer): The count of employee records currently loaded in memory.
Example Payload:
JSON
{
  "status": "online",
  "data_loaded": true,
  "total_employees": 150
}



2. Endpoint: Data Reload
Route: POST /reload-data
Description: This endpoint triggers a manual refresh of the server's dataset by fetching the latest records from the connected MySQL database. This is an action endpoint and does not return a dataset.
Method: POST
Request
Parameters: None
Body: None
Responses
200 OK (Success)
Condition: Returned when the database query executes successfully and one or more records are loaded.
Example Payload:
JSON
{
  "status": "success",
  "message": "Successfully reloaded 150 records from MySQL.",
  "total_employees": 150
}




404 Not Found (Warning)
Condition: Returned when the database query executes successfully but finds no records in the target table.
Example Payload:
JSON
{
    "status": "warning",
    "message": "Reload command executed, but no data was returned from MySQL.",
    "total_employees": 0
}




500 Internal Server Error
Condition: Returned if the API fails to connect to the database or an SQL error occurs during the operation.
Example Payload:
JSON
{
  "error": "Failed to reload data: [Specific database error message]"
}





3. Endpoint: Analytics Summary
Route: GET /summary
Description: This is the primary data-retrieval endpoint for the application's dashboard. It provides a complete, aggregated summary of the HR sentiment data.
Method: GET
Request
Parameters: None
Body: None
Responses
200 OK (Success)
Condition: Returned when data is loaded on the server.
Body Structure:
total_employees (integer): Total number of employee records.
average_sentiment (float): The average sentiment score across all employees.
quadrant_distribution (object): A key-value map where keys are quadrant names (e.g., "Champion") and values are the employee counts for each.
sentiment_by_role (object): A key-value map where keys are job roles and values are the average sentiment scores for each role.
Example Payload:
JSON
{
  "total_employees": 150,
  "average_sentiment": 68.5,
  "quadrant_distribution": {
    "Champion": 40,
    "Concerned but active": 60,
    "At Risk": 20
  },
  "sentiment_by_role": {
    "Software Engineer": 75.2,
    "Product Manager": 80.1
  }
}




404 Not Found
Condition: Returned if the server has no data loaded in memory.
Example Payload:
JSON
{
  "error": "No data loaded. Please check database connection."
}





4. Endpoint: Employee Records
Route: GET /employees
Description: Retrieves a list of all individual employee records. Supports optional filtering by sentiment quadrant.
Method: GET
Request
Parameters (Optional):
quadrant (string): If provided, the response will be filtered to include only employees from the specified quadrant (e.g., ?quadrant=At%20Risk).
Body: None
Responses
200 OK (Success)
Condition: Always returned on success. The response is an array of employee objects. The array may be empty if the filter yields no results.
Example Payload:
JSON
[
  {
    "id": 102,
    "employee_id": 102,
    "employee_name": "Jane Smith",
    "content": "Feedback indicating risk...",
    "role": "Product Manager",
    "sentiment_score": 25.0,
    "quadrant": "At Risk"
  }
]




404 Not Found
Condition: Returned if the server has no data loaded in memory.
Example Payload:
JSON
{
  "error": "No data loaded."
}





5. Endpoint: AI Analysis
Route: POST /analyze
Description: Provides access to the AI analysis engine. It processes a natural language query against the context of the entire dataset to generate insights.
Method: POST
Request
Parameters: None
Body (Required): A JSON object containing the user's query.
Body Structure:
query (string): The natural language question to be analyzed.
Example Body:
JSON
{
  "query": "What are the primary concerns for at-risk employees?"
}




Responses
200 OK (Success)
Condition: Returned when the AI model successfully generates a response.
Example Payload:
JSON
{
  "analysis": "The primary concerns for at-risk employees appear to revolve around workload and lack of recognition..."
}




400 Bad Request
Condition: Returned if the request body is missing the required query field.
Example Payload:
JSON
{
  "error": "Missing 'query' in request body."
}




503 Service Unavailable
Condition: Returned if the AI model is not configured or if no data is loaded on the server to provide context.
Example Payload:
JSON
{
    "error": "AI Analyzer is not ready or data is not loaded."
}





