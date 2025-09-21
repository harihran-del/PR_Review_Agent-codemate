from flask import Flask, request, jsonify, render_template
from datetime import datetime
import json
import os
from pr_reviewer import get_pr_details, generate_ai_review

# Initialize Flask app
app = Flask(__name__)

# Configuration
REVIEW_HISTORY_FILE = 'review_history.json'

def load_review_history():
    """Load review history from JSON file"""
    try:
        with open(REVIEW_HISTORY_FILE, 'r') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def save_review_history(history):
    """Save review history to JSON file"""
    with open(REVIEW_HISTORY_FILE, 'w') as f:
        json.dump(history, f, indent=2)

@app.route('/')
def index():
    """Serve the main HTML page"""
    return render_template('index.html')

@app.route('/review', methods=['POST'])
def review_pr():
    """Endpoint for web form submission"""
    try:
        pr_url = request.form.get('pr_url')
        if not pr_url:
            return jsonify({'success': False, 'error': 'PR URL is required'})
        
        pr_details = get_pr_details(pr_url)
        review = generate_ai_review(pr_details)
        
        # Save to history
        history = load_review_history()
        history.insert(0, {
            'timestamp': datetime.now().isoformat(),
            'pr_url': pr_url,
            'provider': pr_details.get('provider', 'github'),
            'title': pr_details.get('title', ''),
            'review': review,
            'changed_files': pr_details.get('changed_files', 0)
        })
        save_review_history(history[:50])  # Keep last 50 reviews
        
        return jsonify({
            'success': True,
            'review': review,
            'provider': pr_details.get('provider', 'github'),
            'title': pr_details.get('title', ''),
            'changed_files': pr_details.get('changed_files', 0)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/history')
def get_review_history():
    """API endpoint to get review history"""
    return jsonify(load_review_history())

@app.route('/api/stats')
def get_review_stats():
    """API endpoint to get review statistics"""
    history = load_review_history()
    total = len(history)
    
    # Calculate average score from review content
    scores = []
    for review in history:
        # Extract score from review text (assuming format "SCORE: XX/100")
        review_text = review.get('review', '')
        if 'SCORE:' in review_text:
            try:
                score_part = review_text.split('SCORE:')[1].split('/')[0].strip()
                score = int(score_part)
                scores.append(score)
            except (ValueError, IndexError):
                pass
    
    avg_score = sum(scores) / len(scores) if scores else 0
    
    return jsonify({
        'total_reviews': total,
        'avg_score': round(avg_score, 1),
        'providers': len(set(review.get('provider', '') for review in history))
    })

@app.route('/api/review', methods=['POST'])
def api_review():
    """API endpoint for programmatic access"""
    try:
        pr_url = request.json.get('pr_url')
        if not pr_url:
            return jsonify({'error': 'PR URL is required'}), 400
        
        pr_details = get_pr_details(pr_url)
        review = generate_ai_review(pr_details)
        
        # Save to history
        history = load_review_history()
        history.insert(0, {
            'timestamp': datetime.now().isoformat(),
            'pr_url': pr_url,
            'provider': pr_details.get('provider', 'github'),
            'title': pr_details.get('title', ''),
            'review': review,
            'changed_files': pr_details.get('changed_files', 0)
        })
        save_review_history(history[:50])  # Keep last 50 reviews
        
        return jsonify({
            'success': True,
            'review': review,
            'provider': pr_details.get('provider', 'github'),
            'title': pr_details.get('title', ''),
            'changed_files': pr_details.get('changed_files', 0)
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

if __name__ == '__main__':
    # Create review history file if it doesn't exist
    if not os.path.exists(REVIEW_HISTORY_FILE):
        save_review_history([])
    
    app.run(debug=True, host='0.0.0.0', port=5000)