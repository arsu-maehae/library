from django.contrib.staticfiles.testing import StaticLiveServerTestCase
from django.contrib.auth.models import User
from django.utils import timezone
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from datetime import timedelta
import time
from librarian.models import Member, Book, BorrowRecord, Category


class LibraryUserStoryTest(StaticLiveServerTestCase):

    def setUp(self):
        self.browser = webdriver.Chrome()
        self.wait = WebDriverWait(self.browser, 5)

        # สร้างบัญชี admin ของ Sarah ไว้รอในระบบ
        self.sarah = User.objects.create_superuser(
            username='sarah', password='adminpass123'
        )

        # สร้างหนังสือไว้รอในระบบ
        category = Category.objects.create(name='Database')
        self.book = Book.objects.create(
            id=2403000123,
            name='Database System',
            author='Héctor García-Molina',
            category=category,
        )

    def tearDown(self):
        self.browser.quit()

    def sarah_login(self):
        """Sarah ล็อกอินเข้าระบบ admin ใหม่"""
        self.browser.get(self.live_server_url + '/librarian/auth/')
        self.wait.until(EC.presence_of_element_located((By.NAME, 'username')))
        self.browser.find_element(By.NAME, 'username').send_keys('sarah')
        self.browser.find_element(By.NAME, 'password').send_keys('adminpass123')
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)

    def go_admin(self, path):
        """ไปหน้า admin และ login ใหม่ถ้า session หลุด"""
        self.browser.get(self.live_server_url + path)
        time.sleep(0.5)
        if path not in self.browser.current_url:
            self.sarah_login()
            self.browser.get(self.live_server_url + path)
            time.sleep(0.5)

    def test_full_library_story(self):

        # ──────────────────────────────────────────────────────────────────
        # ช่วงเช้า — Sarah ล็อกอินเข้าระบบ admin
        # ──────────────────────────────────────────────────────────────────

        # Sarah เปิดหน้า login ของ admin แล้วล็อกอิน
        self.sarah_login()

        # Sarah ล็อกอินสำเร็จ เห็น navbar ของ admin
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('Books', page_text)

        # ──────────────────────────────────────────────────────────────────
        # Sarah ไปหน้า Users แล้วสร้างสมาชิกใหม่ให้ Alex
        # ──────────────────────────────────────────────────────────────────

        # Sarah ไปหน้า Users
        self.go_admin('/librarian/users/')
        self.assertIn('/librarian/users/', self.browser.current_url)

        # Sarah กดปุ่ม Add User เพื่อเปิด modal
        self.browser.find_element(By.XPATH, "//button[contains(text(), '+ Add User')]").click()

        # รอให้ modal เปิดก่อนกรอก
        ssid_field = self.wait.until(
            EC.visibility_of_element_located((By.CSS_SELECTOR, "#addUserModal [name='ssid']"))
        )

        # Sarah กรอกข้อมูลของ Alex ครบทุกช่อง
        ssid_field.send_keys('65010234')
        self.browser.find_element(By.CSS_SELECTOR, "#addUserModal [name='name']").send_keys('Alex Tan')
        self.browser.find_element(By.CSS_SELECTOR, "#addUserModal [name='email']").send_keys('alex.tan@email.com')
        self.browser.find_element(By.CSS_SELECTOR, "#addUserModal [name='phone']").send_keys('0812345678')

        # Sarah กดปุ่ม Confirm ระบบสร้างสมาชิก Alex เสร็จเรียบร้อย
        self.wait.until(EC.element_to_be_clickable(
            (By.CSS_SELECTOR, "#addUserModal .modal-footer button[type='submit']")
        )).click()
        time.sleep(1)

        # Alex ปรากฏในตารางรายชื่อสมาชิก
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('Alex Tan', page_text)
        self.assertIn('65010234', page_text)

        # ──────────────────────────────────────────────────────────────────
        # คล้อยหลังไม่กี่นาที — Sarah ค้นหา Alex ด้วย SSID
        # ──────────────────────────────────────────────────────────────────

        # Sarah พิมพ์รหัสสมาชิกของ Alex ในช่องค้นหา
        search = self.wait.until(EC.element_to_be_clickable((By.NAME, 'ssid')))
        search.clear()
        search.send_keys('65010234')
        self.browser.find_element(By.XPATH, "//button[text()='Search']").click()
        time.sleep(0.5)

        # ระบบดึงข้อมูล Alex ขึ้นมา Sarah เห็นชื่อและ SSID ในตาราง
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('Alex Tan', page_text)
        self.assertIn('65010234', page_text)

        # ──────────────────────────────────────────────────────────────────
        # Alex หยิบหนังสือมาที่เคาน์เตอร์ — Sarah บันทึกการยืม
        # ──────────────────────────────────────────────────────────────────

        # Sarah ไปหน้า Borrow
        self.go_admin('/librarian/borrow/')
        self.assertIn('/librarian/borrow/', self.browser.current_url)

        # Sarah สแกนบัตรสมาชิกของ Alex → กรอก SSID
        self.browser.find_element(By.NAME, 'ssid').send_keys('65010234')

        # Sarah สแกนบาร์โค้ดหนังสือ → กรอก Book ID
        self.browser.find_element(By.NAME, 'book_id').send_keys('2403000123')

        # Sarah ตั้งระยะเวลายืม 14 วัน (= 2 สัปดาห์)
        duration = self.browser.find_element(By.NAME, 'duration')
        duration.clear()
        duration.send_keys('14')
        Select(self.browser.find_element(By.NAME, 'unit')).select_by_value('days')

        # Sarah กดยืนยัน
        submit_btn = self.browser.find_element(By.XPATH, "//button[text()='Confirm']")
        self.browser.execute_script("arguments[0].scrollIntoView(true);", submit_btn)
        self.browser.execute_script("arguments[0].click();", submit_btn)
        time.sleep(1)

        # Sarah เห็นข้อความยืนยันว่ายืมสำเร็จ
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('Successfully', page_text)

        # ตรวจว่า BorrowRecord ถูกสร้างในฐานข้อมูลจริง
        alex = Member.objects.get(ssid='65010234')
        record = BorrowRecord.objects.get(member=alex, book=self.book)
        self.assertIsNone(record.return_date)
        self.assertEqual(record.due_date, timezone.now().date() + timedelta(days=14))

        # ──────────────────────────────────────────────────────────────────
        # ช่วงบ่าย — Alex นำหนังสือมาคืน Sarah บันทึกการคืน
        # ──────────────────────────────────────────────────────────────────

        # Sarah ไปหน้า Return (re-login อัตโนมัติถ้า session หลุด)
        self.go_admin('/librarian/return/')
        self.assertIn('/librarian/return/', self.browser.current_url)

        # Sarah พิมพ์รหัสสมาชิกของ Alex เพื่อค้นหารายการยืม
        self.browser.find_element(By.NAME, 'ssid').send_keys('65010234')
        # ระบุปุ่ม Search ใน form[method='get'] เท่านั้น ไม่ใช่ปุ่ม Return ใน form[method='post']
        search_btn = self.browser.find_element(
            By.CSS_SELECTOR, "form[method='get'] button[type='submit']"
        )
        self.browser.execute_script("arguments[0].click();", search_btn)
        time.sleep(0.5)

        # Sarah เห็นรายการหนังสือที่ Alex ยืมอยู่
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('Database System', page_text)

        # Sarah กดปุ่ม Return เพื่อบันทึกการคืนหนังสือ
        return_btn = self.browser.find_element(By.XPATH, "//button[text()='Return']")
        self.browser.execute_script("arguments[0].click();", return_btn)
        time.sleep(0.5)

        # ระบบบันทึกวันที่คืนเรียบร้อย
        record.refresh_from_db()
        self.assertIsNotNone(record.return_date)
        self.assertEqual(record.return_date, timezone.now().date())

        # ──────────────────────────────────────────────────────────────────
        # ฝั่งของ Alex — เปิดเว็บดูสถานะการยืมด้วย SSID
        # ──────────────────────────────────────────────────────────────────

        # Alex เปิดเว็บไซต์ห้องสมุดและล็อกอินด้วยรหัสสมาชิก
        self.browser.get(self.live_server_url + '/login/')
        self.browser.find_element(By.ID, 'id_student_id').send_keys('65010234')
        self.browser.find_element(By.CSS_SELECTOR, "button[type='submit']").click()
        time.sleep(0.5)

        # Alex ถูกพาไปหน้า profile เห็น SSID ของตัวเอง
        self.assertIn('/profile/', self.browser.current_url)
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('65010234', page_text)

        # Alex กดดูประวัติการยืมทั้งหมด
        self.browser.find_element(By.PARTIAL_LINK_TEXT, 'History').click()
        time.sleep(0.5)
        self.assertIn('/history/', self.browser.current_url)

        # Alex เห็นหนังสือ Database System ในประวัติ พร้อมวันที่คืนแล้ว
        page_text = self.browser.find_element(By.TAG_NAME, 'body').text
        self.assertIn('Database System', page_text)
        self.assertIn(str(record.return_date.day), page_text)