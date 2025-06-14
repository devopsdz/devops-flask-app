# 1. نبداو من صورة رسمية خفيفة فيها بايثون
FROM python:3.13-slim

# 2. نحددو وين نخدمو فداخل الحاوية
WORKDIR /app

# 3. ننسخو الملفات من جهازنا الى الحاوية
COPY requirements.txt .


# 4. نثبتو المكتبات الضرورية
RUN pip install --no-cache-dir -r requirements.txt
COPY . .

EXPOSE 4000

# 5. وقت لي الحاوية تخدم, هاد الأمر يتنفذ
#CMD ["python", "app.py"]
CMD ["gunicorn", "app:app", "-b", "0.0.0.0:4000"]
# الهدف: نحطو فيه تعليمات باش نبني image تاع التطبيق تاعنا.

