from fastapi import Depends

from app.database.init_db import get_db

session = Depends(get_db)
