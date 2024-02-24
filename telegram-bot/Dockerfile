FROM python:3.9-slim

# Copy application files to the container image
WORKDIR /usr/src/app
COPY . .

# Install dependencies
RUN pip install -r requirements.txt

# Run the application
CMD [ "python", "mvp.py" ]
