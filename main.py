from flask import Flask, render_template, request, jsonify
import torch
from transformers import AutoTokenizer, AutoModelForCausalLM
from typing import List, Dict, Tuple
import json
import os
import argparse

app = Flask(__name__)

# Load configuration
def load_config():
    config_path = os.path.join(os.path.dirname(__file__), 'config.json')
    with open(config_path, 'r') as f:
        return json.load(f)

config = load_config()

class TokenGenerator:
    def __init__(self, model_name):
        """Initialize the token generator with a pre-trained model."""
        if torch.cuda.is_available():
            self.device = torch.device("cuda")
        elif torch.backends.mps.is_available():
            self.device = torch.device("mps")
        else:
            self.device = torch.device("cpu")
        print(f"Using device: {self.device}")
        
        # Load tokenizer and model
        self.tokenizer = AutoTokenizer.from_pretrained(model_name)
        self.model = AutoModelForCausalLM.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()
        
        # Add padding token if it doesn't exist
        if self.tokenizer.pad_token is None:
            self.tokenizer.pad_token = self.tokenizer.eos_token
    
    def get_next_token_probabilities(self, text: str, top_k: int = 10, temperature: float = 1.0, top_p: float = 0.9) -> Tuple[List[Dict], Dict]:
        """
        Given the text input, get the top token candidates and the selected token.
        Returns: (top_k_tokens_with_probs, selected_token_dict)
        """
        # Tokenize input
        inputs = self.tokenizer.encode(text, return_tensors="pt").to(self.device)
        
        with torch.no_grad():
            # Get model outputs
            outputs = self.model(inputs)
            logits = outputs.logits[0, -1, :]  # Get logits for the last token
            
            # Apply temperature scaling
            if temperature != 1.0:
                logits = logits / temperature
            
            # Convert to probabilities
            probs = torch.softmax(logits, dim=-1)
            
            # Apply top-k filtering
            if top_k > 0:
                top_k_probs, top_k_indices = torch.topk(probs, min(top_k, probs.size(-1)))
                # Zero out probabilities for tokens not in top-k
                filtered_probs = torch.zeros_like(probs)
                filtered_probs.scatter_(0, top_k_indices, top_k_probs)
                probs = filtered_probs
            
            # Apply top-p (nucleus) filtering
            if top_p < 1.0:
                sorted_probs, sorted_indices = torch.sort(probs, descending=True)
                cumulative_probs = torch.cumsum(sorted_probs, dim=0)
                
                # Find the cutoff point for top-p (include the token that exceeds top_p)
                cutoff_index = torch.where(cumulative_probs > top_p)[0]
                if len(cutoff_index) > 0:
                    cutoff_index = cutoff_index[0] + 1  # Include the token that exceeded top_p
                    # Zero out probabilities beyond the cutoff
                    sorted_probs[cutoff_index:] = 0
                    # Restore original order
                    probs = torch.zeros_like(probs)
                    probs.scatter_(0, sorted_indices, sorted_probs)
            
            # Renormalize probabilities
            probs = probs / probs.sum()
            
            # Sample from the filtered distribution for the selected token
            selected_token_id = torch.multinomial(probs, 1).item()
            selected_token_text = self.tokenizer.decode([selected_token_id])
            selected_token_prob = probs[selected_token_id].item()
            
            # Create selected token dictionary
            selected_token = {
                'token_id': selected_token_id,
                'token_text': selected_token_text,
                'probability': selected_token_prob
            }
            
            # Get top tokens for display (from final filtered probabilities)
            display_top_probs, display_top_indices = torch.topk(probs, min(12, (probs > 0).sum().item()))
            
            # Convert to list of dictionaries
            display_top_tokens = []
            for i in range(len(display_top_indices)):
                token_id = display_top_indices[i].item()
                token_text = self.tokenizer.decode([token_id])
                probability = display_top_probs[i].item()
                
                display_top_tokens.append({
                    'token_id': token_id,
                    'token_text': token_text,
                    'probability': probability
                })
            
            return display_top_tokens, selected_token
    
    def decode_token(self, token_id: int) -> str:
        """Decode a single token ID to text."""
        return self.tokenizer.decode([token_id])

# Global token generator instance
token_gen = None

@app.route('/')
def index():
    """Serve the main application page."""
    return render_template('index.html')

@app.route('/config')
def get_config():
    """Return the configuration including available models and sampling parameters."""
    return jsonify(config)

@app.route('/models', methods=['GET'])
def get_available_models():
    """Return the list of available models from configuration."""
    return jsonify({
        'status': 'success',
        'models': config['available_models'],
        'default_model': config.get('default_model')
    })

@app.route('/initialize', methods=['POST'])
def initialize_model():
    """Initialize the token generator model."""
    global token_gen
    try:
        model_name = request.json.get('model_name')
        if not model_name:
            return jsonify({'status': 'error', 'message': 'Model name is required'}), 400
        
        # Validate model name against config
        available_models = [model['id'] for model in config['available_models']]
        if model_name not in available_models:
            return jsonify({'status': 'error', 'message': f'Model {model_name} not available'}), 400
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
        temperature = data.get('temperature', config['sampling_parameters']['temperature']['default'])
        top_p = data.get('top_p', config['sampling_parameters']['top_p']['default'])
        
        # Get token probabilities and selected token
        top_k_tokens, selected_token = token_gen.get_next_token_probabilities(text, top_k, temperature, top_p)
        
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
        temperature = data.get('temperature', config['sampling_parameters']['temperature']['default'])
        top_p = data.get('top_p', config['sampling_parameters']['top_p']['default'])
        
        generated_tokens = []
        current_text = text
        
        for _ in range(max_tokens):
            top_k_tokens, selected_token = token_gen.get_next_token_probabilities(current_text, top_k, temperature, top_p)
            
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

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='LLM Token Visualizer')
    parser.add_argument('--host', type=str, default=config['server']['host'],
                        help=f"Host to bind to (default: {config['server']['host']})")
    parser.add_argument('--port', type=int, default=config['server']['port'],
                        help=f"Port to bind to (default: {config['server']['port']})")
    return parser.parse_args()

if __name__ == '__main__':
    args = parse_args()
    app.run(debug=True, host=args.host, port=args.port)
