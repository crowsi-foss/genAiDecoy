# GenAIDecoy

GenAIDecoy is an AI-powered honeypot decoy tailormade for the CROWSI plarform. It engages potential attackers by generating dynamic responses while masking its AI nature.

## Overview

This project allows users to deploy a decoy service that mimics a vehicle backend API. It leverages generative AI models (e.g., OpenAI, Gemini) to dynamically generate responses to HTTP requests. The configuration is fully customizable through a `config.json` file.

## Features

- Supports multiple AI providers (e.g., OpenAI, Gemini)
- Session-aware: remembers the last 10 messages per client
- Customizable prompts and context
- Flexible and extendable architecture
- ECS-compatible logging for seamless integration with ElasticSearch

## Getting Started

### Prerequisites

- Python 3.10+
- Access to an AI provider (e.g., OpenAI, Gemini) and a valid API key

### Installation

1. Clone the repository:

   ```bash
   git clone https://github.com/your-repo/genai-decoy.git
   cd genai-decoy
   ```

2. Set up a virtual environment:

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:

   ```bash
   pip install -r requirements.txt
   ```

### Environment Variables

Ensure your AI provider's API key is available as an environment variable:

```bash
export GENAI_API_KEY=your_api_key
```

### Running the Application

Start the decoy server:

```bash
python main.py
```

The server will be available on the configured port (e.g., `http://localhost:8080`).

### Logging

The project uses ECS-compatible logging, which integrates smoothly with ElasticSearch. Logs include request metadata, session details, and generated responses.


## Contributing

Contributions are welcome! Feel free to open issues and submit pull requests.

## License

Overall this project is licensed under the MLP 2.0 License. See the [LICENSE](LICENSE) file for more details.
However, to allow you to make changes to the /genai_decoy/config/config.json file or the dockerfile without the need to publish them afterwards, these two files fall under the Apache-2.0 license.



