# utils/threading_utils.py
import threading

def run_in_thread(target, *args, **kwargs):
    """
    Chạy hàm target trong thread riêng, tránh đơ GUI.
    """
    thread = threading.Thread(target=target, args=args, kwargs=kwargs, daemon=True)
    thread.start()
    return thread
