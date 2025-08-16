class TokenVisualizer {
    constructor() {
        this.isModelInitialized = false;
        this.currentTokens = [];
        this.originalPrompt = '';
        this.generatedTokensData = [];
        
        this.initializeElements();
        this.bindEvents();
    }

    initializeElements() {
        // Get DOM elements
        this.modelSelect = document.getElementById('model-select');
        this.initializeBtn = document.getElementById('initialize-btn');
        this.modelStatus = document.getElementById('model-status');
        this.promptInput = document.getElementById('prompt-input');
        this.generateNextBtn = document.getElementById('generate-next-btn');
        this.generateAllBtn = document.getElementById('generate-all-btn');
        this.resetBtn = document.getElementById('reset-btn');
        this.generatedText = document.getElementById('generated-text');
        this.promptTextSpan = document.querySelector('.prompt-text');
        this.generatedTokensSpan = document.querySelector('.generated-tokens');
        this.tokenDetails = document.getElementById('token-details');
    }

    bindEvents() {
        this.initializeBtn.addEventListener('click', () => this.initializeModel());
        this.generateNextBtn.addEventListener('click', () => this.generateNextToken());
        this.generateAllBtn.addEventListener('click', () => this.generateToEnd());
        this.resetBtn.addEventListener('click', () => this.reset());
        this.promptInput.addEventListener('input', () => this.updatePromptDisplay());
        
        // Close dropdowns when clicking outside
        document.addEventListener('click', (e) => {
            if (!e.target.closest('.token')) {
                this.closeAllDropdowns();
            }
        });
    }

    async initializeModel() {
        const modelName = this.modelSelect.value;
        this.setModelStatus('loading', 'Initializing...');
        this.initializeBtn.disabled = true;

        try {
            const response = await fetch('/initialize', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ model_name: modelName })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.isModelInitialized = true;
                this.setModelStatus('success', 'Ready');
                this.generateNextBtn.disabled = false;
                this.generateAllBtn.disabled = false;
            } else {
                this.setModelStatus('error', data.message);
            }
        } catch (error) {
            this.setModelStatus('error', 'Failed to initialize');
            console.error('Initialization error:', error);
        } finally {
            this.initializeBtn.disabled = false;
        }
    }

    setModelStatus(type, message) {
        this.modelStatus.className = `status ${type}`;
        this.modelStatus.textContent = message;
    }

    updatePromptDisplay() {
        this.promptTextSpan.textContent = this.promptInput.value;
        this.originalPrompt = this.promptInput.value;
    }

    async generateNextToken() {
        if (!this.isModelInitialized) return;

        const currentText = this.getCurrentText();
        this.generateNextBtn.disabled = true;
        this.generateAllBtn.disabled = true;

        try {
            const response = await fetch('/generate_next_token', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    text: currentText,
                    top_k: 10 
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                this.addToken(data.selected_token, data.top_k_tokens);
            } else {
                console.error('Generation error:', data.message);
            }
        } catch (error) {
            console.error('Request error:', error);
        } finally {
            this.generateNextBtn.disabled = false;
            this.generateAllBtn.disabled = false;
        }
    }

    async generateToEnd() {
        if (!this.isModelInitialized) return;

        const currentText = this.getCurrentText();
        this.generateNextBtn.disabled = true;
        this.generateAllBtn.disabled = true;

        try {
            const response = await fetch('/generate_to_end', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ 
                    text: currentText,
                    max_tokens: 50 
                })
            });

            const data = await response.json();
            
            if (data.status === 'success') {
                for (const tokenData of data.generated_tokens) {
                    this.addToken(tokenData.selected_token, tokenData.top_k_tokens);
                }
            } else {
                console.error('Generation error:', data.message);
            }
        } catch (error) {
            console.error('Request error:', error);
        } finally {
            this.generateNextBtn.disabled = false;
            this.generateAllBtn.disabled = false;
        }
    }

    addToken(selectedToken, topKTokens) {
        const tokenData = {
            selected: selectedToken,
            alternatives: topKTokens,
            index: this.generatedTokensData.length
        };
        
        this.generatedTokensData.push(tokenData);
        this.renderTokens();
        this.updateTokenDetails(tokenData);
    }

    renderTokens() {
        this.generatedTokensSpan.innerHTML = '';
        
        this.generatedTokensData.forEach((tokenData, index) => {
            const tokenElement = this.createTokenElement(tokenData, index);
            this.generatedTokensSpan.appendChild(tokenElement);
        });
    }

    createTokenElement(tokenData, index) {
        const tokenSpan = document.createElement('span');
        tokenSpan.className = `token ${this.getProbabilityClass(tokenData.selected.probability)}`;
        tokenSpan.textContent = tokenData.selected.token_text;
        tokenSpan.dataset.index = index;

        // Add click event for dropdown
        tokenSpan.addEventListener('click', (e) => {
            e.stopPropagation();
            this.toggleDropdown(tokenSpan, tokenData);
        });

        return tokenSpan;
    }

    getProbabilityClass(probability) {
        if (probability > 0.7) return 'prob-very-high';
        if (probability > 0.5) return 'prob-high';
        if (probability > 0.3) return 'prob-medium';
        if (probability > 0.1) return 'prob-low';
        return 'prob-very-low';
    }

    toggleDropdown(tokenElement, tokenData) {
        // Close other dropdowns
        this.closeAllDropdowns();

        // Create and show dropdown
        const dropdown = this.createDropdown(tokenData, tokenElement);
        tokenElement.appendChild(dropdown);
        dropdown.classList.add('show');
        tokenElement.classList.add('selected');
    }

    createDropdown(tokenData, tokenElement) {
        const dropdown = document.createElement('div');
        dropdown.className = 'dropdown';

        tokenData.alternatives.forEach(token => {
            const item = document.createElement('div');
            item.className = 'dropdown-item';
            
            const tokenText = document.createElement('span');
            tokenText.className = 'dropdown-token';
            tokenText.textContent = token.token_text;
            
            const probText = document.createElement('span');
            probText.className = 'dropdown-prob';
            probText.textContent = `${(token.probability * 100).toFixed(1)}%`;
            
            item.appendChild(tokenText);
            item.appendChild(probText);
            
            item.addEventListener('click', (e) => {
                e.stopPropagation();
                this.selectAlternativeToken(tokenData.index, token);
            });
            
            dropdown.appendChild(item);
        });

        return dropdown;
    }

    selectAlternativeToken(tokenIndex, selectedToken) {
        // Update the token data
        this.generatedTokensData[tokenIndex].selected = selectedToken;
        
        // Remove all tokens after this index
        this.generatedTokensData = this.generatedTokensData.slice(0, tokenIndex + 1);
        
        // Re-render tokens
        this.renderTokens();
        this.closeAllDropdowns();
        
        // Update token details
        this.updateTokenDetails(this.generatedTokensData[tokenIndex]);
    }

    closeAllDropdowns() {
        const dropdowns = document.querySelectorAll('.dropdown');
        dropdowns.forEach(dropdown => dropdown.remove());
        
        const selectedTokens = document.querySelectorAll('.token.selected');
        selectedTokens.forEach(token => token.classList.remove('selected'));
    }

    updateTokenDetails(tokenData) {
        const details = `
            <strong>Selected Token:</strong> "${tokenData.selected.token_text}"<br>
            <strong>Probability:</strong> ${(tokenData.selected.probability * 100).toFixed(2)}%<br>
            <strong>Token ID:</strong> ${tokenData.selected.token_id}<br>
            <strong>Position:</strong> ${tokenData.index + 1}<br><br>
            <strong>Top Alternatives:</strong><br>
            ${tokenData.alternatives.slice(0, 5).map(token => 
                `"${token.token_text}" (${(token.probability * 100).toFixed(1)}%)`
            ).join('<br>')}
        `;
        this.tokenDetails.innerHTML = details;
    }

    getCurrentText() {
        let text = this.originalPrompt;
        for (const tokenData of this.generatedTokensData) {
            text += tokenData.selected.token_text;
        }
        return text;
    }

    reset() {
        this.generatedTokensData = [];
        this.originalPrompt = '';
        this.promptInput.value = '';
        this.promptTextSpan.textContent = '';
        this.generatedTokensSpan.innerHTML = '';
        this.tokenDetails.innerHTML = 'No tokens generated yet.';
        this.closeAllDropdowns();
    }
}

// Initialize the application when the page loads
document.addEventListener('DOMContentLoaded', () => {
    new TokenVisualizer();
});
