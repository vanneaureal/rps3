import unittest
import time
import random
import sqlite3
import json
import os
import tempfile
from bitonic_sort import bitonic_sort


class TestDatabaseIntegration(unittest.TestCase):
    def setUp(self):
        # ВРЕМЕННАЯ БД в системной папке
        self.test_db = tempfile.mktemp(suffix='.db')

    def tearDown(self):
        try:
            if os.path.exists(self.test_db):
                os.unlink(self.test_db)
        except:
            pass

    def create_test_db(self):
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute('''CREATE TABLE users (id INTEGER PRIMARY KEY, username TEXT, password_hash TEXT)''')
        cursor.execute(
            '''CREATE TABLE arrays (id INTEGER PRIMARY KEY, user_id INTEGER, original_array TEXT, sorted_array TEXT, array_length INTEGER, sorting_time REAL)''')
        conn.commit()
        conn.close()

    def save_test_array(self, user_id, original, sorted_arr, time_val, length):
        conn = sqlite3.connect(self.test_db)
        cursor = conn.cursor()
        cursor.execute(
            '''INSERT INTO arrays (user_id, original_array, sorted_array, array_length, sorting_time) VALUES (?, ?, ?, ?, ?)''',
            (user_id, json.dumps(original), json.dumps(sorted_arr), length, time_val))
        conn.commit()
        conn.close()

    def test_add_arrays(self):
        """✅ А) Добавление 100/1000/10000 массивов"""
        print("\n📥 ТЕСТ А: Добавление массивов")
        self.create_test_db()
        sizes = [100, 1000, 10000]

        for size in sizes:
            start = time.time()
            for _ in range(size):
                arr = [random.randint(1, 1000) for _ in range(10)]
                sorted_arr = bitonic_sort(arr.copy())
                self.save_test_array(1, arr, sorted_arr, 0.001, 10)
            elapsed = time.time() - start
            print(f"✅ {size} массивов: {elapsed:.2f}с ✓")

    def test_cleanup(self):
        """✅ В) Очистка БД"""
        print("\n🧹 ТЕСТ С: Очистка БД")
        self.create_test_db()
        sizes = [100, 1000]

        for size in sizes:
            # Заполняем
            for _ in range(size):
                arr = [random.randint(1, 1000) for _ in range(10)]
                self.save_test_array(1, arr, bitonic_sort(arr.copy()), 0.001, 10)

            # 3 раза очищаем
            for run in range(3):
                start = time.time()
                conn = sqlite3.connect(self.test_db)
                conn.execute("DELETE FROM arrays")
                conn.commit()
                conn.close()
                elapsed = time.time() - start
                print(f"🧹 {size} записей (#{run + 1}): {elapsed:.4f}с ✓")

    def test_load_and_sort(self):
        """✅ Б) Выгрузка + сортировка"""
        print("\n📤 ТЕСТ Б: Выгрузка и сортировка")
        self.create_test_db()
        size = 1000

        # Заполняем
        for _ in range(size):
            arr = [random.randint(1, 1000) for _ in range(10)]
            self.save_test_array(1, arr, bitonic_sort(arr.copy()), 0.001, 10)

        # 3 теста по 100 массивов
        for run in range(3):
            start = time.time()
            total_time = 0

            conn = sqlite3.connect(self.test_db)
            cursor = conn.cursor()
            cursor.execute("SELECT original_array FROM arrays LIMIT 100")
            rows = cursor.fetchall()
            conn.close()

            for row in rows:
                single_start = time.time()
                arr = json.loads(row[0])
                bitonic_sort(arr.copy())
                total_time += (time.time() - single_start)

            elapsed = time.time() - start
            avg_time = total_time / 100
            print(f"📊 Запуск #{run + 1}: {elapsed:.2f}с, среднее: {avg_time:.6f}с ✓")


if __name__ == '__main__':
    print("🔬 ИНТЕГРАЦИОННЫЕ ТЕСТЫ ЛАБОРАТОРНОЙ №3")
    print("=" * 70)
    unittest.main(verbosity=2)
