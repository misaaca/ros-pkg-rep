# مخزن رسمی بسته‌های سیستم‌عامل ROS (ROS Official Package Repository)

[![Repository Verification](https://github.com/misaaca/ros-pkg-rep/actions/workflows/verify-repo.yml/badge.svg)](https://github.com/misaaca/ros-pkg-rep/actions/workflows/verify-repo.yml)
[![License: MIT/Apache-2.0](https://img.shields.io/badge/License-MIT%20%7C%20Apache--2.0-blue.svg)](LICENSE)
[![Target: x86_64](https://img.shields.io/badge/Target-x86__64-orange.svg)](#)
[![OS Version: 0.3.28-rumi](https://img.shields.io/badge/OS%20Version-v0.3.28--rumi-green.svg)](#)

این ریپازیتوری، مخزن رسمی و پیش‌فرض بسته‌های نرم‌افزاری و ایمیج‌های کرنل سیستم‌عامل نیتیو و مدرن **ROS (Rust Operating System)** است. سیستم‌عامل ROS بسته‌های توسعه، زبان‌های برنامه‌نویسی و ابزارهای موردنیاز خود را از طریق مدیر بسته بومی (`pkg` یا `apt`) مستقیماً از این مخزن دریافت و نصب می‌کند.

---

## 🏛 ساختار دایرکتوری‌های مخزن (Repository Layout)

```text
ROS-PKG-REP/
├── Packages.toml          # ایندکس اصلی بسته‌ها با متادیتا، نیازمندی‌ها و چک‌سام SHA-256 (فرمت TOML)
├── Packages.json          # ایندکس ثانویه بسته‌ها برای APIهای تحت وب و یکپارچه‌سازی ابری
├── Packages.gz            # نسخه فشرده‌شده gzip از Packages.toml جهت کاهش مصرف پهنای باند
├── repo.toml              # متادیتای کلی مخزن، نام، نشانی‌ها، معماری‌ها و سکشن‌ها
├── repo.conf              # فایل نمونه پیکربندی کلاینت برای قرارگیری در /etc/pkg/sources.list
├── kernel/                # بیلد‌های باینری رسمی کرنل سیستم‌عامل
│   ├── ros_kernel-v0.3.28-rumi  # باینری رسمی آخرین نسخه پایدار هسته ROS
│   ├── kernel-latest.sha256    # چک‌سام اعتبارسنجی باینری هسته
│   └── kernel.toml             # متادیتای ارتقای هسته و لاگ تغییرات (Changelog)
├── pool/                  # مخزن آرشیو بسته‌های باینری دسته‌بندی‌شده بر اساس حوزه
│   ├── nodejs/            # بسته‌های موتور جاوااسکریپت، npm و ابزارهای وب (vue-cli)
│   ├── python/            # بسته‌های pip، ماژول‌های venv و کتابخانه‌های پایتون
│   ├── rust/              # زنجیره ابزار نیتیو زبان راست شامل rustc و cargo
│   └── system/            # ابزارهای پایه‌ای خط فرمان (coreutils، net-tools)
├── tools/                 # ابزارهای اتوماسیون، پکیج‌بندی و اعتبارسنجی مخزن
│   ├── rop.py             # ماژول پایتون کار با کانتینر باینری رسمی .rop سیستم‌عامل ROS
│   ├── build_package.py   # اسکریپت ساخت پکیج‌های استاندارد .rop و .tar.gz
│   ├── build_all_packages.py # سازنده خودکار کل کاتالوگ بسته‌های مخزن
│   ├── update_index.py    # اسکنر مخزن و تولیدکننده خودکار Packages.toml و Packages.json
│   └── verify_repo.py     # ابزار تست یکپارچگی، چک‌سام‌ها و حل گراف وابستگی‌ها (CI/CD)
└── .github/workflows/
    └── verify-repo.yml    # پایپ‌لاین اجرای خودکار تست‌ها در گیت‌هاب اکشنز
```

---

## 📦 فرمت بسته‌ها: دوگانه و مدرن (Dual Package Format Architecture)

تمامی بسته‌های موجود در این مخزن به صورت دوگانه عرضه می‌شوند:

1. **فرمت بومی ROS با پسوند `.rop` (ROS Official Package):**
   - دارای هدر سخت‌گیرانه ۵۶ بایتی با امضای جادویی `ROP\x01`، نسخه فرمت، متادیتا و بررسی تمامیت SHA-256.
   - شامل بخش مانیفست استاندارد TOML و بخش پی‌لود باینری به همراه پرمیشن‌های فایل (`0o755`, `0o644`).
   - محافظت‌شده در برابر دستکاری با اعتبارسنجی مجزای هش هر فایل و هش کلی آرشیو.
2. **فرمت استاندارد فشرده `.tar.gz`:**
   - سازگار با ابزارهای استاندارد لینوکس (tar/gzip/curl) با حفظ دقیق سلسله‌مراتب سیستم‌فایل یونیکس (`bin/`, `lib/`, `etc/`).

---

## 📑 فهرست بسته‌های رسمی (Official Package Catalog)

| نام بسته | نسخه | شاخه (Section) | پیش‌نیازها | توضیحات |
| :--- | :--- | :--- | :--- | :--- |
| **`python3-pip`** | 24.0 | `python` | `python3` | ابزار رسمی مدیریت و نصب بسته‌های پایتون (`pip install`, `pip list`, `pip freeze`) |
| **`python3-venv`** | 1.0 | `python` | `python3` | ماژول و ابزار ساخت محیط‌های مجازی ایزوله پایتون (`python3 -m venv`, `pyvenv`) |
| **`python3-requests`** | 2.31.0 | `python` | `python3` | کتابخانه پرکاربرد ارسال درخواست‌های HTTP و تعامل با API در پایتون |
| **`nodejs`** | 20.10.0 | `nodejs` | `coreutils` | موتور اجرای جاوااسکریپت مبتنی بر موتور V8 و ماژول‌های داخلی |
| **`npm`** | 10.2.0 | `nodejs` | `nodejs` | مدیر بسته‌های نود، مدیریت وابستگی‌ها و بیلد اسکریپت‌ها (`npm run build`) |
| **`vue-cli`** | 5.0.8 | `nodejs` | `nodejs, npm` | ابزار داربست‌بندی و تولید پروژه‌های مدرن فرانت‌اند Vue.js |
| **`rustc`** | 1.75.0 | `rust` | `coreutils` | کامپایلر نیتیو زبان راست برای توسعه نرم‌افزار و کامپایل کدها |
| **`cargo`** | 1.75.0 | `rust` | `rustc` | مدیر پروژه و ابزار بیلد رسمی زبان راست (`cargo new`, `cargo build`, `cargo run`) |
| **`coreutils`** | 1.2.0 | `system` | — | ابزارهای استاندارد کار با فایل و مدیریت سیستم (`ls`, `cat`, `cp`, `mv`, `rm`) |
| **`net-tools`** | 0.3.0 | `system` | `coreutils` | ابزارهای تشخیص و مدیریت اتصالات شبکه (`netstat`, `hosts`, `resolv.conf`) |

---

## 💻 نحوه استفاده در سیستم‌عامل ROS (Usage in ROS)

### ۱. پیکربندی مخزن در سیستم‌عامل
در فایل `/etc/pkg/sources.list`:
```toml
[repository]
name = "ros-official"
url = "https://raw.githubusercontent.com/misaaca/ros-pkg-rep/main"
```

### ۲. به‌روزرسانی شاخص بسته‌ها
```bash
pkg update
# یا
apt update
```

### ۳. نصب اکوسیستم پایتون و ایجاد Virtual Environment
```bash
pkg install python3-pip python3-venv

# ایجاد محیط مجازی
python3 -m venv myenv

# فعال‌سازی محیط
source myenv/bin/activate
# اعلان پرامپت تغییر می‌کند: (myenv) admin@ros:/home/user#

# نصب بسته درون محیط مجازی
pip install requests
pip list
```

### ۴. نصب نود، npm و بیلد پروژه Vue.js
```bash
pkg install nodejs npm vue-cli

# ایجاد پروژه و بیلد
npm init -y
npm install vue
npm run build
# فایل‌های خروجی استاتیک در پوشه dist/ تولید می‌شوند
```

### ۵. نصب زنجیره ابزار Rust و توسعه نیتیو
```bash
pkg install rustc cargo

# ایجاد و اجرای پروژه جدید با کارگو
cargo new my_app --bin
cd my_app
cargo build
cargo run
```

### ۶. به‌روزرسانی کرنل سیستم‌عامل
```bash
pkg upgrade kernel
# یا
apt upgrade kernel
# باینری جدید در /boot/ros_kernel جایگزین شده و تغییرات روی دیسک ذخیره می‌شود
```

---

## 🛠 ابزارهای مدیریت مخزن (Repository Maintenance Tools)

### ۱. اعتبارسنجی کامل مخزن (Verification)
```bash
python3 tools/verify_repo.py
```
این دستور صحت تمامی هش‌های SHA-256، سلامت آرشیو‌های `.rop`، نبود بن‌بست یا حلقه در وابستگی‌ها و تطابق نسخه باینری کرنل را بررسی می‌کند.

### ۲. به‌روزرسانی خودکار ایندکس‌ها (Update Indexes)
```bash
python3 tools/update_index.py
```
فایل‌های `Packages.toml`، `Packages.json`، `Packages.gz`، `repo.toml` و مشخصات کرنل را بازتولید می‌کند.

### ۳. ساخت مجدد بسته‌ها (Rebuild Packages)
```bash
python3 tools/build_all_packages.py
```

---

## 📄 لایسنس
کدهای این مخزن و بسته‌های رسمی سیستم‌عامل تحت دو لایسنس **MIT** یا **Apache-2.0** منتشر شده‌اند.
