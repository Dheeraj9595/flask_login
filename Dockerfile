# Use an official Python runtime as a base image
FROM python:3-alpine3.15

# Set the working directory in the container
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Make port 5000 available to the world outside this container
EXPOSE 5000

# Run your Flask application when the container launches
CMD python ./main.py
