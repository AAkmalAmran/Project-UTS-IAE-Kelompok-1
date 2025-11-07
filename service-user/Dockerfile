# service-user/Dockerfile

# 1. Mulai dari base image Python yang ringan
FROM python:3.12-slim

# 2. Set folder kerja di dalam container
WORKDIR /app

# 3. Copy file requirements DULU dan install
#    Ini memanfaatkan Docker cache. Jika requirements.txt tidak berubah,
#    langkah ini akan di-skip saat build ulang, jadi lebih cepat.
COPY requirements.txt .
RUN pip install -r requirements.txt

# 4. Copy sisa kode aplikasi Anda
COPY . .

# 5. Pastikan folder 'instance' ada di dalam container dengan permission yang tepat
RUN mkdir -p /app/instance && \
    chmod 777 /app/instance && \
    chown -R nobody:nogroup /app/instance

# 6. Beri tahu Docker bahwa aplikasi ini akan berjalan di port 5001
EXPOSE 5001

# 7. Perintah untuk menjalankan aplikasi saat container dimulai
#    Kita menggunakan variabel dari .env yang akan di-inject oleh Docker Compose
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]