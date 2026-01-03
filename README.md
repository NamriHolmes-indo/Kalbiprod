# Kalbiprod – Product Pricing Recommendation Module for Odoo

## 📌 Overview

**Kalbiprod** adalah custom module Odoo yang dibuat untuk membantu pengguna **menentukan harga jual produk secara optimal** berdasarkan **bahan dan data yang tersedia di Stock Inventory** Odoo.

Modul ini berfokus pada **perhitungan harga berbasis biaya (cost-based pricing)** dan menyediakan **beberapa rekomendasi margin keuntungan** sebagai bahan pertimbangan dalam pengambilan keputusan bisnis.

---

## 🎯 Tujuan Modul

- Membantu pengguna menentukan harga jual produk dengan lebih akurat
- Menggunakan data aktual dari Inventory Odoo
- Memberikan rekomendasi margin harga yang fleksibel
- Mengurangi kesalahan perhitungan manual

---

## ⚙️ Fitur Utama

- ✅ Perhitungan harga berbasis biaya
- ✅ Integrasi dengan produk dan inventory Odoo
- ✅ Pengelolaan data pricing order
- ✅ Penomoran otomatis menggunakan sequence
- ✅ Tampilan menu dan form khusus
- ✅ Hak akses terkontrol melalui security rules

---

## 🧩 Alur Kerja Modul

1. Pengguna membuat **Pricing Order**
2. Sistem mengambil data produk & komponen terkait
3. Total biaya dihitung berdasarkan data yang tersedia
4. Sistem menghasilkan:
   - Harga dasar
   - Rekomendasi harga dengan beberapa margin
5. Hasil dapat digunakan sebagai referensi harga jual

---

## 🏗️ Struktur Modul

```text
kalbiprod/
├── data/
│   └── sequence.xml
├── models/
│   ├── pricing_order.py
│   ├── res_users.py
│   └── __init__.py
├── security/
│   └── ir.model.access.csv
├── views/
│   ├── menu.xml
│   └── pricing_order_view.xml
├── __manifest__.py
├── __init__.py
├── README.md
