FROM python:3.10-slim

# 2. Set folder kerja di dalam container
WORKDIR /app

# 3. Copy file requirements DULU dan install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copy sisa kode aplikasi Anda
COPY . .

# 5. Pastikan folder 'instance' ada di dalam container dengan permission yang tepat
RUN mkdir -p /app/instance && \
    chmod 777 /app/instance && \
    chown -R nobody:nogroup /app/instance

# 6. Beri tahu Docker bahwa aplikasi ini akan berjalan di port 5001
EXPOSE 5001

# 7. Perintah untuk menjalankan aplikasi saat container dimulai
CMD ["flask", "run", "--host=0.0.0.0", "--port=5001"]