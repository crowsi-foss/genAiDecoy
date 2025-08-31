# Helm Chart for GenAiDecoy

## Purpose

This Helm chart is designed to deploy the GenAiDecoy application on a CROWSI platform Kubernetes cluster. It provides an easy and efficient way to manage the deployment, scaling, and configuration of the application.

## Configuration

The following table lists the configurable parameters of the GenAiDecoy chart and their default values.

| Parameter                     | Description                                      | Default                          |
|-------------------------------|--------------------------------------------------|----------------------------------|
| `imagereference`              | Image reference                                  | `crowsi/genaidecoy:0.1.0`        |
| `containerPort`               | Container port                                   | `8000`                           |
| `genAIApiKeyEnvVariableName`  | Environment variable name for GenAI API key      | `GENAI_API_KEY`                  |
| `useSecretProvider`           | Use secret provider                              | `true`                           |
| `secretProvider`              | Secret provider name                             | `genaidecoy-secret-provider`     |
| `secretKeyRefName`            | Secret key reference name                        | `AIapi-secret`                   |
| `secretKeyRefKey`             | Secret key reference key                         | `genAIApiKey`                    |
| `Pathprefix`                  | Path prefix                                      | `PathPrefix(`/api`)`             |
| `priority`                    | Priority                                         | `2`                              |

You can specify each parameter using the `--set key=value[,key=value]` argument to `helm install` or `helm upgrade`.

Alternatively, you can provide a YAML file that specifies the values for the parameters when installing or upgrading the chart:

```sh
helm install genAiDecoyRelease genAiDecoyRepo/genAiDecoy -f values.yaml
```

For more information, please refer to the [Helm documentation](https://helm.sh/docs/).
