# GenAIDecoy
httpCatcherDecoy is a docker container hosting a python based low interaction http endpoint decoy that can receive and log http requests.

it logs data to stdout making use of the elastic common schema to allow a simple log processing afterwards.

GenAIDecoy is an AI-powered honeypot decoy tailormade for the CROWSI plarform. It engages potential attackers by generating dynamic responses while masking its AI nature.

This project allows users to deploy a decoy service that mimics a vehicle backend API. It leverages generative AI models (e.g., OpenAI, Gemini) to dynamically generate responses to HTTP requests. The configuration is fully customizable through a `config.json` file.

## Quick Start
### Prerequisites
### Deployment

## Customization

## Logging

The project uses ECS-compatible logging, which integrates smoothly with ElasticSearch. Logs include request metadata, session details, and generated responses.

## roadmap

## Contributing

Contributions are welcome! Feel free to open issues and submit pull requests.

## License Note

Overall this project is licensed under the MLP 2.0 License. See the [LICENSE](LICENSE) file for more details.
However, to allow you to make changes to the /genai_decoy/config/config.json file or the dockerfile without the need to publish them afterwards, these two files fall under the Apache-2.0 license.



