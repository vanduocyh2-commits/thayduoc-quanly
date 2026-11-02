import logging,threading
from server import create_app
app=create_app()
def reminder_loop():
 while True:
  try:
   with app.extensions['school_engine'].begin() as db:app.extensions['assignment_reminders'](db)
  except Exception:logging.exception('Assignment reminder check failed')
  threading.Event().wait(60)
threading.Thread(target=reminder_loop,name='assignment-reminders',daemon=True).start()
