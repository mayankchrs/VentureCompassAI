"""
Entry point for AWS Elastic Beanstalk
"""
import os
from app.main import app

# This is the WSGI application that EB will use
application = app

if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run(application, host="0.0.0.0", port=port)