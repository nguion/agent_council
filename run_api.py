#!/usr/bin/env python3
"""
Run the Agent Council Web API server.
"""

import uvicorn

if __name__ == "__main__":
    print("Starting Agent Council API server...")
    print("API docs available at: http://localhost:8000/docs")
    print("Frontend should connect to: http://localhost:8000")
    
    uvicorn.run(
        "src.web.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,  # Auto-reload on code changes
        log_level="info"
    )
