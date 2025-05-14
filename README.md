# GenAIDecoy

The CROWSI GenAIDecoy is an AI-powered honeypot decoy tailor-made for the CROWSI platform. It engages potential attackers by generating dynamic responses while masking its AI nature.

It logs data to stdout making use of the Elastic Common Schema to allow simple log processing afterward.

This repository contains the necessary code to build the honeypot decoy that can emulate different web services using GenAI, package this into a container, and run it on a CROWSI honeypot platform deployment.

The configuration of the honeypot is fully customizable through a `config.yaml` file.

More information on the CROWSI platform is available here:
- [CROWSI Platform GitHub](https://github.com/crowsi-foss/crowsi-platform)
- [CROWSI Website](https://crowsi.com/)

## Table of Contents
- [Features](#features)
  - [Current Features](#current-features)
  - [Features to Come](#features-to-come)
- [Quick Start](#quick-start)
  - [Prerequisites](#prerequisites)
  - [Deployment](#deployment)
- [Logging](#logging)
- [Contributing](#contributing)
- [License Note](#license-note)

## Features

### Current Features
- Python-based modular framework to build different web service-based honeypots where responses are created by a GenAI backend integration
- Currently supported web services:
  - HTTP
  - SSH
- Currently supported GenAI Providers:
  - Gemini
- All logs are formatted in the Elastic Common Schema for simple processing
- All logs are written to stdout for easy collection in Kubernetes
- YAML-based config file (`/decoy/code/config/config.yaml`) for customization of various parameters
- Basic Dockerfile as a baseline for customization
- Baseline Docker container available on Docker Hub
- Helm chart for direct deployment on the CROWSI platform including various customization options

### Features to Come
- Other GenAI providers:
  - OpenAI
- More web services:
  - MQTT
- Session Management accross multiple replicas and connection sessions

## Quick Start

Although also suitable as a standalone project, this honeypot decoy is intended to be used on the CROWSI honeypot platform. Therefore, this guide describes this scenario.

### Prerequisites
- Basic knowledge about the technology stack used by this project (Python, Docker, GenAI, Kubernetes, Helm)
- Running CROWSI deployment (see [CROWSI Platform GitHub](https://github.com/crowsi-foss/crowsi-platform))
- GenAI provider API key (see [Gemini API Documentation](https://ai.google.dev/gemini-api/docs/api-key))
- Helm installed
- In case you want to make customizations:
  - Python to test your changes
  - Docker to build your own customized Docker image
  - Private or public container registry to store your container image (e.g. Docker Hub)

### Deployment
We recommend the following steps to get started with using the CROWSI GenAIDecoy:

1. After cloning the repository, start with a review of the `/decoy/code/config/config.yaml` file. Here you can define several aspects of the GenAIDecoy like the realized protocol, the port the web service listens on, and most importantly, the prompt that is given to the AI API to generate a meaningful response. For production use, we highly recommend tailoring this prompt to your specific use case. Reach out to us if you need support.
2. After making your customizations, set a local environment variable on your system containing your API key and make sure to call it according to your name definition in the `config.yaml` file.
3. Install the necessary dependencies using the `requirements.txt` file and run the `main.py` file locally to try out your changes. For the HTTP protocol, you can try out changes by sending some test requests to the local port you defined (e.g., using Postman or Bruno) and evaluate the responses that you get.
4. After you're happy with your customizations, build your container image using Docker and push it to your registry. Make sure to adjust the exposed port in the Dockerfile in case you changed the port in the `config.yaml` file.
5. From the machine that has `kubectl` access to your CROWSI Kubernetes cluster, add a secret containing your API key and potentially the ImagePullSecret. We recommend doing this using the Kubernetes Secrets Store CSI Driver.
6. Afterwards, run the `helm install` command for the `./helm/genAIDecoy` chart. Make sure to adjust the Helm values accordingly. For example, you might want to change the reference to your respective container image as well as the references for your secrets. Check the `values.yaml` file for an overview of the potential customizations.

These steps might sound complex, so if you just want to give it a try without customizations, you just need to define a Kubernetes secret according to the default namings of the `values.yaml` file. If you then face any challenges later during your customizations, we're happy to help. Just reach out via [contact@crowsi.com](mailto:contact@crowsi.com).

## Logging

The project uses ECS-compatible logging, which integrates smoothly with ElasticSearch. Logs include request metadata, session details, and generated responses.

## Contributing

This project is in an early stage. Therefore, we would very much appreciate any feedback. Contributions are more than welcome! Feel free to open issues and submit pull requests. Let’s build a world where every attack ends in a decoy trap!

## License Note

Overall, this project is licensed under the MLP 2.0 License. See the [LICENSE](LICENSE) file for more details. However, to allow you to make changes to the `/decoy/code/config/config.yaml` file or the Dockerfile without the need to publish them afterward, these two files fall under the Apache-2.0 license.



