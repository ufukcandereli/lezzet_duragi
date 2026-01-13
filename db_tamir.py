import sqlite3

def fix_database():
    conn = sqlite3.connect('database.db')
    c = conn.cursor()
    print("🛠️ Veritabanı tamir ediliyor...")

    # masalar tablosu yoksa ekle
    try:
        c.execute('''CREATE TABLE IF NOT EXISTS tables 
                     (id INTEGER PRIMARY KEY, capacity INTEGER, status TEXT DEFAULT 'Available')''')
        # 5 tane masa ekle
        c.execute('SELECT count(*) FROM tables')
        if c.fetchone()[0] == 0:
            for i in range(1, 6): 
                c.execute('INSERT INTO tables (id, capacity, status) VALUES (?, ?, ?)', (i, 4, 'Available'))
            print("✅ Masalar tablosu oluşturuldu.")
        else:
            print("ℹ️ Masalar tablosu zaten var.")
    except Exception as e:
        print(f"Hata (Tables): {e}")

    # siparislere odeme tipi ekle
    try:
        c.execute('ALTER TABLE orders ADD COLUMN payment_type TEXT')
        print("✅ Siparişlere 'payment_type' sütunu eklendi.")
    except:
        print("ℹ️ Siparişlerde 'payment_type' zaten var.")

    conn.commit()
    conn.close()
    print("🎉 TAMAMLANDI! Veritabanın artık rapora uygun.")

if __name__ == '__main__':
    fix_database()