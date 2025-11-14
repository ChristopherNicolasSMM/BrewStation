import os
if os.getenv('FLASK_ENV') == 'DEV':
    from db.dev_database import init_db , db, test_connection 
else:        
    from db.prd_database import init_db , db, test_connection 
    