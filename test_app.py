"""
test dosyasi - projenin duzgun calisip calismadigini kontrol ediyoz
"""
import pytest
import sqlite3
import os
import tempfile
from app import app, get_db, init_db


# test icin gerekli hazirliklar

@pytest.fixture
def client():
    """test icin gecici db olusturuyoz"""
    # gecici db dosyasi
    db_fd, db_path = tempfile.mkstemp()
    
    app.config['TESTING'] = True
    app.config['DATABASE'] = db_path
    
    # get_db yi gecici db ye bagla
    original_get_db = app.config.get('GET_DB_FUNC')
    
    def test_get_db():
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    # fonksiyonu degistir
    import app as app_module
    app_module.get_db = test_get_db
    
    with app.test_client() as client:
        with app.app_context():
            # test db yi hazirla
            conn = test_get_db()
            c = conn.cursor()
            
            # tablolar
            c.execute('''CREATE TABLE IF NOT EXISTS menu (id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT, price REAL, category TEXT, image TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS daily_menu (id INTEGER PRIMARY KEY AUTOINCREMENT, menu_item_id INTEGER, day_of_week TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS reservations (id INTEGER PRIMARY KEY AUTOINCREMENT, customer_name TEXT, party_size INTEGER, date_time TEXT, status TEXT DEFAULT 'Bekliyor', assigned_table INTEGER)''')
            c.execute('''CREATE TABLE IF NOT EXISTS orders (id INTEGER PRIMARY KEY AUTOINCREMENT, table_no INTEGER, status TEXT, items TEXT, total_price REAL, payment_type TEXT)''')
            c.execute('''CREATE TABLE IF NOT EXISTS tables (id INTEGER PRIMARY KEY, capacity INTEGER, status TEXT DEFAULT 'Available')''')
            
            # masalari ekle
            for i in range(1, 6):
                c.execute('INSERT INTO tables (id, capacity, status) VALUES (?, ?, ?)', (i, 4, 'Available'))
            
            conn.commit()
            conn.close()
            
        yield client
    
    # temizle
    os.close(db_fd)
    os.unlink(db_path)


@pytest.fixture
def logged_in_client(client):
    """giris yapmis admin icin"""
    client.post('/login', data={'password': 'admin123'})
    return client


@pytest.fixture
def sample_menu_item(client):
    """ornek yemek ekle teste"""
    import app as app_module
    conn = app_module.get_db()
    cursor = conn.execute(
        'INSERT INTO menu (name, price, category, image) VALUES (?, ?, ?, ?)',
        ('Test Köfte', 85.0, 'Ana Yemek', 'kofte.jpg')
    )
    menu_id = cursor.lastrowid
    conn.execute(
        'INSERT INTO daily_menu (menu_item_id, day_of_week) VALUES (?, ?)',
        (menu_id, 'Monday')
    )
    conn.commit()
    conn.close()
    return menu_id


@pytest.fixture
def sample_reservation(client):
    """ornek rezervasyon ekle"""
    import app as app_module
    conn = app_module.get_db()
    conn.execute(
        'INSERT INTO reservations (customer_name, party_size, date_time, status) VALUES (?, ?, ?, ?)',
        ('Test Müşteri', 4, '2026-01-15T19:00', 'Bekliyor')
    )
    conn.commit()
    res_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return res_id


@pytest.fixture
def sample_order(client, sample_menu_item):
    """ornek siparis ekle"""
    import app as app_module
    conn = app_module.get_db()
    conn.execute(
        'INSERT INTO orders (table_no, status, items, total_price) VALUES (?, ?, ?, ?)',
        (1, 'Aktif', 'Test Köfte', 85.0)
    )
    conn.execute('UPDATE tables SET status = ? WHERE id = ?', ('Occupied', 1))
    conn.commit()
    order_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return order_id


# anasayfa testleri

class TestIndexPage:
    """anasayfa testleri"""
    
    def test_index_page_loads(self, client):
        """anasayfa aciliyo mu diye bak"""
        response = client.get('/')
        assert response.status_code == 200
        assert 'Günün Menüsü'.encode('utf-8') in response.data or b'menu' in response.data.lower()
    
    def test_index_shows_daily_menu(self, client, sample_menu_item):
        """menu gorunuyo mu"""
        response = client.get('/')
        assert response.status_code == 200


# rezervasyon testleri

