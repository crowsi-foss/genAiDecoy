# This file is licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License. You may obtain a copy of the License at  http://www.apache.org/licenses/LICENSE-2.0
# Unless required by applicable law or agreed to in writing, software distributed under the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the License for the specific language governing permissions and limitations under the License.
# The rest of the project repository remains licensed under the MPL-2.0 license. See the LICENSE file for details.

# Base image
FROM python:3.14.0a2-alpine3.19

# Create a non-root user and group with a numeric UID and GID
RUN addgroup -g 1001 -S appuser && adduser -u 1001 -G appuser -S appuser

# Set working directory
WORKDIR /home/genaidecoy
# Copy the application source code
COPY /code/ .   

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Remove the requirements file
RUN rm requirements.txt

# Adjust file permissions for the non-root user
RUN chown -R 1001:1001 /home/genaidecoy

# Switch to the non-root user
USER 1001

# Start the Gunicorn server
CMD ["python", "main.py"]

# Expose port. Make sure to match the port defined in your config file!
EXPOSE 8000   

# No health check routine added as container is intended to be used in Kubernetes environment
