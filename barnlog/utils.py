try:
    from asgiref.local import Local as Local
except ImportError:
    from threading import local as Local
