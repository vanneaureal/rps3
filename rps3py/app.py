from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify, send_file
import time
import random
import json
import sqlite3
from io import BytesIO
from models import init_db, hash_password, register_user, authenticate_user, save_array, get_user_arrays
from bitonic_sort import bitonic_sort

app = Flask(__name__)
app.secret_key = 'your-secret-key-change-in-production'


@app.route('/')
def index():
    if 'user_id' in session:
        return redirect(url_for('main'))
    return redirect(url_for('login'))


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        if register_user(username, password):
            flash('✅ Регистрация успешна! Войдите в систему.', 'success')
            return redirect(url_for('login'))
        else:
            flash('❌ Пользователь уже существует!', 'error')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user_id = authenticate_user(username, password)
        if user_id:
            session['user_id'] = user_id
            session['username'] = username
            flash('✅ Успешный вход!', 'success')
            return redirect(url_for('main'))
        else:
            flash('❌ Неверные логин/пароль!', 'error')
    return render_template('login.html')


@app.route('/main')
def main():
    if 'user_id' not in session:
        return redirect(url_for('login'))
    arrays = get_user_arrays(session['user_id'])
    return render_template('main.html', arrays=arrays, username=session.get('username', ''))


@app.route('/sort', methods=['POST'])
def sort_array():
    if 'user_id' not in session:
        return jsonify({'error': 'Не авторизован'}), 401

    data = request.json
    input_type = data['type']

    if input_type == 'manual':
        try:
            original_arr = [float(x) for x in data['array']]
        except:
            return jsonify({'error': 'Неверный формат массива'}), 400
    else:  # random с диапазоном
        size = data.get('size', 10)
        min_val = data.get('min', 1)
        max_val = data.get('max', 1000)
        original_arr = [random.randint(min_val, max_val) for _ in range(size)]

    start_time = time.time()
    sorted_arr = bitonic_sort(original_arr.copy())
    sorting_time = time.time() - start_time

    return jsonify({
        'original': original_arr,
        'sorted': sorted_arr,
        'time': sorting_time,
        'length': len(original_arr)
    })


@app.route('/save_array', methods=['POST'])
def save_array_route():
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401

    data = request.json
    save_array(session['user_id'], data['original'], data['sorted'], data['time'], data['length'])
    return jsonify({'success': True})


@app.route('/delete_array/<int:array_id>', methods=['POST'])
def delete_array(array_id):
    if 'user_id' not in session:
        return jsonify({'success': False, 'error': 'Не авторизован'}), 401

    try:
        conn = sqlite3.connect('bitonic_app.db')
        cursor = conn.cursor()
        cursor.execute('DELETE FROM arrays WHERE id = ? AND user_id = ?', (array_id, session['user_id']))
        deleted = cursor.rowcount > 0
        conn.commit()
        conn.close()
        return jsonify({'success': deleted})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/export_arrays_txt')
def export_arrays_txt():
    if 'user_id' not in session:
        flash('❌ Нужно авторизоваться!', 'error')
        return redirect(url_for('login'))

    arrays = get_user_arrays(session['user_id'])

    # 🔥 BYTESIO + UTF-8
    output = BytesIO()

    content = ""
    if not arrays:
        content = "📭 У вас нет сохраненных массивов\n"
    else:
        content = f"📚 ВАШИ МАССИВЫ ({len(arrays)} шт.) - {session['username']}\n"
        content += f"Экспорт: {time.strftime('%Y-%m-%d %H:%M:%S')}\n"
        content += "=" * 70 + "\n\n"

        for i, array in enumerate(arrays, 1):
            content += f"МАССИВ #{i}\n"
            content += "-" * 40 + "\n"
            content += f"📅 Дата: {array['created_at'][:16]}\n"
            content += f"📊 Длина: {array['length']} элементов\n"
            content += f"⏱️ Время сортировки: {array['time']:.6f} сек\n\n"

            content += "🔢 ИСХОДНЫЙ МАССИВ:\n"
            content += "[" + ", ".join(map(str, array['original'])) + "]\n\n"

            content += "✅ ОТСОРТИРОВАННЫЙ МАССИВ:\n"
            content += "[" + ", ".join(map(str, array['sorted'])) + "]\n\n"

            content += "-" * 70 + "\n\n"

    output.write(content.encode('utf-8'))
    output.seek(0)

    return send_file(
        output,
        mimetype='text/plain; charset=utf-8',
        as_attachment=True,
        download_name=f'my_arrays_{session["username"]}_{time.strftime("%Y%m%d_%H%M%S")}.txt'
    )


@app.route('/logout')
def logout():
    session.clear()
    flash('👋 Вы вышли из системы', 'info')
    return redirect(url_for('login'))


if __name__ == '__main__':
    init_db()
    app.run(debug=True, host='127.0.0.1', port=5000)