class TestReservation:
    """rezervasyon testleri"""
    
    def test_reservation_page_loads(self, client):
        """rezervasyon sayfasi aciliyo mu"""
        response = client.get('/rezervasyon')
        assert response.status_code == 200
        assert 'Rezervasyon'.encode('utf-8') in response.data
    
    def test_create_reservation(self, client):
        """rezervasyon yapabiliyo muyuz"""
        response = client.post('/rezervasyon', data={
            'name': 'Ahmet Yılmaz',
            'party_size': '4',
            'date_time': '2026-01-20T19:30'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # db de var mi kontrol et
        import app as app_module
        conn = app_module.get_db()
        res = conn.execute('SELECT * FROM reservations WHERE customer_name = ?', ('Ahmet Yılmaz',)).fetchone()
        conn.close()
        
        assert res is not None
        assert res['party_size'] == 4
        assert res['status'] == 'Bekliyor'
    
    def test_reservation_redirects_to_index(self, client):
        """rezervasyon sonrasi anasayfaya donuyo mu"""
        response = client.post('/rezervasyon', data={
            'name': 'Test User',
            'party_size': '2',
            'date_time': '2026-01-25T20:00'
        }, follow_redirects=False)
        
        assert response.status_code == 302
        assert '/' in response.location or 'index' in response.location.lower()


# siparis testleri

class TestOrder:
    """siparis testleri"""
    
    def test_create_order(self, client, sample_menu_item):
        """siparis verebiliyo muyuz"""
        response = client.post('/order', data={
            'table_no': '2',
            'items': 'Test Köfte'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # db de kontrol
        import app as app_module
        conn = app_module.get_db()
        order = conn.execute('SELECT * FROM orders WHERE table_no = ?', (2,)).fetchone()
        table = conn.execute('SELECT * FROM tables WHERE id = ?', (2,)).fetchone()
        conn.close()
        
        assert order is not None
        assert order['status'] == 'Aktif'
        assert order['total_price'] == 85.0
        assert table['status'] == 'Occupied'
    
    def test_empty_order_redirects(self, client):
        """bos siparis gonderince ne oluyo"""
        response = client.post('/order', data={
            'table_no': '1',
            'items': ''
        }, follow_redirects=False)
        
        assert response.status_code == 302
    
    def test_order_calculates_total_price(self, client, sample_menu_item):
        """fiyat dogru hesaplaniyo mu"""
        # bi yemek daha ekle
        import app as app_module
        conn = app_module.get_db()
        cursor = conn.execute(
            'INSERT INTO menu (name, price, category, image) VALUES (?, ?, ?, ?)',
            ('Test Pizza', 120.0, 'Ana Yemek', 'pizza.jpg')
        )
        conn.commit()
        conn.close()
        
        response = client.post('/order', data={
            'table_no': '3',
            'items': 'Test Köfte, Test Pizza'
        }, follow_redirects=True)
        
        conn = app_module.get_db()
        order = conn.execute('SELECT * FROM orders WHERE table_no = ?', (3,)).fetchone()
        conn.close()
        
        assert order['total_price'] == 205.0  # 85 + 120


# giris cikis testleri

class TestAuthentication:
    """login logout testleri"""
    
    def test_login_page_loads(self, client):
        """login sayfasi aciliyo mu"""
        response = client.get('/login')
        assert response.status_code == 200
    
    def test_successful_login(self, client):
        """dogru sifreyle giris"""
        response = client.post('/login', data={
            'password': 'admin123'
        }, follow_redirects=False)
        
        assert response.status_code == 302
        assert 'admin' in response.location
    
    def test_failed_login(self, client):
        """yanlis sifre girince ne oluyo"""
        response = client.post('/login', data={
            'password': 'yanlis_sifre'
        })
        
        assert response.status_code == 200
        assert 'Hatalı'.encode('utf-8') in response.data or b'error' in response.data.lower()
    
    def test_logout(self, logged_in_client):
        """cikis yapinca ne oluyo"""
        response = logged_in_client.get('/logout', follow_redirects=False)
        
        assert response.status_code == 302
        
        # cikis yapinca admine giremezsin
        response = logged_in_client.get('/admin', follow_redirects=False)
        assert response.status_code == 302  # Login'e yönlendirir


# admin panel testleri

class TestAdminPanel:
    """admin paneli testleri"""
    
    def test_admin_requires_login(self, client):
        """giris yapmadan admine gidemezsin"""
        response = client.get('/admin', follow_redirects=False)
        assert response.status_code == 302
        assert 'login' in response.location
    
    def test_admin_accessible_when_logged_in(self, logged_in_client):
        """giris yapinca admin aciliyo mu"""
        response = logged_in_client.get('/admin')
        assert response.status_code == 200
        assert 'Yönetici'.encode('utf-8') in response.data or b'admin' in response.data.lower()
    
    def test_admin_shows_tables(self, logged_in_client):
        """masalar gorunuyo mu"""
        response = logged_in_client.get('/admin')
        assert response.status_code == 200
        assert 'Masa'.encode('utf-8') in response.data


# odeme testleri

class TestPayment:
    """odeme testleri"""
    
    def test_pay_bill_requires_login(self, client, sample_order):
        """odeme icin giris lazim mi"""
        response = client.post('/pay_bill', data={
            'order_id': sample_order,
            'payment_type': 'Nakit'
        }, follow_redirects=False)
        
        assert response.status_code == 302
        assert 'login' in response.location
    
    def test_pay_bill_cash(self, logged_in_client, sample_order):
        """nakit odeme calisiyo mu"""
        response = logged_in_client.post('/pay_bill', data={
            'order_id': str(sample_order),
            'payment_type': 'Nakit'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        # siparis durumuna bak
        import app as app_module
        conn = app_module.get_db()
        order = conn.execute('SELECT * FROM orders WHERE id = ?', (sample_order,)).fetchone()
        table = conn.execute('SELECT * FROM tables WHERE id = ?', (1,)).fetchone()
        conn.close()
        
        assert order['status'] == 'Ödendi'
        assert order['payment_type'] == 'Nakit'
        assert table['status'] == 'Available'
    
    def test_pay_bill_card(self, logged_in_client, sample_order):
        """kartla odeme calisiyo mu"""
        response = logged_in_client.post('/pay_bill', data={
            'order_id': str(sample_order),
            'payment_type': 'Kredi Kartı'
        }, follow_redirects=True)
        
        import app as app_module
        conn = app_module.get_db()
        order = conn.execute('SELECT * FROM orders WHERE id = ?', (sample_order,)).fetchone()
        conn.close()
        
        assert order['payment_type'] == 'Kredi Kartı'


# menu yonetimi testleri

class TestMenuManagement:
    """menu ekleme silme testleri"""
    
    def test_add_menu_item(self, logged_in_client):
        """yemek ekleyebiliyo muyuz"""
        response = logged_in_client.post('/add_item', data={
            'name': 'Yeni Yemek',
            'price': '75',
            'category': 'Ana Yemek',
            'image': 'yeni.jpg',
            'day': 'Tuesday'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        import app as app_module
        conn = app_module.get_db()
        item = conn.execute('SELECT * FROM menu WHERE name = ?', ('Yeni Yemek',)).fetchone()
        daily = conn.execute('SELECT * FROM daily_menu WHERE menu_item_id = ?', (item['id'],)).fetchone()
        conn.close()
        
        assert item is not None
        assert item['price'] == 75.0
        assert daily['day_of_week'] == 'Tuesday'
    
    def test_delete_menu_item(self, logged_in_client, sample_menu_item):
        """yemek silebiliyo muyuz"""
        response = logged_in_client.post(f'/delete_item/{sample_menu_item}', follow_redirects=True)
        
        assert response.status_code == 200
        
        import app as app_module
        conn = app_module.get_db()
        item = conn.execute('SELECT * FROM menu WHERE id = ?', (sample_menu_item,)).fetchone()
        daily = conn.execute('SELECT * FROM daily_menu WHERE menu_item_id = ?', (sample_menu_item,)).fetchone()
        conn.close()
        
        assert item is None
        assert daily is None


# rezervasyon yonetimi

class TestReservationManagement:
    """rezervasyon islemleri testleri"""
    
    def test_delete_reservation(self, logged_in_client, sample_reservation):
        """rezervasyon silebiliyo muyuz"""
        response = logged_in_client.post(f'/delete_reservation/{sample_reservation}', follow_redirects=True)
        
        assert response.status_code == 200
        
        import app as app_module
        conn = app_module.get_db()
        res = conn.execute('SELECT * FROM reservations WHERE id = ?', (sample_reservation,)).fetchone()
        conn.close()
        
        assert res is None
    
    def test_assign_table_to_reservation(self, logged_in_client, sample_reservation):
        """masa atayabiliyo muyuz"""
        response = logged_in_client.post(f'/assign_table/{sample_reservation}', data={
            'table_no': '3'
        }, follow_redirects=True)
        
        assert response.status_code == 200
        
        import app as app_module
        conn = app_module.get_db()
        res = conn.execute('SELECT * FROM reservations WHERE id = ?', (sample_reservation,)).fetchone()
        conn.close()
        
        assert res['status'] == 'Masaya Oturdu'
        assert res['assigned_table'] == 3


# haftalik menu testleri

class TestGeneralMenu:
    """genel menu sayfasi testleri"""
    
    def test_general_menu_page_loads(self, client):
        """haftalik menu sayfasi aciliyo mu"""
        response = client.get('/genel-menu')
        assert response.status_code == 200
    
    def test_general_menu_shows_weekly_items(self, client, sample_menu_item):
        """haftalik yemekler gorunuyo mu"""
        response = client.get('/genel-menu')
        assert response.status_code == 200
        # pazartesi yemegi var mi
        assert 'Pazartesi'.encode('utf-8') in response.data


# yardimci fonksiyon testleri

class TestHelperFunctions:
    """diger fonksiyonlarin testleri"""
    
    def test_get_days_tr(self):
        """gunler turkceye dogru cevrilyo mu"""
        from app import get_days_tr
        
        days = get_days_tr()
        
        assert days['Monday'] == 'Pazartesi'
        assert days['Tuesday'] == 'Salı'
        assert days['Wednesday'] == 'Çarşamba'
        assert days['Thursday'] == 'Perşembe'
        assert days['Friday'] == 'Cuma'
        assert days['Saturday'] == 'Cumartesi'
        assert days['Sunday'] == 'Pazar'
        assert len(days) == 7


# butunlesik testler

class TestIntegration:
    """bastan sona senaryo testleri"""
    
    def test_full_order_flow(self, client, sample_menu_item):
        """siparis ver odeme al tam test"""
        # siparis ver
        client.post('/order', data={
            'table_no': '1',
            'items': 'Test Köfte'
        })
        
        # admin giris
        client.post('/login', data={'password': 'admin123'})
        
        # siparis id al
        import app as app_module
        conn = app_module.get_db()
        order = conn.execute('SELECT * FROM orders WHERE table_no = ?', (1,)).fetchone()
        table_before = conn.execute('SELECT * FROM tables WHERE id = ?', (1,)).fetchone()
        conn.close()
        
        assert order['status'] == 'Aktif'
        assert table_before['status'] == 'Occupied'
        
        # odeme al
        client.post('/pay_bill', data={
            'order_id': str(order['id']),
            'payment_type': 'Nakit'
        })
        
        # kontrol et
        conn = app_module.get_db()
        order_after = conn.execute('SELECT * FROM orders WHERE id = ?', (order['id'],)).fetchone()
        table_after = conn.execute('SELECT * FROM tables WHERE id = ?', (1,)).fetchone()
        conn.close()
        
        assert order_after['status'] == 'Ödendi'
        assert table_after['status'] == 'Available'
    
    def test_full_reservation_flow(self, client):
        """rezervasyon yap masa ata tam test"""
        # rezervasyon yap
        client.post('/rezervasyon', data={
            'name': 'Entegrasyon Test',
            'party_size': '6',
            'date_time': '2026-02-14T20:00'
        })
        
        # admin giris
        client.post('/login', data={'password': 'admin123'})
        
        # rez id al
        import app as app_module
        conn = app_module.get_db()
        res = conn.execute('SELECT * FROM reservations WHERE customer_name = ?', ('Entegrasyon Test',)).fetchone()
        conn.close()
        
        assert res['status'] == 'Bekliyor'
        
        # masa ata
        client.post(f'/assign_table/{res["id"]}', data={'table_no': '5'})
        
        # kontrol et
        conn = app_module.get_db()
        res_after = conn.execute('SELECT * FROM reservations WHERE id = ?', (res['id'],)).fetchone()
        conn.close()
        
        assert res_after['status'] == 'Masaya Oturdu'
        assert res_after['assigned_table'] == 5


# testleri calistir

if __name__ == '__main__':
    pytest.main([__file__, '-v', '--tb=short'])

