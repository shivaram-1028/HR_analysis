# api.py
import logging
from functools import lru_cache
from flask import Flask, jsonify, request
from flask_cors import CORS
from main import HRAnalyzer  # We still use the original HRAnalyzer class

# === FLASK APP SETUP ===
app = Flask(__name__)
CORS(app)  # Enable Cross-Origin Resource Sharing

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("HR_API")

# === SINGLETON INITIALIZATION of HRANALYZER ===
# The @lru_cache decorator ensures the HRAnalyzer is initialized only once.
@lru_cache()
def get_analyzer():
    """Initializes and returns a single instance of HRAnalyzer."""
    logger.info("Initializing HRAnalyzer instance...")
    analyzer = HRAnalyzer()
    if not analyzer.load_data():
        logger.warning("Warning: HRAnalyzer loaded with no initial data from the database.")
    return analyzer

# === API ENDPOINTS ===

@app.route('/status', methods=['GET'])
def get_status():
    """Endpoint to check API status and data load status."""
    analyzer = get_analyzer()
    data_loaded = True if analyzer and analyzer.data else False
    return jsonify({
        "status": "online",
        "data_loaded": data_loaded,
        "total_employees": len(analyzer.data) if data_loaded else 0
    })

@app.route('/summary', methods=['GET'])
def get_summary():
    """Returns the main analytics summary dashboard data."""
    analyzer = get_analyzer()
    if not analyzer.data:
        return jsonify({"error": "No data loaded. Please check database connection."}), 404
    summary = analyzer.get_analytics_summary()
    return jsonify(summary)

@app.route('/employees', methods=['GET'])
def get_employees():
    """Returns a list of all employees, with an option to filter by quadrant."""
    analyzer = get_analyzer()
    if not analyzer.data:
        return jsonify({"error": "No data loaded."}), 404
    
    quadrant = request.args.get('quadrant')
    if quadrant:
        filtered_employees = [emp for emp in analyzer.data if emp.get('quadrant') == quadrant]
        return jsonify(filtered_employees)
        
    return jsonify(analyzer.data)

@app.route('/analyze', methods=['POST'])
def analyze_query():
    """Performs AI analysis based on a user query."""
    analyzer = get_analyzer()
    if not analyzer.data or not analyzer.gemini_model:
        return jsonify({"error": "AI Analyzer is not ready or data is not loaded."}), 503

    data = request.get_json()
    if not data or 'query' not in data:
        return jsonify({"error": "Missing 'query' in request body."}), 400

    query = data['query']
    
    # Build context on the server-side for the AI model
    summary = analyzer.get_analytics_summary()
    quadrant_info = ", ".join([f"{k}: {v}" for k, v in summary["quadrant_distribution"].items()])
    role_info = ", ".join([f"{role}: {sent:.1f}%" for role, sent in summary["sentiment_by_role"].items()])
    
    context = f"""
    Total Employees: {summary['total_employees']}
    Average Sentiment: {summary['average_sentiment']:.1f}%
    Quadrant Distribution: {quadrant_info}
    Sentiment by Role: {role_info}
    """

    try:
        response = analyzer.analyze_with_ai(query, context)
        return jsonify({"analysis": response})
    except Exception as e:
        logger.error(f"AI Analysis failed: {e}")
        return jsonify({"error": f"AI analysis failed: {str(e)}"}), 500

@app.route('/reload-data', methods=['POST'])
def reload_data():
    """Triggers a reload of data from the MySQL database."""
    analyzer = get_analyzer()
    try:
        if analyzer.load_data():
            return jsonify({
                "status": "success",
                "message": f"Successfully reloaded {len(analyzer.data)} records from MySQL.",
                "total_employees": len(analyzer.data)
            })
        else:
            return jsonify({
                "status": "warning",
                "message": "Reload command executed, but no data was returned from MySQL.",
                "total_employees": 0
            }), 404
    except Exception as e:
        logger.error(f"Failed to reload data: {e}")
        return jsonify({"error": f"Failed to reload data: {str(e)}"}), 500

# === MAIN EXECUTION ===
if __name__ == '__main__':
    # Initialize the analyzer on startup
    get_analyzer()
    # Run the Flask app
    app.run(host='0.0.0.0', port=8000, debug=True)