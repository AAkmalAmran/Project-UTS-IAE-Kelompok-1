FROM python:3.10-slim

# Set direktori kerja di dalam container
WORKDIR /app

# Copy file requirements dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sisa kode aplikasi
COPY . .

# Expose port yang digunakan oleh Gunicorn (port gateway)
EXPOSE 5000

# Perintah untuk menjalankan aplikasi
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "app:app"]