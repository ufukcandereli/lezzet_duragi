import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'gizli_anahtar_proje_icin'

def get_db():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# db yoksa olusturuyoz burda
def init_db():
    conn = get_db()
    c = conn.cursor()
    
    # tablolari yaratalim
    c.execute('''CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, category TEXT, image TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS daily_menu (id INTEGER PRIMARY KEY AUTOINCREMENT, menu_item_id INTEGER, day_of_week TEXT)''')
    c.execute('''CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, party_size INTEGER, date_time TEXT, status TEXT DEFAULT 'Bekliyor', assigned_table INTEGER)''')
    
    # siparisler tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, table_no INTEGER, status TEXT, items TEXT, total_price REAL)''')
    try:
        c.execute('ALTER TABLE orders ADD COLUMN payment_type TEXT')
    except sqlite3.OperationalError: pass
    
    # masa tablosu
    c.execute('''CREATE TABLE IF NOT EXISTS tables (id INTEGER PRIMARY KEY, capacity INTEGER, status TEXT DEFAULT 'Available')''')
    
    # bos ise 5 tane masa ekleyelim baslangic icin
    c.execute('SELECT count(*) FROM tables')
    if c.fetchone()[0] == 0:
        for i in range(1, 6): 
            c.execute('INSERT INTO tables (id, capacity, status) VALUES (?, ?, ?)', (i, 4, 'Available'))
            
    conn.commit()
    conn.close()

# program acilinca db kontrol edilsin
init_db()

# yardimci fonksiyonlar
def get_days_tr():
    return {'Monday': 'Pazartesi', 'Tuesday': 'Salı', 'Wednesday': 'Çarşamba', 'Thursday': 'Perşembe', 'Friday': 'Cuma', 'Saturday': 'Cumartesi', 'Sunday': 'Pazar'}

# anasayfa kismi
@app.route('/')
def index():
    conn = get_db()
    today_eng = datetime.now().strftime('%A')
    days_tr = get_days_tr()
    today_tr = days_tr.get(today_eng, today_eng)
    
    # bugunun menusunu cek
    query = '''SELECT m.* FROM menu m JOIN daily_menu d ON m.id = d.menu_item_id WHERE d.day_of_week = ?'''
    menu_items = conn.execute(query, (today_eng,)).fetchall()
    
    # masalari da alalim dropdown icin lazim
    tables = conn.execute('SELECT * FROM tables').fetchall()
    
    conn.close()
    return render_template('index.html', menu=menu_items, day=today_tr, menu_empty=len(menu_items)==0, tables=tables)

# rezervasyon sayfasi
@app.route('/rezervasyon', methods=['GET', 'POST'])
def reserve():
    if request.method == 'POST':
        # form gonderildiyse kaydet
        conn = get_db()
        conn.execute('INSERT INTO reservations (customer_name, party_size, date_time) VALUES (?, ?, ?)',
                     (request.form['name'], request.form['party_size'], request.form['date_time']))
        conn.commit()
        conn.close()
        return redirect(url_for('index'))
    
    # get istegi ise sayfayi goster
    return render_template('reservation.html')

# siparis verme
@app.route('/order', methods=['POST'])
def order():
    table_no = request.form['table_no']
    items_text = request.form['items'] 
    if not items_text: return redirect(url_for('index'))

    conn = get_db()
    item_list = [x.strip() for x in items_text.split(',')]
    total_price = 0
    
    # fiyatlari topla
    for item_name in item_list:
        row = conn.execute('SELECT price FROM menu WHERE name = ?', (item_name,)).fetchone()
        if row: total_price += row['price']
    
    conn.execute('INSERT INTO orders (table_no, status, items, total_price) VALUES (?, ?, ?, ?)', 
                 (table_no, 'Aktif', items_text, total_price))
    
    # masayi dolu olarak isaretle
    conn.execute('UPDATE tables SET status = ? WHERE id = ?', ('Occupied', table_no))
    
    conn.commit()
    conn.close()
    return redirect(url_for('index'))

# admin paneli burasi
@app.route('/admin')
def admin():
    if not session.get('logged_in'): return redirect(url_for('login'))
    conn = get_db()
    reservations = conn.execute('SELECT * FROM reservations').fetchall()
    orders = conn.execute('SELECT * FROM orders').fetchall()
    all_menu = conn.execute('SELECT * FROM menu').fetchall()
    # masa durumlarini da cekelim
    tables = conn.execute('SELECT * FROM tables').fetchall()
    conn.close()
    return render_template('admin.html', reservations=reservations, orders=orders, all_menu=all_menu, tables=tables)

# odeme islemi
@app.route('/pay_bill', methods=['POST'])
def pay_bill():
    if not session.get('logged_in'): return redirect(url_for('login'))
    order_id = request.form['order_id']
    payment_type = request.form['payment_type']
    
    conn = get_db()
    order = conn.execute('SELECT table_no FROM orders WHERE id = ?', (order_id,)).fetchone()
    
    if order:
        conn.execute('UPDATE orders SET status = ?, payment_type = ? WHERE id = ?', ('Ödendi', payment_type, order_id))
        conn.execute('UPDATE tables SET status = ? WHERE id = ?', ('Available', order['table_no']))
        conn.commit()
        
    conn.close()
    return redirect(url_for('admin'))

# haftalik menu sayfasi
@app.route('/genel-menu')
def genel_menu():
    conn = get_db()
    query = '''SELECT m.name, m.price, m.category, m.image, d.day_of_week FROM menu m JOIN daily_menu d ON m.id = d.menu_item_id'''
    data = conn.execute(query).fetchall()
    conn.close()
    
    days_tr = get_days_tr() # gunleri turkceye cevirmek icin
    
    days_order = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
    weekly_menu = {day: [] for day in days_order}
    for item in data:
        if item['day_of_week'] in weekly_menu: weekly_menu[item['day_of_week']].append(item)
        
    return render_template('general_menu.html', weekly_menu=weekly_menu, days_tr=days_tr)

# giris cikis ve diger islemler
@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        if request.form['password'] == "admin123":
            session['logged_in'] = True
            return redirect(url_for('admin'))
        else: return render_template('login.html', error="Hatalı Şifre!")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    return redirect(url_for('index'))

@app.route('/add_item', methods=['POST'])
def add_item():
    conn = get_db()
    cursor = conn.execute('INSERT INTO menu (name, price, category, image) VALUES (?, ?, ?, ?)', 
                 (request.form['name'], request.form['price'], request.form['category'], request.form['image']))
    conn.execute('INSERT INTO daily_menu (menu_item_id, day_of_week) VALUES (?, ?)', (cursor.lastrowid, request.form['day']))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/delete_item/<int:id>', methods=['POST'])
def delete_item(id):
    conn = get_db()
    conn.execute('DELETE FROM menu WHERE id = ?', (id,))
    conn.execute('DELETE FROM daily_menu WHERE menu_item_id = ?', (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/delete_reservation/<int:res_id>', methods=['POST'])
def delete_reservation(res_id):
    conn = get_db()
    conn.execute('DELETE FROM reservations WHERE id = ?', (res_id,))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

@app.route('/assign_table/<int:res_id>', methods=['POST'])
def assign_table(res_id):
    conn = get_db()
    conn.execute('UPDATE reservations SET status = ?, assigned_table = ? WHERE id = ?', ('Masaya Oturdu', request.form['table_no'], res_id))
    conn.commit()
    conn.close()
    return redirect(url_for('admin'))

if __name__ == '__main__':
    app.run(debug=True, threaded=True)