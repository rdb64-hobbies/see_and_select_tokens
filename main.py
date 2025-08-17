from flask import Flask, render_template, request, jsonify
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict, Tuple

app = Flask(__name__)

class TokenGenerator:
    def __init__(self, model_name="gpt2"):
        """Initialize the token generator with a pre-trained model."""
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        print(f"Using device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        
        # Add padding token if it doesn't exist
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def get_next_token_probabilities(self, text: str, top_k: int = 10) -> Tuple[List[Dict], Dict]:
        """
        Get the top-k token probabilities for the next token given the input text.
        Returns: (top_k_tokens_with_probs, selected_token_dict)
        """
        # Tokenize input
        inputs = self.tokenizer.encode(text, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            # Get model outputs
            outputs = self.model(inputs)
            logits = outputs.logits[0, -1, :]  # Get logits for the last token
            
            # Convert to probabilities
            probs = torch.softmax(logits, dim=-1)
            
            # Get top-k tokens and their probabilities
            top_k_probs, top_k_indices = torch.topk(probs, top_k)
            
            # Sample from the distribution for the selected token
            selected_token_id = torch.multinomial(probs, 1).item()
            selected_token_text = self.tokenizer.decode([selected_token_id])
            selected_token_prob = probs[selected_token_id].item()
            
            # Create selected token dictionary
            selected_token = {
                'token_id': selected_token_id,
                'token_text': selected_token_text,
                'probability': selected_token_prob
            }
            
            # Convert to list of dictionaries
            top_k_tokens = []
            for i in range(top_k):
                token_id = top_k_indices[i].item()
                token_text = self.tokenizer.decode([token_id])
                probability = top_k_probs[i].item()
                
                top_k_tokens.append({
                    'token_id': token_id,
                    'token_text': token_text,
                    'probability': probability
                })
            
            return top_k_tokens, selected_token
    
    def decode_token(self, token_id: int) -> str:
        """Decode a single token ID to text."""
        return self.tokenizer.decode([token_id])

# Global token generator instance
token_gen = None

@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')

@app.route('/initialize', methods=['POST'])
def initialize_model():
    """Initialize the token generator model."""
    global token_gen
    try:
        model_name = request.json.get('model_name', 'gpt2')
        token_gen = TokenGenerator(model_name)
        return jsonify({'status': 'success', 'message': 'Model initialized successfully'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/generate_next_token', methods=['POST'])
def generate_next_token():
    """Generate the next token and return top-k alternatives."""
    global token_gen
    
    if token_gen is None:
        return jsonify({'status': 'error', 'message': 'Model not initialized'}), 400
    
    try:
        data = request.json
        text = data.get('text', '')
        top_k = data.get('top_k', 10)
        
        # Get token probabilities and selected token
        top_k_tokens, selected_token = token_gen.get_next_token_probabilities(text, top_k)
        
        return jsonify({
            'status': 'success',
            'selected_token': selected_token,
            'top_k_tokens': top_k_tokens
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

@app.route('/generate_to_end', methods=['POST'])
def generate_to_end():
    """Generate tokens until a stopping condition is met."""
    global token_gen
    
    if token_gen is None:
        return jsonify({'status': 'error', 'message': 'Model not initialized'}), 400
    
    try:
        data = request.json
        text = data.get('text', '')
        max_tokens = data.get('max_tokens', 50)
        top_k = data.get('top_k', 10)
        
        generated_tokens = []
        current_text = text
        
        for _ in range(max_tokens):
            top_k_tokens, selected_token = token_gen.get_next_token_probabilities(current_text, top_k)
            
            generated_tokens.append({
                'selected_token': selected_token,
                'top_k_tokens': top_k_tokens
            })
            
            current_text += selected_token['token_text']
            
            # Stop if we hit an end token
            if selected_token['token_id'] == token_gen.tokenizer.eos_token_id:
                break
        
        return jsonify({
            'status': 'success',
            'generated_tokens': generated_tokens
        })
    
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5001)
