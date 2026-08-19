FROM python:3.11-slim-bullseye

# Set working directory

WORKDIR /app

# Copy your requirements file
COPY requirements.txt requirements.txt

# Install Python dependencies
#pip install --no-cache-dir → makes image smaller.
RUN pip install --no-cache-dir -r requirements.txt

#Copy the project to the current directory in the docker space
COPY . .

# Run your app
CMD ["python", "manage.py","runserver","0.0.0.0:8000"]
