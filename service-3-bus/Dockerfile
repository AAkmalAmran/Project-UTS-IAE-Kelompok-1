# Gunakan base image Python 3.10 slim
FROM python:3.10-slim

# Set direktori kerja di dalam container
WORKDIR /app

# Copy file requirements dan install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy sisa kode aplikasi
COPY . .

# Buat folder 'instance' jika belum ada (untuk SQLite)
RUN mkdir -p instance

# Expose port yang digunakan oleh Gunicorn (sesuai port di CMD)
EXPOSE 5004

# Perintah untuk menjalankan aplikasi (production)
# Gunicorn akan mencari objek 'app' di dalam file 'app.py'
CMD ["gunicorn", "--bind", "0.0.0.0:5004", "app:app"]