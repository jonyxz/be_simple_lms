  - Johan Ridho Akbar Auradhana / A11.2022.14472

## Backend Simple LMS

Merupakan proyek backend untuk aplikasi LMS sederhana yang dibuat untuk tujuan studi kasus pembelajaran backend developement menggunakan Django dan Django Ninja.

## Persyaratan

- **Docker** dan **Docker Compose**

## 📥 Clone Repository

```bash
    git clone https://github.com/jonyxz/be_simple_lms.git
    cd be_simple_lms
```

## 📦 Instalasi 

### Build Aplikasi

Build dan jalankan aplikasi menggunakan `docker compose` :

```bash
    docker-compose up -d --build
```

### Migrasi Database

Masuk ke shell container aplikasi `be_simple_lms` dan migrasi database untuk membuat tabel:

```bash
    python manage.py makemigrations
    python manage.py migrate
```
