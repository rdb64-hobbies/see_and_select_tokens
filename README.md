# LLM Token Visualizer

A web application that allows users to visualize and interact with individual tokens as they are generated from a Language Model (LLM). Users can see token probabilities, select alternative tokens, and observe how different choices affect the generation process.

## Features

- **Interactive Token Generation**: Generate tokens one by one or all at once
- **Probability Visualization**: Each token is color-coded based on its probability
- **Alternative Token Selection**: Click on any token to see top alternatives with probabilities
- **Regeneration from Any Point**: Select an alternative token to restart generation from that position
- **Sampling Parameter Control**: Adjust temperature, top-p, and top-k parameters
- **Multiple Model Support**: Choose from several Hugging Face models
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
   uv run main.py
   ```
   
   Or with custom host/port:
   ```bash
   uv run main.py --host 127.0.0.1 --port 3000
   ```

2. Open your browser and navigate to `http://localhost:8080` (or your custom host/port)

3. **Initialize the Model**:
   - Available models are loaded automatically from configuration
   - Select a model from the dropdown
   - Click "Initialize Model" and wait for it to load

4. **Enter a Prompt**:
   - Enter your prompt in the text area

5. **Adjust Sampling Parameters**:
   - Adjust the temperature, top-p, and top-k sliders to change the sampling behavior

6. **Generate Tokens**:
   - Click "Generate Next Token" to generate one token at a time
   - Click "Generate to End" to generate multiple tokens automatically
   - Click "Reset" to clear all generated tokens and start over

7. **Interact with Tokens**:
   - Each generated token is colored based on its probability
   - Click on any token to see alternative options
   - Select an alternative to restart generation from that point

## Technical Architecture

### Backend (Python/Flask)
- **TokenGenerator Class**: Handles model loading and token generation
- **Configuration System**: Models and settings loaded from `config.json`
- **Flask Routes**:
  - `/`: Serves the main application
  - `/config`: Returns the full configuration
  - `/models`: Returns available models from configuration
  - `/initialize`: Initializes the selected model with validation
  - `/generate_next_token`: Generates a single token with alternatives
  - `/generate_to_end`: Generates multiple tokens until completion

### Frontend (HTML/CSS/JavaScript)
- **TokenVisualizer Class**: Manages the interactive UI
- **Responsive Design**: Works on desktop and mobile devices
- **Real-time Updates**: Dynamic token rendering and probability visualization

## Dependencies

- Flask 3.0+: Web framework
- PyTorch 2.1+: Deep learning framework
- Transformers 4.35+: Hugging Face model library
- NumPy: Numerical computations

## Model Configuration

The application uses a configurable list of models via `config.json`.

To add new models, edit `config.json`:
```json
{
  "available_models": [
    {
      "id": "model-name",
      "name": "Display Name",
      "description": "Model description"
    }
  ],
  "default_model": "model-name"
}
```

Models are automatically downloaded on first use and cached locally.

## Browser Compatibility

- Chrome/Chromium 80+
- Firefox 75+
- Safari 13+
- Edge 80+

## Performance Notes

- First model initialization may take 1-2 minutes
- GPU acceleration is used automatically if available:
  - **CUDA** (NVIDIA GPUs) - preferred
  - **MPS** (Apple Silicon GPUs) - for Mac with M1/M2/M3 chips
  - **CPU** - fallback option
- Token generation typically takes 100-500ms per token
- Memory usage: depends on model size

## Software Development and Version History

Development was done almost entirely by Windsurf Cascade using Claude Sonnet 4 (BYOK).

### Version 0.1.0

The first version of this application (and everything in this README file above this point) was created entirely by Cascade from the following prompt:

> You are acting as a senior system architect and full stack engineer, and your task is to design and help build a Web application that allows the user to see and select individual tokens as they are generated from an LLM. The input from the user is a text prompt. That text prompt is provided as the input to an LLM which is used to generate and select tokens, one by one, which are displayed as output to the user. Each selected token should be displayed with its background color according to its associated probabilty and with a drop-down menu that displays the top 10 tokens considered with their associated probabilities. The user can select a token from the drop-down menu which then resets the token generation process back to that position. There should be a button that allows the user to generate a single next token and another button that allows the user to generate tokens all the way to the end. At each token-selection step, you will first need to have the LLM generate the next-token probabilities. From those probabilities, you can do random sampling to select the next token. That selected token is what gets displayed to the user with the background color according to the associated probability. In addition to selecting the next token, you need to save the tokens with the top 10 probabilities to generate the drop-down menu for that selected token. Use Python for as much of the code as possible, and use uv, not pip, to manage the environment. Also, use Flask for the front-end.

### Version 0.1.1

Removed some redundancy in the backend code. This was also done by Cascade with the following prompt:

> I see some places for improvement. First, in the backend, main.py, the method get_next_token_probabilities, for the second element in the returned tuple, rather than just returning the selected_token_id, it should return a dictionary with all of the relevant information about the selected token: the token_id, the token_text, and the probability. That way, the calling functions, generate_next_token and generate_to_end, don't have to redo the work of retrieving the selected token's text and probability.

Included the top_k parameter in generate_to_end to be consistent with generate_next_token. Also done by Cascade with the following prompt:

> Next, I think the generate_to_end function, like generate_next_token, should receive a top_k parameter in the request.json.

### Version 0.1.2

Made model selection configurable through a configuration file system. Done by Cascade with the following prompt:

> Now let's make the set of available models in the model-select menu be configurable. Take the list of available models from a configuaration file. Also, remove the gpt2 default from the back-end functions.

### Version 0.1.3

Changed the token colors and probability thresholds (done by hand). Fixed the problem with the dropdown menu appearing below the generated tokens (done by Cascade).

### Version 0.1.4

Added comprehensive sampling parameter controls with sliders for temperature, top-p, and top-k parameters. The slider configuration is done through the config.json file. Mostly done by Cascade with the following prompt:

> Now I want to add some new functionality. I want to allow the user to be able to control the temperature, top-p, and top-k values that are used in token sampling. The user will be able to set those values with slider bars, and for each one, slider's minimum, maximum, and default values should be read from the config.json file. Those 3 values, temperature, top-p, and top-k, should then be used by get_next_token_probabilities to chose the selected_token_id.

### Version 0.1.5

Added command-line arguments for host and port. Done by Cascade.

### Version 0.1.6

Added MPS (Metal Performance Shaders) support for Apple Silicon GPU acceleration. The device detection now prioritizes CUDA > MPS > CPU, providing significant performance improvements on Mac with M1/M2/M3 chips. Done by Cascade.