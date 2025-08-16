# LLM Token Visualizer

A web application that allows users to visualize and interact with individual tokens as they are generated from a Language Model (LLM). Users can see token probabilities, select alternative tokens, and observe how different choices affect the generation process.

## Features

- **Interactive Token Generation**: Generate tokens one by one or all at once
- **Probability Visualization**: Each token is color-coded based on its probability
- **Alternative Token Selection**: Click on any token to see top-10 alternatives with probabilities
- **Regeneration from Any Point**: Select an alternative token to restart generation from that position
- **Multiple Model Support**: Choose from GPT-2, GPT-2 Medium, or DistilGPT-2
- **Real-time Token Details**: View detailed information about selected tokens

## Installation

1. Make sure you have Python 3.13+ and `uv` installed
2. Clone or navigate to the project directory
3. Install dependencies:
   ```bash
   uv sync
   ```

## Usage

1. Start the Flask server:
   ```bash
   uv run python main.py
   ```

2. Open your browser and navigate to `http://localhost:5000`

3. **Initialize the Model**:
   - Select a model from the dropdown (GPT-2, GPT-2 Medium, or DistilGPT-2)
   - Click "Initialize Model" and wait for it to load

4. **Generate Tokens**:
   - Enter your prompt in the text area
   - Click "Generate Next Token" to generate one token at a time
   - Click "Generate to End" to generate multiple tokens automatically

5. **Interact with Tokens**:
   - Each generated token is colored based on its probability:
     - Green: Very high probability (>70%)
     - Blue: High probability (50-70%)
     - Purple: Medium probability (30-50%)
     - Orange: Low probability (10-30%)
     - Red: Very low probability (<10%)
   - Click on any token to see alternative options
   - Select an alternative to restart generation from that point

6. **Reset**: Click "Reset" to clear all generated tokens and start over

## Technical Architecture

### Backend (Python/Flask)
- **TokenGenerator Class**: Handles model loading and token generation
- **Flask Routes**:
  - `/`: Serves the main application
  - `/initialize`: Initializes the selected model
  - `/generate_next_token`: Generates a single token with alternatives
  - `/generate_to_end`: Generates multiple tokens until completion

### Frontend (HTML/CSS/JavaScript)
- **TokenVisualizer Class**: Manages the interactive UI
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Dynamic token rendering and probability visualization

### Key Components
- **Probability Calculation**: Uses PyTorch softmax on model logits
- **Token Sampling**: Multinomial sampling from probability distribution
- **Alternative Generation**: Top-k token selection with probabilities
- **State Management**: Tracks token history for regeneration

## Dependencies

- Flask 3.0+: Web framework
- PyTorch 2.1+: Deep learning framework
- Transformers 4.35+: Hugging Face model library
- NumPy: Numerical computations

## Model Information

The application uses Hugging Face transformers models:
- **GPT-2**: 124M parameters, fastest generation
- **GPT-2 Medium**: 355M parameters, better quality
- **DistilGPT-2**: 82M parameters, lightweight version

Models are automatically downloaded on first use and cached locally.

## Browser Compatibility

- Chrome/Chromium 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Performance Notes

- First model initialization may take 1-2 minutes
- GPU acceleration is used automatically if available
- Token generation typically takes 100-500ms per token
- Memory usage: ~1-4GB depending on model size